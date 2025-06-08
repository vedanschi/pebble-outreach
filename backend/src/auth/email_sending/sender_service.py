# backend/src/email_sending/sender_service.py
import asyncio # For potential async operations like batch delays
from typing import List, Dict, Any, Tuple, Optional

# Placeholder for a hypothetical ESP client
class MockESPClient:
    def __init__(self, api_key: str):
        if not api_key:
            raise ValueError("API key is required for ESP client.")
        self.api_key = api_key
        print(f"MockESPClient initialized.")

    async def send_email(
        self,
        to_email: str,
        from_email: str, # Should be a verified sender with the ESP
        subject: str,
        body_html: str, # Assuming HTML body for rich content
        # body_text: Optional[str] = None # Plain text version
    ) -> Dict[str, Any]:
        """Simulates sending an email via an ESP."""
        print(f"ESP Client: Sending email to '{to_email}' from '{from_email}' with subject '{subject}'.")
        # Simulate potential ESP responses
        if "fail" in to_email: # Simple way to simulate a failure
            return {"status": "failed", "error_message": "Invalid recipient address", "message_id": None}

        # Simulate successful send
        # In a real ESP, message_id would be crucial for tracking
        return {"status": "sent", "message_id": f"mock_esp_msg_id_{to_email.replace('@','_')}", "error_message": None}

# Placeholder for database interaction functions
# async def db_get_draft_emails_for_campaign(campaign_id: int) -> List[Dict[str, Any]]:
#     # Fetches emails from SentEmails table with status 'draft' for the campaign
#     pass

# async def db_update_sent_email_status(email_id: Any, new_status: str, message_id: str = None, error_info: str = None) -> None:
#     # Updates the status of an email in the SentEmails table
#     pass

class EmailSendingError(Exception):
    """Custom exception for email sending service issues."""
    pass

async def send_campaign_emails(
    campaign_id: int,
    esp_client: MockESPClient, # Pass the initialized ESP client
    default_from_email: str, # Default 'from' email for the campaign
    # Injected DB functions
    db_get_draft_emails_func,
    db_update_sent_email_status_func,
    batch_size: int = 50, # Number of emails to send before a small pause
    delay_between_batches: float = 2.0 # Seconds to wait between batches
) -> Tuple[int, int, List[str]]: # sent_count, failed_count, error_messages
    """
    Sends all draft emails for a specified campaign.

    Args:
        campaign_id: The ID of the campaign whose emails are to be sent.
        esp_client: An instance of an email service provider client.
        default_from_email: The email address to use as the sender.
        db_get_draft_emails_func: Async function to fetch draft emails.
        db_update_sent_email_status_func: Async function to update email status.
        batch_size: How many emails to process in one go before an optional delay.
        delay_between_batches: Time in seconds to pause between batches to respect rate limits.

    Returns:
        A tuple: (number_successfully_sent, number_failed, list_of_error_details).
    """

    sent_count = 0
    failed_count = 0
    error_details: List[str] = []

    try:
        draft_emails = await db_get_draft_emails_func(campaign_id)
        if not draft_emails:
            print(f"No draft emails found for campaign ID {campaign_id} to send.")
            return 0, 0, []
    except Exception as e:
        raise EmailSendingError(f"Failed to retrieve draft emails for campaign {campaign_id}: {e}")

    print(f"Found {len(draft_emails)} draft emails to send for campaign {campaign_id}.")

    for i, email_draft in enumerate(draft_emails):
        email_id = email_draft.get("id")
        to_address = email_draft.get("email_address") # This should be the recipient's email
        subject = email_draft.get("subject")
        body = email_draft.get("body") # Assuming this is HTML body

        if not all([email_id, to_address, subject, body]):
            error_message = f"Skipping email ID {email_id}: missing crucial data (to_address, subject, or body)."
            print(error_message)
            error_details.append(error_message)
            failed_count += 1
            # Optionally update status to 'failed_preprocessing' or similar
            await db_update_sent_email_status_func(email_id, "failed", error_info=error_message)
            continue

        try:
            print(f"Attempting to send email ID {email_id} to {to_address}...")
            send_result = await esp_client.send_email(
                to_email=to_address,
                from_email=default_from_email,
                subject=subject,
                body_html=body # Assuming body is already HTML formatted
            )

            if send_result.get("status") == "sent":
                await db_update_sent_email_status_func(
                    email_id,
                    "sent",
                    message_id=send_result.get("message_id")
                )
                sent_count += 1
            else:
                error_msg = send_result.get("error_message", "Unknown ESP error")
                await db_update_sent_email_status_func(
                    email_id,
                    "failed",
                    error_info=error_msg
                )
                failed_count += 1
                error_details.append(f"Failed to send to {to_address} (ID: {email_id}): {error_msg}")

        except Exception as e:
            # Catch errors from ESP client call or DB update for this specific email
            error_msg = f"Error processing email ID {email_id} for {to_address}: {e}"
            print(error_msg)
            try:
                await db_update_sent_email_status_func(email_id, "failed", error_info=str(e))
            except Exception as db_e: # If updating status itself fails
                 error_msg += f" | Also failed to update DB status: {db_e}"
            failed_count += 1
            error_details.append(error_msg)

        # Basic rate limiting: pause after each batch
        if (i + 1) % batch_size == 0 and (i + 1) < len(draft_emails):
            print(f"Sent batch of {batch_size}. Pausing for {delay_between_batches}s...")
            await asyncio.sleep(delay_between_batches)
            print("Resuming sending...")

    return sent_count, failed_count, error_details


