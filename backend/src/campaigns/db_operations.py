# backend/src/campaigns/db_operations.py
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from datetime import datetime

from sqlalchemy import select, and_, exists # Added and_, exists
from src.models.campaign_models import Campaign
from src.models.contact_models import Contact
from src.models.email_template_models import EmailTemplate
from src.models.sent_email_models import SentEmail # Added for subquery
from src.schemas.campaign_schemas import CampaignCreate
from src.schemas.contact_schemas import ContactCreate
from src.schemas.email_template_schemas import EmailTemplateCreate

# Placeholder for custom exceptions if needed
# class CampaignDBError(Exception): pass

async def db_create_campaign(db: Session, campaign_data: CampaignCreate, user_id: int) -> Campaign:
    """
    Creates a new Campaign instance and adds it to the session.
    Does not commit the transaction.
    """
    # Note: The CampaignCreate schema might not have user_id if it's derived from auth.
    # The user_id is passed separately here.
    # Ensure Campaign model's __init__ or field assignment handles this.
    # If CampaignCreate includes user_id, it should be consistent or handled.
    db_campaign = Campaign(
        **campaign_data.model_dump(),
        user_id=user_id # Explicitly setting user_id
        # created_at and updated_at are likely handled by DB defaults or model events
    )
    db.add(db_campaign)
    # No commit here, service layer will handle transaction
    return db_campaign

async def db_create_contact(db: Session, contact_data: ContactCreate, campaign_id: int, owner_id: int) -> Contact:
    """
    Creates a new Contact instance and adds it to the session.
    Does not commit the transaction.
    owner_id added based on Contact model structure for associating with a user.
    """
    db_contact = Contact(
        **contact_data.model_dump(),
        campaign_id=campaign_id,
        owner_id=owner_id # Set owner_id for the contact
    )
    db.add(db_contact)
    # No commit here, service layer will handle transaction
    return db_contact

# The function db_get_campaign_by_name_and_user is omitted for now as per prompt.
# async def db_get_campaign_by_name_and_user(db: Session, name: str, user_id: int) -> Optional[Campaign]:
#     pass

async def db_create_email_template(
    db: Session,
    template_data: EmailTemplateCreate,
    # owner_id: int, # Removed as EmailTemplate is owned via campaign
    is_primary: bool = False
) -> EmailTemplate:
    """
    Creates a new EmailTemplate instance and adds it to the session.
    Does not commit the transaction.
    """
    db_email_template = EmailTemplate(
        **template_data.model_dump(),
        is_primary=is_primary
    )
    db.add(db_email_template)
    return db_email_template

async def db_get_email_template_by_id(db: Session, template_id: int) -> Optional[EmailTemplate]:
    """
    Fetches an EmailTemplate by its ID.
    """
    statement = select(EmailTemplate).where(EmailTemplate.id == template_id)
    result = await db.execute(statement)
    return result.scalar_one_or_none()

async def db_get_contacts_for_campaign(db: Session, campaign_id: int) -> List[Contact]:
    """
    Fetches all contacts for a given campaign ID.
    """
    statement = select(Contact).where(Contact.campaign_id == campaign_id)
    result = await db.execute(statement)
    return result.scalars().all()

async def db_get_campaign_by_id(db: Session, campaign_id: int) -> Optional[Campaign]:
    """
    Fetches a Campaign by its ID.
    """
    statement = select(Campaign).where(Campaign.id == campaign_id)
    result = await db.execute(statement)
    return result.scalar_one_or_none()

async def db_get_primary_template_for_campaign(db: Session, campaign_id: int) -> Optional[EmailTemplate]:
    """
    Fetches the primary email template for a given campaign ID.
    """
    statement = select(EmailTemplate).where(
        and_( # Explicitly use and_ for multiple conditions
            EmailTemplate.campaign_id == campaign_id,
            EmailTemplate.is_primary == True
        )
    )
    result = await db.execute(statement)
    return result.scalar_one_or_none()

async def db_get_eligible_contacts_for_campaign_sending(db: Session, campaign_id: int) -> List[Contact]:
    """
    Fetches contacts for a campaign that have not yet received the initial email.
    """
    # Subquery for contacts that already received the initial email for this campaign
    subquery = (
        select(SentEmail.contact_id)
        .where(
            SentEmail.campaign_id == campaign_id,
            SentEmail.is_follow_up == False, # Initial email, not a follow-up
            SentEmail.status.in_(['sent', 'delivered', 'opened', 'clicked', 'replied']) # Considered "successfully processed"
        )
        .distinct()
    )

    statement = (
        select(Contact)
        .where(
            Contact.campaign_id == campaign_id,
            Contact.id.notin_(subquery) # Contact has not received the initial email
            # Add other eligibility criteria if needed, e.g., not unsubscribed
            # Contact.unsubscribed == False
        )
    )
    result = await db.execute(statement)
    return result.scalars().all()
