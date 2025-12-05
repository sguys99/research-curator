"""Feedback-related Pydantic schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class FeedbackBase(BaseModel):
    """Base feedback schema."""

    rating: int = Field(..., ge=1, le=5, description="Rating (1-5 stars)")
    comment: str | None = Field(
        None,
        max_length=500,
        description="Optional feedback comment",
    )


class FeedbackCreate(BaseModel):
    """Schema for creating feedback."""

    article_id: UUID = Field(..., description="Article ID")
    rating: int = Field(..., ge=1, le=5, description="Rating (1-5 stars)")
    comment: str | None = Field(
        None,
        max_length=1000,
        description="Optional feedback comment",
    )


class FeedbackUpdate(BaseModel):
    """Schema for updating feedback."""

    rating: int | None = Field(None, ge=1, le=5, description="Rating")
    comment: str | None = Field(None, max_length=1000, description="Comment")


class FeedbackResponse(FeedbackBase):
    """Feedback response schema."""

    id: UUID = Field(..., description="Feedback ID")
    user_id: UUID = Field(..., description="User ID")
    article_id: UUID = Field(..., description="Article ID")
    created_at: datetime = Field(..., description="Creation time")

    model_config = {"from_attributes": True}


class FeedbackListResponse(BaseModel):
    """List of feedbacks with pagination."""

    feedback: list[FeedbackResponse] = Field(..., description="List of feedbacks")
    total: int = Field(..., description="Total number of feedbacks")
    skip: int = Field(..., description="Number of items skipped")
    limit: int = Field(..., description="Number of items returned")


class FeedbackStatsResponse(BaseModel):
    """Feedback statistics response."""

    article_id: UUID = Field(..., description="Article ID")
    count: int = Field(..., description="Total feedback count")
    average_rating: float = Field(..., description="Average rating (0.00-5.00)")
    rating_distribution: dict[int, int] = Field(
        ...,
        description="Rating distribution (1-5 stars with counts)",
    )
