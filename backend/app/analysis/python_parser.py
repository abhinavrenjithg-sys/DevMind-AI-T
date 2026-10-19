import ast
from typing import Dict, List, Any, Optional
import tree_sitter
import tree_sitter_python

class PythonCodeParser:
    def __init__(self):
        try:
            self.ts_lang = tree_sitter.Language(tree_sitter_python.language())
            self.ts_parser = tree_sitter.Parser(self.ts_lang)
        except Exception:
            self.ts_parser = None

    def parse_file(self, content: str, file_path: str) -> Dict[str, Any]:
        """
        Parses a Python file using both Tree-sitter and AST for maximum fidelity.
        Returns extracted symbols, imports, calls, and parse status.
        """
        symbols: List[Dict[str, Any]] = []
        imports: List[Dict[str, Any]] = []
        calls: List[Dict[str, Any]] = []
        parse_status = "parsed"
        error_msg = None

        # 1. Primary AST parsing for deep Python semantics
        try:
            tree = ast.parse(content, filename=file_path)
            symbols, imports, calls = self._extract_from_ast(tree, content)
        except SyntaxError as e:
            parse_status = "syntax_error"
            error_msg = str(e)
            # Fall back to Tree-sitter which can parse partially broken/incomplete syntax
            if self.ts_parser:
                try:
                    ts_tree = self.ts_parser.parse(content.encode("utf-8"))
                    symbols, imports, calls = self._extract_from_tree_sitter(ts_tree, content)
                    parse_status = "tree_sitter_fallback"
                except Exception as ts_err:
                    error_msg = f"AST Error: {e} | TS Error: {ts_err}"
                    parse_status = "failed"
        except Exception as e:
            parse_status = "failed"
            error_msg = str(e)

        return {
            "symbols": symbols,
            "imports": imports,
            "calls": calls,
            "status": parse_status,
            "error": error_msg
        }

    def _extract_from_ast(self, tree: ast.AST, content: str) -> tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]]]:
        symbols: List[Dict[str, Any]] = []
        imports: List[Dict[str, Any]] = []
        calls: List[Dict[str, Any]] = []

        lines = content.splitlines()

        for node in ast.walk(tree):
            # Imports
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append({
                        "module": alias.name,
                        "name": alias.asname or alias.name,
                        "alias": alias.asname,
                        "is_relative": False,
                        "level": 0,
                        "line": getattr(node, "lineno", 1)
                    })
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                level = node.level or 0
                for alias in node.names:
                    imports.append({
                        "module": module,
                        "name": alias.name,
                        "alias": alias.asname,
                        "is_relative": level > 0,
                        "level": level,
                        "line": getattr(node, "lineno", 1)
                    })

            # Calls
            elif isinstance(node, ast.Call):
                call_name = self._get_call_name(node.func)
                if call_name:
                    calls.append({
                        "name": call_name,
                        "line": getattr(node, "lineno", 1)
                    })

        # Top-level and class-level symbol traversal to preserve hierarchy
        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                sym = self._function_to_symbol(node, lines)
                symbols.append(sym)
            elif isinstance(node, ast.ClassDef):
                cls_sym = self._class_to_symbol(node, lines)
                symbols.append(cls_sym)
                for item in node.body:
                    if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        method_sym = self._function_to_symbol(item, lines, parent_class=node.name)
                        symbols.append(method_sym)

        return symbols, imports, calls

    def _get_call_name(self, func_node: ast.AST) -> Optional[str]:
        if isinstance(func_node, ast.Name):
            return func_node.id
        elif isinstance(func_node, ast.Attribute):
            val = self._get_call_name(func_node.value)
            return f"{val}.{func_node.attr}" if val else func_node.attr
        return None

    def _function_to_symbol(self, node: ast.AST, lines: List[str], parent_class: Optional[str] = None) -> Dict[str, Any]:
        name = getattr(node, "name", "unknown")
        start_line = getattr(node, "lineno", 1)
        end_line = getattr(node, "end_lineno", start_line)
        start_col = getattr(node, "col_offset", 0)
        end_col = getattr(node, "end_col_offset", 0)

        is_method = parent_class is not None
        kind = "method" if is_method else "function"
        qualified_name = f"{parent_class}.{name}" if parent_class else name

        docstring = ast.get_docstring(node)

        # Decorators
        decorators = []
        for dec in getattr(node, "decorator_list", []):
            if isinstance(dec, ast.Name):
                decorators.append(dec.id)
            elif isinstance(dec, ast.Attribute):
                decorators.append(f"{self._get_call_name(dec.value)}.{dec.attr}")
            elif isinstance(dec, ast.Call):
                decorators.append(self._get_call_name(dec.func) or "call")

        # Parameters
        parameters = []
        args = getattr(node, "args", None)
        if args:
            for arg in args.args:
                arg_name = arg.arg
                type_ann = ast.unparse(arg.annotation) if arg.annotation else None
                parameters.append({"name": arg_name, "type": type_ann})

        # Return type
        return_type = ast.unparse(node.returns) if getattr(node, "returns", None) else None

        # Build signature string
        param_strs = [p["name"] + (f": {p['type']}" if p["type"] else "") for p in parameters]
        ret_str = f" -> {return_type}" if return_type else ""
        is_async = isinstance(node, ast.AsyncFunctionDef)
        async_str = "async " if is_async else ""
        signature = f"{async_str}def {name}({', '.join(param_strs)}){ret_str}"

        visibility = "private" if name.startswith("_") and not (name.startswith("__") and name.endswith("__")) else "public"

        return {
            "name": name,
            "qualified_name": qualified_name,
            "kind": kind,
            "signature": signature,
            "docstring": docstring,
            "start_line": start_line,
            "end_line": end_line,
            "start_col": start_col,
            "end_col": end_col,
            "visibility": visibility,
            "decorators": decorators,
            "parameters": parameters,
            "return_type": return_type
        }

    def _class_to_symbol(self, node: ast.ClassDef, lines: List[str]) -> Dict[str, Any]:
        name = node.name
        start_line = getattr(node, "lineno", 1)
        end_line = getattr(node, "end_lineno", start_line)
        docstring = ast.get_docstring(node)

        decorators = [self._get_call_name(d) or "dec" for d in getattr(node, "decorator_list", [])]
        bases = [ast.unparse(b) for b in getattr(node, "bases", [])]
        base_str = f"({', '.join(bases)})" if bases else ""
        signature = f"class {name}{base_str}"

        return {
            "name": name,
            "qualified_name": name,
            "kind": "class",
            "signature": signature,
            "docstring": docstring,
            "start_line": start_line,
            "end_line": end_line,
            "start_col": getattr(node, "col_offset", 0),
            "end_col": getattr(node, "end_col_offset", 0),
            "visibility": "public" if not name.startswith("_") else "private",
            "decorators": decorators,
            "parameters": [{"name": b, "type": "base_class"} for b in bases],
            "return_type": None
        }

    def _extract_from_tree_sitter(self, ts_tree: Any, content: str) -> tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]]]:
        symbols: List[Dict[str, Any]] = []
        imports: List[Dict[str, Any]] = []
        calls: List[Dict[str, Any]] = []
        lines = content.splitlines()

        def visit(node: Any, parent_class: Optional[str] = None):
            if node.type == "function_definition":
                name_node = node.child_by_field_name("name")
                if name_node:
                    name = content[name_node.start_byte:name_node.end_byte]
                    start_line = node.start_point[0] + 1
                    end_line = node.end_point[0] + 1
                    kind = "method" if parent_class else "function"
                    q_name = f"{parent_class}.{name}" if parent_class else name
                    symbols.append({
                        "name": name,
                        "qualified_name": q_name,
                        "kind": kind,
                        "signature": f"def {name}(...)",
                        "docstring": None,
                        "start_line": start_line,
                        "end_line": end_line,
                        "start_col": node.start_point[1],
                        "end_col": node.end_point[1],
                        "visibility": "public" if not name.startswith("_") else "private",
                        "decorators": [],
                        "parameters": [],
                        "return_type": None
                    })
            elif node.type == "class_definition":
                name_node = node.child_by_field_name("name")
                if name_node:
                    cls_name = content[name_node.start_byte:name_node.end_byte]
                    symbols.append({
                        "name": cls_name,
                        "qualified_name": cls_name,
                        "kind": "class",
                        "signature": f"class {cls_name}",
                        "docstring": None,
                        "start_line": node.start_point[0] + 1,
                        "end_line": node.end_point[0] + 1,
                        "start_col": node.start_point[1],
                        "end_col": node.end_point[1],
                        "visibility": "public",
                        "decorators": [],
                        "parameters": [],
                        "return_type": None
                    })
                    for child in node.children:
                        visit(child, parent_class=cls_name)
                    return

            for child in node.children:
                visit(child, parent_class=parent_class)

        visit(ts_tree.root_node)
        return symbols, imports, calls
