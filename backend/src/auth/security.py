# src/auth/security.py
from passlib.context import CryptContext

# It's recommended to put this in configuration
PWD_CONTEXT = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies a plain password against a hashed password."""
    return PWD_CONTEXT.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Hashes a plain password."""
    return PWD_CONTEXT.hash(password)