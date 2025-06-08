# backend/src/followups/rules_service.py
from typing import List, Dict, Any, Optional # Keep Dict, Any for conditions if they are JSON
import datetime
from sqlalchemy.orm import Session

# Assuming ORM models and Pydantic schemas are correctly defined and importable
try:
    from src.models.follow_up_models import FollowUpRule
    from src.schemas.follow_up_schemas import FollowUpRuleCreate, FollowUpRuleUpdate
except ImportError:
    # Placeholders for robustness
    class FollowUpRule: pass
    class FollowUpRuleCreate: pass
    class FollowUpRuleUpdate: pass

# Import DB operations
from .db_operations import (
    db_create_follow_up_rule,
    db_get_follow_up_rule,
    db_get_follow_up_rules_for_campaign,
    db_update_follow_up_rule,
    db_delete_follow_up_rule,
)

class FollowUpRuleServiceError(Exception):
    pass

async def create_rule(
    db: Session,
    campaign_id: int,
    original_email_template_id: int,
    follow_up_email_template_id: int,
    delay_days: int, # Changed to delay_days
    condition: str,  # Changed to condition: str
    is_active: bool = True
) -> FollowUpRule:
    """Creates a new follow-up rule."""
    if delay_days < 0:
        raise FollowUpRuleServiceError("Delay days cannot be negative.")

    # Optional: Validate condition string if it's from a predefined set
    # valid_conditions = ["not_opened_within_delay", "not_clicked_within_delay", "sent_anyway"]
    # if condition not in valid_conditions:
    #     raise FollowUpRuleServiceError(f"Invalid condition: {condition}")

    rule_data = FollowUpRuleCreate( # Assumes FollowUpRuleCreate schema expects delay_days and condition
        campaign_id=campaign_id,
        original_email_template_id=original_email_template_id,
        follow_up_email_template_id=follow_up_email_template_id,
        delay_days=delay_days,
        condition=condition,
        is_active=is_active,
    )

    created_rule = await db_create_follow_up_rule(db, rule_data)
    # The DB operation should raise an error if creation fails, or return the object.
    # No need to explicitly check for `not created_rule` unless db_op can return None on success.
    return created_rule

async def get_rule(db: Session, rule_id: int) -> Optional[FollowUpRule]:
    """Retrieves a specific follow-up rule by its ID."""
    rule = await db_get_follow_up_rule(db, rule_id)
    return rule

async def get_rules_for_campaign(db: Session, campaign_id: int) -> List[FollowUpRule]:
    """Retrieves all follow-up rules for a given campaign."""
    rules = await db_get_follow_up_rules_for_campaign(db, campaign_id)
    return rules

async def update_rule(
    db: Session,
    rule_id: int,
    # Pass individual fields or a Pydantic schema for updates
    # Using individual fields for clarity on what's updatable via service layer
    original_email_template_id: Optional[int] = None,
    follow_up_email_template_id: Optional[int] = None,
    delay_days: Optional[int] = None,    # Changed to delay_days
    condition: Optional[str] = None,     # Changed to condition: str
    is_active: Optional[bool] = None
) -> Optional[FollowUpRule]:
    """Updates an existing follow-up rule."""

    if delay_days is not None and delay_days < 0:
        raise FollowUpRuleServiceError("Delay days cannot be negative if provided.")

    # Optional: Validate condition string if provided
    # if condition is not None and condition not in ["not_opened_within_delay", ...]:
    #     raise FollowUpRuleServiceError(f"Invalid condition: {condition}")

    update_data_dict = { # Assumes FollowUpRuleUpdate schema expects delay_days and condition
        "original_email_template_id": original_email_template_id,
        "follow_up_email_template_id": follow_up_email_template_id,
        "delay_days": delay_days,
        "condition": condition,
        "is_active": is_active,
    }
    # Filter out None values to only update provided fields
    filtered_updates = {k: v for k, v in update_data_dict.items() if v is not None}

    if not filtered_updates:
        # Or fetch and return the existing rule if no update fields are provided
        raise FollowUpRuleServiceError("No update data provided.")

    rule_update_schema = FollowUpRuleUpdate(**filtered_updates)

    updated_rule = await db_update_follow_up_rule(db, rule_id, rule_update_schema)
    # db_update_follow_up_rule will return None if rule not found, or the updated rule.
    if not updated_rule:
         # This could mean rule not found, or update failed if db_op handled it that way.
         # Assuming db_op returns None if not found.
        pass # Or raise specific "not found" error from service layer if desired.
    return updated_rule

async def delete_rule(db: Session, rule_id: int) -> bool:
    """Deletes a follow-up rule."""
    success = await db_delete_follow_up_rule(db, rule_id)
    return success