from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.models import SourceFile, Symbol, DependencyEdge
from app.schemas import ChangeImpactRequest, ChangeImpactResponse, DependentItem
from app.analysis.graph_engine import GraphEngine
from app.analysis.impact_analyzer import ChangeImpactAnalyzer

router = APIRouter()

@router.post("/{revision_id}/analyze", response_model=ChangeImpactResponse)
async def analyze_change_impact(
    revision_id: str,
    payload: ChangeImpactRequest,
    db: AsyncSession = Depends(get_db)
):
    # 1. Fetch files
    files_res = await db.execute(select(SourceFile).where(SourceFile.revision_id == revision_id))
    files = files_res.scalars().all()
    files_data = [
        {"id": f.id, "path": f.path, "file_name": f.file_name, "lines_of_code": f.lines_of_code, "layer": f.layer}
        for f in files
    ]

    # 2. Fetch symbols
    syms_res = await db.execute(
        select(Symbol, SourceFile.path)
        .join(SourceFile, SourceFile.id == Symbol.file_id)
        .where(Symbol.revision_id == revision_id)
    )
    symbols_data = []
    for s, fpath in syms_res.all():
        symbols_data.append({
            "id": s.id,
            "name": s.name,
            "qualified_name": s.qualified_name,
            "kind": s.kind,
            "file_path": fpath,
            "signature": s.signature
        })

    # 3. Fetch edges
    edges_res = await db.execute(select(DependencyEdge).where(DependencyEdge.revision_id == revision_id))
    edges = edges_res.scalars().all()
    edges_data = [
        {
            "source_id": e.source_id,
            "source_name": e.source_name,
            "source_type": e.source_type,
            "target_id": e.target_id,
            "target_name": e.target_name,
            "target_type": e.target_type,
            "relationship": e.relationship,
            "certainty": e.certainty,
            "source_line": e.source_line
        }
        for e in edges
    ]

    graph_engine = GraphEngine(files_data, symbols_data, edges_data)
    analyzer = ChangeImpactAnalyzer(graph_engine, files_data, symbols_data)

    target_id = payload.symbol_id
    if not target_id:
        if payload.symbol_name:
            for s in symbols_data:
                if s["name"] == payload.symbol_name or s["qualified_name"] == payload.symbol_name:
                    target_id = s["id"]
                    break
        elif payload.file_path:
            for f in files_data:
                if f["path"] == payload.file_path:
                    target_id = f["id"]
                    break

    if not target_id and files_data:
        # Default to first file or entry point
        target_id = files_data[0]["id"]

    if not target_id:
        raise HTTPException(status_code=400, detail="Target symbol or file could not be identified")

    result = analyzer.analyze_symbol_impact(target_id, depth=payload.depth or 3)

    return ChangeImpactResponse(
        target_name=result["target_name"],
        target_path=result["target_path"],
        blast_radius_depth=result["blast_radius_depth"],
        summary=result["summary"],
        direct_dependents=[DependentItem(**d) for d in result["direct_dependents"]],
        transitive_dependents=[DependentItem(**t) for t in result["transitive_dependents"]],
        affected_tests=result["affected_tests"],
        candidate_review_areas=result["candidate_review_areas"],
        graph_blast_radius=result["graph_blast_radius"]
    )
