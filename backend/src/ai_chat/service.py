from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any # Added Dict, Any
from fastapi import HTTPException, status # Added HTTPException, status

from src.models.user_models import User as UserORMModel # SQLAlchemy model
from src.schemas.user_schemas import User as UserSchemaModel # Pydantic schema from auth
from src.ai_chat.schemas import ChatMessage # Pydantic schema for chat messages
from src.llm.email_generator import generate_personalized_email, LLMIntegrationError # For final template generation
from src.models.email_template_models import EmailTemplate # SQLAlchemy model for saving
from src.models.contact_models import Contact # SQLAlchemy model for preview contact. NOTE: followups.db_operations.db_get_contact_details returns this.
from src.schemas.email_template_schemas import EmailTemplateCreate # Pydantic schema for creation
from src.llm.email_generator import generate_chat_response # Keep for existing method
from src.campaigns.personalization_service import PersonalizationService # For preview
# Corrected import for db_create_email_template
from src.campaigns.db_operations import db_create_email_template
from .db_operations import db_set_other_templates_not_primary # This one is local to ai_chat
from src.followups.db_operations import db_get_contact_details # For preview contact


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

        # 3. Fetch sample contact data if contact_id_for_preview is provided for LLM context
        contact_data_for_llm: Dict[str, Any] = {}
        # This contact_for_preview is for the LLM context, not necessarily the same as one for final preview display
        # The one for final preview display is fetched later.
        if contact_id_for_preview:
            # Using db_get_contact_details which fetches by contact_id.
            # We need to ensure this contact is appropriate for the campaign/user if used for LLM context.
            # For now, just fetching it. Authorization for its use might be implicit (user owns campaign).
            temp_contact_for_llm_context = await db_get_contact_details(db, contact_id_for_preview)
            if temp_contact_for_llm_context and temp_contact_for_llm_context.owner_id == current_user_schema.id: # Basic auth check
                contact_data_for_llm = {
                    "first_name": temp_contact_for_llm_context.first_name or "",
                    "last_name": temp_contact_for_llm_context.last_name or "",
                    "email": temp_contact_for_llm_context.email or "",
                    "job_title": temp_contact_for_llm_context.job_title or "",
                    "company_name": temp_contact_for_llm_context.company_name or "",
                }
                contact_data_for_llm = {k: v for k, v in contact_data_for_llm.items() if v}

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

        # --- Database Operations for Template Creation ---
        try:
            # Step 1: Set is_primary = False for all other templates of this campaign
            await db_set_other_templates_not_primary(db, campaign_id=campaign_id)

            # Step 2: Create the new EmailTemplate with is_primary = True
            new_email_template_data = EmailTemplateCreate(
                campaign_id=campaign_id,
                name=f"AI Finalized Style - Campaign {campaign_id} - {final_user_prompt_text[:30]}...",
                user_prompt=final_user_prompt_text,
                subject_template=generated_subject,
                body_template=generated_body
            )
            db_email_template = await db_create_email_template(
                db,
                template_data=new_email_template_data,
                # owner_id is not taken by the centralized db_create_email_template
                is_primary=True
            )

            await db.commit()
            await db.refresh(db_email_template)

        except Exception as e:
            await db.rollback()
            # Log error e (e.g., import logging; logging.error(f"DB Error: {e}"))
            raise ValueError(f"Database error during email template finalization: {str(e)}")

        # --- Generate Personalized Preview (outside main transaction) ---
        preview_subject_str: Optional[str] = None
        preview_body_str: Optional[str] = None

        if contact_id_for_preview:
            # Fetch contact using db_get_contact_details
            contact_for_preview = await db_get_contact_details(db, contact_id_for_preview)

            # Ensure contact exists, belongs to the user, and is part of the campaign
            if contact_for_preview and \
               contact_for_preview.owner_id == current_user_schema.id and \
               contact_for_preview.campaign_id == campaign_id:
                try:
                    personalization_serv = PersonalizationService(db=db) # db is already a Session
                    preview_data = await personalization_serv.preview_personalized_email(
                        template_id=db_email_template.id,
                        contact_id=contact_id_for_preview
                    )
                    preview_subject_str = preview_data.get("subject")
                    preview_body_str = preview_data.get("body")
                except Exception as e:
                    # Log this error, but don't let it fail the whole finalization.
                    print(f"Error generating personalized preview for template {db_email_template.id}, contact {contact_id_for_preview}: {str(e)}")
            elif contact_for_preview:
                print(f"Contact {contact_id_for_preview} found but does not belong to campaign {campaign_id} or current user.")
            else:
                print(f"Contact {contact_id_for_preview} not found for preview.")

        return {
            "email_template": db_email_template, # The ORM object
            "preview_subject": preview_subject_str,
            "preview_body": preview_body_str
        }
