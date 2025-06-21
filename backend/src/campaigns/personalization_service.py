# backend/src/campaigns/personalization_service.py
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
import openai
from datetime import datetime
from typing import List, Dict, Any, Optional # Ensure these are here
from sqlalchemy.orm import Session # Ensure this is here
import openai # Ensure this is here

from src.core.config import settings
from src.models.user_models import Campaign, Contact, EmailTemplate
# Import new DB operation functions
from .db_operations import (
    db_get_email_template_by_id,
    db_create_email_template,
    db_get_contacts_for_campaign,
    db_get_campaign_by_id
)
from src.followups.db_operations import db_get_contact_details # For specific contact
from src.schemas.email_template_schemas import EmailTemplateCreate # For creating template

class PersonalizationService:
    def __init__(self, db: Session):
        self.db = db
        openai.api_key = settings.OPENAI_API_KEY

    async def generate_campaign_emails(
        self,
        campaign_id: int,
        user_prompt: str
    ) -> Optional[EmailTemplate]:
        """
        Generates personalized email templates for a campaign based on user prompt
        and contact data.
        """
        # Get campaign and contacts
        campaign = await db_get_campaign_by_id(self.db, campaign_id)
        if not campaign:
            raise ValueError(f"Campaign {campaign_id} not found")

        contacts = await db_get_contacts_for_campaign(self.db, campaign_id)
        if not contacts:
            raise ValueError(f"No contacts found for campaign {campaign_id}")

        # Get sample contact for template generation
        sample_contact = contacts[0]

        # Create system prompt for better email generation
        system_prompt = self._create_system_prompt(sample_contact)
        
        # Generate base template
        generated_template_dict = await self._generate_base_template(user_prompt, system_prompt, sample_contact)
        
        # Prepare data for new email template
        email_template_data = EmailTemplateCreate(
            campaign_id=campaign_id,
            name=f"AI Generated Template for {campaign.name} - {user_prompt[:30]}...", # Auto-generated name
            user_prompt=user_prompt,
            subject_template=generated_template_dict["subject"],
            body_template=generated_template_dict["body"]
            # is_primary defaults to False in db_create_email_template, adjust if needed here
        )
        
        # Save template to database using db operation
        # Note: Current db_create_email_template doesn't set owner_id.
        # EmailTemplate model doesn't have owner_id directly, it's via campaign.
        # is_primary might need specific handling if this is the first/only template.
        # For now, assuming default is_primary=False from db_op is acceptable.
        email_template = await db_create_email_template(
            self.db,
            template_data=email_template_data
            # is_primary=True # Consider if this should be the primary by default
        )

        try:
            await self.db.commit()
            await self.db.refresh(email_template)
        except Exception as e:
            await self.db.rollback()
            raise Exception(f"Error saving generated email template: {str(e)}")
        
        return email_template

    def _create_system_prompt(self, contact: Contact) -> str:
        """
        Creates a system prompt that guides the AI in generating appropriate emails.
        """
        return f"""You are an expert email writer specializing in personalized outreach campaigns.
Your task is to create email templates that will be personalized for each recipient.
Available personalization variables:
- {{first_name}} - Recipient's first name
- {{last_name}} - Recipient's last name
- {{full_name}} - Recipient's full name
- {{company_name}} - Company name
- {{job_title}} - Job title
- {{industry}} - Company industry
- {{company_website}} - Company website
- {{city}} - City
- {{country}} - Country
- {{linkedin_url}} - LinkedIn profile URL

Guidelines:
1. Create professional, engaging emails
2. Use personalization variables naturally
3. Keep subject lines clear and compelling
4. Maintain a friendly yet professional tone
5. Focus on value proposition
6. Include a clear call to action
7. Keep paragraphs short and scannable
8. Avoid spam trigger words
9. Make content relevant to recipient's industry and role

Example contact data for reference:
Name: {contact.full_name}
Company: {contact.company_name}
Title: {contact.job_title}
Industry: {contact.industry}"""

    async def _generate_base_template(
        self,
        user_prompt: str,
        system_prompt: str,
        sample_contact: Contact
    ) -> Dict[str, str]:
        """
        Generates the base email template using OpenAI's GPT.
        """
        try:
            completion = await openai.chat.completions.create(
                model="gpt-4",  # or your preferred model
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"""
Create an email template based on this request: {user_prompt}

The email should be personalized and professional. Generate both subject line and body.
Format the response as:
SUBJECT: [Your subject line]
BODY:
[Your email body]

Example contact:
Name: {sample_contact.full_name}
Company: {sample_contact.company_name}
Title: {sample_contact.job_title}
Industry: {sample_contact.industry}
                    """}
                ],
                temperature=0.7
            )

            response = completion.choices[0].message.content
            
            # Parse the response into subject and body
            subject = ""
            body = ""
            
            if "SUBJECT:" in response and "BODY:" in response:
                parts = response.split("BODY:")
                subject = parts[0].replace("SUBJECT:", "").strip()
                body = parts[1].strip()
            
            return {
                "subject": subject,
                "body": body
            }

        except Exception as e:
            raise Exception(f"Error generating email template: {str(e)}")

    async def preview_personalized_email(
        self,
        template_id: int,
        contact_id: int
    ) -> Dict[str, str]:
        """
        Previews how an email will look for a specific contact.
        """
        template = await db_get_email_template_by_id(self.db, template_id)
        # Using db_get_contact_details from followups.db_operations
        contact = await db_get_contact_details(self.db, contact_id)
        
        if not template or not contact:
            raise ValueError("Template or contact not found")
            
        # Create personalization mapping
        replacements = {
            "{first_name}": contact.first_name,
            "{last_name}": contact.last_name,
            "{full_name}": contact.full_name,
            "{company_name}": contact.company_name,
            "{job_title}": contact.job_title or "",
            "{industry}": contact.industry or "",
            "{company_website}": contact.company_website or "",
            "{city}": contact.city or "",
            "{country}": contact.country or "",
            "{linkedin_url}": contact.linkedin_url or ""
        }
        
        # Personalize subject and body
        subject = template.subject_template
        body = template.body_template
        
        for key, value in replacements.items():
            subject = subject.replace(key, str(value))
            body = body.replace(key, str(value))
            
        return {
            "subject": subject,
            "body": body
        }

    async def validate_template(self, template_id: int) -> List[Dict[str, Any]]:
        """
        Validates a template by checking for any missing or invalid personalization variables.
        """
        template = await db_get_email_template_by_id(self.db, template_id)
        if not template:
            raise ValueError("Template not found")

        validation_results = []
        all_variables = [
            "{first_name}", "{last_name}", "{full_name}", "{company_name}",
            "{job_title}", "{industry}", "{company_website}", "{city}",
            "{country}", "{linkedin_url}"
        ]

        # Check for valid variables
        for var in all_variables:
            if var in template.subject_template or var in template.body_template:
                validation_results.append({
                    "variable": var,
                    "status": "valid",
                    "location": []
                })
                if var in template.subject_template:
                    validation_results[-1]["location"].append("subject")
                if var in template.body_template:
                    validation_results[-1]["location"].append("body")

        return validation_results