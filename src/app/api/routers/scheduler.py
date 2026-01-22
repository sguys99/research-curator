"""스케줄러 관리를 위한 API 엔드포인트."""

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
    현재 스케줄러 상태를 조회한다.

    스케줄러 실행 상태, 타임존, 현재 시각, 등록된 작업 정보를 반환한다.
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
    등록된 모든 스케줄러 작업을 조회한다.

    작업 ID, 이름, 다음 실행 시각, 트리거 정보를 반환한다.
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
async def trigger_job(
    request: TriggerJobRequest,
) -> TriggerJobResponse:
    """
    스케줄된 작업을 수동으로 실행한다.

    정상 스케줄과 별개로 즉시 실행할 수 있다. 테스트나 수동 수집에 유용하다.

    사용 가능한 작업 ID:
    - `collect_data`: arXiv 및 뉴스 소스에서 아티클 수집
    - `process_articles`: 수집된 아티클을 LLM으로 처리
    - `send_digests`: 사용자에게 이메일 다이제스트 발송
    """
    try:
        job = scheduler.get_job(request.job_id)

        if not job:
            raise HTTPException(
                status_code=404,
                detail=f"Job with ID '{request.job_id}' not found",
            )

        # 작업 함수를 동기적으로 실행
        logger.info(f"Manually triggering job: {job.name} (ID: {request.job_id})")

        triggered_at = datetime.now(KST).isoformat()

        try:
            # 동기 실행 후 완료 대기
            job.func()

            return TriggerJobResponse(
                success=True,
                message=f"Job '{job.name}' completed successfully",
                job_id=request.job_id,
                triggered_at=triggered_at,
            )
        except Exception as job_error:
            logger.error(f"Job execution failed: {job_error}")
            return TriggerJobResponse(
                success=False,
                message=f"Job execution failed: {str(job_error)}",
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
    스케줄러를 제어한다(start/stop).

    Actions:
    - `start`: 등록된 모든 작업으로 스케줄러 시작
    - `stop`: 스케줄러를 정상 종료

    참고: 일반적으로 앱 시작 시 자동으로 실행된다. 이 엔드포인트는 주로 관리용이다.
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
