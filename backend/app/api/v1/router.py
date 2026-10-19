from fastapi import APIRouter
from app.api.v1 import (
    workspaces,
    repositories,
    analysis,
    code,
    graph,
    search,
    ai,
    impact,
    security,
    compare,
    reports
)

api_router = APIRouter()

api_router.include_router(workspaces.router, prefix="/workspaces", tags=["Workspaces"])
api_router.include_router(repositories.router, prefix="/repositories", tags=["Repositories"])
api_router.include_router(analysis.router, prefix="/analysis", tags=["Analysis Jobs"])
api_router.include_router(code.router, prefix="/code", tags=["Code & Symbols"])
api_router.include_router(graph.router, prefix="/graph", tags=["Dependency Graph"])
api_router.include_router(search.router, prefix="/search", tags=["Code Search"])
api_router.include_router(ai.router, prefix="/ai", tags=["AI Codebase Assistant"])
api_router.include_router(impact.router, prefix="/impact", tags=["Change Impact"])
api_router.include_router(security.router, prefix="/security", tags=["Security & Quality"])
api_router.include_router(compare.router, prefix="/compare", tags=["Revision Comparison"])
api_router.include_router(reports.router, prefix="/reports", tags=["Architecture Reports"])
