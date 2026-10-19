import re
from pathlib import Path
from typing import Dict, List, Any, Optional

class SearchEngine:
    def __init__(self, repo_path: str, files: List[Dict[str, Any]], symbols: List[Dict[str, Any]]):
        self.repo_path = Path(repo_path)
        self.files = files
        self.symbols = symbols

    def search(
        self,
        query: str,
        search_type: str = "all",
        language: Optional[str] = None,
        layer: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Executes unified code search across symbols, files, and full-text code content.
        """
        results: List[Dict[str, Any]] = []
        q = query.strip()
        if not q:
            return results

        q_lower = q.lower()

        # 1. Symbol Search
        if search_type in ("all", "symbol"):
            for s in self.symbols:
                name = s["name"]
                qname = s.get("qualified_name", name)
                score = 0.0

                if name.lower() == q_lower:
                    score = 100.0
                elif qname.lower() == q_lower:
                    score = 90.0
                elif name.lower().startswith(q_lower):
                    score = 80.0
                elif q_lower in name.lower():
                    score = 60.0
                elif q_lower in (s.get("docstring") or "").lower():
                    score = 30.0

                if score > 0:
                    results.append({
                        "type": "symbol",
                        "title": name,
                        "subtitle": s.get("signature") or s.get("kind"),
                        "file_path": s.get("file_path", ""),
                        "start_line": s["start_line"],
                        "end_line": s["end_line"],
                        "language": self._get_file_language(s.get("file_path", "")),
                        "score": score,
                        "excerpt": s.get("signature") or (s.get("docstring", "")[:120] if s.get("docstring") else None),
                        "symbol_kind": s.get("kind")
                    })

        # 2. File Name Search
        if search_type in ("all", "file"):
            for f in self.files:
                path = f["path"]
                fname = f.get("file_name") or path.split("/")[-1]
                score = 0.0

                if fname.lower() == q_lower:
                    score = 95.0
                elif fname.lower().startswith(q_lower):
                    score = 75.0
                elif q_lower in path.lower():
                    score = 50.0

                if score > 0:
                    results.append({
                        "type": "file",
                        "title": fname,
                        "subtitle": path,
                        "file_path": path,
                        "start_line": 1,
                        "end_line": min(f.get("lines_of_code", 1), 30),
                        "language": f.get("language", "text"),
                        "score": score,
                        "excerpt": f"File: {path} ({f.get('lines_of_code', 0)} LOC, {f.get('layer', 'General')})",
                        "symbol_kind": None
                    })

        # 3. Full-Text Code Search
        if search_type in ("all", "fulltext", "regex"):
            is_regex = (search_type == "regex")
            regex_pat = None
            if is_regex:
                try:
                    regex_pat = re.compile(q, re.IGNORECASE)
                except re.error:
                    regex_pat = None

            for f in self.files:
                if language and f.get("language") != language:
                    continue
                if layer and f.get("layer") != layer:
                    continue

                abs_path = self.repo_path / f["path"]
                if not abs_path.exists():
                    continue

                try:
                    with open(abs_path, "r", encoding="utf-8", errors="ignore") as file_obj:
                        lines = file_obj.readlines()
                except Exception:
                    continue

                for line_idx, line in enumerate(lines):
                    line_num = line_idx + 1
                    matched = False
                    if is_regex and regex_pat:
                        matched = bool(regex_pat.search(line))
                    else:
                        matched = (q_lower in line.lower())

                    if matched:
                        # Extract 3-line context
                        start_ctx = max(0, line_idx - 1)
                        end_ctx = min(len(lines), line_idx + 2)
                        excerpt = "".join(lines[start_ctx:end_ctx]).strip()

                        results.append({
                            "type": "fulltext",
                            "title": f"{f['file_name']}:{line_num}",
                            "subtitle": line.strip()[:100],
                            "file_path": f["path"],
                            "start_line": line_num,
                            "end_line": line_num,
                            "language": f.get("language", "text"),
                            "score": 45.0,
                            "excerpt": excerpt,
                            "symbol_kind": None
                        })

                        if len(results) >= limit * 3:
                            break

        # Filter by language or layer if requested
        if language:
            results = [r for r in results if r["language"] == language]
        if layer:
            # Look up file layer
            file_layer_map = {f["path"]: f.get("layer") for f in self.files}
            results = [r for r in results if file_layer_map.get(r["file_path"]) == layer]

        # Sort by score descending
        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:limit]

    def _get_file_language(self, path: str) -> str:
        for f in self.files:
            if f["path"] == path:
                return f.get("language", "text")
        return "text"
