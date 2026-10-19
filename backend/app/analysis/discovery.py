import os
from pathlib import Path
from typing import Dict, List, Set, Any, Tuple
from app.core.config import settings

class RepositoryDiscovery:
    def __init__(self, repo_path: str):
        self.repo_path = Path(repo_path).resolve()

    def discover_files(self) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """
        Safely enumerates repository files, excluding noise and checking limits.
        Returns list of file descriptors and repository metadata/statistics.
        """
        discovered_files: List[Dict[str, Any]] = []
        languages: Dict[str, int] = {}
        total_loc = 0
        total_size = 0
        file_count = 0

        for root, dirs, files in os.walk(self.repo_path):
            # Prune excluded directories in-place
            dirs[:] = [d for d in dirs if d not in settings.EXCLUDED_DIRS and not d.startswith(".")]

            for file_name in files:
                file_path = Path(root) / file_name
                try:
                    rel_path = file_path.relative_to(self.repo_path).as_posix()
                except ValueError:
                    continue

                # Path traversal check
                resolved_file = file_path.resolve()
                if not str(resolved_file).startswith(str(self.repo_path)):
                    continue

                ext = file_path.suffix.lower()
                if ext not in settings.SUPPORTED_EXTENSIONS:
                    continue

                try:
                    stat = file_path.stat()
                    size_bytes = stat.st_size
                except OSError:
                    continue

                if size_bytes > settings.MAX_FILE_SIZE_BYTES:
                    continue

                file_count += 1
                if file_count > settings.MAX_FILE_COUNT:
                    break

                language = self._detect_language(ext, file_name)
                loc = self._count_lines(file_path)

                total_loc += loc
                total_size += size_bytes
                languages[language] = languages.get(language, 0) + 1

                discovered_files.append({
                    "path": rel_path,
                    "file_name": file_name,
                    "extension": ext,
                    "language": language,
                    "size_bytes": size_bytes,
                    "lines_of_code": loc,
                    "absolute_path": str(resolved_file)
                })

            if file_count > settings.MAX_FILE_COUNT:
                break

        frameworks = self._detect_frameworks(discovered_files)
        entry_points = self._detect_entry_points(discovered_files)

        summary = {
            "total_files": len(discovered_files),
            "total_loc": total_loc,
            "total_size_bytes": total_size,
            "languages": languages,
            "frameworks": frameworks,
            "entry_points": entry_points
        }

        return discovered_files, summary

    def _detect_language(self, ext: str, file_name: str) -> str:
        ext_map = {
            ".py": "python",
            ".pyi": "python",
            ".ts": "typescript",
            ".tsx": "typescript-react",
            ".js": "javascript",
            ".jsx": "javascript-react",
            ".mjs": "javascript",
            ".cjs": "javascript",
            ".json": "json",
            ".yaml": "yaml",
            ".yml": "yaml",
            ".toml": "toml",
            ".md": "markdown",
            ".sql": "sql",
            ".html": "html",
            ".css": "css"
        }
        return ext_map.get(ext, "text")

    def _count_lines(self, file_path: Path) -> int:
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                return sum(1 for _ in f)
        except Exception:
            return 0

    def _detect_frameworks(self, files: List[Dict[str, Any]]) -> List[str]:
        paths = {f["path"].lower() for f in files}
        frameworks = []

        if any("fastapi" in p or "app/main.py" in p for p in paths):
            frameworks.append("FastAPI")
        if any("django" in p or "manage.py" in p for p in paths):
            frameworks.append("Django")
        if any("flask" in p for p in paths):
            frameworks.append("Flask")
        if any("next.config" in p for p in paths):
            frameworks.append("Next.js")
        if any(f["extension"] == ".tsx" for f in files) or any("vite.config" in p for p in paths):
            frameworks.append("React")
        if any("vue" in p for p in paths):
            frameworks.append("Vue")
        if any("package.json" in p for p in paths):
            frameworks.append("Node.js")
        if any("pytest" in p or "test_" in p for p in paths):
            frameworks.append("Pytest")

        return sorted(list(set(frameworks)))

    def _detect_entry_points(self, files: List[Dict[str, Any]]) -> List[str]:
        candidates = [
            "main.py", "app.py", "wsgi.py", "asgi.py", "manage.py",
            "index.ts", "main.ts", "index.tsx", "main.tsx", "index.js", "server.js",
            "app/main.py", "src/main.tsx", "src/index.tsx", "src/index.ts", "src/main.ts"
        ]
        entry_points = []
        for f in files:
            p = f["path"]
            if p in candidates or any(p.endswith(f"/{c}") for c in candidates):
                entry_points.append(p)
        return sorted(entry_points)
