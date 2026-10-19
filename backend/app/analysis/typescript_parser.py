from typing import Dict, List, Any, Optional
import tree_sitter
import tree_sitter_typescript

class TypeScriptCodeParser:
    def __init__(self):
        try:
            self.ts_lang = tree_sitter.Language(tree_sitter_typescript.language_typescript())
            self.tsx_lang = tree_sitter.Language(tree_sitter_typescript.language_tsx())
            self.ts_parser = tree_sitter.Parser(self.ts_lang)
            self.tsx_parser = tree_sitter.Parser(self.tsx_lang)
        except Exception:
            self.ts_parser = None
            self.tsx_parser = None

    def parse_file(self, content: str, file_path: str) -> Dict[str, Any]:
        """
        Parses TypeScript / TSX / JavaScript files using Tree-sitter.
        Extracts functions, arrow functions, classes, interfaces, types, imports, and calls.
        """
        symbols: List[Dict[str, Any]] = []
        imports: List[Dict[str, Any]] = []
        calls: List[Dict[str, Any]] = []
        parse_status = "parsed"
        error_msg = None

        parser = self.tsx_parser if file_path.endswith((".tsx", ".jsx")) else self.ts_parser
        if not parser:
            return {
                "symbols": symbols,
                "imports": imports,
                "calls": calls,
                "status": "parser_unavailable",
                "error": "Tree-sitter TypeScript parser not initialized"
            }

        try:
            content_bytes = content.encode("utf-8")
            tree = parser.parse(content_bytes)
            symbols, imports, calls = self._extract_from_tree(tree.root_node, content_bytes)
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

    def _get_node_text(self, node: Any, content_bytes: bytes) -> str:
        return content_bytes[node.start_byte:node.end_byte].decode("utf-8", errors="ignore")

    def _extract_from_tree(self, root_node: Any, content_bytes: bytes) -> tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]]]:
        symbols: List[Dict[str, Any]] = []
        imports: List[Dict[str, Any]] = []
        calls: List[Dict[str, Any]] = []

        def visit(node: Any, parent_class: Optional[str] = None):
            node_type = node.type

            # Imports: import { a, b } from './module'
            if node_type == "import_statement":
                source_node = node.child_by_field_name("source")
                module_name = ""
                if source_node:
                    module_name = self._get_node_text(source_node, content_bytes).strip("'\"`")
                
                # Check for import clauses
                import_clause = None
                for child in node.children:
                    if child.type == "import_clause":
                        import_clause = child
                        break
                
                imported_names = []
                if import_clause:
                    for child in import_clause.children:
                        if child.type == "identifier":
                            imported_names.append(self._get_node_text(child, content_bytes))
                        elif child.type == "named_imports":
                            for spec in child.children:
                                if spec.type == "import_specifier":
                                    name_node = spec.child_by_field_name("name")
                                    if name_node:
                                        imported_names.append(self._get_node_text(name_node, content_bytes))

                if not imported_names:
                    imported_names = [module_name.split("/")[-1]]

                line = node.start_point[0] + 1
                for name in imported_names:
                    imports.append({
                        "module": module_name,
                        "name": name,
                        "alias": None,
                        "is_relative": module_name.startswith("."),
                        "level": module_name.count("..") if module_name.startswith("..") else (1 if module_name.startswith(".") else 0),
                        "line": line
                    })

            # Function Declarations: function foo(...)
            elif node_type == "function_declaration":
                name_node = node.child_by_field_name("name")
                if name_node:
                    name = self._get_node_text(name_node, content_bytes)
                    params_node = node.child_by_field_name("parameters")
                    params_str = self._get_node_text(params_node, content_bytes) if params_node else "()"
                    ret_node = node.child_by_field_name("return_type")
                    ret_str = self._get_node_text(ret_node, content_bytes) if ret_node else ""
                    sig = f"function {name}{params_str}{ret_str}"

                    symbols.append({
                        "name": name,
                        "qualified_name": f"{parent_class}.{name}" if parent_class else name,
                        "kind": "method" if parent_class else "function",
                        "signature": sig,
                        "docstring": None,
                        "start_line": node.start_point[0] + 1,
                        "end_line": node.end_point[0] + 1,
                        "start_col": node.start_point[1],
                        "end_col": node.end_point[1],
                        "visibility": "public" if not name.startswith("_") else "private",
                        "decorators": [],
                        "parameters": [],
                        "return_type": ret_str.replace(":", "").strip() if ret_str else None
                    })

            # Arrow Function assigned to const/let: const foo = () => ...
            elif node_type in ("lexical_declaration", "variable_declaration"):
                for decl in node.children:
                    if decl.type == "variable_declarator":
                        name_node = decl.child_by_field_name("name")
                        val_node = decl.child_by_field_name("value")
                        if name_node and val_node and val_node.type in ("arrow_function", "function_expression"):
                            name = self._get_node_text(name_node, content_bytes)
                            sig = f"const {name} = () => ..."
                            symbols.append({
                                "name": name,
                                "qualified_name": f"{parent_class}.{name}" if parent_class else name,
                                "kind": "function",
                                "signature": sig,
                                "docstring": None,
                                "start_line": node.start_point[0] + 1,
                                "end_line": node.end_point[0] + 1,
                                "start_col": node.start_point[1],
                                "end_col": node.end_point[1],
                                "visibility": "public" if not name.startswith("_") else "private",
                                "decorators": [],
                                "parameters": [],
                                "return_type": None
                            })

            # Class Declaration: class Foo extends Bar
            elif node_type == "class_declaration":
                name_node = node.child_by_field_name("name")
                if name_node:
                    cls_name = self._get_node_text(name_node, content_bytes)
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
                    # Visit class body methods
                    body_node = node.child_by_field_name("body")
                    if body_node:
                        for item in body_node.children:
                            if item.type == "method_definition":
                                m_name_node = item.child_by_field_name("name")
                                if m_name_node:
                                    m_name = self._get_node_text(m_name_node, content_bytes)
                                    symbols.append({
                                        "name": m_name,
                                        "qualified_name": f"{cls_name}.{m_name}",
                                        "kind": "method",
                                        "signature": f"{m_name}()",
                                        "docstring": None,
                                        "start_line": item.start_point[0] + 1,
                                        "end_line": item.end_point[0] + 1,
                                        "start_col": item.start_point[1],
                                        "end_col": item.end_point[1],
                                        "visibility": "public" if not m_name.startswith("_") else "private",
                                        "decorators": [],
                                        "parameters": [],
                                        "return_type": None
                                    })
                        return

            # Interface Declaration: interface User { ... }
            elif node_type == "interface_declaration":
                name_node = node.child_by_field_name("name")
                if name_node:
                    name = self._get_node_text(name_node, content_bytes)
                    symbols.append({
                        "name": name,
                        "qualified_name": name,
                        "kind": "interface",
                        "signature": f"interface {name}",
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

            # Type Alias: type ID = string | number
            elif node_type == "type_alias_declaration":
                name_node = node.child_by_field_name("name")
                if name_node:
                    name = self._get_node_text(name_node, content_bytes)
                    symbols.append({
                        "name": name,
                        "qualified_name": name,
                        "kind": "type_alias",
                        "signature": f"type {name} = ...",
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

            # Function Call: foo(...)
            elif node_type == "call_expression":
                func_node = node.child_by_field_name("function")
                if func_node:
                    func_text = self._get_node_text(func_node, content_bytes)
                    calls.append({
                        "name": func_text,
                        "line": node.start_point[0] + 1
                    })

            for child in node.children:
                visit(child, parent_class=parent_class)

        visit(root_node)
        return symbols, imports, calls
