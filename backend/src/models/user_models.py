# src/models/user_models.py
from typing import Optional
# Assuming Pydantic for data validation and serialization, common with FastAPI
# If not using Pydantic, these would be simple classes or dataclasses.
try:
    from pydantic import BaseModel, EmailStr
except ImportError:
    # Fallback if Pydantic is not available in the subtask environment
    class BaseModel: pass
    EmailStr = str


class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: Optional[str] = None

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: int
    email: EmailStr
    full_name: Optional[str] = None

    class Config:
        orm_mode = True # or from_attributes = True for Pydantic v2

class TokenData(BaseModel):
    email: Optional[str] = None

class Token(BaseModel):
    access_token: str
    token_type: str