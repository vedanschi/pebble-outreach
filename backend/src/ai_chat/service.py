from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any # Added Dict, Any
from fastapi import HTTPException, status # Added HTTPException, status

from src.models.user_models import User as UserORMModel # SQLAlchemy model
from src.schemas.user_schemas import User as UserSchemaModel # Pydantic schema from auth
from src.ai_chat.schemas import ChatMessage # Pydantic schema for chat messages
from src.llm.email_generator import generate_personalized_email, LLMIntegrationError # For final template generation
from src.models.email_template_models import EmailTemplate # SQLAlchemy model for saving
from src.models.contact_models import Contact # SQLAlchemy model for preview contact
from src.schemas.email_template_schemas import EmailTemplateCreate # Pydantic schema for creation
from src.llm.email_generator import generate_chat_response # Keep for existing method
from src.campaigns.personalization_service import PersonalizationService # For preview


class AIChatService:
    async def process_chat_interaction(
        self,
        db: Session,
        campaign_id: int,
        conversation_history: List[ChatMessage],
        current_user: UserSchemaModel # Changed to Pydantic User schema model
    ) -> str:
        """
        Processes a chat interaction, gets a response from the LLM,
        and returns the AI's reply.
        """
        # Optionally, fetch campaign details or more user details if needed for context
        # campaign = db.query(Campaign).filter(Campaign.id == campaign_id, Campaign.owner_id == current_user.id).first()
        # if not campaign:
        #     # This check should ideally be in routes before calling service
        #     raise ValueError("Campaign not found or user mismatch")

        # For now, current_user ORM object is passed directly to generate_chat_response
        # which expects certain attributes like full_name, user_company_name, user_role.
        # Ensure the User model passed (current_user: User) has these, or adapt.
        # The UserORM in email_generator.py is a placeholder if actual User model doesn't match.
        # We assume current_user (src.models.user_models.User) has these fields.

        db_user_instance = db.query(UserORMModel).filter(UserORMModel.id == current_user.id).first()
        if not db_user_instance:
            # This should be rare if the token is valid and user is active
            raise ValueError("Authenticated user not found in database.")

        ai_reply_content = await generate_chat_response(
            conversation_history=conversation_history,
            current_user=db_user_instance, # Pass the SQLAlchemy ORM model instance
            campaign_id=campaign_id
            # api_key can be passed if needed, or rely on environment setup in email_generator
        )
        return ai_reply_content

    async def finalize_style_and_create_template(
        self,
        db: Session,
        campaign_id: int,
        final_conversation_history: List[ChatMessage],
        current_user_schema: UserSchemaModel, # Pydantic schema from auth
        contact_id_for_preview: Optional[int]
    ) -> Dict[str, Any]: # Return a dictionary with template and preview data

        # 1. Fetch the SQLAlchemy User model instance for current_user
        db_user_instance = db.query(UserORMModel).filter(UserORMModel.id == current_user_schema.id).first()
        if not db_user_instance:
            raise ValueError("Authenticated user not found in database for style finalization.")

        # 2. Distill a "final prompt" from the conversation history.
        final_user_prompt_text = "No specific user prompt extracted from final conversation." # Default
        if final_conversation_history:
            final_message = final_conversation_history[-1]
            if final_message.role == "user":
                final_user_prompt_text = final_message.content
            elif len(final_conversation_history) > 1 and final_conversation_history[-2].role == "user":
                final_user_prompt_text = final_conversation_history[-2].content
            else:
                final_user_prompt_text = final_message.content

        # 3. Fetch sample contact data if contact_id_for_preview is provided
        contact_data_for_llm: Dict[str, Any] = {}
        if contact_id_for_preview:
            # Assuming Contact model has owner_id to check against current_user_schema.id for authorization
            # This check might be better suited in the route or a dedicated contact service
            contact_for_preview = db.query(Contact).filter(
                Contact.id == contact_id_for_preview,
                Contact.owner_id == current_user_schema.id # Authorization check
            ).first()
            if contact_for_preview:
                contact_data_for_llm = {
                    "first_name": contact_for_preview.first_name or "",
                    "last_name": contact_for_preview.last_name or "",
                    "email": contact_for_preview.email or "",
                    "job_title": contact_for_preview.job_title or "",
                    "company_name": contact_for_preview.company_name or "",
                    # Add other fields as expected by generate_personalized_email
                }
                contact_data_for_llm = {k: v for k, v in contact_data_for_llm.items() if v}
            # else: # If contact not found or not authorized, proceed without it or raise error
                 # raise ValueError("Preview contact not found or access denied.")

        # 4. Call LLM to generate subject and body
        try:
            generated_subject, generated_body = await generate_personalized_email(
                user_core_prompt=final_user_prompt_text,
                contact_data=contact_data_for_llm, # Will be empty if no preview contact
                current_user=db_user_instance,
                is_template_generation=True # Crucial change
            )
        except LLMIntegrationError as e:
            # Log error e (e.g., import logging; logging.error(f"LLM Error: {e}"))
            raise ValueError(f"LLM email generation failed during finalization: {str(e)}")
        except Exception as e:
            # Log error e
            raise ValueError(f"Unexpected error during final LLM call: {str(e)}")

        if not generated_subject or not generated_body:
            raise ValueError("LLM returned empty subject or body during finalization.")

        # --- Manage is_primary flag ---
        # Step 1: Set is_primary = False for all other templates of this campaign
        try:
            existing_templates = db.query(EmailTemplate).filter(EmailTemplate.campaign_id == campaign_id).all()
            updated_existing = False
            for tmpl in existing_templates:
                if tmpl.is_primary: # Only update if it was primary
                    tmpl.is_primary = False
                    db.add(tmpl) # Add to session for update
                    updated_existing = True
            if updated_existing: # Only commit if there were templates to update
                db.commit()
        except Exception as e:
            db.rollback()
            # Log error e (e.g., import logging; logging.error(f"Error updating existing templates for campaign {campaign_id}: {str(e)}"))
            # Depending on policy, you might raise ValueError here or just log
            # For now, raising an error as this is a critical part of maintaining data integrity for 'is_primary'
            raise ValueError(f"Failed to update primary status of existing templates for campaign {campaign_id}: {str(e)}")

        # Step 2: Create the new EmailTemplate with is_primary = True
        new_email_template_data = EmailTemplateCreate(
            campaign_id=campaign_id,
            name=f"AI Finalized Style - Campaign {campaign_id} - {final_user_prompt_text[:30]}...",
            user_prompt=final_user_prompt_text,
            subject_template=generated_subject,
            body_template=generated_body
            # is_primary will be set directly on the ORM model instance
        )

        db_email_template = EmailTemplate(
            **new_email_template_data.model_dump(),
            owner_id=current_user_schema.id, # Explicitly set owner_id
            is_primary=True # Set the new template as primary
        )

        try:
            db.add(db_email_template)
            db.commit()
            db.refresh(db_email_template)
        except Exception as e:
            db.rollback()
            # Log error e
            raise ValueError(f"Database error saving finalized email template: {str(e)}")

        # --- Generate Personalized Preview ---
        preview_subject_str: Optional[str] = None
        preview_body_str: Optional[str] = None

        if contact_id_for_preview:
            # Re-fetch contact, ensuring it's part of the campaign for relevance & security
            contact_for_preview = db.query(Contact).filter(
                Contact.id == contact_id_for_preview,
                Contact.campaign_id == campaign_id, # Ensure contact is in the same campaign
                Contact.owner_id == current_user_schema.id # Ensure contact belongs to the user
            ).first()

            if contact_for_preview:
                try:
                    personalization_serv = PersonalizationService(db=db)
                    preview_data = await personalization_serv.preview_personalized_email(
                        template_id=db_email_template.id,
                        contact_id=contact_id_for_preview
                    )
                    preview_subject_str = preview_data.get("subject")
                    preview_body_str = preview_data.get("body")
                except Exception as e:
                    # Log this error, but don't let it fail the whole finalization.
                    print(f"Error generating personalized preview for template {db_email_template.id}, contact {contact_id_for_preview}: {str(e)}")
            else:
                print(f"Contact {contact_id_for_preview} not found in campaign {campaign_id} or not owned by user for preview.")

        return {
            "email_template": db_email_template, # The ORM object
            "preview_subject": preview_subject_str,
            "preview_body": preview_body_str
        }
