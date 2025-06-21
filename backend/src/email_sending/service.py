# backend/src/email_sending/service.py
import asyncio
import aiosmtplib
from email.message import EmailMessage
from typing import Tuple, Optional, Dict, Any, List
from uuid import uuid4
from datetime import datetime

from sqlalchemy.orm import Session
from ..core.config import settings
from ..models.user_models import SentEmail, Contact, EmailTemplate, Campaign # Keep these for other methods if needed
from .db_operations import db_record_email_open_event # Import the new DB operation

class EmailSendingError(Exception):
    """Custom exception for email sending issues."""
    pass

async def send_single_email_smtp(
    recipient_email: str,
    subject: str,
    body: str,
    smtp_config: Dict[str, Any]
) -> Tuple[bool, Optional[str]]:
    """
    Sends a single email using SMTP with aiosmtplib.

    Args:
        recipient_email: The email address of the recipient.
        subject: The subject of the email.
        body: The HTML or plain text body of the email.
        smtp_config: A dictionary containing SMTP server configuration.
            Expected keys:
            - 'host': (str) SMTP server hostname.
            - 'port': (int) SMTP server port.
            - 'username': (Optional[str]) Username for SMTP authentication.
            - 'password': (Optional[str]) Password for SMTP authentication.
            - 'use_tls': (bool) Whether to use STARTTLS.
            - 'sender_email': (str) The email address to set as the sender.
            - 'timeout': (Optional[int]) Connection timeout in seconds (default: 10).

    Returns:
        A tuple (success: bool, error_message: Optional[str]).
        `success` is True if the email was sent successfully, False otherwise.
        `error_message` contains a description of the error if sending failed.
    """
    if not all(k in smtp_config for k in ['host', 'port', 'sender_email']):
        return False, "SMTP configuration missing required keys (host, port, sender_email)."

    msg = EmailMessage()
    msg["From"] = smtp_config["sender_email"]
    msg["To"] = recipient_email
    msg["Subject"] = subject
    msg.set_content(body, subtype='html') # Assuming HTML body, change to 'plain' if needed

    hostname = smtp_config["host"]
    port = smtp_config["port"]
    username = smtp_config.get("username")
    password = smtp_config.get("password")
    use_tls = smtp_config.get("use_tls", True) # Default to True if not specified
    timeout = smtp_config.get("timeout", 10)  # Default timeout 10 seconds

    try:
        smtp_client = aiosmtplib.SMTP(hostname=hostname, port=port, timeout=timeout)
        await smtp_client.connect()

        if use_tls:
            await smtp_client.starttls()

        if username and password:
            await smtp_client.login(username, password)

        await smtp_client.send_message(msg)
        await smtp_client.quit()
        return True, None

    except aiosmtplib.SMTPConnectError as e:
        return False, f"SMTP Connection Error: Failed to connect to {hostname}:{port}. ({e})"
    except aiosmtplib.SMTPHeloError as e:
        return False, f"SMTP HELO/EHLO Error: {e.code} - {e.message}"
    except aiosmtplib.SMTPAuthenticationError as e:
        return False, f"SMTP Authentication Error: {e.code} - {e.message}"
    except aiosmtplib.SMTPResponseException as e: # Catch other SMTP protocol errors
        return False, f"SMTP Protocol Error: {e.code} - {e.message}"
    except aiosmtplib.SMTPSenderRefused as e:
        return False, f"SMTP Sender Refused: {e.code} - {e.message} (Sender: {e.sender})"
    except aiosmtplib.SMTPRecipientsRefused as e:
        # This error can contain multiple recipient refusal details
        errors = [f"{rcpt}: {err_code} {err_msg}" for rcpt, (err_code, err_msg) in e.recipients.items()]
        return False, f"SMTP Recipient(s) Refused: {'; '.join(errors)}"
    except asyncio.TimeoutError: # Catch timeout errors specifically if not caught by aiosmtplib's timeout
         return False, f"SMTP operation timed out after {timeout} seconds connecting to {hostname}:{port}."
    except Exception as e:
        # Catch any other unexpected errors (network issues, etc.)
        return False, f"An unexpected error occurred while sending email: {e}"

