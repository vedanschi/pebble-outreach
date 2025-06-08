# backend/src/followups/processor_service.py
from typing import List, Dict, Any, Optional
import datetime

# Placeholder for DB interaction functions
# async def db_get_active_follow_up_rules() -> List[Dict[str, Any]]: pass
# async def db_get_initial_emails_for_rule(campaign_id: int, original_template_id: int, sent_before_date: datetime.datetime) -> List[Dict[str, Any]]: pass
# async def db_has_follow_up_been_sent(original_email_id: int) -> bool: pass
# async def db_get_contact_details(contact_id: int) -> Optional[Dict[str, Any]]: pass
# async def db_get_email_template(template_id: int) -> Optional[Dict[str, Any]]: pass
# async def db_create_sent_email_record(email_data: Dict[str, Any]) -> Dict[str, Any]: pass

# Placeholder for LLM email generation function (if used for advanced personalization)
# from ..llm.email_generator import generate_personalized_email

class FollowUpProcessorError(Exception):
    pass

async def process_due_follow_ups(
    # Injected DB functions
    db_get_active_follow_up_rules_func,
    db_get_initial_emails_for_rule_func, # To get SentEmails matching original criteria
    db_has_follow_up_been_sent_func,   # To check SentEmails if a follow-up exists
    db_get_contact_details_func,
    db_get_email_template_func,
    db_create_sent_email_record_func, # To create new entry in SentEmails for the follow-up
    # Injected personalization/LLM function (optional, for advanced follow-ups)
    # generate_llm_follow_up_email_func = None
) -> Dict[str, int]:
    """
    Processes all active follow-up rules and creates draft follow-up emails where conditions are met.
    This function would be called periodically by a scheduler.
    """
    print(f"PROCESSOR_SERVICE: Starting to process due follow-ups at {datetime.datetime.now(datetime.timezone.utc)}")
    processed_rules = 0
    created_follow_ups = 0

    active_rules = await db_get_active_follow_up_rules_func()
    if not active_rules:
        print("PROCESSOR_SERVICE: No active follow-up rules found.")
        return {"processed_rules": 0, "created_follow_ups": 0}

    for rule in active_rules:
        processed_rules += 1
        rule_id = rule.get("id")
        campaign_id = rule.get("campaign_id")
        original_template_id = rule.get("original_email_template_id")
        follow_up_template_id = rule.get("follow_up_email_template_id")
        delay_days = rule.get("delay_days")
        condition = rule.get("condition") # e.g., 'not_opened_within_delay'

        # Calculate the cutoff date for when original emails should have been sent
        sent_before_cutoff = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=delay_days)

        # Fetch initial emails that match the rule criteria and are old enough
        initial_emails = await db_get_initial_emails_for_rule_func(
            campaign_id, original_template_id, sent_before_cutoff
        )

        for initial_email in initial_emails:
            initial_email_id = initial_email.get("id")
            contact_id = initial_email.get("contact_id")
            initial_email_status = initial_email.get("status") # e.g., 'sent', 'delivered', 'opened', 'clicked'

            # 1. Check if a follow-up has already been sent for this initial_email_id
            already_followed_up = await db_has_follow_up_been_sent_func(initial_email_id)
            if already_followed_up:
                continue # Skip to next initial email

            # 2. Check condition
            condition_met = False
            if condition == 'not_opened_within_delay':
                # Email is considered not opened if status is 'sent' or 'delivered'.
                # If status is 'opened' or 'clicked', it was opened.
                if initial_email_status in ['sent', 'delivered', 'hard_bounced', 'soft_bounced']: # Add bounce checks
                    condition_met = True
            elif condition == 'not_clicked_within_delay': # Requires click tracking data
                 if initial_email_status not in ['clicked']: # Simplified
                    condition_met = True
            elif condition == 'sent_anyway':
                condition_met = True
            # Add more conditions like 'not_replied' (complex, requires inbox integration - not handled here)

            if not condition_met:
                continue # Skip to next initial email

            # 3. If all checks pass, create and store the follow-up email
            print(f"PROCESSOR_SERVICE: Conditions met for follow-up to email ID {initial_email_id} (Rule ID {rule_id})")

            contact = await db_get_contact_details_func(contact_id)
            follow_up_template = await db_get_email_template_func(follow_up_template_id)

            if not contact or not follow_up_template:
                print(f"PROCESSOR_SERVICE: Missing contact or template for follow-up to email ID {initial_email_id}. Skipping.")
                continue

            # Personalize the follow-up email (simple placeholder replacement for now)
            # TODO: Integrate with LLM for more advanced follow-up personalization if desired
            subject = follow_up_template.get("subject_template", "").replace("{{first_name}}", contact.get("first_name", "")) # Example
            body = follow_up_template.get("body_template", "").replace("{{first_name}}", contact.get("first_name", ""))       # Example

            # Create new SentEmail record for the follow-up
            follow_up_email_data = {
                "campaign_id": campaign_id,
                "contact_id": contact_id,
                "email_template_id": follow_up_template_id,
                "subject": subject,
                "body": body,
                "status": "draft", # Or 'pending_send' to be picked by sender service
                "is_follow_up": True,
                "follows_up_on_email_id": initial_email_id,
                # tracking_pixel_id will be generated when this email is processed for sending
            }
            await db_create_sent_email_record_func(follow_up_email_data)
            created_follow_ups += 1
            print(f"PROCESSOR_SERVICE: Created draft follow-up for contact {contact.get('email')} (Original Email ID: {initial_email_id})")

    print(f"PROCESSOR_SERVICE: Finished processing. Processed {processed_rules} rules, Created {created_follow_ups} follow-up drafts.")
    return {"processed_rules": processed_rules, "created_follow_ups": created_follow_ups}