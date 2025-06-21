# backend/src/campaigns/sending_service.py
from typing import Tuple, List, Optional, Dict, Any
from datetime import datetime
import uuid
from sqlalchemy.orm import Session # Keep Session
# Remove select, and_ if not used directly after refactor
# from sqlalchemy import select, and_
import uuid # Keep uuid

from src.core.config import settings
# Model imports might not be needed if all DB access is via db_operations
# from src.models.user_models import Campaign, Contact, EmailTemplate, SentEmail
from src.models.user_models import Campaign, Contact, EmailTemplate # Keep for type hints if methods return them
from src.schemas.email_schemas import SentEmailCreate # Keep for creating SentEmail
from src.email_sending.service import send_single_email_smtp # Keep
from src.email_sending.db_operations import db_create_sent_email # New
from .db_operations import ( # New
    db_get_campaign_by_id,
    db_get_primary_template_for_campaign,
    db_get_eligible_contacts_for_campaign_sending
)
# This import might still be needed if other methods of EmailSendingService are used by CampaignSendingService
from src.email_sending.service import EmailSendingService


class CampaignSendingError(Exception):
    """Custom exception for campaign sending errors"""
    pass

class CampaignSendingService:
    def __init__(self, db: Session):
        self.db = db
        self.email_service = EmailSendingService(db)

    async def process_and_send_campaign(
        self,
        campaign_id: int,
    ) -> Tuple[int, int]:
        """
        Processes a campaign and sends emails to eligible contacts.
        
        Args:
            campaign_id: ID of the campaign to process
            
        Returns:
            Tuple of (successful_sends, failed_sends)
        """
        successful_sends = 0
        failed_sends = 0

        # Get campaign with related data using DB operation
        campaign = await db_get_campaign_by_id(self.db, campaign_id)
        if not campaign:
            # No need to update campaign status if not found initially
            raise CampaignSendingError(f"Campaign {campaign_id} not found")

        # Validate campaign status
        if not self._is_campaign_sendable(campaign):
            # Campaign status not suitable for sending, no status update needed beyond what it is
            return 0, 0 # Or raise error if this state is unexpected

        # Update campaign status to sending (this commits immediately)
        await self._update_campaign_status(campaign, "sending")

        # Get email template using DB operation
        template = await db_get_primary_template_for_campaign(self.db, campaign_id)
        if not template:
            await self._update_campaign_status(campaign, "error_no_template") # Commit
            raise CampaignSendingError(f"No primary template found for campaign {campaign_id}")

        # Get eligible contacts using DB operation
        contacts = await db_get_eligible_contacts_for_campaign_sending(self.db, campaign_id)
        if not contacts:
            await self._update_campaign_status(campaign, "completed") # Commit
            return 0, 0

        # --- Main Transaction Block for Sending and Recording Emails ---
        all_ops_successful_in_loop = True
        try:
            for contact in contacts:
                success, error = await self._process_contact(campaign, contact, template) # _process_contact now calls db_create_sent_email
                if success:
                    successful_sends += 1
                else:
                    failed_sends += 1
                    all_ops_successful_in_loop = False
                    print(f"Failed to send or record for {contact.email}: {error}")
                    # Decide if one failure should stop all, or continue. Current logic continues.

            if all_ops_successful_in_loop or successful_sends > 0: # Commit if all ops in loop were ok, or if some succeeded.
                await self.db.commit() # Commit all successfully added SentEmail records
            else: # All operations in loop failed or no successful sends
                await self.db.rollback() # Rollback any SentEmail records added to session but not committed

        except Exception as e: # Catch errors from loop or commit
            await self.db.rollback()
            # Log the exception e
            # Update campaign status to reflect an error during the sending batch
            await self._update_campaign_status(campaign, "error_sending_batch")
            raise CampaignSendingError(f"Error during email processing loop for campaign {campaign_id}: {str(e)}")
        # --- End Main Transaction Block ---

        # Update final campaign status (this also commits)
        await self._update_final_campaign_status(campaign, successful_sends, failed_sends)

        return successful_sends, failed_sends

    # _get_campaign method removed, using db_get_campaign_by_id

    def _is_campaign_sendable(self, campaign: Campaign) -> bool:
        """Checks if campaign is in a sendable state"""
        return campaign.status in ["active", "sending", "pending"] # 'sending' included if resuming

    async def _update_campaign_status(self, campaign: Campaign, status: str) -> None:
        """Updates campaign status. This method now handles its own commit for status updates."""
        campaign.status = status
        self.db.add(campaign) # Add to session if it was detached or for clarity
        try:
            await self.db.commit()
            await self.db.refresh(campaign) # Ensure campaign object has updated state if needed later
        except Exception as e:
            await self.db.rollback()
            # Log this error, as it's critical for campaign state
            print(f"Critical Error: Failed to update campaign {campaign.id} status to {status}: {str(e)}")
            # Depending on policy, might re-raise or handle
            raise CampaignSendingError(f"Failed to update campaign status for campaign {campaign.id}: {str(e)}")


    # _get_campaign_template method removed, using db_get_primary_template_for_campaign
    # _get_eligible_contacts method removed, using db_get_eligible_contacts_for_campaign_sending

    async def _process_contact(
        self,
        campaign: Campaign,
        contact: Contact,
        template: EmailTemplate
    ) -> Tuple[bool, Optional[str]]:
        """Processes and sends email to a single contact"""
        if not contact.email:
            return False, "Contact has no email address"

        try:
            # Personalize email
            subject = self._personalize_content(template.subject_template, contact)
            body = self._personalize_content(template.body_template, contact)

            # Add tracking pixel
            tracking_pixel_id = str(uuid.uuid4())
            final_body = self._add_tracking_pixel(body, tracking_pixel_id)

            # Send email
            smtp_config_dict = {
                "host": settings.SMTP_HOST,
                "port": settings.SMTP_PORT,
                "username": settings.SMTP_USER,
                "password": settings.SMTP_PASSWORD,
                "use_tls": settings.SMTP_USE_TLS,
                "sender_email": settings.SMTP_SENDER_EMAIL, # Or a campaign-specific sender if available
                "timeout": settings.SMTP_TIMEOUT if hasattr(settings, 'SMTP_TIMEOUT') else 10 # Default to 10 if not in settings
            }

            success, error = await send_single_email_smtp(
                recipient_email=contact.email,
                subject=subject,
                body=final_body, # This is the body with tracking pixel
                smtp_config=smtp_config_dict
            )

            # Record email status using db_create_sent_email
            # This adds to session, commit happens in process_and_send_campaign
            sent_email_data = SentEmailCreate(
                campaign_id=campaign.id,
                contact_id=contact.id,
                email_template_id=template.id,
                subject=subject,
                body=final_body, # This is the body with tracking pixel
                status="sent" if success else "failed",
                status_reason=error if not success else None,
                sent_at=datetime.utcnow() if success else None,
                is_follow_up=False,
                tracking_pixel_id=tracking_pixel_id
            )
            await db_create_sent_email(self.db, sent_email_data=sent_email_data)
            # Note: db_create_sent_email does not commit.

            return success, error

        except Exception as e:
            return False, str(e)

    def _personalize_content(self, content: str, contact: Contact) -> str:
        """Personalizes email content with contact data"""
        replacements = {
            "{{first_name}}": contact.first_name or "there",
            "{{last_name}}": contact.last_name or "",
            "{{full_name}}": contact.full_name or "",
            "{{company_name}}": contact.company_name or "your company",
            "{{job_title}}": contact.job_title or "",
            "{{industry}}": contact.industry or "",
            "{{city}}": contact.city or "",
            "{{country}}": contact.country or ""
        }

        for key, value in replacements.items():
            content = content.replace(key, value)
        return content

    def _add_tracking_pixel(self, body: str, tracking_pixel_id: str) -> str:
        """Adds tracking pixel to email body"""
        pixel_url = f"{settings.APP_BASE_URL}/track/open/{tracking_pixel_id}.png"
        pixel_tag = f'<img src="{pixel_url}" width="1" height="1" alt="" style="display:none;">'
        
        if "</body>" in body: # Simple check, might need more robust HTML parsing for some cases
            return body.replace("</body>", f"{pixel_tag}</body>", 1) # Replace only once
        return f"{body}{pixel_tag}"

    # _create_sent_email_record method removed, using db_create_sent_email

    async def _update_final_campaign_status(
        self,
        campaign: Campaign,
        successful_sends: int,
        failed_sends: int
    ) -> None:
        """Updates campaign status based on sending results"""
        if failed_sends > 0 and successful_sends > 0:
            status = "active_with_errors"
        elif failed_sends > 0 and successful_sends == 0:
            status = "failed"
        elif failed_sends == 0 and successful_sends > 0:
            status = "completed"
        else:
            status = "completed"  # No contacts to process

        await self._update_campaign_status(campaign, status)
