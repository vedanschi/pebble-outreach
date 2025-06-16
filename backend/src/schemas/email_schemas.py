# backend/src/schemas/email_schemas.py
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

class SentEmailBase(BaseModel):
    campaign_id: int
    contact_id: int
    email_template_id: int
    subject: str
    body: str
    status: str
    status_reason: Optional[str] = None
    tracking_pixel_id: Optional[str] = None
    is_follow_up: bool = False
    follows_up_on_email_id: Optional[int] = None
    triggered_by_rule_id: Optional[int] = None

class SentEmailCreate(SentEmailBase):
    sent_at: Optional[datetime] = None

class SentEmailResponse(SentEmailBase):
    id: int
    created_at: datetime
    sent_at: Optional[datetime]
    delivered_at: Optional[datetime]
    opened_at: Optional[datetime]
    clicked_at: Optional[datetime]
    first_opened_ip: Optional[str]
    open_count: int = 0

    class Config:
        from_attributes = True