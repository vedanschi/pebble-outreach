# backend/src/auth/service.py
from sqlalchemy.orm import Session
from fastapi import HTTPException, status, Depends # Added Depends for OAuth2PasswordRequestForm
from fastapi.security import OAuth2PasswordRequestForm # For login form data
from typing import Optional

# Assuming models are structured in src.models and can be imported
try:
    from src.models.user_models import User as UserORM, UserCreate, UserResponse, Token # User is ORM, others Pydantic
    from src.schemas.user_schemas import UserCreateDB # Internal Pydantic for DB creation
    from src.users.db_operations import db_get_user_by_email, db_create_user
    from .security import get_password_hash, verify_password
    from .jwt_handler import create_access_token
    # Note on jwt_handler.py: JWT_SECRET is currently hardcoded.
    # For production, this MUST be moved to environment variables or a secure config.
except ImportError:
    # Simplified Placeholders for robustness during development if imports fail
    class UserORM: id: int; email: str; full_name: Optional[str]; hashed_password: str
    class UserCreate: email: str; password: str; full_name: Optional[str] = None
    class UserResponse: id: int; email: str; full_name: Optional[str] = None
    class Token: access_token: str; token_type: str
    class UserCreateDB: email: str; hashed_password: str; full_name: Optional[str] = None

    async def db_get_user_by_email(db: Session, email: str) -> Optional[UserORM]: return None
    async def db_create_user(db: Session, user_create_data: UserCreateDB) -> UserORM:
        return UserORM(id=1, email=user_create_data.email, full_name=user_create_data.full_name, hashed_password="hashed") # type: ignore
    def get_password_hash(password: str) -> str: return "hashed_" + password
    def verify_password(plain_password: str, hashed_password: str) -> bool: return True
    def create_access_token(data: dict) -> str: return "fake_jwt_token_for_" + data.get("sub","unknown")


async def signup_user(user_create: UserCreate, db: Session) -> UserResponse:
    """
    Handles user signup.
    1. Check if user with this email already exists.
    2. Hash the password.
    3. Create user in the database.
    4. Return user information (excluding password).
    """
    db_user = await db_get_user_by_email(db, email=user_create.email)
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    hashed_password = get_password_hash(user_create.password)

    user_create_db_data = UserCreateDB(
        email=user_create.email,
        hashed_password=hashed_password,
        full_name=user_create.full_name
    )

    created_user_orm = await db_create_user(db, user_create_data=user_create_db_data)

    return UserResponse(
        id=created_user_orm.id,
        email=created_user_orm.email,
        full_name=created_user_orm.full_name
    )


async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends() # Assuming get_db will be used in the route for this
) -> Token:
    """
    Handles user login using OAuth2PasswordRequestForm.
    1. Retrieve user by email (username from form_data).
    2. Verify password.
    3. If valid, create and return JWT access token.
    """
    user = await db_get_user_by_email(db, email=form_data.username) # form_data.username is the email
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"}, # Standard for token errors
        )

    # Create JWT token. Subject can be user's email or ID. Using ID is common.
    access_token_data = {"sub": str(user.id)}
    access_token = create_access_token(data=access_token_data)

    return Token(access_token=access_token, token_type="bearer")

# Security Note for jwt_handler.py:
# The JWT_SECRET key is critical for the security of token generation and validation.
# Currently, if it's hardcoded in jwt_handler.py, it poses a significant security risk.
# This secret MUST be:
# 1. Strong and randomly generated.
# 2. Loaded from environment variables or a secure configuration management system.
#    Example: os.getenv("JWT_SECRET")
# 3. Kept confidential and not committed to version control if hardcoded.
# Failure to secure the JWT_SECRET properly can lead to unauthorized access and token forgery.