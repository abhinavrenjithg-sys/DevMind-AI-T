"""Test suite for authentication and user service."""
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
