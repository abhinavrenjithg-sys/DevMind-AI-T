import json
import re
import subprocess
from pathlib import Path
from typing import Dict, List, Any

class SecurityAndQualityScanner:
    def __init__(self, repo_path: str, files: List[Dict[str, Any]]):
        self.repo_path = Path(repo_path)
        self.files = files

    def run_all_checks(self) -> List[Dict[str, Any]]:
        """
        Executes static analysis safely without running repository code.
        Runs Ruff, Bandit, and language AST security pattern scanners.
        """
        findings: List[Dict[str, Any]] = []

        # 1. Run Ruff on Python files
        has_python = any(f["extension"] in (".py", ".pyi") for f in self.files)
        if has_python:
            findings.extend(self._run_ruff())
            findings.extend(self._run_bandit())

        # 2. Run TypeScript/JavaScript AST security scanner
        findings.extend(self._scan_javascript_ast())

        # 3. Secret and token scanner across all files
        findings.extend(self._scan_hardcoded_secrets())

        return findings

    def _run_ruff(self) -> List[Dict[str, Any]]:
        findings = []
        try:
            # Run ruff check --output-format json
            res = subprocess.run(
                ["ruff", "check", "--output-format", "json", str(self.repo_path)],
                capture_output=True,
                text=True,
                timeout=30
            )
            raw_out = res.stdout
            if raw_out.strip():
                try:
                    data = json.loads(raw_out)
                    for item in data[:40]: # Cap to top findings
                        filepath = Path(item.get("filename", "")).resolve()
                        try:
                            rel_path = filepath.relative_to(self.repo_path.resolve()).as_posix()
                        except ValueError:
                            rel_path = filepath.name

                        findings.append({
                            "file_path": rel_path,
                            "line_number": item.get("location", {}).get("row", 1),
                            "end_line_number": item.get("end_location", {}).get("row", 1),
                            "tool": "ruff",
                            "rule_id": item.get("code", "RUFF"),
                            "severity": "low" if item.get("code", "").startswith("E") else "medium",
                            "message": item.get("message", "Lint finding"),
                            "code_snippet": None,
                            "is_dismissed": False
                        })
                except json.JSONDecodeError:
                    pass
        except Exception:
            # Ruff might not be in PATH or failed; non-fatal
            pass
        return findings

    def _run_bandit(self) -> List[Dict[str, Any]]:
        findings = []
        try:
            res = subprocess.run(
                ["bandit", "-r", "-f", "json", "-q", str(self.repo_path)],
                capture_output=True,
                text=True,
                timeout=30
            )
            raw_out = res.stdout
            if raw_out.strip():
                try:
                    data = json.loads(raw_out)
                    for item in data.get("results", [])[:30]:
                        filepath = Path(item.get("filename", "")).resolve()
                        try:
                            rel_path = filepath.relative_to(self.repo_path.resolve()).as_posix()
                        except ValueError:
                            rel_path = filepath.name

                        severity_map = {
                            "HIGH": "high",
                            "MEDIUM": "medium",
                            "LOW": "low"
                        }
                        sev = severity_map.get(item.get("issue_severity", "MEDIUM"), "medium")

                        findings.append({
                            "file_path": rel_path,
                            "line_number": item.get("line_number", 1),
                            "end_line_number": item.get("line_range", [1])[-1],
                            "tool": "bandit",
                            "rule_id": item.get("test_id", "B000"),
                            "severity": sev,
                            "message": item.get("issue_text", "Security risk detected"),
                            "code_snippet": item.get("code", "").strip() or None,
                            "is_dismissed": False
                        })
                except json.JSONDecodeError:
                    pass
        except Exception:
            pass
        return findings

    def _scan_javascript_ast(self) -> List[Dict[str, Any]]:
        findings = []
        js_files = [f for f in self.files if f["extension"] in (".ts", ".tsx", ".js", ".jsx")]

        dangerous_patterns = [
            (r"\.innerHTML\s*=", "XSS-INNERHTML", "high", "Direct assignment to innerHTML can lead to Cross-Site Scripting (XSS)."),
            (r"\beval\s*\(", "DANGEROUS-EVAL", "critical", "Execution of eval() poses severe code injection vulnerabilities."),
            (r"new\s+Function\s*\(", "EVAL-LIKE-CONSTRUCTOR", "high", "Function constructor allows arbitrary code execution from strings.")
        ]

        for f in js_files:
            abs_path = self.repo_path / f["path"]
            if not abs_path.exists():
                continue
            try:
                with open(abs_path, "r", encoding="utf-8", errors="ignore") as fp:
                    lines = fp.readlines()
                for line_idx, line in enumerate(lines):
                    for pat, rule_id, sev, msg in dangerous_patterns:
                        if re.search(pat, line):
                            findings.append({
                                "file_path": f["path"],
                                "line_number": line_idx + 1,
                                "end_line_number": line_idx + 1,
                                "tool": "devmind_sec",
                                "rule_id": rule_id,
                                "severity": sev,
                                "message": msg,
                                "code_snippet": line.strip()[:150],
                                "is_dismissed": False
                            })
            except Exception:
                continue
        return findings

    def _scan_hardcoded_secrets(self) -> List[Dict[str, Any]]:
        findings = []
        secret_patterns = [
            (r"(?i)(api_key|apikey|secret_key|client_secret)\s*[:=]\s*['\"][a-zA-Z0-9_\-]{16,}['\"]", "SECRET-KEY-EXPOSURE", "critical", "Possible hardcoded API key or client secret detected."),
            (r"(?i)(password|passwd|pwd)\s*[:=]\s*['\"][^'\"]{6,}['\"]", "HARDCODED-PASSWORD", "high", "Possible hardcoded password detected in source file.")
        ]

        for f in self.files:
            if f.get("language") not in ("python", "typescript", "typescript-react", "javascript", "javascript-react"):
                continue
            abs_path = self.repo_path / f["path"]
            if not abs_path.exists():
                continue
            try:
                with open(abs_path, "r", encoding="utf-8", errors="ignore") as fp:
                    lines = fp.readlines()
                for line_idx, line in enumerate(lines):
                    # Skip test files and comments
                    if "test" in f["path"].lower() or line.strip().startswith(("#", "//", "/*")):
                        continue
                    for pat, rule_id, sev, msg in secret_patterns:
                        if re.search(pat, line):
                            findings.append({
                                "file_path": f["path"],
                                "line_number": line_idx + 1,
                                "end_line_number": line_idx + 1,
                                "tool": "devmind_sec",
                                "rule_id": rule_id,
                                "severity": sev,
                                "message": msg,
                                "code_snippet": re.sub(r"['\"][a-zA-Z0-9_\-]{8,}['\"]", "'[REDACTED]'", line.strip()),
                                "is_dismissed": False
                            })
            except Exception:
                continue
        return findings
