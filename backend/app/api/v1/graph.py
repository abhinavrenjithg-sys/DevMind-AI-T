from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional

from app.core.database import get_db
from app.models import SourceFile, Symbol, DependencyEdge
from app.schemas import DependencyGraphResponse
from app.analysis.graph_engine import GraphEngine

router = APIRouter()

@router.get("/{revision_id}", response_model=DependencyGraphResponse)
async def get_dependency_graph(
    revision_id: str,
    node_type: Optional[str] = "file", # "file", "symbol", "all"
    relationship: Optional[str] = "all", # "import", "calls", "inherits", "contains", "all"
    db: AsyncSession = Depends(get_db)
):
    # 1. Fetch files
    files_res = await db.execute(
        select(SourceFile).where(SourceFile.revision_id == revision_id)
    )
    files = files_res.scalars().all()
    files_data = [
        {
            "id": f.id,
            "path": f.path,
            "file_name": f.file_name,
            "layer": f.layer,
            "lines_of_code": f.lines_of_code
        }
        for f in files
    ]

    # 2. Fetch symbols if node_type is symbol or all
    symbols_data = []
    if node_type in ("symbol", "all"):
        syms_res = await db.execute(
            select(Symbol, SourceFile.path)
            .join(SourceFile, SourceFile.id == Symbol.file_id)
            .where(Symbol.revision_id == revision_id)
            .limit(300) # Cap for visual graph rendering performance
        )
        for s, fpath in syms_res.all():
            symbols_data.append({
                "id": s.id,
                "name": s.name,
                "qualified_name": s.qualified_name,
                "kind": s.kind,
                "file_path": fpath,
                "layer": "General",
                "signature": s.signature
            })

    # 3. Fetch edges
    edges_stmt = select(DependencyEdge).where(DependencyEdge.revision_id == revision_id)
    if relationship and relationship != "all":
        edges_stmt = edges_stmt.where(DependencyEdge.relationship == relationship)

    edges_res = await db.execute(edges_stmt)
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

    engine = GraphEngine(files_data, symbols_data, edges_data)
    flow_data = engine.to_react_flow(filter_type=node_type, filter_relationship=relationship)

    return flow_data
