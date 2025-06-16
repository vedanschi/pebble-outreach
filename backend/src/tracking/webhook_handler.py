# backend/src/tracking/webhook_handler.py
from typing import Dict, Any, List
from datetime import datetime
import json
from fastapi import APIRouter, Request, Depends, HTTPException, Header
from sqlalchemy.orm import Session

from src.core.config import settings
from src.core.config.database import get_db
from src.models.user_models import SentEmail
from src.core.config.security import verify_webhook_signature

router = APIRouter(
    prefix="/webhooks",
    tags=["webhooks"]
)

async def db_update_email_status_from_webhook(
    db: Session,
    identifier: str,
    event_type: str,
    event_timestamp: datetime,
    details: Dict[str, Any]
) -> bool:
    """Update email status based on webhook event"""
    sent_email = db.query(SentEmail).filter(
        SentEmail.esp_message_id == identifier
    ).first()

    if not sent_email:
        return False

    # Update status based on event type
    status_mapping = {
        "delivered": "delivered",
        "bounce": "bounced",
        "complaint": "spam_complaint",
        "reject": "failed",
        "open": "opened",
        "click": "clicked"
    }

    sent_email.status = status_mapping.get(event_type, sent_email.status)
    
    # Update timestamps based on event
    if event_type == "delivered":
        sent_email.delivered_at = event_timestamp
    elif event_type == "open":
        sent_email.opened_at = sent_email.opened_at or event_timestamp
        sent_email.last_opened_at = event_timestamp
        sent_email.open_count += 1
    elif event_type == "click":
        sent_email.clicked_at = sent_email.clicked_at or event_timestamp
        sent_email.last_clicked_at = event_timestamp
        sent_email.click_count += 1

    # Store event details in tracking history
    tracking_data = sent_email.tracking_history or []
    tracking_data.append({
        "event": event_type,
        "timestamp": event_timestamp.isoformat(),
        "details": details
    })
    sent_email.tracking_history = tracking_data

    try:
        db.add(sent_email)
        db.commit()
        return True
    except Exception as e:
        db.rollback()
        raise e

@router.post("/email/events")
async def handle_esp_webhook(
    request: Request,
    signature: str = Header(None),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Handle incoming ESP webhook events"""
    # Verify webhook signature
    payload = await request.json()
    if not verify_webhook_signature(payload, signature, settings.WEBHOOK_SECRET):
        raise HTTPException(status_code=403, detail="Invalid signature")

    if settings.DEBUG:
        print(f"Webhook payload: {json.dumps(payload)[:200]}...")

    events = []
    if isinstance(payload, list):
        events = payload
    elif isinstance(payload, dict) and "events" in payload:
        events = payload["events"]
    elif isinstance(payload, dict) and "event" in payload:
        events = [payload]
    else:
        raise HTTPException(status_code=400, detail="Invalid payload structure")

    processed_count = 0
    errors_count = 0

    for event_data in events:
        try:
            event_type = event_data.get("event") or event_data.get("type")
            esp_message_id = event_data.get("message_id") or event_data.get("MessageID")

            if not esp_message_id or not event_type:
                errors_count += 1
                continue

            timestamp_str = event_data.get("timestamp") or event_data.get("time")
            try:
                event_timestamp = datetime.fromtimestamp(
                    float(timestamp_str), 
                    datetime.timezone.utc
                )
            except (ValueError, TypeError):
                event_timestamp = datetime.utcnow()

            updated = await db_update_email_status_from_webhook(
                db=db,
                identifier=esp_message_id,
                event_type=event_type.lower(),
                event_timestamp=event_timestamp,
                details=event_data
            )

            if updated:
                processed_count += 1
            else:
                errors_count += 1

        except Exception as e:
            if settings.DEBUG:
                print(f"Error processing event: {str(e)}")
            errors_count += 1

    return {
        "status": "success",
        "processed": processed_count,
        "errors": errors_count
    }