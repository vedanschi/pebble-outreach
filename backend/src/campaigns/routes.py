# backend/src/campaigns/routes.py
from typing import List, Optional, Dict
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, selectinload
from pydantic import BaseModel

# Assuming these dependencies and models are available and correctly set up
# Adjust paths based on your project structure
try:
    from src.database import get_db
    from src.auth.dependencies import get_current_active_user
    from src.models.user_models import User
    from src.models.campaign_models import Campaign
    from src.models.contact_models import Contact
    from src.models.email_template_models import EmailTemplate

    # Pydantic Schemas
    # Assuming these are defined in a schemas directory, e.g., src.schemas.campaign_schemas
    from src.schemas.campaign_schemas import (
        CampaignCreate, CampaignUpdate, CampaignResponse, CampaignDetailResponse
    )
    from src.schemas.contact_schemas import ContactResponse
    from src.schemas.email_template_schemas import EmailTemplateResponse

    # Import the new sending service
    from .sending_service import process_and_send_campaign, CampaignSendingError
    # For SMTP config - will be mocked or loaded from settings
    from src.core.config import settings # Assuming settings are loaded here
except ImportError as e:
    print(f"Error importing modules for campaigns/routes.py: {e}. Using placeholder types.")
    # Define placeholders if imports fail
    class BaseModel: pass
    class CampaignSendingError(Exception): pass
    async def process_and_send_campaign(campaign_id: int, db: Session, smtp_config: dict): return 0,0
    class settings: SMTP_HOST: str = "localhost"; SMTP_PORT: int = 1025; SMTP_USER: Optional[str] = None; SMTP_PASSWORD: Optional[str] = None; SMTP_SENDER_EMAIL: str = "noreply@example.com"; SMTP_USE_TLS: bool = False
    class User: id: int
    class Campaign: pass
    class Contact: pass
    class EmailTemplate: pass
    class CampaignCreate(BaseModel): name: str; status: Optional[str] = "draft"
    class CampaignUpdate(BaseModel): name: Optional[str] = None; status: Optional[str] = None
    class CampaignResponse(BaseModel): id: int; user_id: int; name: str; status: str; created_at: datetime; updated_at: datetime
    class ContactResponse(BaseModel): id: int; email: str # simplified
    class EmailTemplateResponse(BaseModel): id: int; subject_template: str # simplified
    class CampaignDetailResponse(CampaignResponse): contacts: List[ContactResponse] = []; email_templates: List[EmailTemplateResponse] = []

    def get_db(): pass
    def get_current_active_user() -> User: return User(id=1) # Placeholder

router = APIRouter(
    prefix="/campaigns", # Assuming a prefix for all campaign routes
    tags=["campaigns"]   # Tag for API documentation
)

# Helper function to get a campaign and check ownership
def get_campaign_or_404(campaign_id: int, db: Session, user_id: int, preload_relations: bool = False) -> Campaign:
    query = db.query(Campaign).filter(Campaign.id == campaign_id)
    if preload_relations:
        query = query.options(
            selectinload(Campaign.contacts),
            selectinload(Campaign.email_templates)
        )

    campaign = query.first()

    if not campaign:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Campaign not found")
    if campaign.user_id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to access this campaign")
    return campaign

