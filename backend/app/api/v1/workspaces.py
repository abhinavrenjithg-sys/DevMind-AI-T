from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List
import re

from app.core.database import get_db
from app.models import Workspace, Repository
from app.schemas import WorkspaceCreate, WorkspaceResponse

router = APIRouter()

@router.post("/", response_model=WorkspaceResponse)
async def create_workspace(payload: WorkspaceCreate, db: AsyncSession = Depends(get_db)):
    slug = payload.slug or re.sub(r"[^a-zA-Z0-9]+", "-", payload.name.lower()).strip("-")
    
    # Check if slug exists
    res = await db.execute(select(Workspace).where(Workspace.slug == slug))
    existing = res.scalar_one_or_none()
    if existing:
        slug = f"{slug}-{int(func.random() * 1000)}"

    workspace = Workspace(
        name=payload.name,
        slug=slug,
        description=payload.description
    )
    db.add(workspace)
    await db.commit()
    await db.refresh(workspace)
    return workspace

@router.get("/", response_model=List[WorkspaceResponse])
async def list_workspaces(db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(Workspace).order_by(Workspace.created_at.desc()))
    workspaces = res.scalars().all()
    out = []
    for ws in workspaces:
        # Count repos
        repo_count_res = await db.execute(
            select(func.count(Repository.id)).where(Repository.workspace_id == ws.id)
        )
        count = repo_count_res.scalar() or 0
        resp = WorkspaceResponse.model_validate(ws)
        resp.repository_count = count
        out.append(resp)
    return out

@router.get("/{workspace_id}", response_model=WorkspaceResponse)
async def get_workspace(workspace_id: str, db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(Workspace).where(Workspace.id == workspace_id))
    ws = res.scalar_one_or_none()
    if not ws:
        raise HTTPException(status_code=404, detail="Workspace not found")
    
    repo_count_res = await db.execute(
        select(func.count(Repository.id)).where(Repository.workspace_id == ws.id)
    )
    count = repo_count_res.scalar() or 0
    resp = WorkspaceResponse.model_validate(ws)
    resp.repository_count = count
    return resp
