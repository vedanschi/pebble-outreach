# backend/src/users/db_operations.py
from typing import Optional, List
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import select, update, and_, or_
from sqlalchemy.exc import IntegrityError

from src.models.user_models import User, UserRole
from src.schemas.user_schemas import UserCreateDB, UserUpdate, PasswordUpdate
from src.core.config.security import get_password_hash, verify_password

class UserDBError(Exception):
    """Base exception for user database operations"""
    pass

class UserNotFoundError(UserDBError):
    """Raised when a user is not found"""
    pass

class EmailAlreadyExistsError(UserDBError):
    """Raised when trying to create a user with an existing email"""
    pass

async def db_get_user_by_email(db: Session, email: str) -> Optional[User]:
    """
    Retrieves a user from the database by their email address.
    
    Args:
        db: Database session
        email: User's email address
    
    Returns:
        User object if found, None otherwise
    """
    statement = select(User).where(User.email == email)
    result = await db.execute(statement)
    return result.scalar_one_or_none()

async def db_get_user_by_id(db: Session, user_id: int) -> Optional[User]:
    """
    Retrieves a user from the database by their ID.
    
    Args:
        db: Database session
        user_id: User's ID
    
    Returns:
        User object if found, None otherwise
    """
    statement = select(User).where(User.id == user_id)
    result = await db.execute(statement)
    return result.scalar_one_or_none()

async def db_create_user(db: Session, user_create_data: UserCreateDB) -> User:
    """
    Creates a new user in the database.
    
    Args:
        db: Database session
        user_create_data: Validated user creation data with hashed password
    
    Returns:
        Created User object
    
    Raises:
        EmailAlreadyExistsError: If email already exists
    """
    try:
        db_user = User(**user_create_data.model_dump())
        db.add(db_user)
        await db.commit()
        await db.refresh(db_user)
        return db_user
    except IntegrityError:
        await db.rollback()
        raise EmailAlreadyExistsError(f"Email {user_create_data.email} already registered")

async def db_update_user(
    db: Session,
    user_id: int,
    user_update_data: UserUpdate
) -> User:
    """
    Updates an existing user's information.
    
    Args:
        db: Database session
        user_id: User's ID
        user_update_data: Validated update data
    
    Returns:
        Updated User object
    
    Raises:
        UserNotFoundError: If user is not found
    """
    db_user = await db_get_user_by_id(db, user_id)
    if not db_user:
        raise UserNotFoundError(f"User with ID {user_id} not found")

    update_data = user_update_data.model_dump(exclude_unset=True)
    if update_data:
        for key, value in update_data.items():
            setattr(db_user, key, value)
        
        db_user.updated_at = datetime.utcnow()
        db.add(db_user)
        await db.commit()
        await db.refresh(db_user)
    
    return db_user

async def db_update_password(
    db: Session,
    user_id: int,
    current_password: str,
    new_password: str
) -> bool:
    """
    Updates a user's password.
    
    Args:
        db: Database session
        user_id: User's ID
        current_password: Current password for verification
        new_password: New password to set
    
    Returns:
        True if password was updated successfully
    
    Raises:
        UserNotFoundError: If user is not found
        ValueError: If current password is incorrect
    """
    db_user = await db_get_user_by_id(db, user_id)
    if not db_user:
        raise UserNotFoundError(f"User with ID {user_id} not found")

    if not verify_password(current_password, db_user.password_hash):
        raise ValueError("Current password is incorrect")

    db_user.password_hash = get_password_hash(new_password)
    db_user.updated_at = datetime.utcnow()
    db.add(db_user)
    await db.commit()
    return True

async def db_verify_email(db: Session, user_id: int) -> User:
    """
    Marks a user's email as verified.
    
    Args:
        db: Database session
        user_id: User's ID
    
    Returns:
        Updated User object
    
    Raises:
        UserNotFoundError: If user is not found
    """
    db_user = await db_get_user_by_id(db, user_id)
    if not db_user:
        raise UserNotFoundError(f"User with ID {user_id} not found")

    db_user.email_verified = True
    db_user.updated_at = datetime.utcnow()
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return db_user

async def db_update_last_login(db: Session, user_id: int) -> None:
    """
    Updates the last login timestamp for a user.
    
    Args:
        db: Database session
        user_id: User's ID
    
    Raises:
        UserNotFoundError: If user is not found
    """
    db_user = await db_get_user_by_id(db, user_id)
    if not db_user:
        raise UserNotFoundError(f"User with ID {user_id} not found")

    db_user.last_login = datetime.utcnow()
    db.add(db_user)
    await db.commit()

async def db_deactivate_user(db: Session, user_id: int) -> User:
    """
    Deactivates a user account.
    
    Args:
        db: Database session
        user_id: User's ID
    
    Returns:
        Updated User object
    
    Raises:
        UserNotFoundError: If user is not found
    """
    db_user = await db_get_user_by_id(db, user_id)
    if not db_user:
        raise UserNotFoundError(f"User with ID {user_id} not found")

    db_user.is_active = False
    db_user.updated_at = datetime.utcnow()
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return db_user

async def db_search_users(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    role: Optional[UserRole] = None,
    is_active: Optional[bool] = None
) -> List[User]:
    """
    Searches users based on various criteria.
    
    Args:
        db: Database session
        skip: Number of records to skip
        limit: Maximum number of records to return
        search: Search term for email or full_name
        role: Filter by user role
        is_active: Filter by active status
    
    Returns:
        List of matching User objects
    """
    query = select(User)
    
    conditions = []
    if search:
        conditions.append(
            or_(
                User.email.ilike(f"%{search}%"),
                User.full_name.ilike(f"%{search}%")
            )
        )
    if role:
        conditions.append(User.role == role)
    if is_active is not None:
        conditions.append(User.is_active == is_active)
    
    if conditions:
        query = query.where(and_(*conditions))
    
    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()
