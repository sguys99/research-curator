"""스케줄러 API 엔드포인트용 Pydantic 스키마."""

from pydantic import BaseModel, ConfigDict, Field


class JobInfo(BaseModel):
    """스케줄된 작업 정보."""

    id: str = Field(..., description="고유 작업 식별자")
    name: str = Field(..., description="표시용 작업 이름")
    next_run_time: str | None = Field(None, description="다음 실행 시각(ISO 형식)")
    trigger: str = Field(..., description="트리거 설명")


class SchedulerStatusResponse(BaseModel):
    """스케줄러 상태 응답 스키마."""

    running: bool = Field(..., description="스케줄러 실행 여부")
    timezone: str = Field(..., description="스케줄러 타임존")
    current_time: str = Field(..., description="현재 시각(ISO 형식)")
    jobs: list[JobInfo] = Field(..., description="등록된 작업 목록")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "running": True,
                "timezone": "Asia/Seoul",
                "current_time": "2025-12-04T10:30:00+09:00",
                "jobs": [
                    {
                        "id": "collect_data",
                        "name": "Daily Data Collection",
                        "next_run_time": "2025-12-05T01:00:00+09:00",
                        "trigger": "cron[hour='1', minute='0']",
                    },
                ],
            },
        },
    )


class TriggerJobRequest(BaseModel):
    """작업 수동 실행 요청 스키마."""

    job_id: str = Field(..., description="실행할 작업 ID")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "job_id": "collect_data",
            },
        },
    )


class TriggerJobResponse(BaseModel):
    """작업 실행 응답 스키마."""

    success: bool = Field(..., description="작업 실행 성공 여부")
    message: str = Field(..., description="결과 메시지")
    job_id: str = Field(..., description="실행된 작업 ID")
    triggered_at: str = Field(..., description="작업 실행 시각(ISO 형식)")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "success": True,
                "message": "Job 'collect_data' triggered successfully",
                "job_id": "collect_data",
                "triggered_at": "2025-12-04T10:30:00+09:00",
            },
        },
    )


class JobListResponse(BaseModel):
    """전체 작업 목록 응답 스키마."""

    total: int = Field(..., description="등록된 작업 총 수")
    jobs: list[JobInfo] = Field(..., description="모든 등록 작업 목록")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "total": 3,
                "jobs": [
                    {
                        "id": "collect_data",
                        "name": "Daily Data Collection",
                        "next_run_time": "2025-12-05T01:00:00+09:00",
                        "trigger": "cron[hour='1', minute='0']",
                    },
                    {
                        "id": "process_articles",
                        "name": "Process Collected Articles",
                        "next_run_time": "2025-12-05T01:30:00+09:00",
                        "trigger": "cron[hour='1', minute='30']",
                    },
                    {
                        "id": "send_digests",
                        "name": "Send Email Digests",
                        "next_run_time": "2025-12-05T08:00:00+09:00",
                        "trigger": "cron[hour='8', minute='0']",
                    },
                ],
            },
        },
    )


class SchedulerControlRequest(BaseModel):
    """스케줄러 제어 요청 스키마(start/stop)."""

    action: str = Field(..., description="수행할 동작: 'start' 또는 'stop'")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "action": "start",
            },
        },
    )


class SchedulerControlResponse(BaseModel):
    """스케줄러 제어 응답 스키마."""

    success: bool = Field(..., description="동작 성공 여부")
    message: str = Field(..., description="결과 메시지")
    running: bool = Field(..., description="현재 스케줄러 실행 상태")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "success": True,
                "message": "Scheduler started successfully",
                "running": True,
            },
        },
    )
