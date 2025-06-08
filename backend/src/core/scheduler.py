# backend/src/core/scheduler.py
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from typing import Optional

# Assuming SessionLocal is defined in database.py for creating DB sessions for background tasks
try:
    from src.database import SessionLocal # Adjust import path as per your project
    from src.followups.processor_service import process_due_follow_ups
    from src.email_sending.draft_service import send_pending_emails
    from src.core.config import settings # For SMTP configuration
except ImportError:
    print("Scheduler: Could not import SessionLocal, services, or settings. Using placeholders.")
    # Placeholders if actual imports fail
    class SessionLocal: # type: ignore
        def __init__(self): pass
        def __enter__(self): return self
        def __exit__(self, exc_type, exc_val, exc_tb): pass
        def close(self): pass

    async def process_due_follow_ups(db_session) -> dict: # type: ignore
        print("Placeholder process_due_follow_ups called.")
        return {"processed_rules": 0, "created_follow_ups": 0}

    async def send_pending_emails(db_session, smtp_config_dict) -> tuple[int, int]: # type: ignore
        print("Placeholder send_pending_emails called.")
        return 0,0

    class settings: # type: ignore
        SMTP_HOST: str = "localhost"; SMTP_PORT: int = 1025; SMTP_USER: Optional[str] = None
        SMTP_PASSWORD: Optional[str] = None; SMTP_SENDER_EMAIL: str = "scheduler@example.com"
        SMTP_USE_TLS: bool = False; SMTP_TIMEOUT: int = 10


# Global scheduler instance
scheduler: Optional[AsyncIOScheduler] = None

async def scheduled_follow_up_job():
    """
    The actual job that APScheduler will run.
    It creates a new database session, calls the follow-up processor,
    and handles session closing and exceptions.
    """
    print("Scheduler: Running scheduled_follow_up_job...")
    db = None
    try:
        db = SessionLocal() # Create a new session for this job
        results = await process_due_follow_ups(db)
        print(f"Scheduler: process_due_follow_ups completed. Results: {results}")
    except Exception as e:
        print(f"Scheduler: Error during scheduled_follow_up_job: {e}")
        # Add more detailed error logging here if needed (e.g., traceback)
    finally:
        if db:
            db.close() # Ensure the session is closed
            print("Scheduler: Database session closed for scheduled_follow_up_job.")

async def scheduled_draft_email_sender_job():
    """
    The actual job that APScheduler will run for sending draft/pending emails.
    It creates a new database session, constructs SMTP config,
    calls the draft email sender service, and handles session closing and exceptions.
    """
    print("Scheduler: Running scheduled_draft_email_sender_job...")
    db = None
    try:
        db = SessionLocal() # Create a new session for this job

        # Construct SMTP config from settings
        # Ensure your settings object provides these, or adjust loading mechanism
        smtp_config = {
            "host": settings.SMTP_HOST,
            "port": settings.SMTP_PORT,
            "username": settings.SMTP_USER,
            "password": settings.SMTP_PASSWORD,
            "use_tls": settings.SMTP_USE_TLS,
            "sender_email": settings.SMTP_SENDER_EMAIL, # This might be a generic sender for drafts
            "timeout": getattr(settings, 'SMTP_TIMEOUT', 10) # Use a default if not set
        }
        if not smtp_config["host"] or not smtp_config["sender_email"]:
            print("Scheduler: SMTP settings (host, sender_email) not configured for draft sender job. Skipping.")
            return

        results = await send_pending_emails(db, smtp_config)
        print(f"Scheduler: send_pending_emails completed. Successful: {results[0]}, Failed: {results[1]}")
    except Exception as e:
        print(f"Scheduler: Error during scheduled_draft_email_sender_job: {e}")
        # Add more detailed error logging here if needed
    finally:
        if db:
            db.close() # Ensure the session is closed
            print("Scheduler: Database session closed for scheduled_draft_email_sender_job.")


def start_scheduler():
    """
    Initializes and starts the APScheduler.
    Adds jobs to the scheduler.
    """
    global scheduler
    if scheduler is None: # Ensure scheduler is initialized only once
        scheduler = AsyncIOScheduler(timezone="UTC") # Or your desired timezone

        # Add the follow-up processing job
        # Runs every 10 minutes. Adjust interval as needed.
        scheduler.add_job(
            scheduled_follow_up_job,
            trigger=IntervalTrigger(minutes=10), # Example: run every 10 minutes
            id="process_follow_ups_job",
            name="Process Due Follow-up Emails",
            replace_existing=True
        )

        # Add the draft email sender job
        # Runs every 1 minute. Adjust interval as needed.
        scheduler.add_job(
            scheduled_draft_email_sender_job,
            trigger=IntervalTrigger(minutes=1), # Example: run every 1 minute
            id="draft_email_sender_job",
            name="Send Draft/Pending Emails",
            replace_existing=True
        )

        scheduler.start()
        print("Scheduler: APScheduler started.")
    else:
        print("Scheduler: APScheduler already initialized.")


def shutdown_scheduler():
    """
    Shuts down the APScheduler.
    """
    global scheduler
    if scheduler and scheduler.running:
        scheduler.shutdown()
        print("Scheduler: APScheduler shut down.")
    elif scheduler:
        print("Scheduler: APScheduler was initialized but not running.")
    else:
        print("Scheduler: APScheduler not initialized.")

# Example of how to add another job:
# def another_scheduled_task():
#     print("Another task is running")

# if scheduler: # Ensure scheduler is initialized before adding more jobs outside start_scheduler
#    scheduler.add_job(another_scheduled_task, IntervalTrigger(hours=1), id="another_task")
```
