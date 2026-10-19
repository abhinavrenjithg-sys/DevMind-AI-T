"""FastAPI Application Entry Point."""
from fastapi import FastAPI
from .api.auth import auth_router
from .core.security import verify_secret_token

app = FastAPI(title="CloudVault Gateway", version="2.4.0")

@app.on_event("startup")
async def startup_event():
    """Bootstrap services and verify token configuration."""
    verify_secret_token("system_init")

app.include_router(auth_router, prefix="/api/v1/auth")
