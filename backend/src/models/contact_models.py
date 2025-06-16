# backend/src/models/contact_models.py
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship

from . import Base

class Contact(Base):
    __tablename__ = "contacts"

    id = Column(Integer, primary_key=True, index=True)
    campaign_id = Column(Integer, ForeignKey('campaigns.id', ondelete='CASCADE'), nullable=False)
    
    # Personal Information
    linkedin_url = Column(String(255))
    full_name = Column(String(255), nullable=False)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    email = Column(String(255), nullable=False)
    job_title = Column(String(255))
    
    # Company Information
    company_name = Column(String(255), nullable=False)
    company_website = Column(String(255))
    city = Column(String(100))
    state = Column(String(100))
    country = Column(String(100))
    industry = Column(String(255))
    keywords = Column(Text)
    employees = Column(Integer)
    
    # Company Location
    company_city = Column(String(100))
    company_state = Column(String(100))
    company_country = Column(String(100))
    
    # Social Links
    company_linkedin_url = Column(String(255))
    company_twitter_url = Column(String(255))
    company_facebook_url = Column(String(255))
    company_phone_numbers = Column(String(255))
    twitter_url = Column(String(255))
    facebook_url = Column(String(255))

    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    campaign = relationship("Campaign", back_populates="contacts")
    sent_emails = relationship("SentEmail", back_populates="contact", cascade="all, delete-orphan")