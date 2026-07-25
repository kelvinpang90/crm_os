"""Background AutoCount sync task.

Uses APScheduler to run the same sync_all() the manual "Sync Now" button
calls, on a fixed interval — see app/tasks/email_poller.py for the sibling
pattern this follows.
"""

import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.config import settings
from app.database import get_db

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()


async def poll_job():
    """Scheduled job to sync AutoCount customers/invoices/quotations."""
    from app.services import autocount_service

    async for db in get_db():
        try:
            result = await autocount_service.sync_all(db)
            logger.info(f"AutoCount sync: {result}")
        except Exception:
            logger.exception("AutoCount sync job failed")


def start_autocount_poller():
    """Start the AutoCount poller if credentials are configured."""
    if not settings.autocount_account_book_id or not settings.autocount_api_key:
        logger.info("AutoCount credentials not configured, poller disabled")
        return

    interval = settings.autocount_poll_interval_seconds
    scheduler.add_job(poll_job, "interval", seconds=interval, id="autocount_poller")
    scheduler.start()
    logger.info(f"AutoCount poller started, interval={interval}s")


def stop_autocount_poller():
    """Stop the AutoCount poller."""
    if scheduler.running:
        scheduler.shutdown(wait=False)
