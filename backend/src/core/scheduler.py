# backend/src/core/scheduler.py
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.triggers.interval import IntervalTrigger
from typing import Optional
from datetime import datetime, timedelta

from sqlalchemy.orm import Session
from src.core.config import settings, get_db
from src.email_sending.draft_service import send_pending_emails
from src.followups.processor_service import process_due_follow_ups
from src.campaigns.personalization_service import PersonalizationService

# Global scheduler instance
scheduler: Optional[AsyncIOScheduler] = None

async def scheduled_follow_up_job():
    """
    Processes follow-up emails based on campaign rules and email tracking data.
    - Checks for emails that haven't been opened
    - Processes follow-up rules for each campaign
    - Creates and schedules follow-up emails
    """
    print(f"Scheduler: Running follow-up job at {datetime.utcnow()} UTC")
    db = None
    try:
        db = next(get_db())
        
        # Process follow-ups and get results
        results = await process_due_follow_ups(db)
        
        print(f"Scheduler: Follow-up processing complete. "
              f"Processed rules: {results['processed_rules']}, "
              f"Created follow-ups: {results['created_follow_ups']}")
              
    except Exception as e:
        print(f"Scheduler: Error in follow-up job: {str(e)}")
        # You might want to add more detailed error logging here
    finally:
        if db:
            db.close()
            print("Scheduler: Database session closed for follow-up job")

async def scheduled_draft_email_sender_job():
    """
    Processes and sends emails marked as draft or pending.
    - Handles email personalization
    - Adds tracking pixels
    - Manages email status updates
    - Processes emails in batches
    """
    print(f"Scheduler: Running draft sender job at {datetime.utcnow()} UTC")
    db = None
    try:
        db = next(get_db())
        
        smtp_config = {
            "host": settings.SMTP_HOST,
            "port": settings.SMTP_PORT,
            "username": settings.SMTP_USER,
            "password": settings.SMTP_PASSWORD,
            "use_tls": settings.SMTP_USE_TLS,
            "sender_email": settings.SMTP_SENDER_EMAIL,
            "timeout": settings.SMTP_TIMEOUT
        }

        # Validate SMTP configuration
        if not all([smtp_config["host"], smtp_config["sender_email"]]):
            print("Scheduler: Incomplete SMTP configuration. Skipping draft sender job.")
            return

        # Process pending emails
        successful, failed = await send_pending_emails(db)
        
        print(f"Scheduler: Draft sending complete. "
              f"Successful: {successful}, Failed: {failed}")

    except Exception as e:
        print(f"Scheduler: Error in draft sender job: {str(e)}")
    finally:
        if db:
            db.close()
            print("Scheduler: Database session closed for draft sender job")

async def scheduled_email_tracking_cleanup():
    """
    Cleans up old tracking data and updates campaign statistics.
    """
    print(f"Scheduler: Running tracking cleanup at {datetime.utcnow()} UTC")
    db = None
    try:
        db = next(get_db())
        
        # Archive old tracking data (older than 90 days)
        cutoff_date = datetime.utcnow() - timedelta(days=90)
        
        # Your cleanup logic here
        # Example: Move old tracking data to archive table
        # Update campaign statistics
        
        print("Scheduler: Tracking cleanup complete")
        
    except Exception as e:
        print(f"Scheduler: Error in tracking cleanup: {str(e)}")
    finally:
        if db:
            db.close()

def start_scheduler():
    """
    Initializes and starts the APScheduler with all necessary jobs.
    - Follow-up processing
    - Draft email sending
    - Email tracking cleanup
    """
    global scheduler
    if scheduler is None:
        jobstores = {
            'default': SQLAlchemyJobStore(url=settings.DATABASE_URL)
        }
        scheduler = AsyncIOScheduler(jobstores=jobstores, timezone="UTC")

        # Follow-up processing job - every 10 minutes
        scheduler.add_job(
            scheduled_follow_up_job,
            trigger=IntervalTrigger(minutes=10),
            id="process_follow_ups_job",
            name="Process Due Follow-up Emails",
            replace_existing=True,
            max_instances=1  # Prevent overlapping runs
        )

        # Draft email sender job - every minute
        scheduler.add_job(
            scheduled_draft_email_sender_job,
            trigger=IntervalTrigger(minutes=1),
            id="draft_email_sender_job",
            name="Send Draft/Pending Emails",
            replace_existing=True,
            max_instances=1
        )

        # Email tracking cleanup job - daily at midnight UTC
        scheduler.add_job(
            scheduled_email_tracking_cleanup,
            trigger='cron',
            hour=0,
            minute=0,
            id="tracking_cleanup_job",
            name="Clean up old tracking data",
            replace_existing=True
        )

        scheduler.start()
        print(f"Scheduler: Started successfully at {datetime.utcnow()} UTC")
    else:
        print("Scheduler: Already initialized")

def shutdown_scheduler():
    """
    Safely shuts down the scheduler and all running jobs.
    """
    global scheduler
    if scheduler and scheduler.running:
        try:
            scheduler.shutdown(wait=True)  # Wait for running jobs to complete
            print("Scheduler: Shut down successfully")
        except Exception as e:
            print(f"Scheduler: Error during shutdown: {str(e)}")
    else:
        print("Scheduler: Not running")

# Error handling decorator for scheduled jobs
def handle_scheduler_errors(func):
    """
    Decorator to handle errors in scheduled jobs and prevent job interruption.
    """
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            print(f"Scheduler Error in {func.__name__}: {str(e)}")
            # You might want to add notification logic here
    return wrapper
