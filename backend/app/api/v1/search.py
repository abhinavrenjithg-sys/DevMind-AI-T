from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.models import SourceFile, Symbol, RepositoryRevision, Repository
from app.schemas import SearchQuery, SearchResponse, SearchResultItem
from app.analysis.search_engine import SearchEngine

router = APIRouter()

@router.post("/{revision_id}", response_model=SearchResponse)
async def search_code(
    revision_id: str,
    payload: SearchQuery,
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
    files_res = await db.execute(
        select(SourceFile).where(SourceFile.revision_id == revision_id)
    )
    files = files_res.scalars().all()
    files_data = [
        {
            "id": f.id,
            "path": f.path,
            "file_name": f.file_name,
            "language": f.language,
            "lines_of_code": f.lines_of_code,
            "layer": f.layer
        }
        for f in files
    ]

    # Fetch symbols
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
            "signature": s.signature,
            "docstring": s.docstring,
            "start_line": s.start_line,
            "end_line": s.end_line,
            "file_path": fpath
        })

    engine = SearchEngine(repo.local_path, files_data, symbols_data)
    results = engine.search(
        query=payload.query,
        search_type=payload.search_type,
        language=payload.language,
        layer=payload.layer,
        limit=payload.limit
    )

    items = [SearchResultItem.model_validate(r) for r in results]
    return SearchResponse(
        query=payload.query,
        total_results=len(items),
        results=items
    )
