from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.models import RepositoryRevision, SourceFile, Symbol, DependencyEdge
from app.schemas import RevisionCompareRequest, RevisionCompareResponse, SymbolResponse
from app.analysis.diff_comparator import RevisionComparator

router = APIRouter()

@router.post("/revisions", response_model=RevisionCompareResponse)
async def compare_revisions(
    payload: RevisionCompareRequest,
    db: AsyncSession = Depends(get_db)
):
    # Fetch base revision
    base_res = await db.execute(select(RepositoryRevision).where(RepositoryRevision.id == payload.base_revision_id))
    base_rev = base_res.scalar_one_or_none()
    if not base_rev:
        raise HTTPException(status_code=404, detail="Base revision not found")

    target_res = await db.execute(select(RepositoryRevision).where(RepositoryRevision.id == payload.target_revision_id))
    target_rev = target_res.scalar_one_or_none()
    if not target_rev:
        raise HTTPException(status_code=404, detail="Target revision not found")

    async def get_rev_data(rev_id: str, commit_hash: str):
        files_res = await db.execute(select(SourceFile).where(SourceFile.revision_id == rev_id))
        files = [{"path": f.path, "lines_of_code": f.lines_of_code} for f in files_res.scalars().all()]

        syms_res = await db.execute(
            select(Symbol, SourceFile.path)
            .join(SourceFile, SourceFile.id == Symbol.file_id)
            .where(Symbol.revision_id == rev_id)
        )
        symbols = []
        for s, fpath in syms_res.all():
            sr = SymbolResponse.model_validate(s)
            sr.file_path = fpath
            symbols.append(sr.model_dump())

        edges_res = await db.execute(select(DependencyEdge).where(DependencyEdge.revision_id == rev_id))
        edges = edges_res.scalars().all()

        return {
            "commit_hash": commit_hash,
            "files": files,
            "symbols": symbols,
            "edges": edges
        }

    base_data = await get_rev_data(base_rev.id, base_rev.commit_hash)
    target_data = await get_rev_data(target_rev.id, target_rev.commit_hash)

    comparator = RevisionComparator()
    diff_result = comparator.compare_revisions(base_data, target_data)

    return RevisionCompareResponse(
        base_commit=diff_result["base_commit"],
        target_commit=diff_result["target_commit"],
        changed_files=diff_result["changed_files"],
        added_symbols=[SymbolResponse(**s) for s in diff_result["added_symbols"]],
        removed_symbols=[SymbolResponse(**s) for s in diff_result["removed_symbols"]],
        modified_symbols=diff_result["modified_symbols"],
        edge_diff=diff_result["edge_diff"],
        impacted_modules=diff_result["impacted_modules"],
        related_tests=diff_result["related_tests"]
    )
