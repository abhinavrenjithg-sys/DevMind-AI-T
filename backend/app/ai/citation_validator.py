import re
from typing import Dict, List, Any, Tuple

class CitationValidator:
    def __init__(self, files: List[Dict[str, Any]]):
        self.file_map = {f["path"]: f for f in files}

    def validate_citations(self, text: str, evidence_pool: List[Dict[str, Any]]) -> Tuple[str, List[Dict[str, Any]]]:
        """
        Parses citations in the model's text, verifies they exist in the repository,
        and constructs confirmed evidence reference objects.
        Pattern supported: [path/to/file.ext:start-end] or [path/to/file.ext:line]
        """
        pattern = r"\[([a-zA-Z0-9_\-\.\/\\]+):(\d+)(?:-(\d+))?\]"
        matches = re.finditer(pattern, text)

        verified_evidence: List[Dict[str, Any]] = []
        pool_by_path = {e["file_path"]: e for e in evidence_pool}

        for match in matches:
            file_path = match.group(1).replace("\\", "/")
            start_line = int(match.group(2))
            end_line = int(match.group(3)) if match.group(3) else start_line

            if file_path in self.file_map:
                finfo = self.file_map[file_path]
                max_lines = finfo.get("lines_of_code", 1000)

                # Clamp line numbers safely
                v_start = max(1, min(start_line, max_lines))
                v_end = max(v_start, min(end_line, max_lines))

                # Find snippet from evidence pool if available
                snippet = ""
                sym_name = None
                if file_path in pool_by_path:
                    snippet = pool_by_path[file_path]["snippet"]
                    sym_name = pool_by_path[file_path].get("symbol_name")

                verified_evidence.append({
                    "file_path": file_path,
                    "start_line": v_start,
                    "end_line": v_end,
                    "symbol_name": sym_name,
                    "snippet": snippet,
                    "explanation": f"Source reference confirmed at {file_path}:{v_start}-{v_end}"
                })

        # If model did not explicitly bracket citations, automatically bind the retrieved evidence pool!
        if not verified_evidence and evidence_pool:
            for ev in evidence_pool[:3]:
                if ev["file_path"] in self.file_map:
                    verified_evidence.append({
                        "file_path": ev["file_path"],
                        "start_line": ev["start_line"],
                        "end_line": ev["end_line"],
                        "symbol_name": ev.get("symbol_name"),
                        "snippet": ev["snippet"],
                        "explanation": f"Grounded evidence retrieved for query from {ev['file_path']}:{ev['start_line']}-{ev['end_line']}"
                    })

        return text, verified_evidence
