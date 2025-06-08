# backend/src/tracking/pixel_handler.py
import base64
from fastapi import APIRouter, Request, Depends, HTTPException, status
from fastapi.responses import Response
from sqlalchemy.orm import Session

try:
    from src.database import get_db
    from src.followups.db_operations import db_record_email_open # Actual DB operation
except ImportError:
    # Placeholders for robustness
    print("TrackingAPI: Could not import DB components. Using placeholders.")
    class Session: pass # type: ignore
    def get_db(): return Session() # type: ignore
    async def db_record_email_open(db: Session, tracking_pixel_id: str, opened_ip: str) -> bool: # type: ignore
        print(f"Placeholder db_record_email_open called with pixel_id: {tracking_pixel_id}, IP: {opened_ip}")
        return True # Simulate found and processed for basic testing

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

@router.get("/open/{pixel_id}.png")
async def handle_open_tracking_pixel_request_api(
    pixel_id: str,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Handles requests for an email open tracking pixel.
    Records the open event and returns a minimal PNG image.
    """
    client_ip = request.client.host if request.client else "unknown"

    # print(f"TrackingAPI: Pixel request received for ID: {pixel_id} from IP: {client_ip}") # Optional: reduce noise

    try:
        success = await db_record_email_open(
            db=db,
            tracking_pixel_id=pixel_id,
            opened_ip=client_ip
        )
        # if success:
            # print(f"TrackingAPI: Email open successfully recorded for pixel ID: {pixel_id}") # Optional: reduce noise
        # else:
            # print(f"TrackingAPI: Pixel ID not found or failed to record: {pixel_id}") # Optional: reduce noise
            # Still return the image to avoid broken images in emails even if the ID is invalid.
    except Exception as e:
        # Log the error, but still return the image to avoid breaking client.
        print(f"TrackingAPI: Error processing pixel ID {pixel_id}: {e}")
        # Consider more detailed logging for production.

    # Always return the 1x1 transparent PNG image.
    # Set cache-control headers to prevent caching of the tracking pixel.
    return Response(
        content=MINIMAL_PNG_BYTES,
        media_type="image/png",
        headers={
            "Cache-Control": "no-cache, no-store, must-revalidate, private, max-age=0",
            "Pragma": "no-cache",
            "Expires": "0",
        }
    )

# Example of how this router might be included in a main FastAPI app:
# from fastapi import FastAPI
# from src.tracking import pixel_handler # Assuming this file is src/tracking/pixel_handler.py
# app = FastAPI()
# app.include_router(pixel_handler.router)
```
