# backend/src/models/campaign_models.py
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship

from . import Base

class Campaign(Base):
    __tablename__ = "campaigns"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    name = Column(String(255), nullable=False)
    status = Column(String(50), default='draft')  # draft, active, paused, completed
    
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="campaigns")
    contacts = relationship("Contact", back_populates="campaign", cascade="all, delete-orphan")
    email_templates = relationship("EmailTemplate", back_populates="campaign", cascade="all, delete-orphan")
    sent_emails = relationship("SentEmail", back_populates="campaign", cascade="all, delete-orphan")