"""Authentication routing endpoints."""
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
