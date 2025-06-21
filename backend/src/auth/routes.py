# backend/src/auth/routes.py
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from src.database import get_db
from src.models.user_models import UserCreate, UserResponse, Token
from .service import signup_user, login_for_access_token

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)

@router.post("/signup", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def api_signup_user(
    user_in: UserCreate,
    db: Session = Depends(get_db)
):
    """
    User registration endpoint.
    """
    return await signup_user(user_create=user_in, db=db)

@router.post("/login/token", response_model=Token)
async def api_login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """
    OAuth2 compatible token login. The client should send 'username' (email) and 'password' as form-data.
    Returns a JWT access token if credentials are valid.
    """
    return await login_for_access_token(form_data=form_data, db=db)
