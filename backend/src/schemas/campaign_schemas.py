# backend/src/schemas/campaign_schemas.py
from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class CampaignBase(BaseModel):
    name: str
    user_id: int
    status: Optional[str] = "draft"

class CampaignCreate(CampaignBase):
    pass

class CampaignResponse(CampaignBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True