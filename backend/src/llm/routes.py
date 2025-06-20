# backend/src/llm/routes.py
from typing import Optional, Dict, Any
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

# Assuming these dependencies are available and correctly set up
# Adjust paths based on your project structure
# try: # Assuming imports will work now
from src.database import get_db
from src.auth.dependencies import get_current_active_user
from src.models.user_models import User as UserORMModel
from src.schemas.user_schemas import User as UserSchema # Pydantic User schema for auth response
from src.models.contact_models import Contact # Still needed for type hint if db_get_contact_details returns it
# EmailTemplate ORM model is used by db_operations, not directly here after refactor for creation
# from src.models.email_template_models import EmailTemplate
from src.schemas.email_template_schemas import EmailTemplateResponse, EmailTemplateCreate
# New imports for DB operations
from src.campaigns.db_operations import db_create_email_template
from src.ai_chat.db_operations import db_set_other_templates_not_primary
from src.followups.db_operations import db_get_contact_details # For fetching contact
# except ImportError as e:
    # print(f"Error importing modules for llm/routes.py: {e}. Using placeholder types.")
    # Define placeholders if imports fail, to allow basic script structure checks
    class BaseModel: pass
    class User: pass
    class Contact: pass
    class EmailTemplate: pass
    class EmailTemplateResponse: pass
    class EmailTemplateCreate: pass
    def get_db(): pass
    def get_current_active_user(): pass

# Import the email generation function
from .email_generator import generate_personalized_email, LLMIntegrationError

router = APIRouter()

# --- Pydantic Models for API Request and Response ---

class GenerateEmailTemplateRequest(BaseModel):
    campaign_id: int
    user_prompt: str
    # your_company_name: Optional[str] = "Your Company" # Removed, will use current_user's profile
    contact_id_for_preview: Optional[int] = None

# Note: EmailTemplateResponse is assumed to be defined elsewhere,
# matching the structure from 004_create_email_templates_table.sql.
# Example structure if it needs to be defined here for clarity:
# class EmailTemplateResponse(BaseModel):
#     id: int
#     campaign_id: int
#     user_prompt: str
#     subject_template: str
#     body_template: str
#     created_at: datetime
#     updated_at: datetime
#
#     class Config:
#         orm_mode = True


@router.post("/generate-campaign-template/", response_model=EmailTemplateResponse, status_code=status.HTTP_201_CREATED)
async def generate_email_template_endpoint(
    request: GenerateEmailTemplateRequest,
    db: Session = Depends(get_db),
    current_user_auth: UserSchema = Depends(get_current_active_user) # This is Pydantic schema
):
    """
    Generates an email template using an LLM based on a user prompt and campaign context.
    Optionally uses a specific contact's data to make the generated template more concrete.
    """
    # Fetch the User ORM instance
    user_db_instance = db.query(UserORMModel).filter(UserORMModel.id == current_user_auth.id).first()
    if not user_db_instance:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Authenticated user not found in database.")

    contact_data_for_llm: Dict[str, Any] = {} # Ensure Any is imported from typing
    if request.contact_id_for_preview:
        contact_for_preview = await db_get_contact_details(db, request.contact_id_for_preview)

        if not contact_for_preview:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Preview contact with id {request.contact_id_for_preview} not found."
            )

        # Authorization check: ensure contact belongs to the user
        if contact_for_preview.owner_id != current_user_auth.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to preview contact."
            )

        contact_data_for_llm = {
            "first_name": contact_for_preview.first_name or "",
            "last_name": contact_for_preview.last_name or "",
            "email": contact_for_preview.email or "",
            "job_title": contact_for_preview.job_title or "",
            "company_name": contact_for_preview.company_name or "",
            # Add other fields if your Contact model and LLM prompt expect more
        }
        contact_data_for_llm = {k: v for k, v in contact_data_for_llm.items() if v}

    try:
        generated_subject, generated_body = await generate_personalized_email(
            user_core_prompt=request.user_prompt,
            contact_data=contact_data_for_llm,
            current_user=user_db_instance, # Pass the ORM instance
            is_template_generation=True
            # API key is handled by generate_personalized_email internally
        )
    except LLMIntegrationError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"LLM email generation failed: {e}"
        )
    except Exception as e: # Catch any other unexpected errors from the generator
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred during email generation: {e}"
        )

    if not generated_subject or not generated_body:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="LLM returned empty subject or body."
        )

    # Ensure current_user is the ORM model if needed by any logic here,
    # though db_create_email_template in campaigns doesn't take owner_id directly.
    # The campaign_id links to the user. The type hint current_user: UserORMModel should ensure this.

    try:
        # Set other templates for this campaign to not be primary
        # Note: db_set_other_templates_not_primary is async
        await db_set_other_templates_not_primary(db, campaign_id=request.campaign_id)

        email_template_data = EmailTemplateCreate(
            campaign_id=request.campaign_id,
            user_prompt=request.user_prompt,
            subject_template=generated_subject,
            body_template=generated_body
            # is_primary will be set by db_create_email_template call
        )

        # Note: db_create_email_template is async
        db_email_template = await db_create_email_template(
            db,
            template_data=email_template_data,
            is_primary=True # Make this new template primary
        )

        await db.commit()
        await db.refresh(db_email_template)

        return db_email_template # FastAPI will convert to EmailTemplateResponse

    except Exception as e: # Catch potential errors from DB ops or commit
        await db.rollback()
        # Log error e (e.g., import logging; logging.error(f"DB Error: {e}", exc_info=True))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error saving email template after LLM generation: {str(e)}"
        )
