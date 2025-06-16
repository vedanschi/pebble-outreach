# backend/src/models/email_template_models.py
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Boolean
from sqlalchemy.orm import relationship

from . import Base

class EmailTemplate(Base):
    __tablename__ = "email_templates"

    id = Column(Integer, primary_key=True, index=True)
    campaign_id = Column(Integer, ForeignKey('campaigns.id', ondelete='CASCADE'), nullable=False)
    
    name = Column(String(255), nullable=False)
    subject_template = Column(String(255), nullable=False)
    body_template = Column(Text, nullable=False)
    user_prompt = Column(Text)  # Stores the prompt used to generate the template
    
    is_follow_up = Column(Boolean, default=False)
    is_primary = Column(Boolean, default=True)
    
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    campaign = relationship("Campaign", back_populates="email_templates")
    sent_emails = relationship("SentEmail", back_populates="email_template")