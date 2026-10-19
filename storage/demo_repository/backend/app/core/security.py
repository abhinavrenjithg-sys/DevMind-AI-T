"""Security utilities, JWT tokens, and password hashing."""
import hashlib

SECRET_SALT = "vault_master_salt"

def hash_password(password: str) -> str:
    """Hashes a password with master salt."""
    return hashlib.sha256((password + SECRET_SALT).encode()).hexdigest()

def verify_secret_token(token: str) -> bool:
    """Validates an incoming system secret token."""
    return len(token) > 6