# 1. Create Campaign
@router.post("/", response_model=CampaignResponse, status_code=status.HTTP_201_CREATED)
async def create_campaign(
    campaign_in: CampaignCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Create a new campaign.
    """
    db_campaign = Campaign(
        **campaign_in.model_dump(),
        user_id=current_user.id
        # created_at and updated_at are usually handled by DB defaults or model events
    )
    db.add(db_campaign)
    db.commit()
    db.refresh(db_campaign)
    return db_campaign

# 2. List Campaigns
@router.get("/", response_model=List[CampaignResponse])
async def list_campaigns(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    skip: int = 0,
    limit: int = 100
):
    """
    List all campaigns owned by the current user.
    """
    campaigns = db.query(Campaign).filter(Campaign.user_id == current_user.id).offset(skip).limit(limit).all()
    return campaigns

# 3. Get Campaign Details
@router.get("/{campaign_id}", response_model=CampaignDetailResponse)
async def get_campaign_details(
    campaign_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Retrieve details for a specific campaign, including its contacts and email templates.
    """
    campaign = get_campaign_or_404(campaign_id, db, current_user.id, preload_relations=True)

    # The response model CampaignDetailResponse should automatically handle
    # serialization of campaign.contacts and campaign.email_templates
    # if they are correctly defined as relationships in the ORM model
    # and the Pydantic schemas (ContactResponse, EmailTemplateResponse) are correctly set up.
    return campaign

# 4. Update Campaign
@router.put("/{campaign_id}", response_model=CampaignResponse)
async def update_campaign(
    campaign_id: int,
    campaign_in: CampaignUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Update a campaign's name and/or status.
    """
    db_campaign = get_campaign_or_404(campaign_id, db, current_user.id)

    update_data = campaign_in.model_dump(exclude_unset=True) # Only update provided fields
    for key, value in update_data.items():
        setattr(db_campaign, key, value)

    # db_campaign.updated_at = datetime.utcnow() # Handled by ORM/DB if configured
    db.add(db_campaign) # Not strictly necessary if already in session and modified
    db.commit()
    db.refresh(db_campaign)
    return db_campaign

# 5. Delete Campaign
@router.delete("/{campaign_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_campaign(
    campaign_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Delete a campaign. Database cascade should handle related entities.
    """
    db_campaign = get_campaign_or_404(campaign_id, db, current_user.id)

    db.delete(db_campaign)
    db.commit()
    # No response body needed for 204
    return None # Or return Response(status_code=status.HTTP_204_NO_CONTENT)

@router.post("/campaigns/upload")
async def upload_campaign_csv(
    campaign_name: str,
    file: UploadFile,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    content = await file.read()
    campaign, contacts, errors = await process_csv_upload(
        user_id=current_user.id,
        campaign_name=campaign_name,
        csv_file_content=content,
        db=db
    )
    
    return {
        "campaign": campaign,
        "contacts_imported": len(contacts),
        "errors": errors
    }

# backend/src/campaigns/routes.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, Any

from src.core.config import get_db
from .personalization_service import PersonalizationService

router = APIRouter()

@router.post("/campaigns/{campaign_id}/generate-emails")
async def generate_campaign_emails(
    campaign_id: int,
    prompt: Dict[str, str],
    db: Session = Depends(get_db)
):
    try:
        service = PersonalizationService(db)
        template = await service.generate_campaign_emails(
            campaign_id=campaign_id,
            user_prompt=prompt["prompt"]
        )
        return {"template_id": template.id}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/campaigns/preview-email")
async def preview_email(
    template_id: int,
    contact_id: int,
    db: Session = Depends(get_db)
):
    try:
        service = PersonalizationService(db)
        preview = await service.preview_personalized_email(template_id, contact_id)
        return preview
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/campaigns/validate-template/{template_id}")
async def validate_template(
    template_id: int,
    db: Session = Depends(get_db)
):
    try:
        service = PersonalizationService(db)
        validation = await service.validate_template(template_id)
        return validation
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# If you have other campaign-related routes (like CSV upload from previous subtasks),
# they could be added to this router or managed in a separate file and included
# in the main application's router setup.
# For example, if csv_processor.py has its own router, you would do:
# from .csv_processor_routes import router as csv_router # Assuming it's moved/refactored
# main_app.include_router(csv_router, prefix="/campaigns/{campaign_id}/csv", tags=["campaign-csv"])

# Note: The CampaignDetailResponse relies on the Campaign ORM model having
# 'contacts' and 'email_templates' relationships defined, e.g.:
# class Campaign(Base):
#     # ... other fields
#     contacts = relationship("Contact", back_populates="campaign", cascade="all, delete-orphan")
#     email_templates = relationship("EmailTemplate", back_populates="campaign", cascade="all, delete-orphan")

# And ContactResponse/EmailTemplateResponse being able to serialize from those ORM objects.
# Ensure your Pydantic schemas have `Config.orm_mode = True` or `model_config = {"from_attributes": True}` for Pydantic v2.
# Example (Pydantic v2):
# class ContactResponse(BaseModel):
#     id: int
#     # ... other fields
#     model_config = {"from_attributes": True}

# class EmailTemplateResponse(BaseModel):
#     id: int
#     # ... other fields
#     model_config = {"from_attributes": True}

# class CampaignDetailResponse(CampaignResponse):
#     contacts: List[ContactResponse] = []
#     email_templates: List[EmailTemplateResponse] = []
#     # model_config = {"from_attributes": True} # if CampaignResponse doesn't have it already


# --- Campaign Sending Endpoint ---
class CampaignSendResponse(BaseModel):
    message: str
    successful_sends: int
    failed_sends: int

@router.post("/{campaign_id}/send", response_model=CampaignSendResponse)
async def send_campaign_emails(
    campaign_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Initiates the sending of a campaign.
    Fetches contacts, personalizes emails, and sends them.
    """
    # Ensure the current user owns this campaign before sending
    campaign = get_campaign_or_404(campaign_id, db, current_user.id)
    if not campaign: # Should be handled by get_campaign_or_404, but defensive check
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Campaign not found or not authorized.")

    # Retrieve SMTP configuration (e.g., from application settings or environment variables)
    # For this subtask, we can mock it or assume it's loaded via a settings object
    smtp_config = {
        "host": settings.SMTP_HOST,
        "port": settings.SMTP_PORT,
        "username": settings.SMTP_USER,
        "password": settings.SMTP_PASSWORD,
        "use_tls": settings.SMTP_USE_TLS,
        "sender_email": settings.SMTP_SENDER_EMAIL, # Or a campaign-specific sender
        "timeout": 10
    }
    if not smtp_config["host"] or not smtp_config["sender_email"]:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="SMTP server settings are not configured."
        )

    try:
        successful, failed = await process_and_send_campaign(
            campaign_id=campaign_id,
            db=db,
            smtp_config=smtp_config
        )
        return CampaignSendResponse(
            message=f"Campaign {campaign_id} processing completed.",
            successful_sends=successful,
            failed_sends=failed
        )
    except CampaignSendingError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        # Log the exception e
        print(f"Unexpected error sending campaign {campaign_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An unexpected error occurred while sending the campaign.")

# --- Personalization Routes ---
from .personalization_service import PersonalizationService

@router.post("/{campaign_id}/generate-emails")
async def generate_campaign_emails(
    campaign_id: int,
    prompt: Dict[str, str],
    db: Session = Depends(get_db)
):
    try:
        service = PersonalizationService(db)
        template = await service.generate_campaign_emails(
            campaign_id=campaign_id,
            user_prompt=prompt["prompt"]
        )
        return {"template_id": template.id}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/preview-email")
async def preview_email(
    template_id: int,
    contact_id: int,
    db: Session = Depends(get_db)
):
    try:
        service = PersonalizationService(db)
        preview = await service.preview_personalized_email(template_id, contact_id)
        return preview
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/validate-template/{template_id}")
async def validate_template(
    template_id: int,
    db: Session = Depends(get_db)
):
    try:
        service = PersonalizationService(db)
        validation = await service.validate_template(template_id)
        return validation
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
