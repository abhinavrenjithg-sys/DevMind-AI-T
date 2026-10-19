"""User domain logic and authentication service."""
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
