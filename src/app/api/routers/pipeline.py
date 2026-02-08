"""1회성 파이프라인 수동 실행 API 엔드포인트."""

import asyncio
import logging
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException

from app.api.dependencies import get_current_user
from app.db.models import User
from app.scheduler.tasks import unified_collect_and_send_task_async

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/pipeline", tags=["Pipeline"])

# 모듈 레벨 상태 (단일 프로세스 환경에서 충분)
_pipeline_running: bool = False
_pipeline_result: dict | None = None


async def _run_pipeline() -> None:
    """백그라운드에서 수집+처리 파이프라인을 실행한다."""
    global _pipeline_running, _pipeline_result
    try:
        _pipeline_result = {"status": "running", "message": "Pipeline is running..."}
        await unified_collect_and_send_task_async(send_email=False)
        _pipeline_result = {
            "status": "completed",
            "message": "Pipeline completed successfully",
            "completed_at": datetime.now(UTC).isoformat(),
        }
    except Exception as e:
        logger.error(f"Pipeline execution failed: {e}", exc_info=True)
        _pipeline_result = {
            "status": "failed",
            "message": f"Pipeline failed: {str(e)}",
            "completed_at": datetime.now(UTC).isoformat(),
        }
    finally:
        _pipeline_running = False


@router.post("/run")
async def run_pipeline(
    current_user: User = Depends(get_current_user),
) -> dict:
    """
    수집+처리 파이프라인을 1회 실행한다.

    스케줄러와 무관하게 즉시 실행하며, 이메일 발송은 포함하지 않는다.
    백그라운드로 실행되므로 즉시 응답을 반환한다.
    """
    global _pipeline_running, _pipeline_result

    if _pipeline_running:
        raise HTTPException(
            status_code=409,
            detail="Pipeline is already running",
        )

    _pipeline_running = True
    _pipeline_result = {"status": "running", "message": "Pipeline started"}

    asyncio.create_task(_run_pipeline())

    return {"message": "Pipeline started", "status": "running"}


@router.get("/status")
async def get_pipeline_status(
    current_user: User = Depends(get_current_user),
) -> dict:
    """파이프라인 실행 상태를 조회한다."""
    if _pipeline_running:
        return {"status": "running", "message": "Pipeline is running..."}

    if _pipeline_result is None:
        return {"status": "idle", "message": "No pipeline has been run yet"}

    return _pipeline_result
