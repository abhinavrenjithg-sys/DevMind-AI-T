import asyncio
import os
import shutil
import datetime
from pathlib import Path

# Set up environment path to import app modules
import sys
backend_path = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(backend_path))

from app.core.database import init_db, AsyncSessionLocal
from app.models import Workspace, Repository, RepositoryRevision, AnalysisJob
from app.analysis.pipeline import AnalysisPipeline
from sqlalchemy import select

DEMO_REPO_DIR = Path(__file__).resolve().parent.parent / "storage" / "demo_repository"

def create_sample_codebase():
    """Generates a realistic multi-tier Python and TypeScript repository on disk."""
    if DEMO_REPO_DIR.exists():
        shutil.rmtree(DEMO_REPO_DIR)
    
    # 1. Directory Structure
    (DEMO_REPO_DIR / "backend" / "app" / "api").mkdir(parents=True, exist_ok=True)
    (DEMO_REPO_DIR / "backend" / "app" / "services").mkdir(parents=True, exist_ok=True)
    (DEMO_REPO_DIR / "backend" / "app" / "models").mkdir(parents=True, exist_ok=True)
    (DEMO_REPO_DIR / "backend" / "app" / "core").mkdir(parents=True, exist_ok=True)
    (DEMO_REPO_DIR / "backend" / "tests").mkdir(parents=True, exist_ok=True)
    (DEMO_REPO_DIR / "frontend" / "src" / "components").mkdir(parents=True, exist_ok=True)
    (DEMO_REPO_DIR / "frontend" / "src" / "services").mkdir(parents=True, exist_ok=True)
    (DEMO_REPO_DIR / "frontend" / "src" / "hooks").mkdir(parents=True, exist_ok=True)

    # 2. Python Files
    # backend/app/main.py (Entry point)
    with open(DEMO_REPO_DIR / "backend" / "app" / "main.py", "w", encoding="utf-8") as f:
        f.write('''"""FastAPI Application Entry Point."""
from fastapi import FastAPI
from .api.auth import auth_router
from .core.security import verify_secret_token

app = FastAPI(title="CloudVault Gateway", version="2.4.0")

@app.on_event("startup")
async def startup_event():
    """Bootstrap services and verify token configuration."""
    verify_secret_token("system_init")

app.include_router(auth_router, prefix="/api/v1/auth")
''')

    # backend/app/core/security.py
    with open(DEMO_REPO_DIR / "backend" / "app" / "core" / "security.py", "w", encoding="utf-8") as f:
        f.write('''"""Security utilities, JWT tokens, and password hashing."""
import hashlib

SECRET_SALT = "vault_master_salt"

def hash_password(password: str) -> str:
    """Hashes a password with master salt."""
    return hashlib.sha256((password + SECRET_SALT).encode()).hexdigest()

def verify_secret_token(token: str) -> bool:
    """Validates an incoming system secret token."""
    return len(token) > 6
''')

    # backend/app/models/user.py
    with open(DEMO_REPO_DIR / "backend" / "app" / "models" / "user.py", "w", encoding="utf-8") as f:
        f.write('''"""User entities and domain records."""

class BaseEntity:
    def __init__(self, id: str):
        self.id = id

class User(BaseEntity):
    def __init__(self, id: str, username: str, email: str, password_hash: str):
        super().__init__(id)
        self.username = username
        self.email = email
        self.password_hash = password_hash
        self.is_active = True
''')

    # backend/app/services/user_service.py
    with open(DEMO_REPO_DIR / "backend" / "app" / "services" / "user_service.py", "w", encoding="utf-8") as f:
        f.write('''"""User domain logic and authentication service."""
from ..models.user import User
from ..core.security import hash_password

class UserService:
    def __init__(self):
        self._users = {}

    def register_user(self, username: str, email: str, raw_pass: str) -> User:
        """Registers a new user and hashes their password."""
        pass_hash = hash_password(raw_pass)
        user = User(id=str(len(self._users) + 1), username=username, email=email, password_hash=pass_hash)
        self._users[user.id] = user
        return user

    def get_by_username(self, username: str):
        for u in self._users.values():
            if u.username == username:
                return u
        return None
''')

    # backend/app/api/auth.py
    with open(DEMO_REPO_DIR / "backend" / "app" / "api" / "auth.py", "w", encoding="utf-8") as f:
        f.write('''"""Authentication routing endpoints."""
from fastapi import APIRouter, HTTPException
from ..services.user_service import UserService

auth_router = APIRouter()
user_service = UserService()

@auth_router.post("/register")
def register(username: str, email: str, password: str):
    """Register a new user account."""
    if len(password) < 8:
        raise HTTPException(status_code=400, detail="Password too short")
    return user_service.register_user(username, email, password)

@auth_router.get("/user/{username}")
def get_user_profile(username: str):
    user = user_service.get_by_username(username)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user
''')

    # backend/tests/test_auth.py
    with open(DEMO_REPO_DIR / "backend" / "tests" / "test_auth.py", "w", encoding="utf-8") as f:
        f.write('''"""Test suite for authentication and user service."""
from backend.app.services.user_service import UserService

def test_user_registration():
    service = UserService()
    user = service.register_user("alex", "alex@cloudvault.io", "super_secret_123")
    assert user.username == "alex"
    assert user.password_hash is not None

def test_lookup_user():
    service = UserService()
    service.register_user("charlie", "charlie@test.com", "pass12345")
    found = service.get_by_username("charlie")
    assert found is not None
''')

    # 3. TypeScript Files
    # frontend/src/services/api.ts
    with open(DEMO_REPO_DIR / "frontend" / "src" / "services" / "api.ts", "w", encoding="utf-8") as f:
        f.write('''import { UserProfile } from '../types';

export class ApiClient {
    static async getProfile(username: string): Promise<UserProfile> {
        const response = await fetch(`/api/v1/auth/user/${username}`);
        return response.json();
    }
}
''')

    # frontend/src/types.ts
    with open(DEMO_REPO_DIR / "frontend" / "src" / "types.ts", "w", encoding="utf-8") as f:
        f.write('''export interface UserProfile {
    id: string;
    username: string;
    email: string;
    is_active: boolean;
}
''')

    # frontend/src/components/Dashboard.tsx
    with open(DEMO_REPO_DIR / "frontend" / "src" / "components" / "Dashboard.tsx", "w", encoding="utf-8") as f:
        f.write('''import React, { useEffect, useState } from 'react';
import { ApiClient } from '../services/api';
import { UserProfile } from '../types';

export const Dashboard: React.FC = () => {
    const [user, setUser] = useState<UserProfile | null>(null);

    useEffect(() => {
        ApiClient.getProfile("alex").then(setUser);
    }, []);

    return (
        <div className="vault-dashboard">
            <h1>Welcome, {user?.username}</h1>
        </div>
    );
};
''')

    # frontend/src/main.tsx
    with open(DEMO_REPO_DIR / "frontend" / "src" / "main.tsx", "w", encoding="utf-8") as f:
        f.write('''import React from 'react';
import { createRoot } from 'react-dom/client';
import { Dashboard } from './components/Dashboard';

const root = createRoot(document.getElementById('root')!);
root.render(<Dashboard />);
''')

    # package.json and README.md
    with open(DEMO_REPO_DIR / "package.json", "w", encoding="utf-8") as f:
        f.write('''{
  "name": "cloudvault-fullstack",
  "version": "2.4.0",
  "private": true
}
''')

    with open(DEMO_REPO_DIR / "README.md", "w", encoding="utf-8") as f:
        f.write('''# CloudVault Full-Stack Platform
Multi-tier microservices gateway handling user profiles, credentials, and API routing.
''')

