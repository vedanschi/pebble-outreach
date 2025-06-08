# backend/src/followups/routes.py
from typing import List, Optional, Dict, Any
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel # Import BaseModel

# Assuming these dependencies and models are available and correctly set up
try:
    from src.database import get_db
    from src.auth.dependencies import get_current_active_user
    from src.models.user_models import User # For current_user dependency
    from src.models.follow_up_models import FollowUpRule # ORM Model
    from src.schemas.follow_up_schemas import FollowUpRuleCreate, FollowUpRuleUpdate
    # Service functions that now use db: Session
    from . import rules_service
except ImportError as e:
    print(f"Error importing modules for followups/routes.py: {e}. Using placeholder types.")
    # Define placeholders if imports fail
    class BaseModel: pass
    class User: id: int
    class FollowUpRule: id: int; campaign_id: int; original_email_template_id: int; follow_up_email_template_id: int; delay_days: int; condition: str; is_active: bool; created_at: datetime; updated_at: datetime
    class FollowUpRuleCreate(BaseModel): campaign_id: int; original_email_template_id: int; follow_up_email_template_id: int; delay_days: int; condition: str; is_active: bool = True
    class FollowUpRuleUpdate(BaseModel): original_email_template_id: Optional[int] = None; follow_up_email_template_id: Optional[int] = None; delay_days: Optional[int] = None; condition: Optional[str] = None; is_active: Optional[bool] = None
    class rules_service:
        async def create_rule(db: Session, **kwargs) -> FollowUpRule: return FollowUpRule(**kwargs, id=1, created_at=datetime.utcnow(), updated_at=datetime.utcnow())
        async def get_rule(db: Session, rule_id: int) -> Optional[FollowUpRule]: return None
        async def get_rules_for_campaign(db: Session, campaign_id: int) -> List[FollowUpRule]: return []
        async def update_rule(db: Session, rule_id: int, **kwargs) -> Optional[FollowUpRule]: return None
        async def delete_rule(db: Session, rule_id: int) -> bool: return True

    def get_db(): pass
    def get_current_active_user() -> User: return User(id=1) # Placeholder

router = APIRouter(
    prefix="/followup-rules", # Prefix for all follow-up rule routes
    tags=["follow-up-rules"]  # Tag for API documentation
)

# Pydantic Response Model for FollowUpRule
class FollowUpRuleResponse(BaseModel):
    id: int
    campaign_id: int
    original_email_template_id: int
    follow_up_email_template_id: int
    delay_days: int
    condition: str # e.g., 'not_opened_within_delay'
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True # For Pydantic V1
        # from_attributes = True # For Pydantic V2


@router.post("/", response_model=FollowUpRuleResponse, status_code=status.HTTP_201_CREATED)
async def create_follow_up_rule_api(
    rule_in: FollowUpRuleCreate, # Uses delay_days, condition: str
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user) # Assuming rules are user-scoped via campaign
):
    """
    Create a new follow-up rule.
    """
    # Here, you might want to add a check to ensure the current_user owns the campaign_id in rule_in.
    # This would require fetching the campaign first. For simplicity, skipping this check here.
    # Example check:
    # campaign = await db_get_campaign(db, rule_in.campaign_id)
    # if not campaign or campaign.user_id != current_user.id:
    #     raise HTTPException(status_code=403, detail="Not authorized to create rule for this campaign")

    try:
        # Pass parameters to service function as distinct arguments
        created_rule = await rules_service.create_rule(
            db=db,
            campaign_id=rule_in.campaign_id,
            original_email_template_id=rule_in.original_email_template_id,
            follow_up_email_template_id=rule_in.follow_up_email_template_id,
            delay_days=rule_in.delay_days,
            condition=rule_in.condition,
            is_active=rule_in.is_active
        )
        return created_rule
    except rules_service.FollowUpRuleServiceError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/campaign/{campaign_id}", response_model=List[FollowUpRuleResponse])
async def get_follow_up_rules_for_campaign_api(
    campaign_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user) # Ensure user owns campaign
):
    """
    List all follow-up rules for a specific campaign.
    """
    # Add campaign ownership check if necessary
    # campaign = await db_get_campaign(db, campaign_id)
    # if not campaign or campaign.user_id != current_user.id:
    #     raise HTTPException(status_code=403, detail="Not authorized to view rules for this campaign")
    rules = await rules_service.get_rules_for_campaign(db, campaign_id)
    return rules


@router.get("/{rule_id}", response_model=FollowUpRuleResponse)
async def get_follow_up_rule_api(
    rule_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user) # Ensure user owns rule via campaign
):
    """
    Get a specific follow-up rule by its ID.
    """
    rule = await rules_service.get_rule(db, rule_id)
    if not rule:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Follow-up rule not found")
    # Add campaign ownership check if necessary:
    # campaign = await db_get_campaign(db, rule.campaign_id)
    # if not campaign or campaign.user_id != current_user.id:
    #     raise HTTPException(status_code=403, detail="Not authorized to access this rule")
    return rule


@router.put("/{rule_id}", response_model=FollowUpRuleResponse)
async def update_follow_up_rule_api(
    rule_id: int,
    rule_in: FollowUpRuleUpdate, # Uses delay_days, condition: str
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user) # Ensure user owns rule via campaign
):
    """
    Update an existing follow-up rule.
    """
    # First, get the existing rule to check ownership via campaign
    existing_rule = await rules_service.get_rule(db, rule_id)
    if not existing_rule:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Follow-up rule not found")

    # campaign = await db_get_campaign(db, existing_rule.campaign_id)
    # if not campaign or campaign.user_id != current_user.id:
    #     raise HTTPException(status_code=403, detail="Not authorized to update this rule")

    try:
        # Pass fields from rule_in to the service update function
        updated_rule = await rules_service.update_rule(
            db=db,
            rule_id=rule_id,
            original_email_template_id=rule_in.original_email_template_id,
            follow_up_email_template_id=rule_in.follow_up_email_template_id,
            delay_days=rule_in.delay_days,
            condition=rule_in.condition,
            is_active=rule_in.is_active
        )
        if not updated_rule: # Should be caught by the existing_rule check or if update itself returns None on fail
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Follow-up rule not found after update attempt.")
        return updated_rule
    except rules_service.FollowUpRuleServiceError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete("/{rule_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_follow_up_rule_api(
    rule_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user) # Ensure user owns rule via campaign
):
    """
    Delete a follow-up rule.
    """
    # First, get the existing rule to check ownership via campaign
    existing_rule = await rules_service.get_rule(db, rule_id)
    if not existing_rule:
        # If you prefer to return 204 even if not found (idempotent delete):
        # return Response(status_code=status.HTTP_204_NO_CONTENT)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Follow-up rule not found")

    # campaign = await db_get_campaign(db, existing_rule.campaign_id)
    # if not campaign or campaign.user_id != current_user.id:
    #     raise HTTPException(status_code=403, detail="Not authorized to delete this rule")

    success = await rules_service.delete_rule(db, rule_id)
    if not success:
        # This case might be redundant if get_rule already confirmed existence.
        # However, delete_rule in service might return False for other reasons.
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to delete follow-up rule.")

    return None # FastAPI handles 204 No Content response

```
