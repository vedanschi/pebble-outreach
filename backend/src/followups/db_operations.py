# backend/src/followups/db_operations.py

from typing import List, Optional, Type
import datetime
import uuid # For generating tracking_pixel_id

from sqlalchemy.orm import Session
from sqlalchemy import select, update, delete, and_, or_, exists

# Assuming ORM models are in src.models.*
# Adjust paths as per your project structure
try:
    from src.models.follow_up_models import FollowUpRule
    from src.models.sent_email_models import SentEmail
    from src.models.contact_models import Contact
    from src.models.email_template_models import EmailTemplate
    # Assuming Pydantic schemas for creation/update are in src.schemas.*
    from src.schemas.sent_email_schemas import SentEmailCreate
    from src.schemas.follow_up_schemas import FollowUpRuleCreate, FollowUpRuleUpdate
except ImportError:
    # Define placeholders if actual models/schemas are not found
    # This helps in defining function signatures without breaking if imports are missing
    # In a real application, these imports must be correct.
    # Placeholder models should reflect the change to delay_days and condition (str)
    class FollowUpRule:
        id: int; campaign_id: int; is_active: bool; delay_days: int; condition: str
        original_email_template_id: int; follow_up_email_template_id: int # Added for completeness
    class SentEmail:
        id: int; campaign_id: int; email_template_id: int; contact_id: int;
        sent_at: Optional[datetime.datetime]; status: str; # sent_at can be optional before sending
        follows_up_on_email_id: Optional[int]; triggered_by_rule_id: Optional[int]
        tracking_pixel_id: Optional[str]; open_count: Optional[int]; opened_at: Optional[datetime.datetime]
        last_opened_at: Optional[datetime.datetime]; first_opened_ip: Optional[str]
    class Contact:
        id: int; unsubscribed: bool; first_name: Optional[str]; email: str
    class EmailTemplate:
        id: int; subject_template: Optional[str]; body_template: Optional[str]

    class SentEmailCreate(Type): # Assumed to now allow optional tracking_pixel_id
        tracking_pixel_id: Optional[str] = None
        def model_dump(self): return {"tracking_pixel_id": self.tracking_pixel_id}
    class FollowUpRuleCreate(Type):
        delay_days: int; condition: str
        campaign_id: int; original_email_template_id: int; follow_up_email_template_id: int; is_active: bool
        def model_dump(self): return {
            "delay_days": self.delay_days, "condition": self.condition,
            "campaign_id": self.campaign_id,
            "original_email_template_id": self.original_email_template_id,
            "follow_up_email_template_id": self.follow_up_email_template_id,
            "is_active": self.is_active
            }
    class FollowUpRuleUpdate(Type): # Assumed to now use delay_days, condition (str)
        delay_days: Optional[int] = None; condition: Optional[str] = None
        original_email_template_id: Optional[int] = None
        follow_up_email_template_id: Optional[int] = None
        is_active: Optional[bool] = None
        def model_dump(self, exclude_unset=True): return {
            "delay_days": self.delay_days, "condition": self.condition,
            "original_email_template_id": self.original_email_template_id,
            "follow_up_email_template_id": self.follow_up_email_template_id,
            "is_active": self.is_active
            }


# --- Database Operations for Follow-up Rules Service ---

async def db_create_follow_up_rule(db: Session, rule_data: FollowUpRuleCreate) -> FollowUpRule:
    """
    Creates a new follow-up rule in the database.
    Interacts with: FollowUpRule ORM model.
    Args:
        db: SQLAlchemy Session.
        rule_data: Pydantic schema FollowUpRuleCreate containing data for the new rule.
    Returns:
        The created FollowUpRule ORM object.
    """
    db_rule = FollowUpRule(**rule_data.model_dump())
    db.add(db_rule)
    db.commit()
    db.refresh(db_rule)
    return db_rule

async def db_get_follow_up_rule(db: Session, rule_id: int) -> Optional[FollowUpRule]:
    """
    Retrieves a specific follow-up rule by its ID.
    Interacts with: FollowUpRule ORM model.
    Args:
        db: SQLAlchemy Session.
        rule_id: The ID of the follow-up rule to retrieve.
    Returns:
        The FollowUpRule ORM object if found, else None.
    """
    statement = select(FollowUpRule).where(FollowUpRule.id == rule_id)
    result = await db.execute(statement)
    return result.scalars().first()

async def db_get_follow_up_rules_for_campaign(db: Session, campaign_id: int) -> List[FollowUpRule]:
    """
    Retrieves all follow-up rules associated with a specific campaign ID.
    Interacts with: FollowUpRule ORM model.
    Args:
        db: SQLAlchemy Session.
        campaign_id: The ID of the campaign.
    Returns:
        A list of FollowUpRule ORM objects.
    """
    statement = select(FollowUpRule).where(FollowUpRule.campaign_id == campaign_id)
    result = await db.execute(statement)
    return result.scalars().all()

