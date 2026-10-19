import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.models import RepositoryRevision, Repository, SourceFile, Symbol, DependencyEdge, AnalysisFinding
from app.schemas import ArchitectureReportResponse
from app.analysis.graph_engine import GraphEngine

router = APIRouter()

@router.get("/{revision_id}/architecture", response_model=ArchitectureReportResponse)
async def generate_architecture_report(
    revision_id: str,
    db: AsyncSession = Depends(get_db)
):
    rev_res = await db.execute(
        select(RepositoryRevision, Repository)
        .join(Repository, Repository.id == RepositoryRevision.repository_id)
        .where(RepositoryRevision.id == revision_id)
    )
    row = rev_res.first()
    if not row:
        raise HTTPException(status_code=404, detail="Revision not found")
    rev, repo = row

    # Fetch files
    files_res = await db.execute(select(SourceFile).where(SourceFile.revision_id == revision_id))
    files = files_res.scalars().all()
    files_data = [
        {"id": f.id, "path": f.path, "file_name": f.file_name, "language": f.language, "lines_of_code": f.lines_of_code, "layer": f.layer}
        for f in files
    ]

    # Fetch symbols
    syms_res = await db.execute(select(Symbol).where(Symbol.revision_id == revision_id))
    symbols = syms_res.scalars().all()

    # Fetch edges
    edges_res = await db.execute(select(DependencyEdge).where(DependencyEdge.revision_id == revision_id))
    edges = edges_res.scalars().all()
    edges_data = [
        {"source_id": e.source_id, "source_name": e.source_name, "source_type": e.source_type, "target_id": e.target_id, "target_name": e.target_name, "target_type": e.target_type, "relationship": e.relationship}
        for e in edges
    ]

    # Fetch findings
    findings_res = await db.execute(select(AnalysisFinding).where(AnalysisFinding.revision_id == revision_id))
    findings = findings_res.scalars().all()

    # Compute graph metrics
    graph_engine = GraphEngine(files_data, [], edges_data)
    metrics = graph_engine.calculate_metrics()
    cycles = graph_engine.detect_cycles()

    # Languages
    lang_dist = {}
    for f in files:
        lang_dist[f.language] = lang_dist.get(f.language, 0) + 1

    # Layers
    layers = {}
    for f in files:
        layers.setdefault(f.layer, []).append(f.path)

    # Top Central Modules
    top_central = []
    for f in files_data:
        m = metrics.get(f["id"], {})
        top_central.append({
            "path": f["path"],
            "in_degree": m.get("in_degree", 0),
            "out_degree": m.get("out_degree", 0),
            "centrality": m.get("centrality", 0.0)
        })
    top_central.sort(key=lambda x: x["in_degree"] + x["centrality"], reverse=True)
    top_central = top_central[:8]

    # Entry points
    entry_points = rev.summary_stats.get("entry_points", []) if rev.summary_stats else []

    # Security Summary
    security_summary = {"critical": 0, "high": 0, "medium": 0, "low": 0}
    for fd in findings:
        if not fd.is_dismissed:
            s = fd.severity.lower()
            security_summary[s] = security_summary.get(s, 0) + 1

    limitations = [
        "Static analysis may not capture runtime dynamic imports or reflection-driven calls.",
        "External dependencies are indexed as unresolved unless vendor typings are present.",
        "Graph centrality indicates structural coupling and does not directly equate to business criticality.",
        "Private repositories or local-only configurations are bounded by local execution permissions."
    ]

    # Render Markdown Report
    total_loc = sum(f["lines_of_code"] for f in files_data)
    md_lines = [
        f"# DevMind AI Architecture Report: {repo.name}",
        f"\n**Commit Hash:** `{rev.commit_hash}` | **Analyzed At:** {datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}",
        "\n---\n",
        "## 1. Executive Summary",
        f"- **Repository:** `{repo.name}` ({repo.source_type})",
        f"- **Total Source Files:** {len(files_data):,}",
        f"- **Total Lines of Code:** {total_loc:,}",
        f"- **Discovered Symbols:** {len(symbols):,}",
        f"- **Extracted Dependency Edges:** {len(edges):,}",
        f"- **Circular Dependencies Detected:** {len(cycles)}",
        "\n## 2. Architectural Layers",
    ]

    for layer_name, layer_files in sorted(layers.items()):
        md_lines.append(f"### {layer_name} ({len(layer_files)} files)")
        for lf in layer_files[:5]:
            md_lines.append(f"- `{lf}`")
        if len(layer_files) > 5:
            md_lines.append(f"- *...and {len(layer_files) - 5} more files*")

    md_lines.append("\n## 3. Top Structurally Central Modules")
    md_lines.append("| Module | In-Degree (Dependents) | Out-Degree | Centrality Score |")
    md_lines.append("|---|---|---|---|")
    for tc in top_central:
        md_lines.append(f"| `{tc['path']}` | {tc['in_degree']} | {tc['out_degree']} | {tc['centrality']} |")

    if cycles:
        md_lines.append("\n## 4. Circular Dependencies (Warning)")
        for idx, cycle in enumerate(cycles):
            md_lines.append(f"- **Cycle #{idx + 1}:** {' -> '.join(cycle)}")
    else:
        md_lines.append("\n## 4. Circular Dependencies\n- No circular dependency cycles detected.")

    md_lines.append("\n## 5. Security & Static Analysis Overview")
    md_lines.append(f"- Critical: **{security_summary.get('critical', 0)}**")
    md_lines.append(f"- High: **{security_summary.get('high', 0)}**")
    md_lines.append(f"- Medium: **{security_summary.get('medium', 0)}**")
    md_lines.append(f"- Low: **{security_summary.get('low', 0)}**")

    md_lines.append("\n## 6. Analysis Methodology & Limitations")
    for lim in limitations:
        md_lines.append(f"- {lim}")

    md_report = "\n".join(md_lines)

    return ArchitectureReportResponse(
        repository_name=repo.name,
        analyzed_commit=rev.commit_hash,
        analyzed_at=datetime.datetime.utcnow(),
        metrics={
            "total_files": len(files_data),
            "total_loc": total_loc,
            "total_symbols": len(symbols),
            "total_edges": len(edges)
        },
        languages=lang_dist,
        layers=layers,
        entry_points=[{"path": ep} for ep in entry_points],
        central_modules=top_central,
        circular_dependencies=cycles,
        security_summary=security_summary,
        limitations=limitations,
        markdown_report=md_report
    )
