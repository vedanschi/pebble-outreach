# backend/src/models/user_models.py
from typing import Optional, List
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Enum as SQLEnum
from sqlalchemy.orm import relationship
from pydantic import BaseModel, EmailStr, validator
import enum

# --- SQLAlchemy Base ---
try:
    from src.database import Base
except ImportError:
    from sqlalchemy.ext.declarative import declarative_base
    print("WARNING: Using local Base for User ORM model as shared Base not found.")
    Base = declarative_base()

# --- Enums ---
class UserRole(str, enum.Enum):
    ADMIN = "admin"
    MANAGER = "manager"
    AGENT = "agent"
    USER = "user"

# --- SQLAlchemy ORM Model ---
class User(Base):
    """User model for database representation"""
    __tablename__ = "users"

    # Primary fields
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(255))

    # Role and company information
    role = Column(SQLEnum(UserRole), default=UserRole.USER, nullable=False)
    company_name = Column(String(255))

    # Status and timestamps
    is_active = Column(Boolean, default=True, nullable=False)
    email_verified = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), 
                       default=datetime.utcnow, 
                       onupdate=datetime.utcnow,
                       nullable=False)
    last_login = Column(DateTime(timezone=True))

    # Relationships
    campaigns = relationship(
        "Campaign",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="selectin"
    )

    def __repr__(self) -> str:
        return f"User(id={self.id}, email={self.email}, role={self.role})"

# --- Pydantic Models ---
class UserBase(BaseModel):
    """Base Pydantic model for User data"""
    email: EmailStr
    full_name: Optional[str] = None
    role: Optional[UserRole] = UserRole.USER
    company_name: Optional[str] = None

    @validator('full_name')
    def validate_full_name(cls, v):
        if v:
            v = v.strip()
            if len(v) < 2:
                raise ValueError('Full name must be at least 2 characters long')
        return v

class UserCreate(UserBase):
    """Model for user creation requests"""
    password: str

    @validator('password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not any(char.isupper() for char in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(char.islower() for char in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(char.isdigit() for char in v):
            raise ValueError('Password must contain at least one number')
        return v

class UserCreateDB(UserBase):
    """Internal model for database operations"""
    password_hash: str
    is_active: bool = True
    email_verified: bool = False

class UserUpdate(BaseModel):
    """Model for user update requests"""
    full_name: Optional[str] = None
    role: Optional[UserRole] = None
    company_name: Optional[str] = None
    is_active: Optional[bool] = None

    class Config:
        use_enum_values = True

class UserResponse(UserBase):
    """Model for user response data"""
    id: int
    is_active: bool
    email_verified: bool
    created_at: datetime
    updated_at: datetime
    last_login: Optional[datetime] = None

    class Config:
        from_attributes = True

class UserLogin(BaseModel):
    """Model for login requests"""
    email: EmailStr
    password: str

    @validator('password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        return v

class TokenData(BaseModel):
    """Model for JWT token data"""
    sub: Optional[str] = None
    role: Optional[UserRole] = None
    exp: Optional[datetime] = None

class Token(BaseModel):
    """Model for JWT token response"""
    access_token: str
    token_type: str = "bearer"
    expires_at: datetime

# --- Additional Models ---
class PasswordReset(BaseModel):
    """Model for password reset requests"""
    email: EmailStr

class PasswordUpdate(BaseModel):
    """Model for password update requests"""
    current_password: str
    new_password: str

    @validator('new_password')
    def validate_new_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not any(char.isupper() for char in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(char.islower() for char in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(char.isdigit() for char in v):
            raise ValueError('Password must contain at least one number')
        return v

class EmailVerification(BaseModel):
    """Model for email verification requests"""
    token: str