async def db_update_follow_up_rule(db: Session, rule_id: int, updates: FollowUpRuleUpdate) -> Optional[FollowUpRule]:
    """
    Updates an existing follow-up rule by its ID.
    Interacts with: FollowUpRule ORM model.
    Args:
        db: SQLAlchemy Session.
        rule_id: The ID of the follow-up rule to update.
        updates: Pydantic schema FollowUpRuleUpdate containing the fields to update.
    Returns:
        The updated FollowUpRule ORM object if found and updated, else None.
    """
    db_rule = await db_get_follow_up_rule(db, rule_id)
    if db_rule:
        update_data = updates.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_rule, key, value)
        db.add(db_rule) # Add back to session if changes were made
        db.commit()
        db.refresh(db_rule)
    return db_rule

async def db_delete_follow_up_rule(db: Session, rule_id: int) -> bool:
    """
    Deletes a follow-up rule by its ID.
    Interacts with: FollowUpRule ORM model.
    Args:
        db: SQLAlchemy Session.
        rule_id: The ID of the follow-up rule to delete.
    Returns:
        True if deletion was successful, False otherwise.
    """
    db_rule = await db_get_follow_up_rule(db, rule_id)
    if db_rule:
        db.delete(db_rule)
        db.commit()
        return True
    return False

# --- Database Operations for Follow-up Processor Service ---

async def db_get_active_follow_up_rules(db: Session) -> List[FollowUpRule]:
    """
    Retrieves all active follow-up rules that need to be processed.
    Interacts with: FollowUpRule ORM model.
    Criteria for "active" might include a status field (e.g., FollowUpRule.is_active == True).
    Args:
        db: SQLAlchemy Session.
    Returns:
        A list of active FollowUpRule ORM objects.
    """
    # Assuming FollowUpRule has an 'is_active' boolean field.
    statement = select(FollowUpRule).where(FollowUpRule.is_active == True)
    result = await db.execute(statement)
    return result.scalars().all()

async def db_get_initial_emails_for_rule(
    db: Session,
    campaign_id: int,
    original_template_id: int,
    rule_condition_str: str, # Changed from rule_conditions: dict
    min_delay_before_followup: datetime.timedelta
) -> List[SentEmail]:
    """
    Retrieves initial emails that match a follow-up rule's criteria and are due for a follow-up.
    Interacts with: SentEmail ORM model, Contact ORM model.
    Args:
        db: SQLAlchemy Session.
        campaign_id: Campaign ID to filter initial emails.
        original_template_id: Template ID of the initial email (FollowUpRule.original_email_template_id).
        rule_condition_str: A string like 'not_opened_within_delay' from FollowUpRule.condition.
        min_delay_before_followup: The minimum time that must have passed since the initial email was sent.
                                   Calculated as (SentEmail.sent_at <= current_time - min_delay_before_followup).
    Returns:
        A list of SentEmail ORM objects representing initial emails eligible for follow-up.
    """
    now = datetime.datetime.utcnow()
    eligible_sent_at_max_time = now - min_delay_before_followup

    stmt = select(SentEmail).join(Contact, SentEmail.contact_id == Contact.id).where(
        SentEmail.campaign_id == campaign_id,
        SentEmail.email_template_id == original_template_id,
        SentEmail.sent_at <= eligible_sent_at_max_time, # Ensure delay has passed
        Contact.unsubscribed == False,
        # Ensure it's an initial email, not a follow-up itself
        SentEmail.follows_up_on_email_id == None
    )

    # Apply status conditions based on rule_condition_str
    if rule_condition_str == 'not_opened_within_delay':
        # Considered not opened if status is 'sent', 'delivered', or bounced.
        # Assumes 'opened', 'clicked', 'replied' mean it was opened.
        stmt = stmt.where(SentEmail.status.in_(['sent', 'delivered', 'hard_bounced', 'soft_bounced']))
    elif rule_condition_str == 'not_clicked_within_delay':
        # Considered not clicked if status is 'sent', 'delivered', 'opened', or bounced.
        # Assumes 'clicked', 'replied' mean it was clicked.
        stmt = stmt.where(SentEmail.status.in_(['sent', 'delivered', 'opened', 'hard_bounced', 'soft_bounced']))
    elif rule_condition_str == 'sent_anyway':
        # No additional status filter needed beyond being sent and delay passed.
        pass # No change to stmt based on status
    else:
        # Default behavior or raise error for unknown condition string
        print(f"Warning: Unknown rule condition string '{rule_condition_str}' in db_get_initial_emails_for_rule. No specific status filtering applied.")
        # Depending on desired strictness, could return empty list or raise error:
        # return []
        # raise ValueError(f"Unknown rule condition string: {rule_condition_str}")

    result = await db.execute(stmt)
    return result.scalars().all()

