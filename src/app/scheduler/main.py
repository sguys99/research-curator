"""Main scheduler module using APScheduler."""

import logging
from datetime import datetime

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from pytz import timezone

from app.core.config import settings
from app.scheduler.tasks import collect_data_task, process_articles_task, send_digest_task

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Timezone for scheduling (Korea Standard Time)
KST = timezone("Asia/Seoul")

# Create scheduler instance
scheduler = BackgroundScheduler(timezone=KST)


def setup_jobs() -> None:
    """Setup all scheduled jobs."""
    logger.info("Setting up scheduled jobs...")

    # Job 1: Data Collection - Daily at 01:00 KST
    scheduler.add_job(
        func=collect_data_task,
        trigger=CronTrigger(
            hour=settings.COLLECT_SCHEDULE_HOUR,
            minute=settings.COLLECT_SCHEDULE_MINUTE,
            timezone=KST,
        ),
        id="collect_data",
        name="Daily Data Collection",
        replace_existing=True,
        misfire_grace_time=3600,  # 1 hour grace period
    )
    logger.info(
        f"✅ Scheduled: Data Collection at {settings.COLLECT_SCHEDULE_HOUR:02d}:"
        f"{settings.COLLECT_SCHEDULE_MINUTE:02d} KST",
    )

    # Job 2: Process Articles - Daily at 01:30 KST
    scheduler.add_job(
        func=process_articles_task,
        trigger=CronTrigger(
            hour=1,
            minute=30,
            timezone=KST,
        ),
        id="process_articles",
        name="Process Collected Articles",
        replace_existing=True,
        misfire_grace_time=3600,
    )
    logger.info("✅ Scheduled: Article Processing at 01:30 KST")

    # Job 3: Send Email Digests - Daily at 08:00 KST (configurable per user)
    scheduler.add_job(
        func=send_digest_task,
        trigger=CronTrigger(
            hour=settings.SEND_EMAIL_SCHEDULE_HOUR,
            minute=settings.SEND_EMAIL_SCHEDULE_MINUTE,
            timezone=KST,
        ),
        id="send_digests",
        name="Send Email Digests",
        replace_existing=True,
        misfire_grace_time=3600,
    )
    logger.info(
        f"✅ Scheduled: Email Digest Sending at {settings.SEND_EMAIL_SCHEDULE_HOUR:02d}:"
        f"{settings.SEND_EMAIL_SCHEDULE_MINUTE:02d} KST",
    )


def start_scheduler() -> None:
    """Start the scheduler with all jobs."""
    if scheduler.running:
        logger.warning("Scheduler is already running")
        return

    setup_jobs()
    scheduler.start()
    logger.info("🚀 Scheduler started successfully")

    # Log scheduled jobs
    jobs = scheduler.get_jobs()
    logger.info(f"Active jobs: {len(jobs)}")
    for job in jobs:
        logger.info(f"  - {job.name} (ID: {job.id}) - Next run: {job.next_run_time}")


def stop_scheduler() -> None:
    """Stop the scheduler gracefully."""
    if not scheduler.running:
        logger.warning("Scheduler is not running")
        return

    scheduler.shutdown(wait=True)
    logger.info("🛑 Scheduler stopped")


def get_scheduler_status() -> dict:
    """
    Get current scheduler status.

    Returns:
        Dictionary with scheduler status information
    """
    jobs = scheduler.get_jobs()
    return {
        "running": scheduler.running,
        "timezone": str(KST),
        "current_time": datetime.now(KST).isoformat(),
        "jobs": [
            {
                "id": job.id,
                "name": job.name,
                "next_run_time": job.next_run_time.isoformat() if job.next_run_time else None,
                "trigger": str(job.trigger),
            }
            for job in jobs
        ],
    }


def trigger_job_manually(job_id: str) -> bool:
    """
    Trigger a specific job manually.

    Args:
        job_id: ID of the job to trigger

    Returns:
        True if job was triggered successfully, False otherwise
    """
    try:
        job = scheduler.get_job(job_id)
        if not job:
            logger.error(f"Job with ID '{job_id}' not found")
            return False

        # Run the job immediately
        job.func()
        logger.info(f"✅ Manually triggered job: {job.name}")
        return True
    except Exception as e:
        logger.error(f"Failed to trigger job '{job_id}': {e}")
        return False


if __name__ == "__main__":
    """Run scheduler as standalone process."""
    try:
        logger.info("=" * 60)
        logger.info("Research Curator - Scheduler")
        logger.info("=" * 60)

        start_scheduler()

        # Keep the process running
        logger.info("Press Ctrl+C to stop the scheduler")
        import time

        while True:
            time.sleep(1)

    except (KeyboardInterrupt, SystemExit):
        logger.info("\nReceived shutdown signal")
        stop_scheduler()
        logger.info("Scheduler shutdown complete")
