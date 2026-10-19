from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select

from app.core.config import settings
from app.core.database import init_db, AsyncSessionLocal
from app.models import Workspace
from app.api.v1.router import api_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: ensure tables exist and create default workspace if none
    await init_db()
    async with AsyncSessionLocal() as session:
        res = await session.execute(select(Workspace).limit(1))
        if not res.scalar_one_or_none():
            default_ws = Workspace(
                name="Main Engineering Workspace",
                slug="main-engineering",
                description="Default workspace for repository analysis and codebase intelligence."
            )
            session.add(default_ws)
            await session.commit()
    yield
    # Shutdown logic if any

app = FastAPI(
    title="DevMind AI",
    description="AI-Powered Codebase Intelligence and Software Reverse-Engineering Platform",
    version=settings.VERSION,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API v1
app.include_router(api_router, prefix=settings.API_V1_PREFIX)

@app.get("/health", tags=["Health"])
async def health_check():
    return {
        "status": "healthy",
        "service": "DevMind AI Backend",
        "version": settings.VERSION
    }

@app.get("/", tags=["Root"])
async def root():
    return {
        "name": settings.PROJECT_NAME,
        "tagline": "Understand any codebase. Trace every dependency. Change code with confidence.",
        "version": settings.VERSION,
        "docs": "/docs",
        "api_v1": settings.API_V1_PREFIX
    }
