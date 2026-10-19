from pathlib import Path
from typing import Dict, List, Any, Optional
import re
from app.analysis.search_engine import SearchEngine

class CodebaseRetriever:
    def __init__(self, repo_path: str, files: List[Dict[str, Any]], symbols: List[Dict[str, Any]]):
        self.repo_path = Path(repo_path)
        self.files = files
        self.symbols = symbols
        self.search_engine = SearchEngine(repo_path, files, symbols)

    def retrieve_context(self, question: str, max_snippets: int = 6) -> List[Dict[str, Any]]:
        """
        Retrieves relevant source code fragments and symbol declarations
        with verified line numbers and file paths.
        """
        keywords = self._extract_keywords(question)
        candidates: List[Dict[str, Any]] = []
        seen_ranges = set()

        for kw in keywords[:4]:
            results = self.search_engine.search(kw, search_type="all", limit=5)
            for r in results:
                fpath = r["file_path"]
                start = max(1, r["start_line"] - 2)
                end = min(r["end_line"] + 5, self._get_file_line_count(fpath))

                range_key = f"{fpath}:{start}-{end}"
                if range_key in seen_ranges:
                    continue
                seen_ranges.add(range_key)

                snippet = self._read_file_range(fpath, start, end)
                if snippet:
                    candidates.append({
                        "file_path": fpath,
                        "start_line": start,
                        "end_line": end,
                        "symbol_name": r["title"] if r["type"] == "symbol" else None,
                        "snippet": snippet,
                        "score": r["score"],
                        "relevance_keyword": kw
                    })

        # Rank by score and return top snippets
        candidates.sort(key=lambda x: x["score"], reverse=True)
        return candidates[:max_snippets]

    def _extract_keywords(self, text: str) -> List[str]:
        # Strip common stop words
        stops = {
            "how", "does", "where", "is", "the", "a", "an", "what", "which",
            "in", "on", "for", "of", "and", "or", "to", "work", "show", "me",
            "explain", "tell", "find", "can", "you", "call", "calls", "used"
        }
        words = re.findall(r"[a-zA-Z0-9_\.]+", text)
        keywords = [w for w in words if w.lower() not in stops and len(w) > 2]
        # Keep original case for symbol names e.g. "User", "AuthService"
        return keywords or words[:3]

    def _get_file_line_count(self, file_path: str) -> int:
        for f in self.files:
            if f["path"] == file_path:
                return f.get("lines_of_code", 100)
        return 500

    def _read_file_range(self, file_path: str, start: int, end: int) -> Optional[str]:
        abs_p = self.repo_path / file_path
        if not abs_p.exists():
            return None
        try:
            with open(abs_p, "r", encoding="utf-8", errors="ignore") as fp:
                lines = fp.readlines()
            sliced = lines[max(0, start - 1):end]
            numbered = [f"{start + i:4d} | {line}" for i, line in enumerate(sliced)]
            return "".join(numbered).strip()
        except Exception:
            return None
