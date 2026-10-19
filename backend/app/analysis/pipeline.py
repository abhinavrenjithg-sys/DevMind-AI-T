import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Callable
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.analysis.discovery import RepositoryDiscovery
from app.analysis.python_parser import PythonCodeParser
from app.analysis.typescript_parser import TypeScriptCodeParser
from app.analysis.dependency_resolver import DependencyResolver
from app.analysis.graph_engine import GraphEngine
from app.analysis.architecture_inferer import ArchitectureInferer
from app.analysis.security_scanner import SecurityAndQualityScanner
from app.models import (
    Repository, RepositoryRevision, AnalysisJob, SourceFile, Symbol, DependencyEdge, AnalysisFinding,
    generate_uuid
)

class AnalysisPipeline:
    def __init__(self, session: AsyncSession, repo: Repository, revision: RepositoryRevision, job: AnalysisJob):
        self.session = session
        self.repo = repo
        self.revision = revision
        self.job = job
        self.repo_path = Path(repo.local_path).resolve()

        self.py_parser = PythonCodeParser()
        self.ts_parser = TypeScriptCodeParser()
        self.arch_inferer = ArchitectureInferer()

    async def log_stage(self, stage: str, message: str, progress: int):
        self.job.current_stage = stage
        self.job.progress_percentage = progress
        log_entry = {
            "stage": stage,
            "message": message,
            "progress": progress,
            "timestamp": datetime.datetime.utcnow().isoformat()
        }
        logs = list(self.job.stage_logs or [])
        logs.append(log_entry)
        self.job.stage_logs = logs
        await self.session.commit()

    async def run(self) -> Dict[str, Any]:
        """
        Executes the 7-stage repository analysis pipeline.
        """
        self.job.status = "running"
        self.job.started_at = datetime.datetime.utcnow()
        await self.session.commit()

        try:
            # ---------------------------------------------------------
            # Stage 1: Repository Discovery
            # ---------------------------------------------------------
            await self.log_stage("discovery", "Discovering repository files and detecting languages...", 10)
            discovery = RepositoryDiscovery(str(self.repo_path))
            discovered_files, discovery_summary = discovery.discover_files()
            await self.log_stage("discovery", f"Discovered {len(discovered_files)} supported files.", 20)

            # ---------------------------------------------------------
            # Stage 2: Parsing (Tree-sitter & AST)
            # ---------------------------------------------------------
            await self.log_stage("parsing", "Parsing Python and TypeScript source code...", 30)
            parsed_results: Dict[str, Dict[str, Any]] = {}
            for idx, f in enumerate(discovered_files):
                abs_p = Path(f["absolute_path"])
                if not abs_p.exists():
                    continue

                try:
                    with open(abs_p, "r", encoding="utf-8", errors="ignore") as fp:
                        content = fp.read()
                except Exception:
                    continue

                lang = f["language"]
                if lang == "python":
                    parsed_results[f["path"]] = self.py_parser.parse_file(content, f["path"])
                elif lang in ("typescript", "typescript-react", "javascript", "javascript-react"):
                    parsed_results[f["path"]] = self.ts_parser.parse_file(content, f["path"])
                else:
                    parsed_results[f["path"]] = {
                        "symbols": [],
                        "imports": [],
                        "calls": [],
                        "status": "skipped",
                        "error": None
                    }

            # ---------------------------------------------------------
            # Stage 3: Symbol Indexing & Layer Inference
            # ---------------------------------------------------------
            await self.log_stage("indexing", "Indexing symbols and inferring architectural layers...", 45)
            db_files: List[SourceFile] = []
            db_symbols: List[Symbol] = []
            file_layer_map: Dict[str, str] = {}

            for f in discovered_files:
                path = f["path"]
                res = parsed_results.get(path, {})
                symbols_list = res.get("symbols", [])
                imports_list = res.get("imports", [])

                layer, _ = self.arch_inferer.infer_file_layer(path, imports_list, symbols_list)
                file_layer_map[path] = layer
                f["layer"] = layer

                f_id = generate_uuid()
                f["id"] = f_id
                source_file = SourceFile(
                    id=f_id,
                    revision_id=self.revision.id,
                    path=path,
                    file_name=f["file_name"],
                    extension=f["extension"],
                    language=f["language"],
                    size_bytes=f["size_bytes"],
                    lines_of_code=f["lines_of_code"],
                    ast_parse_status=res.get("status", "skipped"),
                    imports_count=len(imports_list),
                    symbols_count=len(symbols_list),
                    layer=layer
                )
                self.session.add(source_file)
                db_files.append(source_file)

            await self.session.flush()

            for f in discovered_files:
                path = f["path"]
                file_id = f["id"]
                res = parsed_results.get(path, {})
                for sym_data in res.get("symbols", []):
                    s_id = generate_uuid()
                    sym_data["id"] = s_id
                    sym_data["file_path"] = path
                    sym = Symbol(
                        id=s_id,
                        file_id=file_id,
                        revision_id=self.revision.id,
                        name=sym_data["name"],
                        qualified_name=sym_data["qualified_name"],
                        kind=sym_data["kind"],
                        signature=sym_data["signature"],
                        docstring=sym_data["docstring"],
                        start_line=sym_data["start_line"],
                        end_line=sym_data["end_line"],
                        start_col=sym_data["start_col"],
                        end_col=sym_data["end_col"],
                        visibility=sym_data["visibility"],
                        decorators=sym_data["decorators"],
                        parameters=sym_data["parameters"],
                        return_type=sym_data["return_type"]
                    )
                    self.session.add(sym)
                    db_symbols.append(sym)

            await self.session.flush()

            # ---------------------------------------------------------
            # Stage 4: Dependency Extraction
            # ---------------------------------------------------------
            await self.log_stage("dependencies", "Resolving imports and function call dependencies...", 60)
            resolver = DependencyResolver(discovered_files, parsed_results)
            resolved_edges = resolver.resolve_dependencies()

            for edge_data in resolved_edges:
                edge = DependencyEdge(
                    revision_id=self.revision.id,
                    source_type=edge_data["source_type"],
                    source_id=str(edge_data["source_id"]),
                    source_name=edge_data["source_name"],
                    target_type=edge_data["target_type"],
                    target_id=str(edge_data["target_id"]) if edge_data["target_id"] else None,
                    target_name=edge_data["target_name"],
                    relationship=edge_data["relationship"],
                    certainty=edge_data["certainty"],
                    source_line=edge_data["source_line"]
                )
                self.session.add(edge)

            # ---------------------------------------------------------
            # Stage 5: Architecture & Graph Engine
            # ---------------------------------------------------------
            await self.log_stage("architecture", "Computing graph centrality, cycles, and blast radiuses...", 75)
            all_symbols_flat = []
            for path, res in parsed_results.items():
                for s in res.get("symbols", []):
                    all_symbols_flat.append(s)

            graph_engine = GraphEngine(discovered_files, all_symbols_flat, resolved_edges)
            cycles = graph_engine.detect_cycles()
            metrics = graph_engine.calculate_metrics()
            arch_overview = self.arch_inferer.generate_overview(discovered_files, cycles)

            # ---------------------------------------------------------
            # Stage 6: Security and Quality Static Analysis
            # ---------------------------------------------------------
            await self.log_stage("security", "Running static analysis (Ruff, Bandit, AST security)...", 85)
            scanner = SecurityAndQualityScanner(str(self.repo_path), discovered_files)
            findings_data = scanner.run_all_checks()

            for fd in findings_data:
                finding = AnalysisFinding(
                    revision_id=self.revision.id,
                    file_path=fd["file_path"],
                    line_number=fd["line_number"],
                    end_line_number=fd.get("end_line_number"),
                    tool=fd["tool"],
                    rule_id=fd["rule_id"],
                    severity=fd["severity"],
                    message=fd["message"],
                    code_snippet=fd.get("code_snippet"),
                    is_dismissed=False
                )
                self.session.add(finding)

            # ---------------------------------------------------------
            # Stage 7: Reporting and Finalization
            # ---------------------------------------------------------
            await self.log_stage("reporting", "Finalizing architecture report and statistics...", 95)
            summary_stats = {
                "total_files": len(discovered_files),
                "total_loc": discovery_summary["total_loc"],
                "total_size_bytes": discovery_summary["total_size_bytes"],
                "total_symbols": len(db_symbols),
                "total_edges": len(resolved_edges),
                "total_findings": len(findings_data),
                "languages": discovery_summary["languages"],
                "frameworks": discovery_summary["frameworks"],
                "entry_points": discovery_summary["entry_points"],
                "cycle_count": len(cycles),
                "layers": arch_overview["layer_counts"]
            }

            self.revision.summary_stats = summary_stats
            self.repo.is_analyzed = True

            self.job.status = "completed"
            self.job.progress_percentage = 100
            self.job.completed_at = datetime.datetime.utcnow()
            await self.log_stage("completed", "Repository analysis successfully completed.", 100)

            await self.session.commit()
            return summary_stats

        except Exception as e:
            self.job.status = "failed"
            self.job.error_message = str(e)
            self.job.completed_at = datetime.datetime.utcnow()
            await self.log_stage("failed", f"Analysis failed: {e}", self.job.progress_percentage)
            await self.session.commit()
            raise
