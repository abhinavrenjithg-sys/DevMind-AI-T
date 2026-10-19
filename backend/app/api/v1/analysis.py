import asyncio
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db, AsyncSessionLocal
from app.models import Repository, RepositoryRevision, AnalysisJob
from app.schemas import AnalysisJobResponse
from app.analysis.pipeline import AnalysisPipeline

router = APIRouter()

async def run_pipeline_task(job_id: str, repo_id: str, revision_id: str):
    async with AsyncSessionLocal() as session:
        job = (await session.execute(select(AnalysisJob).where(AnalysisJob.id == job_id))).scalar_one_or_none()
        repo = (await session.execute(select(Repository).where(Repository.id == repo_id))).scalar_one_or_none()
        rev = (await session.execute(select(RepositoryRevision).where(RepositoryRevision.id == revision_id))).scalar_one_or_none()

        if not job or not repo or not rev:
            return

        pipeline = AnalysisPipeline(session, repo, rev, job)
        try:
            await pipeline.run()
        except Exception:
            pass

@router.post("/jobs/{repo_id}", response_model=AnalysisJobResponse)
async def start_analysis_job(
    repo_id: str,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    repo_res = await db.execute(select(Repository).where(Repository.id == repo_id))
    repo = repo_res.scalar_one_or_none()
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")

    rev_res = await db.execute(
        select(RepositoryRevision).where(
            RepositoryRevision.repository_id == repo.id,
            RepositoryRevision.is_active == True
        )
    )
    rev = rev_res.scalar_one_or_none()
    if not rev:
        raise HTTPException(status_code=400, detail="Repository has no active revision to analyze")

    job = AnalysisJob(
        repository_id=repo.id,
        revision_id=rev.id,
        status="pending",
        current_stage="discovery",
        progress_percentage=0,
        stage_logs=[]
    )
    db.add(job)
    await db.commit()
    await db.refresh(job)

    # Launch background analysis
    background_tasks.add_task(run_pipeline_task, job.id, repo.id, rev.id)

    return job

@router.get("/jobs/{job_id}", response_model=AnalysisJobResponse)
async def get_job_status(job_id: str, db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(AnalysisJob).where(AnalysisJob.id == job_id))
    job = res.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job

@router.get("/jobs/repo/{repo_id}", response_model=AnalysisJobResponse)
async def get_latest_repo_job(repo_id: str, db: AsyncSession = Depends(get_db)):
    res = await db.execute(
        select(AnalysisJob)
        .where(AnalysisJob.repository_id == repo_id)
        .order_by(AnalysisJob.created_at.desc())
    )
    job = res.scalars().first()
    if not job:
        raise HTTPException(status_code=404, detail="No analysis jobs found for repository")
    return job
