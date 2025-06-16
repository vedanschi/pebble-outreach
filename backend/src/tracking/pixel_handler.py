# backend/src/tracking/pixel_handler.py
import base64
from fastapi import APIRouter, Request, Depends, HTTPException, status
from fastapi.responses import Response
from sqlalchemy.orm import Session
from datetime import datetime

from src.core.config import settings
from src.core.config.database import get_db
from src.models.user_models import SentEmail
from .utils import get_client_info

# --- Minimal PNG Bytes ---
# This is a 1x1 transparent PNG.
# iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII=
MINIMAL_PNG_BYTES = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII="
)

router = APIRouter(
    prefix="/track", # Common prefix for tracking endpoints
    tags=["tracking"]
)

async def db_record_email_open(
    db: Session,
    tracking_pixel_id: str,
    client_info: dict
) -> bool:
    """Record email open event in database"""
    sent_email = db.query(SentEmail).filter(
        SentEmail.tracking_pixel_id == tracking_pixel_id
    ).first()

    if not sent_email:
        return False

    # Update open tracking data
    sent_email.opened_at = sent_email.opened_at or datetime.utcnow()
    sent_email.last_opened_at = datetime.utcnow()
    sent_email.open_count += 1
    
    if not sent_email.first_opened_ip:
        sent_email.first_opened_ip = client_info["ip"]
        sent_email.first_opened_user_agent = client_info["user_agent"]
    
    # Add to tracking history
    tracking_data = sent_email.tracking_history or []
    tracking_data.append({
        "event": "open",
        "timestamp": datetime.utcnow().isoformat(),
        **client_info
    })
    sent_email.tracking_history = tracking_data

    try:
        db.add(sent_email)
        db.commit()
        return True
    except Exception as e:
        db.rollback()
        raise e

@router.get("/open/{pixel_id}.png")
async def handle_open_tracking_pixel_request_api(
    pixel_id: str,
    request: Request,
    db: Session = Depends(get_db)
):
    """Handle email open tracking pixel request"""
    client_info = get_client_info(request)

    try:
        await db_record_email_open(db, pixel_id, client_info)
    except Exception as e:
        if settings.DEBUG:
            print(f"TrackingAPI Error: {str(e)}")

    return Response(
        content=MINIMAL_PNG_BYTES,
        media_type="image/png",
        headers={
            "Cache-Control": "no-cache, no-store, must-revalidate, private, max-age=0",
            "Pragma": "no-cache",
            "Expires": "0",
        }
    )
