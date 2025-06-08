# backend/src/campaigns/csv_processor.py
import csv
import io
from typing import List, Dict, Any, Tuple, Optional

from sqlalchemy.orm import Session
from pydantic import ValidationError

# Assuming ORM models and Pydantic schemas are structured as per the prompt
# Adjust these imports based on your actual project structure
try:
    from src.models.campaign_models import Campaign
    from src.models.contact_models import Contact
    from src.schemas.campaign_schemas import CampaignCreate
    from src.schemas.contact_schemas import ContactCreate, Contact as ContactSchema # Assuming a Contact schema for return
except ImportError:
    # Fallback for environments where these models might not be directly available
    # or for a simplified standalone execution.
    # In a real application, ensure these paths are correct and resolvable.
    print("Warning: Could not import ORM models or Pydantic schemas. Using placeholder types.")
    Campaign = Any
    Contact = Any
    CampaignCreate = Any
    ContactCreate = Any
    ContactSchema = Any


# Expected CSV Headers (based on user's issue description)
# '*' indicates fields considered essential by the user.
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

ESSENTIAL_FIELDS_INTERNAL = ["first_name", "last_name", "email", "company_name"] # Internal keys for essential fields


async def db_create_campaign(db: Session, user_id: int, campaign_name: str) -> Campaign:
    """
    Creates a new Campaign ORM object, adds it to the session, commits, and refreshes.
    Returns the created Campaign ORM instance.
    """
    campaign_data = CampaignCreate(name=campaign_name, user_id=user_id)
    db_campaign = Campaign(**campaign_data.model_dump())
    db.add(db_campaign)
    db.commit()
    db.refresh(db_campaign)
    return db_campaign

async def db_create_contact(db: Session, contact_data: ContactCreate, campaign_id: int) -> Contact:
    """
    Creates a new Contact ORM object from a ContactCreate Pydantic object and campaign_id,
    adds it to the session, commits, and refreshes.
    Returns the created Contact ORM instance.
    """
    # Ensure campaign_id is part of the data for the ORM model
    db_contact = Contact(**contact_data.model_dump(), campaign_id=campaign_id)
    db.add(db_contact)
    db.commit() # Individual commit for each contact as per subtask requirement
    db.refresh(db_contact)
    return db_contact

def map_row_to_contact_dict(row: Dict[str, str], header_map: Dict[str, str]) -> Dict[str, Any]:
    """Maps a CSV row (dict) to a dictionary suitable for contact creation, based on header_map."""
    contact_data = {}
    for internal_key, csv_header_name in header_map.items():
        contact_data[internal_key] = row.get(csv_header_name, "").strip()

    # Basic type conversion examples (more robust validation needed)
    if contact_data.get("employees"):
        try:
            contact_data["employees"] = int(contact_data["employees"])
        except ValueError:
            contact_data["employees"] = None # Or raise error/log
    return contact_data