class EmailSendingService:
    def __init__(self, db: Session):
        self.db = db
        self.smtp_config = {
            "host": settings.SMTP_HOST,
            "port": settings.SMTP_PORT,
            "username": settings.SMTP_USER,
            "password": settings.SMTP_PASSWORD,
            "use_tls": settings.SMTP_USE_TLS,
            "sender_email": settings.SMTP_SENDER_EMAIL,
            "timeout": 10
        }

    # send_campaign_emails method removed
    # _personalize_template method removed

    async def _send_single_email(
        self,
        recipient_email: str,
        subject: str,
        body: str,
    ) -> Tuple[bool, Optional[str]]:
        """
        Sends a single email using configured SMTP settings.
        """
        msg = EmailMessage()
        msg["From"] = self.smtp_config["sender_email"]
        msg["To"] = recipient_email
        msg["Subject"] = subject
        msg.set_content(body, subtype='html')

        try:
            smtp_client = aiosmtplib.SMTP(
                hostname=self.smtp_config["host"],
                port=self.smtp_config["port"],
                timeout=self.smtp_config["timeout"]
            )
            
            await smtp_client.connect()
            
            if self.smtp_config["use_tls"]:
                await smtp_client.starttls()
            
            if self.smtp_config["username"] and self.smtp_config["password"]:
                await smtp_client.login(
                    self.smtp_config["username"],
                    self.smtp_config["password"]
                )
            
            await smtp_client.send_message(msg)
            await smtp_client.quit()
            return True, None

        except Exception as e:
            return False, f"Failed to send email: {str(e)}"

    async def send_follow_up(self, original_email_id: int) -> Tuple[bool, Optional[str]]:
        """
        Sends a follow-up email based on an original sent email.
        """
        original_email = self.db.query(SentEmail).filter(SentEmail.id == original_email_id).first()
        if not original_email:
            return False, "Original email not found"
            
        contact = self.db.query(Contact).filter(Contact.id == original_email.contact_id).first()
        template = self.db.query(EmailTemplate).filter(EmailTemplate.id == original_email.email_template_id).first()
        
        # Generate follow-up subject and body
        subject = f"Re: {original_email.subject}"
        tracking_pixel_id = str(uuid4())
        
        # Send the follow-up email
        success, error = await self._send_single_email(
            contact.email,
            subject,
            template.body_template + f'<img src="{settings.APP_BASE_URL}/track/{tracking_pixel_id}" width="1" height="1" />'
        )
        
        if success:
            # Record follow-up email
            follow_up = SentEmail(
                campaign_id=original_email.campaign_id,
                contact_id=contact.id,
                email_template_id=template.id,
                subject=subject,
                body=template.body_template,
                status='sent',
                sent_at=datetime.utcnow(),
                tracking_pixel_id=tracking_pixel_id,
                is_follow_up=True,
                follows_up_on_email_id=original_email_id
            )
            self.db.add(follow_up)
            self.db.commit()
        
        return success, error

    async def record_email_opened(self, tracking_pixel_id: str, ip_address: Optional[str] = None) -> bool: # Made async
        """
        Records when an email is opened via tracking pixel using db_operations.
        """
        try:
            success = await db_record_email_open_event(
                db=self.db,
                tracking_pixel_id=tracking_pixel_id,
                opened_ip=ip_address
            )
            if success:
                await self.db.commit() # Commit the changes made by db_record_email_open_event
                return True
            # If db_record_email_open_event returns False, it means the record wasn't found.
            # No commit/rollback needed in that specific case from db_op, just return False from service.
            return False
        except Exception as e:
            await self.db.rollback() # Rollback in case of other exceptions during the process
            print(f"Error in record_email_opened service: {str(e)}") # Replace with proper logging
            return False

# Example usage (for testing purposes, typically not run directly from a service file)
async def main_test():
    # This is a MOCK configuration. Replace with a real SMTP server for actual testing.
    # For instance, use a local SMTP debugging server like `python -m smtpd -c DebuggingServer -n localhost:1025`
    # And then configure this to send to localhost:1025 without auth.
    test_smtp_config = {
        "host": "localhost", # Replace with your SMTP server
        "port": 1025,        # Replace with your SMTP server port
        "username": None,    # Replace if auth is needed
        "password": None,    # Replace if auth is needed
        "use_tls": False,    # Often False for local debug servers
        "sender_email": "testsender@example.com",
        "timeout": 5
    }

    print("Attempting to send a test email...")
    success, error = await send_single_email_smtp(
        recipient_email="testrecipient@example.com",
        subject="Test Email from send_single_email_smtp",
        body="<h1>Hello!</h1><p>This is a test email sent via aiosmtplib.</p>",
        smtp_config=test_smtp_config
    )

    if success:
        print("Email sent successfully (according to the function).")
    else:
        print(f"Failed to send email. Error: {error}")

if __name__ == "__main__":
    # To run this test, you would typically need an SMTP server running.
    # e.g., start a local debugging SMTP server: `python -m smtpd -c DebuggingServer -n localhost:1025`
    # Then update test_smtp_config accordingly.
    # This example_usage is primarily for demonstration.
    print("Running email_sending.service.py example...")
    asyncio.run(main_test())
