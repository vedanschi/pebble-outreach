# backend/src/followups/rules_service.py
from typing import List, Dict, Any, Optional
import datetime

# Placeholder for database interaction functions for FollowUpRules table
# async def db_create_follow_up_rule(rule_data: Dict[str, Any]) -> Dict[str, Any]: pass
# async def db_get_follow_up_rule(rule_id: int) -> Optional[Dict[str, Any]]: pass
# async def db_get_follow_up_rules_for_campaign(campaign_id: int) -> List[Dict[str, Any]]: pass
# async def db_update_follow_up_rule(rule_id: int, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]: pass
# async def db_delete_follow_up_rule(rule_id: int) -> bool: pass

class FollowUpRuleServiceError(Exception):
    pass

async def create_rule(
    campaign_id: int,
    original_email_template_id: int, # Or could be broader, e.g., applies to all in campaign
    follow_up_email_template_id: int,
    delay_days: int,
    condition: str, # e.g., 'not_opened_within_delay', 'not_replied_within_delay', 'sent_anyway'
    is_active: bool = True,
    #db_create_follow_up_rule_func # Injected DB function
) -> Dict[str, Any]:
    """Creates a new follow-up rule."""
    if delay_days < 0:
        raise FollowUpRuleServiceError("Delay days cannot be negative.")
    # Add more validation for condition if needed

    rule_data = {
        "campaign_id": campaign_id,
        "original_email_template_id": original_email_template_id,
        "follow_up_email_template_id": follow_up_email_template_id,
        "delay_days": delay_days,
        "condition": condition,
        "is_active": is_active,
        # "created_at": datetime.datetime.now(datetime.timezone.utc) # DB default
    }
    # created_rule = await db_create_follow_up_rule_func(rule_data)
    # For subtask simulation:
    print(f"RULES_SERVICE: Simulating creation of follow-up rule for campaign {campaign_id}")
    created_rule = {**rule_data, "id": 1, "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat()}
    if not created_rule:
        raise FollowUpRuleServiceError("Failed to create follow-up rule in database.")
    return created_rule

async def get_rule(rule_id: int, db_get_follow_up_rule_func) -> Optional[Dict[str, Any]]:
    """Retrieves a specific follow-up rule by its ID."""
    # rule = await db_get_follow_up_rule_func(rule_id)
    # For subtask simulation:
    print(f"RULES_SERVICE: Simulating fetching rule with ID {rule_id}")
    if rule_id == 1: # Simulate found
        return {"id": rule_id, "campaign_id": 101, "delay_days": 3, "condition": "not_opened_within_delay"}
    return None

async def get_rules_for_campaign(campaign_id: int, db_get_follow_up_rules_for_campaign_func) -> List[Dict[str, Any]]:
    """Retrieves all follow-up rules for a given campaign."""
    # rules = await db_get_follow_up_rules_for_campaign_func(campaign_id)
    # For subtask simulation:
    print(f"RULES_SERVICE: Simulating fetching rules for campaign ID {campaign_id}")
    if campaign_id == 101:
         return [{"id": 1, "campaign_id": 101, "delay_days": 3, "condition": "not_opened_within_delay", "is_active": True}]
    return []

async def update_rule(rule_id: int, updates: Dict[str, Any], db_update_follow_up_rule_func) -> Optional[Dict[str, Any]]:
    """Updates an existing follow-up rule."""
    if "delay_days" in updates and updates["delay_days"] < 0:
        raise FollowUpRuleServiceError("Delay days cannot be negative if provided in updates.")
    # updated_rule = await db_update_follow_up_rule_func(rule_id, updates)
    # For subtask simulation:
    print(f"RULES_SERVICE: Simulating update for rule ID {rule_id} with data {updates}")
    updated_rule = {"id": rule_id, **updates}
    if not updated_rule:
        raise FollowUpRuleServiceError(f"Failed to update rule ID {rule_id} or rule not found.")
    return updated_rule

async def delete_rule(rule_id: int, db_delete_follow_up_rule_func) -> bool:
    """Deletes a follow-up rule."""
    # success = await db_delete_follow_up_rule_func(rule_id)
    # For subtask simulation:
    print(f"RULES_SERVICE: Simulating deletion of rule ID {rule_id}")
    return True # Simulate success