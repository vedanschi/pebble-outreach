# backend/src/users/db_operations.py
from typing import Optional, Type

from sqlalchemy.orm import Session
from sqlalchemy import select, update

# Assuming ORM model and Pydantic schemas are defined elsewhere
# For example, in src.models.user_models and src.schemas.user_schemas
try:
    from src.models.user_models import User # ORM Model
    # Pydantic schemas for creation and update, expected to be defined in user_models.py or schemas.user_schemas
    # These should now include user_role and user_company_name
    from src.schemas.user_schemas import UserCreateDB, UserUpdate
except ImportError:
    # Placeholders for robustness if actual models/schemas are not found
    # These placeholders should reflect the fields used by the functions below,
    # including the new user_role and user_company_name.
    class User:
        id: int; email: str; full_name: Optional[str]; hashed_password: str
        user_role: Optional[str]; user_company_name: Optional[str] # Added new fields

    class UserCreateDB(Type):
        email: str; hashed_password: str; full_name: Optional[str] = None
        user_role: Optional[str] = None; user_company_name: Optional[str] = None # Added
        def model_dump(self): return {
            "email": self.email, "hashed_password": self.hashed_password,
            "full_name": self.full_name, "user_role": self.user_role,
            "user_company_name": self.user_company_name
        }

    class UserUpdate(Type):
        full_name: Optional[str] = None
        user_role: Optional[str] = None # Added
        user_company_name: Optional[str] = None # Added
        def model_dump(self, exclude_unset=True):
            data = {}
            if self.full_name is not None: data["full_name"] = self.full_name
            if self.user_role is not None: data["user_role"] = self.user_role
            if self.user_company_name is not None: data["user_company_name"] = self.user_company_name
            return data


async def db_get_user_by_email(db: Session, email: str) -> Optional[User]:
    """
    Retrieves a user from the database by their email address.
    """
    statement = select(User).where(User.email == email)
    result = await db.execute(statement)
    return result.scalars().first()

async def db_get_user_by_id(db: Session, user_id: int) -> Optional[User]:
    """
    Retrieves a user from the database by their ID.
    """
    statement = select(User).where(User.id == user_id)
    result = await db.execute(statement)
    return result.scalars().first()

async def db_create_user(db: Session, user_create_data: UserCreateDB) -> User:
    """
    Creates a new user in the database.
    `user_create_data` should already contain the hashed password.
    """
    # Assuming UserCreateDB directly matches User ORM model fields for email, hashed_password, full_name
    db_user = User(**user_create_data.model_dump())
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

async def db_update_user(db: Session, user_id: int, user_update_data: UserUpdate) -> Optional[User]:
    """
    Updates an existing user's information in the database.
    Only updates fields present in `user_update_data`.
    """
    db_user = await db_get_user_by_id(db, user_id)
    if db_user:
        update_data = user_update_data.model_dump(exclude_unset=True) # Only get provided fields
        if not update_data: # If nothing to update
            return db_user

        for key, value in update_data.items():
            setattr(db_user, key, value)

        db.add(db_user) # Add back to session to mark as dirty
        db.commit()
        db.refresh(db_user)
        return db_user
    return None # User not found
```
