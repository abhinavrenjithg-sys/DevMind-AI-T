from pathlib import Path
from typing import Dict, List, Any, Optional, Set

class DependencyResolver:
    def __init__(self, files: List[Dict[str, Any]], parsed_results: Dict[str, Dict[str, Any]]):
        self.files = files
        self.parsed_results = parsed_results
        # Fast lookup maps
        self.path_to_file: Dict[str, Dict[str, Any]] = {f["path"]: f for f in files}
        self.clean_path_map: Dict[str, str] = {} # e.g. "app/models" -> "app/models.py"
        self._build_path_map()

        # Build symbol lookup: (file_path, symbol_name) -> symbol dict
        self.symbol_lookup: Dict[str, List[Dict[str, Any]]] = {}
        for path, res in parsed_results.items():
            self.symbol_lookup[path] = res.get("symbols", [])

    def _build_path_map(self):
        for path in self.path_to_file.keys():
            p = Path(path)
            # Store without extension
            stem_path = (p.parent / p.stem).as_posix()
            self.clean_path_map[stem_path] = path
            # Store python module dot format: e.g. "app.models"
            dot_path = stem_path.replace("/", ".")
            self.clean_path_map[dot_path] = path
            if p.name == "__init__.py" or p.stem == "index":
                parent_stem = p.parent.as_posix()
                self.clean_path_map[parent_stem] = path
                self.clean_path_map[parent_stem.replace("/", ".")] = path

    def resolve_dependencies(self) -> List[Dict[str, Any]]:
        """
        Resolves import declarations, call expressions, inheritance, and containment
        into a unified, verified list of dependency edges.
        """
        edges: List[Dict[str, Any]] = []

        for file_info in self.files:
            file_path = file_info["path"]
            file_id = file_info.get("id", file_path)
            res = self.parsed_results.get(file_path, {})
            symbols = res.get("symbols", [])
            imports = res.get("imports", [])
            calls = res.get("calls", [])

            # 1. Containment edges: File contains Symbol
            for sym in symbols:
                sym_id = sym.get("id", f"{file_path}::{sym['qualified_name']}")
                edges.append({
                    "source_type": "file",
                    "source_id": file_id,
                    "source_name": file_path,
                    "target_type": "symbol",
                    "target_id": sym_id,
                    "target_name": sym["qualified_name"],
                    "relationship": "contains",
                    "certainty": "confirmed",
                    "source_line": sym["start_line"]
                })

                # Inheritance edges: class A inherits B
                if sym["kind"] == "class":
                    for param in sym.get("parameters", []):
                        if param.get("type") == "base_class":
                            base_name = param["name"]
                            target_sym, certainty = self._find_symbol(base_name, file_path)
                            edges.append({
                                "source_type": "symbol",
                                "source_id": sym_id,
                                "source_name": sym["qualified_name"],
                                "target_type": "symbol" if target_sym else "external",
                                "target_id": target_sym.get("id") if target_sym else None,
                                "target_name": target_sym.get("qualified_name") if target_sym else base_name,
                                "relationship": "inherits",
                                "certainty": certainty,
                                "source_line": sym["start_line"]
                            })

            # 2. Import edges
            for imp in imports:
                mod = imp["module"]
                sym_name = imp["name"]
                line = imp["line"]
                is_rel = imp.get("is_relative", False)

                resolved_target_file = self._resolve_import_path(file_path, mod, is_rel)

                if resolved_target_file:
                    target_file_id = self.path_to_file[resolved_target_file].get("id", resolved_target_file)
                    # File-to-file import edge
                    edges.append({
                        "source_type": "file",
                        "source_id": file_id,
                        "source_name": file_path,
                        "target_type": "file",
                        "target_id": target_file_id,
                        "target_name": resolved_target_file,
                        "relationship": "import",
                        "certainty": "confirmed",
                        "source_line": line
                    })

                    # If importing a specific symbol, find it
                    target_sym, sym_cert = self._find_symbol_in_file(sym_name, resolved_target_file)
                    if target_sym:
                        edges.append({
                            "source_type": "file",
                            "source_id": file_id,
                            "source_name": file_path,
                            "target_type": "symbol",
                            "target_id": target_sym.get("id", f"{resolved_target_file}::{sym_name}"),
                            "target_name": target_sym["qualified_name"],
                            "relationship": "references",
                            "certainty": "confirmed",
                            "source_line": line
                        })
                else:
                    # External or unresolved import
                    edges.append({
                        "source_type": "file",
                        "source_id": file_id,
                        "source_name": file_path,
                        "target_type": "external_package",
                        "target_id": None,
                        "target_name": mod or sym_name,
                        "relationship": "import",
                        "certainty": "unresolved" if is_rel else "inferred",
                        "source_line": line
                    })

            # 3. Call edges (statically detected calls)
            for call in calls:
                call_name = call["name"]
                line = call["line"]
                caller_sym = self._find_enclosing_symbol(symbols, line)
                target_sym, certainty = self._find_symbol(call_name, file_path)

                if target_sym:
                    edges.append({
                        "source_type": "symbol" if caller_sym else "file",
                        "source_id": caller_sym.get("id") if caller_sym else file_id,
                        "source_name": caller_sym["qualified_name"] if caller_sym else file_path,
                        "target_type": "symbol",
                        "target_id": target_sym.get("id"),
                        "target_name": target_sym["qualified_name"],
                        "relationship": "calls",
                        "certainty": certainty,
                        "source_line": line
                    })

        return edges

    def _resolve_import_path(self, current_file: str, module_str: str, is_relative: bool) -> Optional[str]:
        cur_path = Path(current_file)
        cur_dir = cur_path.parent

        if is_relative or module_str.startswith("."):
            # Resolve relative import
            # e.g. cur_dir="src/api", module_str="../models/user"
            clean_mod = module_str.lstrip(".")
            rel_prefix = module_str[:-len(clean_mod)] if clean_mod else module_str
            up_levels = max(0, len(rel_prefix) - 1)
            target_dir = cur_dir
            for _ in range(up_levels):
                target_dir = target_dir.parent

            clean_slash = clean_mod.replace(".", "/")
            candidates = [
                (target_dir / clean_mod).as_posix() if clean_mod else target_dir.as_posix(),
                (target_dir / clean_slash).as_posix() if clean_slash else target_dir.as_posix()
            ]

            for cand in candidates:
                for ext in [".py", ".ts", ".tsx", ".js", ".jsx", "/__init__.py", "/index.ts", "/index.tsx", "/index.js"]:
                    chk = Path(cand + ext).as_posix()
                    if chk in self.path_to_file:
                        return chk
                if cand in self.clean_path_map:
                    return self.clean_path_map[cand]
                if cand in self.path_to_file:
                    return cand

        # Check absolute project imports e.g. "app.models" or "src/components"
        if module_str in self.clean_path_map:
            return self.clean_path_map[module_str]

        # Try converting dot notation to path
        slash_path = module_str.replace(".", "/")
        if slash_path in self.clean_path_map:
            return self.clean_path_map[slash_path]

        for ext in [".py", ".ts", ".tsx", ".js", ".jsx"]:
            if (slash_path + ext) in self.path_to_file:
                return slash_path + ext

        return None

    def _find_symbol_in_file(self, symbol_name: str, file_path: str) -> tuple[Optional[Dict[str, Any]], str]:
        syms = self.symbol_lookup.get(file_path, [])
        for s in syms:
            if s["name"] == symbol_name or s["qualified_name"] == symbol_name:
                return s, "confirmed"
        return None, "unresolved"

    def _find_symbol(self, symbol_name: str, current_file: str) -> tuple[Optional[Dict[str, Any]], str]:
        # 1. Search locally in the same file
        sym, cert = self._find_symbol_in_file(symbol_name, current_file)
        if sym:
            return sym, cert

        # 2. Search globally by symbol name
        candidates = []
        for path, syms in self.symbol_lookup.items():
            for s in syms:
                if s["name"] == symbol_name:
                    candidates.append(s)

        if len(candidates) == 1:
            return candidates[0], "inferred"

        return None, "unresolved"

    def _find_enclosing_symbol(self, symbols: List[Dict[str, Any]], line: int) -> Optional[Dict[str, Any]]:
        enclosing = None
        for sym in symbols:
            if sym["start_line"] <= line <= sym["end_line"]:
                if enclosing is None or (sym["end_line"] - sym["start_line"] < enclosing["end_line"] - enclosing["start_line"]):
                    enclosing = sym
        return enclosing
