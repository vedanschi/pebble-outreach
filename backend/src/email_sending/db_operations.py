# backend/src/email_sending/db_operations.py
from sqlalchemy.orm import Session
from typing import Optional # Added Optional for consistency, though not strictly needed by current func

from src.models.sent_email_models import SentEmail
from src.schemas.sent_email_schemas import SentEmailCreate # Assuming path, adjust if different

async def db_create_sent_email(db: Session, sent_email_data: SentEmailCreate) -> SentEmail:
    """
    Creates a new SentEmail record and adds it to the session.
    Does not commit the transaction.
    """
    # Ensure all fields required by SentEmail model are present in SentEmailCreate
    # or handled by defaults in the model.
    db_sent_email = SentEmail(**sent_email_data.model_dump())
    db.add(db_sent_email)
    # No commit here, service layer will handle transaction
    return db_sent_email

async def db_record_email_open_event(
    db: Session,
    tracking_pixel_id: str,
    opened_ip: Optional[str]
) -> bool:
    from sqlalchemy import select, update # Moved imports here to avoid circular if models use these ops
    from datetime import datetime # Moved import here

    # Fetch the email record
    stmt_select = select(SentEmail).where(SentEmail.tracking_pixel_id == tracking_pixel_id)
    # Assuming db.execute is adapted for async if Session is from async_sessionmaker
    # If db is a standard Session, and this is an async def, it implies an async ORM setup.
    # For SQLAlchemy 1.4+ with asyncio, db.execute should be awaited if it's an async session's method.
    # Given other async db ops, we assume db.execute is awaitable.
    result = await db.execute(stmt_select)
    email_record = result.scalar_one_or_none()

    if not email_record:
        return False

    # Prepare updates
    updates_to_apply = {
        "open_count": (email_record.open_count or 0) + 1,
        "last_opened_at": datetime.utcnow()
    }
    if email_record.opened_at is None:
        updates_to_apply["opened_at"] = datetime.utcnow()
    if opened_ip and email_record.first_opened_ip is None:
        updates_to_apply["first_opened_ip"] = opened_ip

    # Update status if appropriate
    # Assuming 'replied' is a status that should also prevent overwriting by 'opened'
    # These are example statuses, adjust to your actual SentEmail status enum/values
    terminal_statuses = ['clicked', 'hard_bounced', 'spam_complaint', 'unsubscribed', 'replied']
    if email_record.status not in terminal_statuses:
        updates_to_apply["status"] = 'opened'

    # Apply updates
    stmt_update = (
        update(SentEmail)
        .where(SentEmail.id == email_record.id)
        .values(**updates_to_apply)
    )
    await db.execute(stmt_update)
    # No commit here, service layer will handle transaction
    return True
