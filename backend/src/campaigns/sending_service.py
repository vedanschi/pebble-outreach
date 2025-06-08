# backend/src/campaigns/sending_service.py
from typing import Tuple, List, Optional, Dict, Any
import datetime
import uuid # For tracking_pixel_id

from sqlalchemy.orm import Session, joinedload
from sqlalchemy import select, and_

# Assuming settings are available for APP_BASE_URL
try:
    from src.core.config import settings
except ImportError:
    class settings: # Placeholder
        APP_BASE_URL: str = "http://localhost:8000" # Default placeholder

try:
    from src.models.campaign_models import Campaign
    from src.models.contact_models import Contact
    from src.models.email_template_models import EmailTemplate
    from src.models.sent_email_models import SentEmail # For checking existing sends
    from src.schemas.sent_email_schemas import SentEmailCreate
    from src.email_sending.service import send_single_email_smtp
    from src.followups.db_operations import db_create_sent_email_record # Re-use for logging
except ImportError:
    # Placeholders for robustness
    class Campaign: id: int; status: str; user_id: int; name: str
    class Contact: id: int; email: str; first_name: Optional[str]; company_name: Optional[str]
    class EmailTemplate: id: int; subject_template: str; body_template: str
    class SentEmail: pass
    class SentEmailCreate(BaseModel): # Assuming BaseModel from pydantic
        campaign_id: int; contact_id: int; email_template_id: int; subject: str; body: str
        status: str; sent_at: Optional[datetime.datetime] = None
        is_follow_up: bool = False; follows_up_on_email_id: Optional[int] = None
        triggered_by_rule_id: Optional[int] = None
        tracking_pixel_id: Optional[str] = None # Added for tracking
        def model_dump(self): return {}

    async def send_single_email_smtp(recipient_email: str, subject: str, body: str, smtp_config: dict) -> Tuple[bool, Optional[str]]:
        return True, None
    async def db_create_sent_email_record(db: Session, email_data: SentEmailCreate) -> SentEmail:
        return SentEmail()


class CampaignSendingError(Exception):
    pass