async def process_csv_upload(
    user_id: int, # Assuming user_id is still relevant for campaign ownership
    campaign_name: str,
    csv_file_content: bytes, # Raw bytes from the uploaded file
    db: Session # SQLAlchemy session
) -> Tuple[Optional[Campaign], List[Contact], List[str]]:
    """
    Processes a CSV file upload to create a campaign and populate contacts using SQLAlchemy.

    Args:
        user_id: ID of the user creating the campaign.
        campaign_name: Name for the new campaign.
        csv_file_content: Content of the CSV file as bytes.
        db: SQLAlchemy Session for database operations.

    Returns:
        A tuple containing:
        - campaign: The created ORM Campaign object, or None if campaign creation failed.
        - imported_contacts: List of successfully created ORM Contact objects.
        - errors: List of error messages for rows that couldn't be processed.
    """
    created_campaign: Optional[Campaign] = None
    imported_contacts: List[Contact] = []
    processing_errors: List[str] = []

    try:
        created_campaign = await db_create_campaign(db=db, user_id=user_id, campaign_name=campaign_name)
    except Exception as e:
        # Handle campaign creation failure
        processing_errors.append(f"Failed to create campaign '{campaign_name}': {e}")
        # If campaign creation fails, we cannot proceed to add contacts to it.
        return None, imported_contacts, processing_errors

    if not created_campaign: # Should be redundant if db_create_campaign raises on failure
        processing_errors.append(f"Campaign object was not created for '{campaign_name}'.")
        return None, imported_contacts, processing_errors

    campaign_id = created_campaign.id
    if campaign_id is None: # Defensive check, should have ID after refresh
        processing_errors.append(f"Campaign ID not found after creating campaign '{campaign_name}'.")
        return created_campaign, imported_contacts, processing_errors

    try:
        # Decode bytes to string and use StringIO to treat it like a file
        csv_file_str = csv_file_content.decode('utf-8')
        csv_file_io = io.StringIO(csv_file_str)
        reader = csv.DictReader(csv_file_io)

        for i, row in enumerate(reader):
            line_num = i + 2 # For user-friendly error reporting (1-based index + header)
            contact_raw_data = map_row_to_contact_dict(row, EXPECTED_HEADERS)

            # Validate essential fields before Pydantic model creation
            missing_essentials = [
                EXPECTED_HEADERS[key] for key in ESSENTIAL_FIELDS_INTERNAL
                if not contact_raw_data.get(key)
            ]
            if missing_essentials:
                processing_errors.append(f"Line {line_num}: Missing essential fields: {', '.join(missing_essentials)}")
                continue

            # Basic email check before Pydantic (can be enhanced in Pydantic model)
            if "@" not in contact_raw_data.get("email", ""):
                processing_errors.append(f"Line {line_num}: Invalid email format for '{contact_raw_data.get('email')}'.")
                continue

            try:
                # Convert dict to Pydantic model for validation and type coercion
                # Note: campaign_id is passed separately to db_create_contact
                contact_schema_data = ContactCreate(**contact_raw_data)
            except ValidationError as ve:
                errors = [f"{err['loc'][0]}: {err['msg']}" for err in ve.errors()]
                processing_errors.append(f"Line {line_num}: Validation error for contact '{contact_raw_data.get('email', 'N/A')}': {'; '.join(errors)}")
                continue
            except Exception as e: # Catch any other model instantiation errors
                processing_errors.append(f"Line {line_num}: Error creating contact model for '{contact_raw_data.get('email', 'N/A')}': {e}")
                continue

            try:
                # Pass Pydantic model to DB creation function
                created_contact_orm = await db_create_contact(db=db, contact_data=contact_schema_data, campaign_id=campaign_id)
                imported_contacts.append(created_contact_orm)
            except Exception as e:
                # Catch errors from db_create_contact (e.g., database integrity errors)
                processing_errors.append(f"Line {line_num}: Failed to save contact '{contact_schema_data.email}': {e}")
                # Depending on transaction strategy, might need to db.rollback() here if not committing per contact.
                # For this subtask, each contact is committed individually.

    except UnicodeDecodeError:
        processing_errors.append("Error decoding CSV file. Please ensure it is UTF-8 encoded.")
    except csv.Error as e:
        processing_errors.append(f"CSV parsing error: {e}")
    except Exception as e:
        processing_errors.append(f"An unexpected error occurred during CSV processing: {e}")
        # Log detailed error for debugging: import traceback; traceback.print_exc();

    if not processing_errors and not imported_contacts and created_campaign:
        processing_errors.append("No data found in CSV or CSV was empty after header.")

    return created_campaign, imported_contacts, processing_errors

# The `if __name__ == "__main__":` block and `example_usage` function
# would require a running database and SQLAlchemy setup to be meaningful.
# For a library file, it's often better to test this functionality
# through dedicated integration tests.
# Consider removing or adapting it for a specific testing context if needed.

# if __name__ == "__main__":
#     # Example setup (requires DB, models, etc.)
#     # from sqlalchemy import create_engine
#     # from sqlalchemy.orm import sessionmaker
#     # from src.database import Base # Assuming your Base for ORM models
#     # from src.models import campaign_models, contact_models # Make sure they are loaded

