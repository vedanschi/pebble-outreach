# backend/src/campaigns/csv_processor.py
import csv
import io
from typing import List, Dict, Any, Tuple

# Assuming Pydantic models are defined elsewhere (e.g., backend/src/models/contact_models.py)
# For this subtask, we'll focus on the processing logic rather than strict model validation.
# from ..models.contact_models import ContactCreate # Example

# Placeholder for database interaction functions/classes
# async def db_create_campaign(user_id: int, campaign_name: str) -> Dict:
#     print(f"DB: Creating campaign '{campaign_name}' for user {user_id}")
#     return {"id": 1, "name": campaign_name} # Mock campaign object

# async def db_create_contact(contact_data: Dict) -> Dict:
#     print(f"DB: Creating contact {contact_data.get('email')} for campaign {contact_data.get('campaign_id')}")
#     return contact_data # Mock contact object

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
    user_id: int,
    campaign_name: str,
    csv_file_content: bytes, # Raw bytes from the uploaded file
    db_create_campaign_func, # Injected dependency for DB op
    db_create_contact_func   # Injected dependency for DB op
) -> Tuple[Dict[str, Any], List[Dict[str, Any]], List[str]]:
    """
    Processes a CSV file upload to create a campaign and populate contacts.

    Args:
        user_id: ID of the user uploading the file.
        campaign_name: Name for the new campaign.
        csv_file_content: Content of the CSV file as bytes.
        db_create_campaign_func: Async function to create a campaign in the DB.
        db_create_contact_func: Async function to create a contact in the DB.

    Returns:
        A tuple containing:
        - campaign_details: Dictionary of the created campaign.
        - imported_contacts: List of successfully imported contact data.
        - errors: List of error messages for rows that couldn't be processed.
    """

    # Simulate campaign creation (in a real app, this is a DB call)
    # campaign_details = await db_create_campaign(user_id=user_id, campaign_name=campaign_name)
    # For subtask, just mock it:
    print(f"CSV_PROCESSOR: Simulating campaign creation: '{campaign_name}' for user {user_id}")
    campaign_details = {"id": "mock_campaign_id_" + str(user_id), "name": campaign_name, "user_id": user_id}

    imported_contacts: List[Dict[str, Any]] = []
    processing_errors: List[str] = []

    try:
        # Decode bytes to string and use StringIO to treat it like a file
        csv_file_str = csv_file_content.decode('utf-8') # Add error handling for decoding if needed
        csv_file_io = io.StringIO(csv_file_str)

        reader = csv.DictReader(csv_file_io)

        # Validate headers - ensure all expected headers are present (optional, depends on strictness)
        # For now, we assume EXPECTED_HEADERS guides the mapping.
        # More sophisticated: normalize headers (lower case, strip spaces) from reader.fieldnames

        for i, row in enumerate(reader):
            line_num = i + 2 # Account for header row and 0-based index

            # Normalize row keys (header names from CSV) if necessary
            # For simplicity, assuming CSV headers match values in EXPECTED_HEADERS

            contact_data = map_row_to_contact_dict(row, EXPECTED_HEADERS)
            contact_data["campaign_id"] = campaign_details["id"] # Link contact to the new campaign

            # Basic Validation for essential fields
            missing_essentials = [
                EXPECTED_HEADERS[key] for key in ESSENTIAL_FIELDS_INTERNAL
                if not contact_data.get(key)
            ]
            if missing_essentials:
                processing_errors.append(f"Line {line_num}: Missing essential fields: {', '.join(missing_essentials)}")
                continue

            # Email validation (very basic example)
            if "@" not in contact_data.get("email", ""):
                processing_errors.append(f"Line {line_num}: Invalid email format for '{contact_data.get('email')}'.")
                continue

            # TODO: Add more specific validation for other fields (e.g., URL formats, data types)

            # Simulate contact creation (in a real app, this is a DB call)
            # created_contact = await db_create_contact(contact_data)
            # For subtask, just mock it:
            print(f"CSV_PROCESSOR: Simulating contact creation for email: {contact_data['email']}")
            created_contact = contact_data # In reality, this would have an ID from DB
            imported_contacts.append(created_contact)

    except UnicodeDecodeError:
        processing_errors.append("Error decoding CSV file. Please ensure it is UTF-8 encoded.")
    except csv.Error as e:
        processing_errors.append(f"CSV parsing error: {e}")
    except Exception as e:
        # Catch-all for other unexpected errors during processing
        processing_errors.append(f"An unexpected error occurred: {e}")
        # Potentially re-raise or log more details for debugging

    # Summary
    if not processing_errors and not imported_contacts:
        processing_errors.append("No data found in CSV or CSV was empty after header.")

    return campaign_details, imported_contacts, processing_errors


async def example_usage():
    """Example of how process_csv_upload might be called."""

    # Mock DB functions for the example
    async def mock_db_create_campaign(user_id: int, campaign_name: str) -> Dict:
        print(f"Mock DB: Creating campaign '{campaign_name}' for user {user_id}")
        return {"id": 123, "name": campaign_name, "user_id": user_id}

    async def mock_db_create_contact(contact_data: Dict) -> Dict:
        print(f"Mock DB: Creating contact {contact_data.get('email')} for campaign {contact_data.get('campaign_id')}")
        contact_data_with_id = contact_data.copy()
        contact_data_with_id["id"] = "mock_contact_id_" + contact_data.get('email', 'unknown')
        return contact_data_with_id

    # Sample CSV content (as bytes, like it would be read from a file upload)
    sample_csv_data = b"""Linkedin Url,Full Name*,First Name*,Last Name*,Email*,Job Title,Company Name*,Company Website,City,State,Country,Industry,Keywords,Employees,Company City,Company State,Company Country,Company Linkedin Url,Company Twitter Url,Company Facebook Url,Company Phone Numbers,Twitter Url,Facebook Url
http://linkedin.com/in/johndoe,John Doe,John,Doe,john.doe@example.com,CEO,Example Corp,http://example.com,New York,NY,USA,Tech,SaaS,100,New York,NY,USA,http://linkedin.com/company/examplecorp,,,,,,
,Jane Smith,Jane,Smith,jane.smith@example.com,CTO,Innovate Ltd.,http://innovate.com,London,,UK,Software,AI,50,London,,UK,,,,,,
incomplete,,Incomplete,User,incomplete.user@test.com,,Test Co,,,,,,,,,,,,,,,,
"""

    user_id = 1
    campaign_name = "Q3 Outreach"

    campaign, imported, errors = await process_csv_upload(
        user_id, campaign_name, sample_csv_data,
        mock_db_create_campaign, mock_db_create_contact
    )

    print("\n--- Processing Summary ---")
    if campaign:
        print(f"Campaign Created: ID {campaign.get('id')}, Name: {campaign.get('name')}")

    print(f"Successfully Imported Contacts: {len(imported)}")
    # for contact in imported:
    #     print(f"  - {contact.get('email')}")

    if errors:
        print(f"Errors Encountered ({len(errors)}):")
        for error in errors:
            print(f"  - {error}")

if __name__ == "__main__":
    # To run the example (requires an asyncio event loop)
    import asyncio
    asyncio.run(example_usage())