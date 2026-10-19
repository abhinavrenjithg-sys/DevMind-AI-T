import shutil
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
import aiofiles

from app.core.database import get_db
from app.core.config import settings
from app.models import Repository, RepositoryRevision, Workspace, AnalysisJob
from app.schemas import RepositoryImportGit, RepositoryResponse
from app.services.ingestion import RepositoryIngestionService, IngestionSecurityError

router = APIRouter()
ingestion_service = RepositoryIngestionService()

@router.post("/import-git", response_model=RepositoryResponse)
async def import_git_repository(payload: RepositoryImportGit, db: AsyncSession = Depends(get_db)):
    # Verify workspace
    ws_res = await db.execute(select(Workspace).where(Workspace.id == payload.workspace_id))
    if not ws_res.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Workspace not found")

    repo = Repository(
        workspace_id=payload.workspace_id,
        name=payload.name,
        source_type="git_url",
        remote_url=payload.git_url,
        local_path="",
        default_branch=payload.branch or "main",
        is_analyzed=False
    )
    db.add(repo)
    await db.flush()

    try:
        clone_meta = ingestion_service.clone_git_repository(
            payload.git_url, repo.id, branch=payload.branch
        )
    except IngestionSecurityError as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

    repo.local_path = clone_meta["local_path"]
    repo.default_branch = clone_meta["branch_name"]

    revision = RepositoryRevision(
        repository_id=repo.id,
        commit_hash=clone_meta["commit_hash"],
        branch_name=clone_meta["branch_name"],
        commit_message=clone_meta["commit_message"],
        author=clone_meta["author"],
        committed_at=clone_meta["committed_at"],
        is_active=True
    )
    db.add(revision)
    await db.commit()
    await db.refresh(repo)

    resp = RepositoryResponse.model_validate(repo)
    resp.active_revision_id = revision.id
    return resp

@router.post("/upload-zip", response_model=RepositoryResponse)
async def upload_zip_repository(
    workspace_id: str = Form(...),
    name: str = Form(...),
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db)
):
    ws_res = await db.execute(select(Workspace).where(Workspace.id == workspace_id))
    if not ws_res.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Workspace not found")

    if not file.filename.lower().endswith(".zip"):
        raise HTTPException(status_code=400, detail="Only .zip repository archives are supported")

    repo = Repository(
        workspace_id=workspace_id,
        name=name,
        source_type="zip_upload",
        local_path="",
        default_branch="main",
        is_analyzed=False
    )
    db.add(repo)
    await db.flush()

    temp_zip = settings.UPLOADS_DIR / f"{repo.id}.zip"
    try:
        async with aiofiles.open(temp_zip, "wb") as out_f:
            while chunk := await file.read(1024 * 1024):
                await out_f.write(chunk)

        zip_meta = ingestion_service.extract_zip_archive(temp_zip, repo.id)
    except IngestionSecurityError as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to process archive: {e}")

    repo.local_path = zip_meta["local_path"]

    revision = RepositoryRevision(
        repository_id=repo.id,
        commit_hash=zip_meta["commit_hash"],
        branch_name="main",
        commit_message=zip_meta["commit_message"],
        author=zip_meta["author"],
        is_active=True
    )
    db.add(revision)
    await db.commit()
    await db.refresh(repo)

    resp = RepositoryResponse.model_validate(repo)
    resp.active_revision_id = revision.id
    return resp

@router.get("/", response_model=List[RepositoryResponse])
async def list_repositories(workspace_id: Optional[str] = None, db: AsyncSession = Depends(get_db)):
    stmt = select(Repository).order_by(Repository.created_at.desc())
    if workspace_id:
        stmt = stmt.where(Repository.workspace_id == workspace_id)
    
    res = await db.execute(stmt)
    repos = res.scalars().all()
    out = []
    for r in repos:
        # Get active revision
        rev_res = await db.execute(
            select(RepositoryRevision).where(
                RepositoryRevision.repository_id == r.id,
                RepositoryRevision.is_active == True
            )
        )
        active_rev = rev_res.scalar_one_or_none()
        resp = RepositoryResponse.model_validate(r)
        if active_rev:
            resp.active_revision_id = active_rev.id
            resp.summary_stats = active_rev.summary_stats
        out.append(resp)
    return out

@router.get("/{repo_id}", response_model=RepositoryResponse)
async def get_repository(repo_id: str, db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(Repository).where(Repository.id == repo_id))
    r = res.scalar_one_or_none()
    if not r:
        raise HTTPException(status_code=404, detail="Repository not found")

    rev_res = await db.execute(
        select(RepositoryRevision).where(
            RepositoryRevision.repository_id == r.id,
            RepositoryRevision.is_active == True
        )
    )
    active_rev = rev_res.scalar_one_or_none()
    resp = RepositoryResponse.model_validate(r)
    if active_rev:
        resp.active_revision_id = active_rev.id
        resp.summary_stats = active_rev.summary_stats
    return resp

@router.delete("/{repo_id}")
async def delete_repository(repo_id: str, db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(Repository).where(Repository.id == repo_id))
    r = res.scalar_one_or_none()
    if not r:
        raise HTTPException(status_code=404, detail="Repository not found")

    local_p = Path(r.local_path)
    if local_p.exists():
        shutil.rmtree(local_p, ignore_errors=True)

    await db.delete(r)
    await db.commit()
    return {"message": "Repository deleted successfully"}
