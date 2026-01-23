"""APScheduler 기반 메인 스케줄러 모듈."""

import logging
from datetime import datetime

from apscheduler.events import EVENT_JOB_ERROR, EVENT_JOB_EXECUTED, EVENT_JOB_SUBMITTED
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from pytz import timezone

from app.scheduler.tasks import (
    unified_collect_and_send_task,
)

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# 스케줄링 타임존(한국 표준시)
KST = timezone("Asia/Seoul")

# 스케줄러 인스턴스 생성
scheduler = BackgroundScheduler(timezone=KST)


# 잡 모니터링 이벤트 리스너
def job_submitted_listener(event):
    """잡 실행 시작 시 로그를 남긴다."""
    job = scheduler.get_job(event.job_id)
    if job:
        logger.info(f"⏰ Job started: {job.name} (ID: {job.id})")


def job_executed_listener(event):
    """잡이 정상 완료되면 로그를 남긴다."""
    job = scheduler.get_job(event.job_id)
    if job:
        logger.info(f"✅ Job completed: {job.name} (ID: {job.id})")


def job_error_listener(event):
    """잡에서 오류가 발생하면 로그를 남긴다."""
    job = scheduler.get_job(event.job_id)
    job_name = job.name if job else event.job_id
    logger.error(f"❌ Job failed: {job_name} - Error: {event.exception}")


# 이벤트 리스너 등록
scheduler.add_listener(job_submitted_listener, EVENT_JOB_SUBMITTED)
scheduler.add_listener(job_executed_listener, EVENT_JOB_EXECUTED)
scheduler.add_listener(job_error_listener, EVENT_JOB_ERROR)


def setup_jobs() -> None:
    """모든 스케줄 잡을 설정한다."""
    logger.info("Setting up scheduled jobs...")

    # 신규 통합 잡: 수집/처리/발송(매일 06:00 KST)
    scheduler.add_job(
        func=unified_collect_and_send_task,
        trigger=CronTrigger(
            hour=6,
            minute=0,
            timezone=KST,
        ),
        id="unified_collect_send",
        name="Unified Collect & Send Digests",
        replace_existing=True,
        misfire_grace_time=3600,  # 1시간 유예
    )
    logger.info("✅ Scheduled: Unified Collect & Send at 06:00 KST")

    # 레거시 잡(호환성 유지용, 기본 비활성)
    # 아래 주석을 해제하면 구 3-작업 시스템을 사용

    # # 잡 1: 데이터 수집 - 매일 01:00 KST
    # scheduler.add_job(
    #     func=collect_data_task,
    #     trigger=CronTrigger(
    #         hour=settings.COLLECT_SCHEDULE_HOUR,
    #         minute=settings.COLLECT_SCHEDULE_MINUTE,
    #         timezone=KST,
    #     ),
    #     id="collect_data",
    #     name="Daily Data Collection",
    #     replace_existing=True,
    #     misfire_grace_time=3600,
    # )
    # logger.info(
    #     f"✅ Scheduled: Data Collection at {settings.COLLECT_SCHEDULE_HOUR:02d}:"
    #     f"{settings.COLLECT_SCHEDULE_MINUTE:02d} KST",
    # )

    # # 잡 2: 아티클 처리 - 매일 01:30 KST
    # scheduler.add_job(
    #     func=process_articles_task,
    #     trigger=CronTrigger(
    #         hour=1,
    #         minute=30,
    #         timezone=KST,
    #     ),
    #     id="process_articles",
    #     name="Process Collected Articles",
    #     replace_existing=True,
    #     misfire_grace_time=3600,
    # )
    # logger.info("✅ Scheduled: Article Processing at 01:30 KST")

    # # 잡 3: 이메일 다이제스트 발송 - 매일 08:00 KST
    # scheduler.add_job(
    #     func=send_digest_task,
    #     trigger=CronTrigger(
    #         hour=settings.SEND_EMAIL_SCHEDULE_HOUR,
    #         minute=settings.SEND_EMAIL_SCHEDULE_MINUTE,
    #         timezone=KST,
    #     ),
    #     id="send_digests",
    #     name="Send Email Digests",
    #     replace_existing=True,
    #     misfire_grace_time=3600,
    # )
    # logger.info(
    #     f"✅ Scheduled: Email Digest Sending at {settings.SEND_EMAIL_SCHEDULE_HOUR:02d}:"
    #     f"{settings.SEND_EMAIL_SCHEDULE_MINUTE:02d} KST",
    # )


def start_scheduler() -> None:
    """모든 잡을 포함해 스케줄러를 시작한다."""
    if scheduler.running:
        logger.warning("Scheduler is already running")
        return

    setup_jobs()
    scheduler.start()
    logger.info("🚀 Scheduler started successfully")

    # 등록된 잡 로그 출력
    jobs = scheduler.get_jobs()
    logger.info(f"Active jobs: {len(jobs)}")
    for job in jobs:
        logger.info(f"  - {job.name} (ID: {job.id}) - Next run: {job.next_run_time}")


def stop_scheduler() -> None:
    """스케줄러를 정상 종료한다."""
    if not scheduler.running:
        logger.warning("Scheduler is not running")
        return

    scheduler.shutdown(wait=True)
    logger.info("🛑 Scheduler stopped")


def get_scheduler_status() -> dict:
    """
    현재 스케줄러 상태를 반환한다.

    Returns:
        스케줄러 상태 정보 딕셔너리
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
    특정 잡을 수동으로 실행한다.

    Args:
        job_id: 실행할 잡 ID

    Returns:
        실행 성공 여부
    """
    try:
        job = scheduler.get_job(job_id)
        if not job:
            logger.error(f"Job with ID '{job_id}' not found")
            return False

        # 즉시 실행
        job.func()
        logger.info(f"✅ Manually triggered job: {job.name}")
        return True
    except Exception as e:
        logger.error(f"Failed to trigger job '{job_id}': {e}")
        return False


if __name__ == "__main__":
    """스케줄러를 단독 프로세스로 실행한다."""
    try:
        logger.info("=" * 60)
        logger.info("Research Curator - Scheduler")
        logger.info("=" * 60)

        start_scheduler()

        # 프로세스 유지
        logger.info("Press Ctrl+C to stop the scheduler")
        import time

        while True:
            time.sleep(1)

    except (KeyboardInterrupt, SystemExit):
        logger.info("\nReceived shutdown signal")
        stop_scheduler()
        logger.info("Scheduler shutdown complete")
