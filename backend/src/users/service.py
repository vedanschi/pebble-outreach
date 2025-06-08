# backend/src/users/service.py
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from typing import Optional

try:
    from src.models.user_models import User as UserORM, UserResponse, UserUpdate
    from .db_operations import db_get_user_by_id, db_update_user
except ImportError:
    # Placeholders - updated to include new fields
    class UserORM:
        id: int; email: str; full_name: Optional[str]
        user_role: Optional[str]; user_company_name: Optional[str]
        is_active: bool; created_at: datetime.datetime; updated_at: datetime.datetime # from UserResponse
    class UserResponse:
        id: int; email: str; full_name: Optional[str]
        user_role: Optional[str]; user_company_name: Optional[str]
        is_active: bool; created_at: datetime.datetime; updated_at: datetime.datetime
    class UserUpdate:
        full_name: Optional[str] = None
        user_role: Optional[str] = None
        user_company_name: Optional[str] = None
        is_active: Optional[bool] = None

    async def db_get_user_by_id(db: Session, user_id: int) -> Optional[UserORM]:
        if user_id == 1: return UserORM(id=1, email="user@example.com", full_name="Test User", user_role="agent", user_company_name="Test Inc", is_active=True, created_at=datetime.datetime.utcnow(), updated_at=datetime.datetime.utcnow()) # type: ignore
        return None
    async def db_update_user(db: Session, user_id: int, user_update_data: UserUpdate) -> Optional[UserORM]:
        if user_id == 1: return UserORM(id=1, email="user@example.com",
                                      full_name=user_update_data.full_name or "Test User Updated",
                                      user_role=user_update_data.user_role or "agent",
                                      user_company_name=user_update_data.user_company_name or "Test Inc",
                                      is_active=True, created_at=datetime.datetime.utcnow(), updated_at=datetime.datetime.utcnow()
                                      ) # type: ignore
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
    # UserResponse is expected to map all fields from UserORM including new ones
    # due to its definition in user_models.py (from_attributes=True)
    return UserResponse.model_validate(user_orm) # Pydantic v2 way
    # For Pydantic v1, it would be UserResponse.from_orm(user_orm)

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

    # UserResponse is expected to map all fields from UserORM including new ones
    return UserResponse.model_validate(updated_user_orm) # Pydantic v2 way
    # For Pydantic v1, it would be UserResponse.from_orm(updated_user_orm)