# src/api/deps.py
"""
Common dependencies for API routes (e.g., get_current_user, pagination, etc.)
"""
from fastapi import Depends
from src.database import get_db

# Example dependency for DB session
get_db_session = Depends(get_db)

# You can add more shared dependencies here, e.g.:
# def get_pagination_params(...): ...