#     # SQLALCHEMY_DATABASE_URL = "sqlite:///./test_csv_processor.db"
#     # engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
#     # Base.metadata.create_all(bind=engine) # Create tables

#     # TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

#     async def run_example():
#         db_session = TestingSessionLocal()
#         try:
#             # Sample CSV content (as bytes, like it would be read from a file upload)
#             sample_csv_data = b"""Full Name*,First Name*,Last Name*,Email*,Company Name*
# John Doe,John,Doe,john.doe@example.com,Example Corp
# Jane Smith,Jane,Smith,jane.smith@example.com,Innovate Ltd.
# Incomplete User,,User,incomplete.user@test.com,Test Co
# Bad Email,Bad,Email,bademail,Company X
# """
#             # Ensure EXPECTED_HEADERS and ESSENTIAL_FIELDS_INTERNAL align with this sample for the example to run
#             # For instance, the sample above is minimal. A more complete one:
#             # sample_csv_data = b"""Linkedin Url,Full Name*,First Name*,Last Name*,Email*,Job Title,Company Name*,Company Website,City,State,Country,Industry,Keywords,Employees,Company City,Company State,Company Country,Company Linkedin Url,Company Twitter Url,Company Facebook Url,Company Phone Numbers,Twitter Url,Facebook Url
# # http://linkedin.com/in/johndoe,John Doe,John,Doe,john.doe@example.com,CEO,Example Corp,http://example.com,New York,NY,USA,Tech,SaaS,100,New York,NY,USA,http://linkedin.com/company/examplecorp,,,,,,
# # ,Jane Smith,Jane,Smith,jane.smith@example.com,CTO,Innovate Ltd.,http://innovate.com,London,,UK,Software,AI,50,London,,UK,,,,,,
# # incomplete,,Incomplete,User,incomplete.user@test.com,,Test Co,,,,,,,,,,,,,,,,
# # """

#             user_id = 1
#             campaign_name = "My Test Campaign"

#             print(f"Running example: Creating campaign '{campaign_name}' for user_id {user_id}")

#             campaign, imported, errors = await process_csv_upload(
#                 user_id=user_id,
#                 campaign_name=campaign_name,
#                 csv_file_content=sample_csv_data,
#                 db=db_session
#             )

#             print("\n--- Processing Summary ---")
#             if campaign:
#                 print(f"Campaign Created: ID {campaign.id}, Name: {campaign.name}, User ID: {campaign.user_id}")
#                 # Query to see if contacts were added to this campaign
#                 # contacts_in_db = db_session.query(Contact).filter(Contact.campaign_id == campaign.id).all()
#                 # print(f"Contacts found in DB for this campaign: {len(contacts_in_db)}")


#             print(f"Successfully Imported Contacts (Objects): {len(imported)}")
#             for contact_obj in imported:
#                 print(f"  - ID: {contact_obj.id}, Email: {contact_obj.email}, Campaign ID: {contact_obj.campaign_id}")

#             if errors:
#                 print(f"Errors Encountered ({len(errors)}):")
#                 for error in errors:
#                     print(f"  - {error}")

#             # Example: Querying all contacts to verify (if needed)
#             # all_contacts = db_session.query(Contact).all()
#             # print(f"Total contacts in DB: {len(all_contacts)}")

#         except Exception as e:
#             print(f"Error during example execution: {e}")
#             # import traceback
#             # traceback.print_exc()
#         finally:
#             db_session.close()
#             # os.remove("./test_csv_processor.db") # Clean up test DB

#     # if __name__ == "__main__":
#     #     import asyncio
#     #     asyncio.run(run_example())
#     # This main guard is usually for executable scripts. For a module, tests are better.
#     # If you want to run this, ensure your environment can import 'src.models' etc.
#     # You might need to adjust PYTHONPATH or run as a module: python -m src.campaigns.csv_processor