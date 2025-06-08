# backend/src/email_sending/service.py
import asyncio
import aiosmtplib
from email.message import EmailMessage
from typing import Tuple, Optional, Dict, Any

# Example of how SMTP configuration might be structured.
# In a real application, this would be loaded from application settings,
# environment variables, or a secure configuration management system.
#
# SMTP_CONFIG_EXAMPLE = {
#     "host": "smtp.example.com",
#     "port": 587,  # Standard port for TLS
#     "username": "user@example.com",
#     "password": "your_smtp_password",
#     "use_tls": True,
#     "sender_email": "noreply@example.com", # Default sender if not specified elsewhere
#     "timeout": 10, # Connection timeout in seconds
# }

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
```
