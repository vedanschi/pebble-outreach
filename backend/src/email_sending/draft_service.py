# backend/src/email_sending/draft_service.py
from typing import Tuple, List, Optional, Dict, Any
import datetime

from sqlalchemy.orm import Session, selectinload, joinedload
from sqlalchemy import select

try:
    from src.models.sent_email_models import SentEmail
    from src.models.contact_models import Contact # To get recipient_email if not directly on SentEmail
    from src.email_sending.service import send_single_email_smtp
except ImportError:
    # Placeholders for robustness
    class SentEmail:
        id: int; subject: str; body: str; status: str; contact_id: int
        sent_at: Optional[datetime.datetime]; status_reason: Optional[str]
        # Assuming a relationship 'contact' that has an 'email' attribute
        contact: 'Contact'
    class Contact:
        id: int; email: str

    async def send_single_email_smtp(recipient_email: str, subject: str, body: str, smtp_config: dict) -> Tuple[bool, Optional[str]]:
        print(f"Mock sending email to {recipient_email} with subject '{subject}'")
        # Simulate random success/failure for testing scheduler
        # import random
        # if random.choice([True, False]):
        #     return True, None
        # else:
        #     return False, "Simulated SMTP error"
        return True, None # Default to success for less noise during non-focused tests


class DraftSendingError(Exception):
    pass

async def send_pending_emails(
    db: Session,
    smtp_config: Dict[str, Any],
    batch_limit: int = 50
) -> Tuple[int, int]:
    """
    Processes and sends emails marked as 'draft' or 'pending_send'.

    Args:
        db: SQLAlchemy Session.
        smtp_config: SMTP configuration dictionary.
        batch_limit: Maximum number of emails to process in this run.

    Returns:
        Tuple (successful_sends, failed_sends).
    """
    successful_sends = 0
    failed_sends = 0

    print(f"DRAFT_SENDER: Checking for pending emails at {datetime.datetime.utcnow()} UTC")

    # 1. Query for 'draft' or 'pending_send' emails, up to batch_limit
    #    Load the related Contact to get the email address.
    stmt = (
        select(SentEmail)
        .options(joinedload(SentEmail.contact)) # Ensure contact is loaded to get email
        .where(SentEmail.status.in_(['draft', 'pending_send']))
        .order_by(SentEmail.created_at) # Process older drafts first
        .limit(batch_limit)
    )

    pending_emails_results = await db.execute(stmt)
    emails_to_send: List[SentEmail] = pending_emails_results.scalars().all()

    if not emails_to_send:
        print("DRAFT_SENDER: No pending emails to send in this batch.")
        return 0, 0

    print(f"DRAFT_SENDER: Found {len(emails_to_send)} emails to process.")

    for email_record in emails_to_send:
        if not email_record.contact or not email_record.contact.email:
            print(f"DRAFT_SENDER: Email record ID {email_record.id} missing contact or contact email. Skipping.")
            email_record.status = "failed"
            email_record.status_reason = "Missing contact information"
            db.add(email_record)
            failed_sends += 1
            continue # Skip to the next email

        recipient_email = email_record.contact.email

        # 2. Update status to 'sending' and commit to lock the record
        email_record.status = "sending"
        email_record.status_reason = None # Clear previous reason
        db.add(email_record)
        try:
            db.commit()
            print(f"DRAFT_SENDER: Marked email ID {email_record.id} for {recipient_email} as 'sending'.")
        except Exception as e:
            db.rollback()
            print(f"DRAFT_SENDER: Error marking email ID {email_record.id} as 'sending'. DB Error: {e}. Skipping.")
            # This email will be picked up in the next run if the DB error is transient.
            # No increment to failed_sends here as it wasn't an SMTP failure yet.
            continue

        # 3. Call send_single_email_smtp
        send_success, error_message = await send_single_email_smtp(
            recipient_email=recipient_email,
            subject=email_record.subject,
            body=email_record.body, # Assuming body is already personalized and stored
            smtp_config=smtp_config
        )

        # 4. Update status based on send result
        if send_success:
            email_record.status = "sent"
            email_record.sent_at = datetime.datetime.utcnow()
            email_record.status_reason = None
            successful_sends += 1
            print(f"DRAFT_SENDER: Successfully sent email ID {email_record.id} to {recipient_email}.")
        else:
            email_record.status = "failed"
            email_record.status_reason = error_message or "Unknown SMTP error"
            failed_sends += 1
            print(f"DRAFT_SENDER: Failed to send email ID {email_record.id} to {recipient_email}. Error: {error_message}")

        db.add(email_record)
        try:
            db.commit() # Commit status update for this email
        except Exception as e:
            db.rollback()
            print(f"DRAFT_SENDER: CRITICAL - DB Error updating status for email ID {email_record.id} after send attempt. DB Error: {e}.")
            # If successful send, but this commit fails, email is sent but status not updated.
            # If failed send, and this commit fails, status remains 'sending'.
            # This scenario needs careful monitoring/manual intervention if it occurs frequently.
            # For now, the successful/failed_sends count reflects the SMTP attempt.

    print(f"DRAFT_SENDER: Batch processing complete. Successful: {successful_sends}, Failed: {failed_sends}")
    return successful_sends, failed_sends

```
