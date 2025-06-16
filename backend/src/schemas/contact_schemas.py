# backend/src/schemas/contact_schemas.py
from pydantic import BaseModel, EmailStr
from typing import Optional

class ContactBase(BaseModel):
    linkedin_url: Optional[str] = None
    first_name: str
    last_name: str
    full_name: str
    email: EmailStr
    job_title: Optional[str] = None
    company_name: str
    company_website: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    industry: Optional[str] = None
    keywords: Optional[str] = None
    employees: Optional[int] = None
    company_city: Optional[str] = None
    company_state: Optional[str] = None
    company_country: Optional[str] = None
    company_linkedin_url: Optional[str] = None
    company_twitter_url: Optional[str] = None
    company_facebook_url: Optional[str] = None
    company_phone_numbers: Optional[str] = None
    twitter_url: Optional[str] = None
    facebook_url: Optional[str] = None

class ContactCreate(ContactBase):
    pass

class ContactResponse(ContactBase):
    id: int
    campaign_id: int

    class Config:
        from_attributes = True