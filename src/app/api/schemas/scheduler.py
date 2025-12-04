"""Pydantic schemas for Scheduler API endpoints."""

from pydantic import BaseModel, Field


class JobInfo(BaseModel):
    """Information about a scheduled job."""

    id: str = Field(..., description="Unique job identifier")
    name: str = Field(..., description="Human-readable job name")
    next_run_time: str | None = Field(None, description="ISO format timestamp of next scheduled run")
    trigger: str = Field(..., description="Trigger description")


class SchedulerStatusResponse(BaseModel):
    """Response schema for scheduler status endpoint."""

    running: bool = Field(..., description="Whether scheduler is currently running")
    timezone: str = Field(..., description="Scheduler timezone")
    current_time: str = Field(..., description="Current time in scheduler timezone (ISO format)")
    jobs: list[JobInfo] = Field(..., description="List of registered jobs")

    class Config:
        json_schema_extra = {
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
        }


class TriggerJobRequest(BaseModel):
    """Request schema for manually triggering a job."""

    job_id: str = Field(..., description="ID of the job to trigger")

    class Config:
        json_schema_extra = {
            "example": {
                "job_id": "collect_data",
            },
        }


class TriggerJobResponse(BaseModel):
    """Response schema for job trigger endpoint."""

    success: bool = Field(..., description="Whether job was triggered successfully")
    message: str = Field(..., description="Result message")
    job_id: str = Field(..., description="ID of the triggered job")
    triggered_at: str = Field(..., description="ISO format timestamp when job was triggered")

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Job 'collect_data' triggered successfully",
                "job_id": "collect_data",
                "triggered_at": "2025-12-04T10:30:00+09:00",
            },
        }


class JobListResponse(BaseModel):
    """Response schema for listing all jobs."""

    total: int = Field(..., description="Total number of registered jobs")
    jobs: list[JobInfo] = Field(..., description="List of all registered jobs")

    class Config:
        json_schema_extra = {
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
        }


class SchedulerControlRequest(BaseModel):
    """Request schema for scheduler control (start/stop)."""

    action: str = Field(..., description="Action to perform: 'start' or 'stop'")

    class Config:
        json_schema_extra = {
            "example": {
                "action": "start",
            },
        }


class SchedulerControlResponse(BaseModel):
    """Response schema for scheduler control endpoint."""

    success: bool = Field(..., description="Whether action was successful")
    message: str = Field(..., description="Result message")
    running: bool = Field(..., description="Current scheduler running status")

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Scheduler started successfully",
                "running": True,
            },
        }
