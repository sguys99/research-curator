"""Scheduler management API endpoints."""

import logging
from datetime import datetime

from fastapi import APIRouter, HTTPException
from pytz import timezone

from app.api.schemas.scheduler import (
    JobInfo,
    JobListResponse,
    SchedulerControlRequest,
    SchedulerControlResponse,
    SchedulerStatusResponse,
    TriggerJobRequest,
    TriggerJobResponse,
)
from app.scheduler.main import get_scheduler_status, scheduler, start_scheduler, stop_scheduler

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/scheduler", tags=["Scheduler"])

KST = timezone("Asia/Seoul")


@router.get("/status", response_model=SchedulerStatusResponse)
async def get_status() -> SchedulerStatusResponse:
    """
    Get current scheduler status.

    Returns information about scheduler running state, timezone,
    current time, and all registered jobs.
    """
    try:
        status = get_scheduler_status()

        jobs = [
            JobInfo(
                id=job["id"],
                name=job["name"],
                next_run_time=job["next_run_time"],
                trigger=job["trigger"],
            )
            for job in status["jobs"]
        ]

        return SchedulerStatusResponse(
            running=status["running"],
            timezone=status["timezone"],
            current_time=status["current_time"],
            jobs=jobs,
        )

    except Exception as e:
        logger.error(f"Failed to get scheduler status: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get scheduler status: {str(e)}",
        ) from e


@router.get("/jobs", response_model=JobListResponse)
async def list_jobs() -> JobListResponse:
    """
    List all registered scheduler jobs.

    Returns a list of all jobs with their IDs, names, next run times,
    and trigger configurations.
    """
    try:
        jobs = scheduler.get_jobs()

        job_list = [
            JobInfo(
                id=job.id,
                name=job.name,
                next_run_time=job.next_run_time.isoformat() if job.next_run_time else None,
                trigger=str(job.trigger),
            )
            for job in jobs
        ]

        return JobListResponse(
            total=len(job_list),
            jobs=job_list,
        )

    except Exception as e:
        logger.error(f"Failed to list jobs: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list jobs: {str(e)}",
        ) from e


@router.post("/jobs/trigger", response_model=TriggerJobResponse)
async def trigger_job(request: TriggerJobRequest) -> TriggerJobResponse:
    """
    Manually trigger a scheduled job.

    This endpoint allows you to run a job immediately, outside of its
    normal schedule. Useful for testing or manual data collection.

    Available job IDs:
    - `collect_data`: Collect articles from arXiv and news sources
    - `process_articles`: Process collected articles with LLM
    - `send_digests`: Send email digests to users
    """
    try:
        job = scheduler.get_job(request.job_id)

        if not job:
            raise HTTPException(
                status_code=404,
                detail=f"Job with ID '{request.job_id}' not found",
            )

        # Execute the job function directly
        logger.info(f"Manually triggering job: {job.name} (ID: {request.job_id})")
        job.func()

        triggered_at = datetime.now(KST).isoformat()

        return TriggerJobResponse(
            success=True,
            message=f"Job '{job.name}' triggered successfully",
            job_id=request.job_id,
            triggered_at=triggered_at,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to trigger job '{request.job_id}': {e}")
        return TriggerJobResponse(
            success=False,
            message=f"Failed to trigger job: {str(e)}",
            job_id=request.job_id,
            triggered_at=datetime.now(KST).isoformat(),
        )


@router.post("/control", response_model=SchedulerControlResponse)
async def control_scheduler(request: SchedulerControlRequest) -> SchedulerControlResponse:
    """
    Control scheduler (start/stop).

    Actions:
    - `start`: Start the scheduler with all registered jobs
    - `stop`: Stop the scheduler gracefully

    Note: Typically the scheduler is started automatically when the
    application starts. This endpoint is mainly for administrative purposes.
    """
    try:
        if request.action == "start":
            if scheduler.running:
                return SchedulerControlResponse(
                    success=False,
                    message="Scheduler is already running",
                    running=True,
                )

            start_scheduler()
            return SchedulerControlResponse(
                success=True,
                message="Scheduler started successfully",
                running=True,
            )

        elif request.action == "stop":
            if not scheduler.running:
                return SchedulerControlResponse(
                    success=False,
                    message="Scheduler is not running",
                    running=False,
                )

            stop_scheduler()
            return SchedulerControlResponse(
                success=True,
                message="Scheduler stopped successfully",
                running=False,
            )

        else:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid action '{request.action}'. Use 'start' or 'stop'",
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to control scheduler: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to control scheduler: {str(e)}",
        ) from e