async def process_and_send_campaign(
    campaign_id: int,
    db: Session,
    smtp_config: dict # Loaded from app settings/env
) -> Tuple[int, int]:
    """
    Processes a campaign, sending initial emails to eligible contacts.

    Returns:
        Tuple (successful_sends, failed_sends).
    """
    successful_sends = 0
    failed_sends = 0

    # 1. Fetch Campaign
    campaign_stmt = select(Campaign).where(Campaign.id == campaign_id)
    campaign: Optional[Campaign] = (await db.execute(campaign_stmt)).scalars().first()

    if not campaign:
        raise CampaignSendingError(f"Campaign with id {campaign_id} not found.")

    # Check campaign status (example: only send if 'active' or 'pending')
    # This status logic might be more complex in a real app (e.g., 'paused', 'archived')
    if campaign.status not in ["active", "sending", "pending"]: # Assuming "pending" is a valid start state
        print(f"Campaign {campaign_id} is not in a sendable status (current: {campaign.status}). No emails will be sent.")
        return 0, 0

    # Update campaign status to 'sending' if it's not already
    if campaign.status != "sending":
        campaign.status = "sending"
        db.add(campaign)
        db.commit() # Commit status change early

    # 2. Fetch Primary Email Template
    # Assuming the first template linked to the campaign is the primary one.
    # This could be made more robust with a specific flag on EmailTemplate or a dedicated relationship.
    template_stmt = select(EmailTemplate).where(EmailTemplate.campaign_id == campaign_id)
    email_template: Optional[EmailTemplate] = (await db.execute(template_stmt)).scalars().first()

    if not email_template:
        # Update campaign status to 'failed' or 'error_no_template'
        campaign.status = "error_no_template"
        db.add(campaign)
        db.commit()
        raise CampaignSendingError(f"No email template found for campaign {campaign_id}.")

    # 3. Fetch Contacts for this campaign that have not yet received an initial email or failed previously
    # Subquery to find contact_ids that have a 'sent' or 'delivered' initial email for this campaign
    subquery_sent_contacts = select(SentEmail.contact_id).where(
        SentEmail.campaign_id == campaign_id,
        SentEmail.follows_up_on_email_id == None, # Identifies initial emails
        SentEmail.status.in_(['sent', 'delivered', 'opened', 'clicked', 'replied']) # Successfully sent
    ).distinct()

    # Main query for contacts
    contacts_stmt = select(Contact).where(
        Contact.campaign_id == campaign_id,
        Contact.id.notin_(subquery_sent_contacts) # Exclude contacts that already got a successful initial email
    )

    eligible_contacts: List[Contact] = (await db.execute(contacts_stmt)).scalars().all()

    if not eligible_contacts:
        print(f"No eligible contacts found for campaign {campaign_id} to send initial emails.")
        # If no contacts, campaign might be considered 'completed' or back to 'active' if it was 'pending'
        if campaign.status == "sending": # Only change if it was actively sending.
            campaign.status = "completed" # Or 'active' if it can be re-run
            db.add(campaign)
            db.commit()
        return 0, 0

    # 4. Loop through eligible contacts
    for contact in eligible_contacts:
        if not contact.email: # Skip if contact has no email
            failed_sends +=1 # Or just log and skip
            print(f"Contact {contact.id} has no email address. Skipping.")
            continue

        # 5. Personalize subject and body
        subject = (email_template.subject_template or "").replace("{{first_name}}", contact.first_name or "there")
        subject = subject.replace("{{company_name}}", contact.company_name or "your company")

        body = (email_template.body_template or "").replace("{{first_name}}", contact.first_name or "there")
        body = body.replace("{{company_name}}", contact.company_name or "your company")

        # Generate tracking pixel
        tracking_pixel_id = uuid.uuid4().hex
        pixel_url = f"{settings.APP_BASE_URL}/track/open/{tracking_pixel_id}.png"
        pixel_img_tag = f'<img src="{pixel_url}" width="1" height="1" alt="" style="display:none;">'

        # Append pixel to body (ensure body is HTML)
        # A more robust solution would parse HTML and append before </body>, or handle plain text.
        # For now, simple append. Assume body is HTML.
        final_body = body + pixel_img_tag

        # 6. Call send_single_email_smtp
        send_success, error_message = await send_single_email_smtp(
            recipient_email=contact.email,
            subject=subject,
            body=final_body, # Send body with embedded pixel
            smtp_config=smtp_config
        )

        current_time = datetime.datetime.utcnow()
        sent_email_status = ""

        if send_success:
            sent_email_status = "sent"
            successful_sends += 1
            print(f"Successfully sent email to {contact.email} for campaign {campaign_id}.")
        else:
            sent_email_status = "failed"
            failed_sends += 1
            print(f"Failed to send email to {contact.email} for campaign {campaign_id}. Error: {error_message}")

        # 7. Log the attempt, including tracking_pixel_id
        sent_email_data = SentEmailCreate(
            campaign_id=campaign.id,
            contact_id=contact.id,
            email_template_id=email_template.id,
            subject=subject,
            body=final_body, # Store the body with the pixel for record-keeping
            status=sent_email_status,
            sent_at=current_time if send_success else None,
            is_follow_up=False,
            follows_up_on_email_id=None,
            triggered_by_rule_id=None,
            tracking_pixel_id=tracking_pixel_id # Store the generated pixel ID
        )
        try:
            await db_create_sent_email_record(db, sent_email_data)
        except Exception as e:
            print(f"Error logging sent email record for contact {contact.id}, campaign {campaign_id}: {e}")
            # Decide if this failure should count towards failed_sends or be handled differently
            if send_success: # If email was sent but logging failed
                # This is problematic. The email is out, but we couldn't record it.
                # This might lead to duplicate sends on retry if not handled carefully.
                # For now, we've already incremented successful_sends.
                print(f"CRITICAL: Email sent to {contact.email} but FAILED to log to SentEmail table.")


    # 8. Update Campaign.status
    # If there were failures, status might be 'active_with_errors' or similar.
    # If all were successful, 'completed'.
    # This logic can be refined.
    if failed_sends > 0 and successful_sends > 0:
        campaign.status = "active_with_errors"
    elif failed_sends > 0 and successful_sends == 0:
        campaign.status = "failed" # All attempts failed
    elif failed_sends == 0 and successful_sends > 0:
        # Check if there are any more contacts that were not processed in this run
        # (e.g. if eligible_contacts was a paginated batch)
        # For now, assume all eligible contacts were processed in this run.
        campaign.status = "completed"
    # If successful_sends == 0 and failed_sends == 0 (e.g. no contacts), status was handled earlier.

    db.add(campaign)
    db.commit()

    return successful_sends, failed_sends

```