async def example_sender_usage():
    """Example of how send_campaign_emails might be called."""

    # --- Mocking dependencies for the example ---
    MOCK_DRAFT_EMAILS_DB = { # campaign_id -> list of draft emails
        789: [
            {"id": "draft_001", "campaign_id": 789, "email_address": "recipient1@example.com", "subject": "Hello Recipient 1", "body": "<p>Test body 1</p>"},
            {"id": "draft_002", "campaign_id": 789, "email_address": "recipient2_fail@example.com", "subject": "Hello Recipient 2", "body": "<p>Test body 2, will fail</p>"},
            {"id": "draft_003", "campaign_id": 789, "email_address": "recipient3@example.com", "subject": "Hello Recipient 3", "body": "<p>Test body 3</p>"},
        ],
        999: [] # No drafts for this campaign
    }
    MOCK_SENT_EMAILS_STATUS_DB = {} # email_id -> {status, message_id, error_info}

    async def mock_db_get_drafts(campaign_id: int) -> List[Dict[str, Any]]:
        print(f"MOCK DB: Getting draft emails for campaign {campaign_id}")
        return MOCK_DRAFT_EMAILS_DB.get(campaign_id, [])

    async def mock_db_update_status(email_id: Any, new_status: str, message_id: str = None, error_info: str = None) -> None:
        print(f"MOCK DB: Updating email {email_id} to status '{new_status}'. Message ID: {message_id}, Error: {error_info}")
        MOCK_SENT_EMAILS_STATUS_DB[email_id] = {"status": new_status, "message_id": message_id, "error_info": error_info}
    # --- End of Mocks ---

    test_campaign_id = 789
    my_esp_client = MockESPClient(api_key="test_esp_api_key")
    my_from_email = "sender@mycompany.com" # This should be a verified sender domain

    print(f"--- Running Email Sending Example for Campaign ID: {test_campaign_id} ---")

    sent, failed, errors = await send_campaign_emails(
        campaign_id=test_campaign_id,
        esp_client=my_esp_client,
        default_from_email=my_from_email,
        db_get_draft_emails_func=mock_db_get_drafts,
        db_update_sent_email_status_func=mock_db_update_status,
        batch_size=2, # Small batch for testing delay
        delay_between_batches=1
    )

    print("\n--- Sending Summary ---")
    print(f"Successfully Sent: {sent}")
    print(f"Failed to Send: {failed}")
    if errors:
        print(f"Error Details ({len(errors)}):")
        for error in errors:
            print(f"  - {error}")

    print("\n--- Final Email Statuses (from mock DB) ---")
    for email_id, status_info in MOCK_SENT_EMAILS_STATUS_DB.items():
        print(f"  Email ID {email_id}: {status_info}")


if __name__ == "__main__":
    import asyncio
    asyncio.run(example_sender_usage())