# backend/src/email_sending/draft_service.py
from typing import Tuple, List, Optional, Dict, Any
from datetime import datetime
from uuid import uuid4

from sqlalchemy.orm import Session, joinedload
from sqlalchemy import select

from src.models.user_models import SentEmail, Contact, Campaign, EmailTemplate
from src.core.config import settings
from .service import EmailSendingService

class DraftSendingError(Exception):
    """Custom exception for draft email sending issues."""
    pass

async def send_pending_emails(
    db: Session,
    batch_limit: int = 50
) -> Tuple[int, int]:
    """
    Processes and sends emails marked as 'draft' or 'pending_send'.
    Handles personalization, tracking pixels, and campaign management.

    Args:
        db: SQLAlchemy Session
        batch_limit: Maximum number of emails to process in one batch

    Returns:
        Tuple (successful_sends, failed_sends)
    """
    successful_sends = 0
    failed_sends = 0
    email_service = EmailSendingService(db)

    print(f"DRAFT_SENDER: Processing pending emails at {datetime.utcnow()} UTC")

    # Query for pending emails with all needed relationships
    stmt = (
        select(SentEmail)
        .options(
            joinedload(SentEmail.contact),
            joinedload(SentEmail.campaign),
            joinedload(SentEmail.email_template)
        )
        .where(SentEmail.status.in_(['draft', 'pending_send']))
        .order_by(SentEmail.created_at)
        .limit(batch_limit)
    )

    pending_emails = db.execute(stmt).scalars().all()

    if not pending_emails:
        print("DRAFT_SENDER: No pending emails found.")
        return 0, 0

    print(f"DRAFT_SENDER: Processing {len(pending_emails)} emails")

    for email in pending_emails:
        if not email.contact or not email.contact.email:
            print(f"DRAFT_SENDER: Email {email.id} missing contact information")
            await _update_email_status(db, email, "failed", "Missing contact information")
            failed_sends += 1
            continue

        try:
            # Mark as sending
            await _update_email_status(db, email, "sending")

            # Personalize email content
            subject = _personalize_content(email.subject, email.contact)
            body = _personalize_content(email.body, email.contact)

            # Add tracking pixel
            tracking_pixel_id = str(uuid4())
            body = _add_tracking_pixel(body, tracking_pixel_id)

            # Send email
            success, error = await email_service._send_single_email(
                recipient_email=email.contact.email,
                subject=subject,
                body=body
            )

            if success:
                await _update_email_status(
                    db, 
                    email, 
                    "sent",
                    tracking_pixel_id=tracking_pixel_id,
                    sent_at=datetime.utcnow()
                )
                successful_sends += 1
                print(f"DRAFT_SENDER: Successfully sent email {email.id} to {email.contact.email}")
            else:
                await _update_email_status(db, email, "failed", error)
                failed_sends += 1
                print(f"DRAFT_SENDER: Failed to send email {email.id}: {error}")

        except Exception as e:
            await _update_email_status(db, email, "failed", str(e))
            failed_sends += 1
            print(f"DRAFT_SENDER: Error processing email {email.id}: {str(e)}")

    print(f"DRAFT_SENDER: Batch complete. Success: {successful_sends}, Failed: {failed_sends}")
    return successful_sends, failed_sends

def _personalize_content(content: str, contact: Contact) -> str:
    """
    Personalizes email content with contact information.
    """
    replacements = {
        "{first_name}": contact.first_name,
        "{last_name}": contact.last_name,
        "{full_name}": contact.full_name,
        "{company_name}": contact.company_name,
        "{job_title}": contact.job_title or "",
        "{company_website}": contact.company_website or "",
        "{industry}": contact.industry or "",
        "{city}": contact.city or "",
        "{country}": contact.country or "",
        "{linkedin_url}": contact.linkedin_url or "",
    }

    personalized = content
    for key, value in replacements.items():
        personalized = personalized.replace(key, str(value))
    
    return personalized

def _add_tracking_pixel(body: str, tracking_pixel_id: str) -> str:
    """
    Adds a tracking pixel to the email body.
    """
    pixel_url = f"{settings.APP_BASE_URL}/track/{tracking_pixel_id}"
    tracking_pixel = f'<img src="{pixel_url}" width="1" height="1" alt="" style="display:none" />'
    
    # Insert before closing </body> tag if it exists, otherwise append
    if "</body>" in body:
        return body.replace("</body>", f"{tracking_pixel}</body>")
    return f"{body}{tracking_pixel}"

async def _update_email_status(
    db: Session,
    email: SentEmail,
    status: str,
    status_reason: Optional[str] = None,
    tracking_pixel_id: Optional[str] = None,
    sent_at: Optional[datetime] = None
) -> None:
    """
    Updates email status and related fields in the database.
    """
    try:
        email.status = status
        email.status_reason = status_reason
        if tracking_pixel_id:
            email.tracking_pixel_id = tracking_pixel_id
        if sent_at:
            email.sent_at = sent_at
        
        db.add(email)
        db.commit()
        db.refresh(email)
    except Exception as e:
        db.rollback()
        print(f"DRAFT_SENDER: Failed to update email {email.id} status: {str(e)}")
        raise

async def schedule_follow_ups(db: Session) -> None:
    """
    Schedules follow-up emails based on campaign rules and email status.
    """
    # Query sent emails that might need follow-ups
    sent_emails = (
        db.query(SentEmail)
        .filter(
            SentEmail.status == "sent",
            SentEmail.is_follow_up == False,  # Only original emails
            SentEmail.sent_at <= datetime.utcnow()  # Sent some time ago
        )
        .all()
    )

    for email in sent_emails:
        campaign = db.query(Campaign).filter(Campaign.id == email.campaign_id).first()
        if not campaign:
            continue

        # Check if follow-up conditions are met (e.g., email not opened after X days)
        if _should_send_follow_up(email):
            await create_follow_up_draft(db, email)

def _should_send_follow_up(email: SentEmail) -> bool:
    """
    Determines if a follow-up email should be sent based on rules.
    """
    if not email.opened_at and (datetime.utcnow() - email.sent_at).days >= 3:
        return True
    return False

async def create_follow_up_draft(db: Session, original_email: SentEmail) -> None:
    """
    Creates a draft follow-up email.
    """
    template = db.query(EmailTemplate).filter(
        EmailTemplate.campaign_id == original_email.campaign_id,
        EmailTemplate.is_follow_up == True
    ).first()

    if not template:
        return

    follow_up = SentEmail(
        campaign_id=original_email.campaign_id,
        contact_id=original_email.contact_id,
        email_template_id=template.id,
        subject=f"Re: {original_email.subject}",
        body=template.body_template,
        status="draft",
        is_follow_up=True,
        follows_up_on_email_id=original_email.id
    )

    db.add(follow_up)
    db.commit()
