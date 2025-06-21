# backend/src/users/routes.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional, List

from src.database import get_db
from src.auth.dependencies import get_current_active_user
from src.models.user_models import User as UserORM, UserResponse, UserUpdate
from .service import get_user_profile, update_user_profile

router = APIRouter(
    prefix="/users",
    tags=["Users"]
)

@router.get("/me", response_model=UserResponse)
async def read_users_me(
    current_user: UserORM = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get current user's profile.
    """
    return await get_user_profile(user_id=current_user.id, db=db)

@router.put("/me", response_model=UserResponse)
async def update_users_me(
    user_update_payload: UserUpdate,
    current_user: UserORM = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Update current user's profile (e.g., full_name, etc).
    """
    return await update_user_profile(
        user_id=current_user.id,
        user_update=user_update_payload,
        db=db
    )

# Optionally, add an admin endpoint to list all users (requires admin privileges)
# Uncomment and implement admin check if needed
# @router.get("/", response_model=List[UserResponse])
# async def list_users(
#     db: Session = Depends(get_db),
#     current_user: UserORM = Depends(get_current_active_user)
# ):
#     if not current_user.is_admin:
#         raise HTTPException(status_code=403, detail="Not authorized")
#     return await list_all_users(db=db)
