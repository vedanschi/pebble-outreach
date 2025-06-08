# backend/src/auth/routes.py
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm # Already imported in service, but good for clarity here
from sqlalchemy.orm import Session

try:
    from src.database import get_db
    from src.models.user_models import UserCreate, UserResponse, Token # Pydantic models
    from .service import signup_user, login_for_access_token # Auth service functions
except ImportError:
    # Placeholders
    from typing import Optional
    class Session: pass
    def get_db(): pass
    class UserCreate: email: str; password: str; full_name: Optional[str] = None
    class UserResponse: id: int; email: str; full_name: Optional[str] = None
    class Token: access_token: str; token_type: str
    class OAuth2PasswordRequestForm: username: str; password: str # Simplified
    async def signup_user(user_create: UserCreate, db: Session) -> UserResponse:
        return UserResponse(id=1, email=user_create.email, full_name=user_create.full_name) # type: ignore
    async def login_for_access_token(form_data: OAuth2PasswordRequestForm, db: Session) -> Token:
        return Token(access_token="fake_token", token_type="bearer") # type: ignore

router = APIRouter(
    prefix="/auth", # Common prefix for auth routes
    tags=["authentication"]
)

@router.post("/signup", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def api_signup_user(
    user_in: UserCreate,
    db: Session = Depends(get_db)
):
    """
    User registration endpoint.
    """
    # The signup_user service function already handles potential HTTPException for existing email.
    return await signup_user(user_create=user_in, db=db)

@router.post("/login/token", response_model=Token)
async def api_login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """
    OAuth2 compatible token login, get an access token for future requests.
    The client should send 'username' (which is email) and 'password' in a form-data body.
    """
    # The login_for_access_token service function handles user lookup, password verification,
    # and token creation, raising HTTPException on errors.
    # Note: The `db` session is passed to `login_for_access_token` because it now expects it,
    # even though the OAuth2PasswordRequestForm is also injected by FastAPI.
    return await login_for_access_token(form_data=form_data, db=db)

```
