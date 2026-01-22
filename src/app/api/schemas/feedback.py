"""피드백 관련 Pydantic 스키마."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class FeedbackBase(BaseModel):
    """피드백 기본 스키마."""

    rating: int = Field(..., ge=1, le=5, description="평점(1-5점)")
    comment: str | None = Field(
        None,
        max_length=500,
        description="선택적 피드백 코멘트",
    )


class FeedbackCreate(BaseModel):
    """피드백 생성 스키마."""

    article_id: UUID = Field(..., description="아티클 ID")
    rating: int = Field(..., ge=1, le=5, description="평점(1-5점)")
    comment: str | None = Field(
        None,
        max_length=1000,
        description="선택적 피드백 코멘트",
    )


class FeedbackUpdate(BaseModel):
    """피드백 수정 스키마."""

    rating: int | None = Field(None, ge=1, le=5, description="평점")
    comment: str | None = Field(None, max_length=1000, description="코멘트")


class FeedbackResponse(FeedbackBase):
    """피드백 응답 스키마."""

    id: UUID = Field(..., description="피드백 ID")
    user_id: UUID = Field(..., description="사용자 ID")
    article_id: UUID = Field(..., description="아티클 ID")
    created_at: datetime = Field(..., description="생성 시각")

    model_config = {"from_attributes": True}


class FeedbackListResponse(BaseModel):
    """페이지네이션이 포함된 피드백 목록."""

    feedback: list[FeedbackResponse] = Field(..., description="피드백 목록")
    total: int = Field(..., description="전체 피드백 수")
    skip: int = Field(..., description="건너뛴 항목 수")
    limit: int = Field(..., description="반환된 항목 수")


class FeedbackStatsResponse(BaseModel):
    """피드백 통계 응답 스키마."""

    article_id: UUID = Field(..., description="아티클 ID")
    count: int = Field(..., description="전체 피드백 수")
    average_rating: float = Field(..., description="평균 평점(0.00-5.00)")
    rating_distribution: dict[int, int] = Field(
        ...,
        description="평점 분포(1-5점별 개수)",
    )
