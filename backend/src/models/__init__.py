# backend/src/models/__init__.py
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

from .user_models import User
from .campaign_models import Campaign
from .contact_models import Contact
from .email_template_models import EmailTemplate
from .sent_email_models import SentEmail

__all__ = [
    'Base',
    'User',
    'Campaign',
    'Contact',
    'EmailTemplate',
    'SentEmail'
]