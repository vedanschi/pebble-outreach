# backend/src/followups/processor_service.py
from typing import List, Dict, Any, Optional
import datetime
import uuid # For tracking_pixel_id
from sqlalchemy.orm import Session

# Assuming ORM models and Pydantic schemas are correctly defined and importable
try:
    from src.core.config import settings # For APP_BASE_URL
    from src.models.follow_up_models import FollowUpRule
    from src.models.sent_email_models import SentEmail
    from src.models.contact_models import Contact
    from src.models.email_template_models import EmailTemplate
    from src.schemas.sent_email_schemas import SentEmailCreate # For creating new SentEmail records
except ImportError:
    # Placeholders for robustness if imports fail during development
    class settings: APP_BASE_URL: str = "http://localhost:8000"
    class FollowUpRule: pass
    class SentEmail: pass
    class Contact: pass
    class EmailTemplate: pass
    class SentEmailCreate: pass


# Import DB operations
from .db_operations import (
    db_get_active_follow_up_rules,
    db_get_initial_emails_for_rule,
    db_has_follow_up_been_sent,
    db_get_contact_details,
    db_get_email_template,
    db_create_sent_email_record,
)

# Placeholder for LLM email generation function (if used for advanced personalization)
# from ..llm.email_generator import generate_personalized_email

class FollowUpProcessorError(Exception):
    pass

async def process_due_follow_ups(db: Session) -> Dict[str, int]:
    """
    Processes all active follow-up rules and creates draft follow-up emails where conditions are met.
    This function would be called periodically by a scheduler.
    """
    print(f"PROCESSOR_SERVICE: Starting to process due follow-ups at {datetime.datetime.now(datetime.timezone.utc)}")
    processed_rules_count = 0
    created_follow_ups_count = 0

    active_rules: List[FollowUpRule] = await db_get_active_follow_up_rules(db)
    if not active_rules:
        print("PROCESSOR_SERVICE: No active follow-up rules found.")
        return {"processed_rules": 0, "created_follow_ups": 0}

    for rule in active_rules:
        processed_rules_count += 1

        # Extract rule details (assuming ORM object attributes)
        rule_id = rule.id
        campaign_id = rule.campaign_id
        original_template_id = rule.original_email_template_id
        follow_up_template_id = rule.follow_up_email_template_id
        # Use rule.delay_days and rule.condition (string)
        delay_days = rule.delay_days  # Changed from delay_hours
        min_delay = datetime.timedelta(days=delay_days) # Changed from hours to days
        rule_condition_str = rule.condition # This is now a string like 'not_opened_within_delay'

        # Fetch initial emails that match the rule criteria and are old enough
        initial_emails: List[SentEmail] = await db_get_initial_emails_for_rule(
            db=db,
            campaign_id=campaign_id,
            original_template_id=original_template_id,
            rule_condition_str=rule_condition_str, # Pass the string condition
            min_delay_before_followup=min_delay
        )

        for initial_email in initial_emails:
            initial_email_id = initial_email.id
            contact_id = initial_email.contact_id
            # initial_email_status = initial_email.status # Status is used within db_get_initial_emails_for_rule

            # 1. Check if a follow-up has already been sent for this initial_email_id by this specific rule
            already_followed_up = await db_has_follow_up_been_sent(db, initial_email_id, rule_id)
            if already_followed_up:
                # print(f"PROCESSOR_SERVICE: Follow-up for email ID {initial_email_id} by rule {rule_id} already sent. Skipping.")
                continue

            # 2. Condition checking is now primarily handled by db_get_initial_emails_for_rule based on rule_condition_str.
            #    If an email is returned, it means its status matched the rule_condition_str criteria.
            #    No further complex condition check needed here unless new logic is added beyond status.
            condition_met = True # If an email is returned by db_get_initial_emails_for_rule, conditions are met.

            # 3. If all checks pass, create and store the follow-up email
            print(f"PROCESSOR_SERVICE: Conditions met for follow-up to email ID {initial_email_id} (Rule ID {rule_id})")

            contact: Optional[Contact] = await db_get_contact_details(db, contact_id)
            follow_up_template: Optional[EmailTemplate] = await db_get_email_template(db, follow_up_template_id)

            if not contact or not follow_up_template:
                print(f"PROCESSOR_SERVICE: Missing contact (ID: {contact_id}) or template (ID: {follow_up_template_id}) for follow-up to email ID {initial_email_id}. Skipping.")
                continue

            if contact.unsubscribed: # Double check, though db_get_initial_emails_for_rule should handle this.
                print(f"PROCESSOR_SERVICE: Contact {contact.id} is unsubscribed. Skipping follow-up for email ID {initial_email_id}.")
                continue

            # Personalize the follow-up email (simple placeholder replacement for now)
            # TODO: Integrate with LLM for more advanced follow-up personalization if desired
            subject = (follow_up_template.subject_template or "").replace("{{first_name}}", contact.first_name or "there")
            subject = subject.replace("{{company_name}}", contact.company_name or "your company") # Assuming company_name exists

            body = (follow_up_template.body_template or "").replace("{{first_name}}", contact.first_name or "there")
            body = body.replace("{{company_name}}", contact.company_name or "your company")

            # Generate tracking pixel
            tracking_pixel_id = uuid.uuid4().hex
            pixel_url = f"{settings.APP_BASE_URL}/track/open/{tracking_pixel_id}.png"
            pixel_img_tag = f'<img src="{pixel_url}" width="1" height="1" alt="" style="display:none;">'
            final_body = body + pixel_img_tag


            # Create new SentEmail record for the follow-up
            follow_up_email_data = SentEmailCreate(
                campaign_id=campaign_id,
                contact_id=contact_id,
                email_template_id=follow_up_template_id,
                subject=subject,
                body=final_body, # Body with tracking pixel
                status="draft",
                sent_at=None,
                # is_follow_up might be deprecated if follows_up_on_email_id is used
                follows_up_on_email_id=initial_email_id,
                triggered_by_rule_id=rule_id,
                tracking_pixel_id=tracking_pixel_id # Add generated pixel ID
            )

            try:
                await db_create_sent_email_record(db, follow_up_email_data)
                created_follow_ups_count += 1
                print(f"PROCESSOR_SERVICE: Created draft follow-up for contact {contact.email} (Original Email ID: {initial_email_id}, Rule ID: {rule_id})")
            except Exception as e:
                print(f"PROCESSOR_SERVICE: Error creating sent email record for contact {contact_id}, initial email {initial_email_id}: {e}")


    print(f"PROCESSOR_SERVICE: Finished processing. Processed {processed_rules_count} rules, Created {created_follow_ups_count} follow-up drafts.")
    return {"processed_rules": processed_rules_count, "created_follow_ups": created_follow_ups_count}