# backend/src/models/user_models.py
from typing import Optional
import datetime # For ORM model timestamps

# SQLAlchemy ORM Imports
from sqlalchemy import Column, Integer, String, DateTime, Boolean

# Pydantic Imports
try:
    from pydantic import BaseModel, EmailStr
except ImportError:
    # Fallback if Pydantic is not available
    class BaseModelMeta(type):
        def __getattr__(cls, name):
            if name == "model_config": # Pydantic v2
                return {"from_attributes": True}
            raise AttributeError(f"'{cls.__name__}' object has no attribute '{name}'")

    class BaseModel(metaclass=BaseModelMeta): # type: ignore
        pass

    EmailStr = str # type: ignore


# --- SQLAlchemy Base ---
# Attempt to import a central Base, otherwise define a local one.
try:
    from src.database import Base # Assuming a common Base for all models in src/database.py
except ImportError:
    from sqlalchemy.ext.declarative import declarative_base # type: ignore
    print("models/user_models.py: Using local Base for User ORM model as shared Base not found.")
    Base = declarative_base()


# --- SQLAlchemy ORM Model ---
class User(Base): # type: ignore
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=True)

    # New Fields for User Role and Company
    user_role = Column(String(100), nullable=True) # e.g., 'admin', 'manager', 'agent'
    user_company_name = Column(String(255), nullable=True)

    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=datetime.datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    # Define relationships here if any, e.g., to campaigns, etc.
    # campaigns = relationship("Campaign", back_populates="user")


# --- Pydantic Models (Schema for API requests/responses) ---

# Base Pydantic model including all common user fields, reflecting ORM model
class UserBase(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None
    user_role: Optional[str] = None
    user_company_name: Optional[str] = None

class UserCreate(UserBase): # For user creation via API (input)
    password: str

# Internal Pydantic model for creating user in DB (includes hashed_password)
# This is used by db_operations and not directly exposed via API
class UserCreateDB(UserBase):
    password_hash: str
    # is_active is defaulted in ORM, so not strictly needed here unless overridable at creation
    is_active: Optional[bool] = True


class UserUpdate(BaseModel): # For updating user profile via API (input)
    full_name: Optional[str] = None
    user_role: Optional[str] = None
    user_company_name: Optional[str] = None
    is_active: Optional[bool] = None # Example: an admin might change this
    # Password updates should be handled separately.
    # Email updates might also need special handling (verification).

class UserResponse(UserBase): # For API responses (output)
    id: int
    is_active: bool # is_active is not optional in response if it has a default in ORM
    created_at: datetime.datetime # Not optional if defaulted in ORM
    updated_at: datetime.datetime # Not optional if defaulted in ORM

    # Pydantic v1 way:
    # class Config:
    #     orm_mode = True
    # Pydantic v2 way:
    model_config = {"from_attributes": True}


class UserLogin(BaseModel): # For login requests
    email: EmailStr # Or username: str
    password: str

class TokenData(BaseModel): # For data encoded in JWT
    sub: Optional[str] = None # Subject (user identifier, e.g. user_id)

class Token(BaseModel): # For returning JWT token
    access_token: str
    token_type: str

```
