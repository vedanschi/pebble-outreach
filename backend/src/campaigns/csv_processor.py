# backend/src/campaigns/csv_processor.py
import csv
import io
from typing import List, Dict, Any, Tuple, Optional
from datetime import datetime

from sqlalchemy.orm import Session
from pydantic import ValidationError, EmailStr

from src.models.user_models import Campaign, Contact
from src.schemas.campaign_schemas import CampaignCreate
from src.schemas.contact_schemas import ContactCreate, ContactResponse

# CSV Headers mapping (internal_field_name: csv_header_name)
EXPECTED_HEADERS = {
    "linkedin_url": "Linkedin Url",
    "full_name": "Full Name*",
    "first_name": "First Name*",
    "last_name": "Last Name*",
    "email": "Email*",
    "job_title": "Job Title",
    "company_name": "Company Name*",
    "company_website": "Company Website",
    "city": "City",
    "state": "State",
    "country": "Country",
    "industry": "Industry",
    "keywords": "Keywords",
    "employees": "Employees",
    "company_city": "Company City",
    "company_state": "Company State",
    "company_country": "Company Country",
    "company_linkedin_url": "Company Linkedin Url",
    "company_twitter_url": "Company Twitter Url",
    "company_facebook_url": "Company Facebook Url",
    "company_phone_numbers": "Company Phone Numbers",
    "twitter_url": "Twitter Url",
    "facebook_url": "Facebook Url"
}

# Required fields that must be present in CSV
ESSENTIAL_FIELDS = ["first_name", "last_name", "email", "company_name"]

class CSVProcessingError(Exception):
    """Custom exception for CSV processing errors"""
    pass

async def create_campaign(
    db: Session,
    user_id: int,
    campaign_name: str
) -> Campaign:
    """Creates a new campaign in the database"""
    try:
        campaign_data = CampaignCreate(
            name=campaign_name,
            user_id=user_id,
            status="draft",
            created_at=datetime.utcnow()
        )
        campaign = Campaign(**campaign_data.dict())
        db.add(campaign)
        db.commit()
        db.refresh(campaign)
        return campaign
    except Exception as e:
        db.rollback()
        raise CSVProcessingError(f"Failed to create campaign: {str(e)}")

async def create_contact(
    db: Session,
    contact_data: ContactCreate,
    campaign_id: int
) -> Contact:
    """Creates a new contact in the database"""
    try:
        contact = Contact(**contact_data.dict(), campaign_id=campaign_id)
        db.add(contact)
        db.commit()
        db.refresh(contact)
        return contact
    except Exception as e:
        db.rollback()
        raise CSVProcessingError(f"Failed to create contact: {str(e)}")

def validate_csv_headers(headers: List[str]) -> List[str]:
    """Validates CSV headers against expected headers"""
    errors = []
    required_headers = [EXPECTED_HEADERS[field] for field in ESSENTIAL_FIELDS]
    missing_headers = [header for header in required_headers if header not in headers]
    
    if missing_headers:
        errors.append(f"Missing required headers: {', '.join(missing_headers)}")
    
    return errors

def process_row_data(row: Dict[str, str], line_number: int) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    """Processes and validates a single row of CSV data"""
    contact_data = {}
    
    # Map CSV fields to internal fields
    for internal_key, csv_header in EXPECTED_HEADERS.items():
        value = row.get(csv_header, "").strip()
        contact_data[internal_key] = value

    # Validate essential fields
    missing_fields = [
        EXPECTED_HEADERS[field]
        for field in ESSENTIAL_FIELDS
        if not contact_data.get(field)
    ]
    
    if missing_fields:
        return None, f"Line {line_number}: Missing required fields: {', '.join(missing_fields)}"

    # Validate email format
    email = contact_data.get("email")
    if not "@" in email or not "." in email:
        return None, f"Line {line_number}: Invalid email format: {email}"

    # Convert employees to integer if present
    if contact_data.get("employees"):
        try:
            contact_data["employees"] = int(contact_data["employees"])
        except ValueError:
            contact_data["employees"] = None

    return contact_data, None

async def process_csv_upload(
    user_id: int,
    campaign_name: str,
    csv_file_content: bytes,
    db: Session
) -> Tuple[Optional[Campaign], List[ContactResponse], List[str]]:
    """
    Process CSV file upload to create a campaign and contacts.
    
    Args:
        user_id: ID of the user creating the campaign
        campaign_name: Name of the campaign
        csv_file_content: Raw CSV file content in bytes
        db: Database session
    
    Returns:
        Tuple containing:
        - Campaign object or None if creation failed
        - List of created contacts
        - List of error messages
    """
    campaign = None
    imported_contacts = []
    errors = []

    try:
        # Create campaign first
        campaign = await create_campaign(db, user_id, campaign_name)

        # Process CSV content
        csv_text = csv_file_content.decode('utf-8-sig')  # Handle BOM if present
        csv_file = io.StringIO(csv_text)
        reader = csv.DictReader(csv_file)

        # Validate headers
        header_errors = validate_csv_headers(reader.fieldnames or [])
        if header_errors:
            raise CSVProcessingError("\n".join(header_errors))

        # Process each row
        for line_number, row in enumerate(reader, start=2):
            # Process and validate row data
            contact_data, error = process_row_data(row, line_number)
            
            if error:
                errors.append(error)
                continue

            try:
                # Create contact schema
                contact_schema = ContactCreate(**contact_data)
                
                # Create contact in database
                contact = await create_contact(db, contact_schema, campaign.id)
                imported_contacts.append(ContactResponse.from_orm(contact))

            except ValidationError as ve:
                errors.append(f"Line {line_number}: Validation error: {str(ve)}")
            except Exception as e:
                errors.append(f"Line {line_number}: Failed to create contact: {str(e)}")

    except UnicodeDecodeError:
        errors.append("Failed to decode CSV file. Please ensure it's UTF-8 encoded.")
        return None, [], errors
    except CSVProcessingError as e:
        errors.append(str(e))
        return None, [], errors
    except Exception as e:
        errors.append(f"Unexpected error: {str(e)}")
        return None, [], errors

    # Handle empty CSV case
    if not errors and not imported_contacts:
        errors.append("No valid contacts found in CSV file")

    return campaign, imported_contacts, errors

def validate_contact_data(contact_data: Dict[str, Any]) -> List[str]:
    """Validates contact data before database insertion"""
    errors = []
    
    # Validate email format
    email = contact_data.get("email", "")
    if not "@" in email or not "." in email:
        errors.append(f"Invalid email format: {email}")
    
    # Validate required fields
    for field in ESSENTIAL_FIELDS:
        if not contact_data.get(field):
            errors.append(f"Missing required field: {EXPECTED_HEADERS[field]}")
    
    return errors