async def db_has_follow_up_been_sent(db: Session, original_email_id: int, follow_up_rule_id: int) -> bool:
    """
    Checks if a specific follow-up (defined by a rule) has already been sent for a given original email.
    Interacts with: SentEmail ORM model.
    Requires SentEmail to have 'triggered_by_rule_id' if we need to check against a specific rule.
    Args:
        db: SQLAlchemy Session.
        original_email_id: The ID of the original email (SentEmail.id).
        follow_up_rule_id: The ID of the follow_up_rule that would trigger this follow-up.
    Returns:
        True if a follow-up email associated with this original_email_id AND follow_up_rule_id exists, False otherwise.
    """
    # This assumes SentEmail has a field 'triggered_by_rule_id' linking it to the FollowUpRule.
    # If not, the check might only be possible on 'follows_up_on_email_id', which is less specific.
    statement = select(exists().where(
        SentEmail.follows_up_on_email_id == original_email_id,
        SentEmail.triggered_by_rule_id == follow_up_rule_id
    ))
    result = await db.execute(statement)
    return result.scalar_one()

async def db_get_contact_details(db: Session, contact_id: int) -> Optional[Contact]:
    """
    Retrieves full details for a specific contact by their ID.
    Interacts with: Contact ORM model.
    Args:
        db: SQLAlchemy Session.
        contact_id: The ID of the contact.
    Returns:
        The Contact ORM object if found, else None.
    """
    statement = select(Contact).where(Contact.id == contact_id)
    result = await db.execute(statement)
    return result.scalars().first()

async def db_get_email_template(db: Session, template_id: int) -> Optional[EmailTemplate]:
    """
    Retrieves an email template by its ID.
    Interacts with: EmailTemplate ORM model.
    Args:
        db: SQLAlchemy Session.
        template_id: The ID of the email template.
    Returns:
        The EmailTemplate ORM object if found, else None.
    """
    statement = select(EmailTemplate).where(EmailTemplate.id == template_id)
    result = await db.execute(statement)
    return result.scalars().first()

async def db_create_sent_email_record(db: Session, email_data: SentEmailCreate) -> SentEmail:
    """
    Creates a record of a sent email (e.g., a follow-up email).
    Interacts with: SentEmail ORM model.
    Args:
        db: SQLAlchemy Session.
        email_data: Pydantic schema SentEmailCreate containing data for the email sent.
                    `tracking_pixel_id` can be optional in `email_data`.
    Returns:
        The created SentEmail ORM object.
    """
    obj_data = email_data.model_dump()
    if 'tracking_pixel_id' not in obj_data or obj_data['tracking_pixel_id'] is None:
        obj_data['tracking_pixel_id'] = uuid.uuid4().hex

    db_sent_email = SentEmail(**obj_data)
    db.add(db_sent_email)
    db.commit()
    db.refresh(db_sent_email)
    return db_sent_email

# --- Database Operations for Email Tracking ---

async def db_record_email_open(db: Session, tracking_pixel_id: str, opened_ip: str) -> bool:
    """
    Records an email open event based on a tracking pixel ID.
    Updates open count, timestamps, IP, and status.
    Interacts with: SentEmail ORM model.
    Args:
        db: SQLAlchemy Session.
        tracking_pixel_id: The unique ID associated with the tracking pixel.
        opened_ip: The IP address from which the open event was recorded.
    Returns:
        True if a SentEmail record was found and updated, False otherwise.
    """
    stmt = select(SentEmail).where(SentEmail.tracking_pixel_id == tracking_pixel_id)
    result = await db.execute(stmt)
    email_record: Optional[SentEmail] = result.scalars().first()

    if email_record:
        email_record.open_count = (email_record.open_count or 0) + 1
        current_time = datetime.datetime.utcnow()
        email_record.last_opened_at = current_time

        if email_record.opened_at is None:
            email_record.opened_at = current_time

        if email_record.first_opened_ip is None:
            email_record.first_opened_ip = opened_ip

        # Update status to 'opened' unless it's already a more definitive terminal state
        # or a subsequent engagement state like 'clicked'.
        if email_record.status not in ['clicked', 'hard_bounced', 'spam_complaint', 'unsubscribed']:
            email_record.status = 'opened'

        db.add(email_record)
        db.commit()
        # db.refresh(email_record) # Not strictly necessary unless returning the object or accessing new defaults
        return True
    return False
```
