# backend/src/llm/routes.py
from typing import Optional, Dict, Any
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

# Assuming these dependencies are available and correctly set up
# Adjust paths based on your project structure
try:
    from src.database import get_db
    from src.auth.dependencies import get_current_active_user
    from src.models.user_models import User
    from src.models.contact_models import Contact
    from src.models.email_template_models import EmailTemplate # Assuming this is the ORM model
    # If EmailTemplateResponse schema is separate:
    from src.schemas.email_template_schemas import EmailTemplateResponse, EmailTemplateCreate # Adjust as needed
except ImportError as e:
    print(f"Error importing modules for llm/routes.py: {e}. Using placeholder types.")
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
    current_user: User = Depends(get_current_active_user) # Assuming User model from user_models
):
    """
    Generates an email template using an LLM based on a user prompt and campaign context.
    Optionally uses a specific contact's data to make the generated template more concrete.
    """
    contact_data_for_llm: Dict[str, str] = {}

    if request.contact_id_for_preview:
        contact_for_preview: Optional[Contact] = db.query(Contact).filter(
            Contact.id == request.contact_id_for_preview,
            # Optional: Add campaign_id filter if contacts are strictly tied to campaigns for preview
            # Contact.campaign_id == request.campaign_id
        ).first()

        if not contact_for_preview:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Contact with id {request.contact_id_for_preview} not found for preview."
            )

        # Convert contact ORM object to dict for the LLM function.
        # Adjust attribute names based on your Contact model.
        contact_data_for_llm = {
            "first_name": contact_for_preview.first_name or "",
            "last_name": contact_for_preview.last_name or "",
            "email": contact_for_preview.email or "",
            "job_title": contact_for_preview.job_title or "",
            "company_name": contact_for_preview.company_name or "",
            "linkedin_url": contact_for_preview.linkedin_url or "",
            "city": contact_for_preview.city or "",
            "state": contact_for_preview.state or "",
            "country": contact_for_preview.country or "",
            # Add other relevant fields from your Contact model
        }
        # Filter out empty values if desired, though LLM might handle them.
        contact_data_for_llm = {k: v for k, v in contact_data_for_llm.items() if v}


    try:
        # Pass the current_user ORM object to the email generation service
        generated_subject, generated_body = await generate_personalized_email(
            user_core_prompt=request.user_prompt,
            contact_data=contact_data_for_llm,
            current_user=current_user, # Pass the authenticated user object
            is_template_generation=True # Crucial change
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

    # Create EmailTemplate ORM object
    # Assuming EmailTemplateCreate Pydantic schema for creation if you use one,
    # otherwise, direct instantiation of the ORM model.
    email_template_data = EmailTemplateCreate(
        campaign_id=request.campaign_id,
        user_prompt=request.user_prompt,
        subject_template=generated_subject,
        body_template=generated_body
        # created_at and updated_at are usually handled by the DB or ORM defaults
    )

    db_email_template = EmailTemplate(**email_template_data.model_dump())
    # If EmailTemplate ORM model doesn't have user_id, but you want to associate it,
    # you might need to adjust the model or how you log creator (e.g. via campaign's user_id)
    # For now, assuming campaign_id is sufficient linkage.

    try:
        db.add(db_email_template)
        db.commit()
        db.refresh(db_email_template)
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error saving email template: {e}"
        )

    # Return using EmailTemplateResponse schema
    # This assumes EmailTemplateResponse can be created from db_email_template
    return db_email_template
