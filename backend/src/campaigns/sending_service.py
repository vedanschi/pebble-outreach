# backend/src/campaigns/sending_service.py
from typing import Tuple, List, Optional, Dict, Any
from datetime import datetime
import uuid
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import select, and_

from src.core.config import settings
from src.models.user_models import Campaign, Contact, EmailTemplate, SentEmail
from src.schemas.email_schemas import SentEmailCreate
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

        # Get campaign with related data
        campaign = await self._get_campaign(campaign_id)
        if not campaign:
            raise CampaignSendingError(f"Campaign {campaign_id} not found")

        # Validate campaign status
        if not self._is_campaign_sendable(campaign):
            return 0, 0

        # Update campaign status to sending
        await self._update_campaign_status(campaign, "sending")

        # Get email template
        template = await self._get_campaign_template(campaign_id)
        if not template:
            await self._update_campaign_status(campaign, "error_no_template")
            raise CampaignSendingError(f"No template found for campaign {campaign_id}")

        # Get eligible contacts
        contacts = await self._get_eligible_contacts(campaign_id)
        if not contacts:
            await self._update_campaign_status(campaign, "completed")
            return 0, 0

        # Process each contact
        for contact in contacts:
            success, error = await self._process_contact(campaign, contact, template)
            if success:
                successful_sends += 1
            else:
                failed_sends += 1
                print(f"Failed to send to {contact.email}: {error}")

        # Update final campaign status
        await self._update_final_campaign_status(campaign, successful_sends, failed_sends)

        return successful_sends, failed_sends

    async def _get_campaign(self, campaign_id: int) -> Optional[Campaign]:
        """Fetches campaign with related data"""
        stmt = select(Campaign).where(Campaign.id == campaign_id)
        return (await self.db.execute(stmt)).scalar_one_or_none()

    def _is_campaign_sendable(self, campaign: Campaign) -> bool:
        """Checks if campaign is in a sendable state"""
        return campaign.status in ["active", "sending", "pending"]

    async def _update_campaign_status(self, campaign: Campaign, status: str) -> None:
        """Updates campaign status"""
        campaign.status = status
        self.db.add(campaign)
        await self.db.commit()

    async def _get_campaign_template(self, campaign_id: int) -> Optional[EmailTemplate]:
        """Fetches primary email template for campaign"""
        stmt = select(EmailTemplate).where(
            EmailTemplate.campaign_id == campaign_id,
            EmailTemplate.is_primary == True
        )
        return (await self.db.execute(stmt)).scalar_one_or_none()

    async def _get_eligible_contacts(self, campaign_id: int) -> List[Contact]:
        """Gets contacts that haven't received initial email"""
        # Subquery for contacts that already received emails
        sent_contacts = select(SentEmail.contact_id).where(
            SentEmail.campaign_id == campaign_id,
            SentEmail.is_follow_up == False,
            SentEmail.status.in_(['sent', 'delivered', 'opened', 'clicked', 'replied'])
        ).distinct()

        # Main query for eligible contacts
        stmt = select(Contact).where(
            Contact.campaign_id == campaign_id,
            Contact.id.notin_(sent_contacts)
        )
        return (await self.db.execute(stmt)).scalars().all()

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
            success, error = await self.email_service.send_single_email(
                contact.email,
                subject,
                final_body
            )

            # Record email status
            await self._create_sent_email_record(
                campaign=campaign,
                contact=contact,
                template=template,
                subject=subject,
                body=final_body,
                tracking_pixel_id=tracking_pixel_id,
                success=success,
                error=error
            )

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
        
        if "</body>" in body:
            return body.replace("</body>", f"{pixel_tag}</body>")
        return f"{body}{pixel_tag}"

    async def _create_sent_email_record(
        self,
        campaign: Campaign,
        contact: Contact,
        template: EmailTemplate,
        subject: str,
        body: str,
        tracking_pixel_id: str,
        success: bool,
        error: Optional[str]
    ) -> None:
        """Creates a record of the sent email"""
        sent_email = SentEmailCreate(
            campaign_id=campaign.id,
            contact_id=contact.id,
            email_template_id=template.id,
            subject=subject,
            body=body,
            status="sent" if success else "failed",
            status_reason=error if not success else None,
            sent_at=datetime.utcnow() if success else None,
            is_follow_up=False,
            tracking_pixel_id=tracking_pixel_id
        )

        db_sent_email = SentEmail(**sent_email.dict())
        self.db.add(db_sent_email)
        await self.db.commit()

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
