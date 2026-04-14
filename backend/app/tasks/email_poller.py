"""Background email polling task.

Uses APScheduler to poll IMAP at configured intervals.
"""

import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.config import settings
from app.database import async_session_factory

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()


async def poll_job():
    """Scheduled job to poll emails."""
    from app.services.email_service import poll_emails
    from app.database import get_db

    async for db in get_db():
        try:
            count = await poll_emails(db)
            if count:
                logger.info(f"Processed {count} new emails")
        except Exception:
            logger.exception("Email poll job failed")


def start_email_poller():
    """Start the email poller if IMAP is configured."""
    if not settings.imap_host or not settings.imap_user:
        logger.info("IMAP not configured, email poller disabled")
        return

    interval = settings.imap_poll_interval_seconds
    scheduler.add_job(poll_job, "interval", seconds=interval, id="email_poller")
    scheduler.start()
    logger.info(f"Email poller started, interval={interval}s")


def stop_email_poller():
    """Stop the email poller."""
    if scheduler.running:
        scheduler.shutdown(wait=False)
