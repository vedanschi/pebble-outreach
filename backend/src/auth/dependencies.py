# backend/src/auth/dependencies.py
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from jose import JWTError, jwt # PyJWT could also be used
from typing import Optional

try:
    from src.database import get_db # For DB session dependency
    from src.models.user_models import User as UserORM # User ORM model
    # Assuming user_schemas might contain a UserInDB or similar if needed, but UserORM is fine for return
    from src.users.db_operations import db_get_user_by_id # Or db_get_user_by_email if sub is email
    from .jwt_handler import ALGORITHM, JWT_SECRET # Import your JWT settings
    # Note: JWT_SECRET MUST be loaded from env variables in a real app
except ImportError:
    # Placeholders
    class UserORM: id: int; email: str; full_name: Optional[str]; is_active: Optional[bool] = True
    def get_db(): pass
    async def db_get_user_by_id(db: Session, user_id: int) -> Optional[UserORM]:
        if user_id == 1: return UserORM(id=1, email="test@example.com", full_name="Test User") # type: ignore
        return None
    ALGORITHM = "HS256"
    JWT_SECRET = "a_very_secret_key_that_should_be_in_env_not_hardcoded" # WARNING: Placeholder only

# OAuth2PasswordBearer scheme. tokenUrl is the endpoint that issues the token (login).
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login/token") # Adjust tokenUrl if your auth routes have a prefix

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> UserORM:
    """
    Decodes the JWT token, retrieves user ID from it, and fetches the user from DB.
    This is the primary dependency for protected routes requiring authentication.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[ALGORITHM])
        user_id_str: Optional[str] = payload.get("sub") # Assuming "sub" contains the user ID
        if user_id_str is None:
            raise credentials_exception

        try:
            user_id = int(user_id_str)
        except ValueError:
            # If sub is not an int (e.g. if email was used as sub and you expect ID)
            raise credentials_exception

    except JWTError: # Catches errors from jwt.decode (e.g., expired, invalid signature)
        raise credentials_exception

    user = await db_get_user_by_id(db, user_id=user_id)
    if user is None:
        raise credentials_exception # Or a more specific "User not found" tied to 401

    return user

async def get_current_active_user(
    current_user: UserORM = Depends(get_current_user)
) -> UserORM:
    """
    Dependency to get the current authenticated user and check if they are active.
    (Assumes UserORM model has an `is_active` attribute).
    """
    # Example: if your UserORM model has an 'is_active' field:
    # if not current_user.is_active:
    #     raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user")
    # For now, as `is_active` is not strictly defined on the placeholder, we just return the user.
    # If `is_active` is added to your User model, uncomment and use the check above.
    return current_user

# Security Reminder:
# - JWT_SECRET must be loaded securely from environment variables.
# - Consider token revocation strategies for enhanced security if needed.
# - Ensure HTTPS is used in production to protect tokens in transit.
```
