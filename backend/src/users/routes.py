# backend/src/users/routes.py
from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from src.core.config import settings
from src.database import get_db
from src.auth.dependencies import get_current_active_user, get_current_admin_user
from src.models.user_models import (
    User as UserORM,
    UserResponse,
    UserUpdate,
    SMTPSettings,
    PasswordUpdate,
    UserCreate
)
from .service import (
    get_user_profile,
    update_user_profile,
    update_user_smtp_settings,
    change_user_password,
    create_new_user,
    deactivate_user,
    get_user_statistics
)

router = APIRouter(
    prefix="/users",
    tags=["users"]
)

@router.get("/me", response_model=UserResponse)
async def read_users_me(
    current_user: UserORM = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get current user's profile."""
    try:
        return await get_user_profile(user_id=current_user.id, db=db)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.put("/me", response_model=UserResponse)
async def update_users_me(
    user_update_payload: UserUpdate,
    current_user: UserORM = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update current user's profile."""
    try:
        return await update_user_profile(
            user_id=current_user.id,
            user_update=user_update_payload,
            db=db
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.put("/me/smtp", response_model=UserResponse)
async def update_smtp_settings(
    smtp_settings: SMTPSettings,
    current_user: UserORM = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update user's SMTP settings."""
    try:
        return await update_user_smtp_settings(
            user_id=current_user.id,
            smtp_settings=smtp_settings,
            db=db
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.put("/me/password")
async def update_password(
    password_update: PasswordUpdate,
    current_user: UserORM = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update user's password."""
    try:
        await change_user_password(
            user_id=current_user.id,
            password_update=password_update,
            db=db
        )
        return {"message": "Password updated successfully"}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.post("/me/avatar", response_model=UserResponse)
async def upload_avatar(
    file: UploadFile = File(...),
    current_user: UserORM = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Upload user avatar."""
    if not file.content_type.startswith('image/'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be an image"
        )
    
    try:
        return await update_user_profile(
            user_id=current_user.id,
            user_update=UserUpdate(avatar=await file.read()),
            db=db
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/me/statistics")
async def get_statistics(
    current_user: UserORM = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get user's email campaign statistics."""
    try:
        return await get_user_statistics(user_id=current_user.id, db=db)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

# Admin routes
@router.post("/", response_model=UserResponse, dependencies=[Depends(get_current_admin_user)])
async def create_user(
    user_create: UserCreate,
    db: Session = Depends(get_db)
):
    """Create a new user (Admin only)."""
    try:
        return await create_new_user(user_create=user_create, db=db)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.delete("/{user_id}", dependencies=[Depends(get_current_admin_user)])
async def delete_user(
    user_id: int,
    db: Session = Depends(get_db)
):
    """Deactivate a user (Admin only)."""
    try:
        await deactivate_user(user_id=user_id, db=db)
        return {"message": "User deactivated successfully"}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )

@router.get("/", response_model=List[UserResponse], dependencies=[Depends(get_current_admin_user)])
async def list_users(
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    active_only: bool = True,
    db: Session = Depends(get_db)
):
    """List all users (Admin only)."""
    try:
        users = await get_user_profile(
            skip=skip,
            limit=limit,
            search=search,
            active_only=active_only,
            db=db
        )
        return users
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
