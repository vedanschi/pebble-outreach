# backend/src/users/routes.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional

try:
    from src.database import get_db
    from src.auth.dependencies import get_current_active_user # For protecting /me endpoints
    from src.models.user_models import User as UserORM, UserResponse, UserUpdate # Pydantic & ORM
    from .service import get_user_profile, update_user_profile # User service functions
except ImportError:
    # Placeholders
    class Session: pass
    def get_db(): pass
    class UserORM: id: int; email: str; full_name: Optional[str]
    class UserResponse: id: int; email: str; full_name: Optional[str]
    class UserUpdate: full_name: Optional[str] = None
    async def get_current_active_user() -> UserORM: return UserORM(id=1, email="test@example.com", full_name="Test User From Token") # type: ignore
    async def get_user_profile(user_id: int, db: Session) -> UserResponse:
        return UserResponse(id=user_id, email="test@example.com", full_name="Test User Profile") # type: ignore
    async def update_user_profile(user_id: int, user_update: UserUpdate, db: Session) -> UserResponse:
        return UserResponse(id=user_id, email="test@example.com", full_name=user_update.full_name or "Updated Test User") # type: ignore


router = APIRouter(
    prefix="/users", # Common prefix for user-related routes
    tags=["users"]
)

@router.get("/me", response_model=UserResponse)
async def read_users_me(
    current_user: UserORM = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get current user's profile.
    """
    # get_user_profile service function handles not found, though get_current_active_user should ensure user exists.
    return await get_user_profile(user_id=current_user.id, db=db)


@router.put("/me", response_model=UserResponse)
async def update_users_me(
    user_update_payload: UserUpdate,
    current_user: UserORM = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Update current user's profile (e.g., full_name).
    """
    # update_user_profile service function handles not found (though unlikely for current_user) and updates.
    return await update_user_profile(
        user_id=current_user.id,
        user_update=user_update_payload,
        db=db
    )

```
