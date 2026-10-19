from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional

from app.core.database import get_db
from app.models import AnalysisFinding
from app.schemas import FindingResponse, DismissFindingRequest

router = APIRouter()

@router.get("/{revision_id}/findings", response_model=List[FindingResponse])
async def list_findings(
    revision_id: str,
    severity: Optional[str] = None,
    tool: Optional[str] = None,
    include_dismissed: bool = False,
    db: AsyncSession = Depends(get_db)
):
    stmt = select(AnalysisFinding).where(AnalysisFinding.revision_id == revision_id)
    if not include_dismissed:
        stmt = stmt.where(AnalysisFinding.is_dismissed == False)
    if severity and severity != "all":
        stmt = stmt.where(AnalysisFinding.severity == severity)
    if tool and tool != "all":
        stmt = stmt.where(AnalysisFinding.tool == tool)

    stmt = stmt.order_by(AnalysisFinding.line_number.asc())
    res = await db.execute(stmt)
    return res.scalars().all()

@router.patch("/findings/{finding_id}/dismiss", response_model=FindingResponse)
async def dismiss_finding(
    finding_id: str,
    payload: DismissFindingRequest,
    db: AsyncSession = Depends(get_db)
):
    res = await db.execute(select(AnalysisFinding).where(AnalysisFinding.id == finding_id))
    finding = res.scalar_one_or_none()
    if not finding:
        raise HTTPException(status_code=404, detail="Finding not found")

    finding.is_dismissed = payload.dismissed
    finding.dismissed_reason = payload.reason
    await db.commit()
    await db.refresh(finding)
    return finding
