# filepath: /home/vedanschi/pebble-outreach/backend/src/core/config/email.py
from typing import List, Optional
from pydantic import EmailStr
from .settings import settings
import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

class EmailConfig:
    async def send_email(
        self,
        to_email: str,
        subject: str,
        body: str,
        html_content: Optional[str] = None
    ) -> bool:
        message = MIMEMultipart('alternative')
        message['Subject'] = subject
        message['From'] = settings.SMTP_SENDER_EMAIL
        message['To'] = to_email

        # Add body as plain text
        message.attach(MIMEText(body, 'plain'))

        # Add HTML version if provided
        if html_content:
            message.attach(MIMEText(html_content, 'html'))

        try:
            await aiosmtplib.send(
                message,
                hostname=settings.SMTP_HOST,
                port=settings.SMTP_PORT,
                username=settings.SMTP_USER,
                password=settings.SMTP_PASSWORD,
                use_tls=settings.SMTP_USE_TLS
            )
            return True
        except Exception as e:
            print(f"Failed to send email: {str(e)}")
            return False

email_client = EmailConfig()