async def seed_database():
    print("Creating sample codebase on disk at:", DEMO_REPO_DIR)
    create_sample_codebase()

    await init_db()

    async with AsyncSessionLocal() as session:
        # 1. Get or create default workspace
        res = await session.execute(select(Workspace).limit(1))
        workspace = res.scalar_one_or_none()
        if not workspace:
            workspace = Workspace(
                name="Main Engineering Workspace",
                slug="main-engineering",
                description="Default workspace for codebase reverse engineering."
            )
            session.add(workspace)
            await session.commit()
            await session.refresh(workspace)

        # 2. Check if demo repository already exists
        repo_res = await session.execute(select(Repository).where(Repository.name == "CloudVault Full-Stack"))
        existing_repo = repo_res.scalar_one_or_none()

        if existing_repo:
            print("Demo repository already exists in database. Re-running analysis pipeline...")
            repo = existing_repo
            rev_res = await session.execute(select(RepositoryRevision).where(RepositoryRevision.repository_id == repo.id))
            rev = rev_res.scalars().first()
        else:
            print("Registering demo repository in database...")
            repo = Repository(
                workspace_id=workspace.id,
                name="CloudVault Full-Stack",
                source_type="git_url",
                remote_url="https://github.com/cloudvault/cloudvault-fullstack",
                local_path=str(DEMO_REPO_DIR),
                default_branch="main",
                is_analyzed=False
            )
            session.add(repo)
            await session.commit()
            await session.refresh(repo)

            rev = RepositoryRevision(
                repository_id=repo.id,
                commit_hash="9f8b2c4e1a0d7e6f",
                branch_name="main",
                commit_message="feat(auth): add user registration service and token validation",
                author="Engineering Team",
                committed_at=datetime.datetime.utcnow(),
                is_active=True
            )
            session.add(rev)
            await session.commit()
            await session.refresh(rev)

        job = AnalysisJob(
            repository_id=repo.id,
            revision_id=rev.id,
            status="pending",
            current_stage="discovery",
            progress_percentage=0
        )
        session.add(job)
        await session.commit()
        await session.refresh(job)

        print("Executing 7-stage analysis pipeline on demo repository...")
        pipeline = AnalysisPipeline(session, repo, rev, job)
        stats = await pipeline.run()

        print("\nAnalysis Pipeline Completed Successfully!")
        print(f"Total Files Indexed: {stats['total_files']}")
        print(f"Total Lines of Code: {stats['total_loc']}")
        print(f"Total Symbols: {stats['total_symbols']}")
        print(f"Total Dependency Edges: {stats['total_edges']}")
        print(f"Frameworks Detected: {stats['frameworks']}")
        print(f"Entry Points: {stats['entry_points']}")

if __name__ == "__main__":
    asyncio.run(seed_database())
