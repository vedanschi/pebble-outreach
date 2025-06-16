# backend/src/models/sent_email_models.py
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Boolean
from sqlalchemy.orm import relationship

from . import Base

class SentEmail(Base):
    __tablename__ = "sent_emails"

    id = Column(Integer, primary_key=True, index=True)
    campaign_id = Column(Integer, ForeignKey('campaigns.id', ondelete='CASCADE'), nullable=False)
    contact_id = Column(Integer, ForeignKey('contacts.id', ondelete='CASCADE'), nullable=False)
    email_template_id = Column(Integer, ForeignKey('email_templates.id', ondelete='SET NULL'))
    
    subject = Column(String(255), nullable=False)
    body = Column(Text, nullable=False)
    
    # Email Status
    status = Column(String(50), nullable=False, default='draft')  # draft, sending, sent, delivered, failed
    status_reason = Column(Text)
    
    # Tracking Information
    tracking_pixel_id = Column(String(100), unique=True)
    esp_message_id = Column(String(255), unique=True)  # Email Service Provider Message ID
    
    # Timing Information
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    sent_at = Column(DateTime(timezone=True))
    delivered_at = Column(DateTime(timezone=True))
    
    # Open Tracking
    opened_at = Column(DateTime(timezone=True))
    first_opened_ip = Column(String(100))
    last_opened_at = Column(DateTime(timezone=True))
    open_count = Column(Integer, default=0)
    
    # Click Tracking
    clicked_at = Column(DateTime(timezone=True))
    first_clicked_ip = Column(String(100))
    last_clicked_at = Column(DateTime(timezone=True))
    click_count = Column(Integer, default=0)
    
    # Follow-up Related
    is_follow_up = Column(Boolean, default=False)
    follows_up_on_email_id = Column(Integer, ForeignKey('sent_emails.id', ondelete='SET NULL'))
    
    # Relationships
    campaign = relationship("Campaign", back_populates="sent_emails")
    contact = relationship("Contact", back_populates="sent_emails")
    email_template = relationship("EmailTemplate", back_populates="sent_emails")
    follow_up_emails = relationship("SentEmail", 
                                  backref=relationship("SentEmail", remote_side=[id]),
                                  cascade="all, delete-orphan")