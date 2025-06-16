from typing import Any, Dict, Optional
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

async def check_database_connection(session: AsyncSession) -> Dict[str, Any]:
    """Check database connection and return status"""
    try:
        result = await session.execute(text("SELECT 1"))
        await result.scalar_one()
        return {
            "status": "connected",
            "message": "Successfully connected to database"
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Database connection failed: {str(e)}"
        }

async def create_database_tables(engine: Any) -> None:
    """Create all database tables"""
    from src.models import Base
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)