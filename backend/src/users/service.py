# backend/src/users/service.py
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from typing import Optional

try:
    from src.models.user_models import User as UserORM, UserResponse, UserUpdate
    from .db_operations import db_get_user_by_id, db_update_user
except ImportError:
    # Placeholders
    class UserORM: id: int; email: str; full_name: Optional[str]
    class UserResponse: id: int; email: str; full_name: Optional[str]
    class UserUpdate: full_name: Optional[str] = None
    async def db_get_user_by_id(db: Session, user_id: int) -> Optional[UserORM]:
        if user_id == 1: return UserORM(id=1, email="user@example.com", full_name="Test User") # type: ignore
        return None
    async def db_update_user(db: Session, user_id: int, user_update_data: UserUpdate) -> Optional[UserORM]:
        if user_id == 1: return UserORM(id=1, email="user@example.com", full_name=user_update_data.full_name or "Test User Updated") # type: ignore
        return None


async def get_user_profile(user_id: int, db: Session) -> UserResponse:
    """
    Retrieves the profile of a user by their ID.
    """
    user_orm = await db_get_user_by_id(db, user_id=user_id)
    if not user_orm:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    return UserResponse(
        id=user_orm.id,
        email=user_orm.email,
        full_name=user_orm.full_name
    )

async def update_user_profile(
    user_id: int,
    user_update: UserUpdate,
    db: Session
) -> UserResponse:
    """
    Updates the profile of a user by their ID.
    """
    updated_user_orm = await db_update_user(db, user_id=user_id, user_update_data=user_update)

    if not updated_user_orm:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, # Or 400 if update data was invalid, though db_update_user handles not found
            detail="User not found or update failed",
        )

    return UserResponse(
        id=updated_user_orm.id,
        email=updated_user_orm.email,
        full_name=updated_user_orm.full_name
    )