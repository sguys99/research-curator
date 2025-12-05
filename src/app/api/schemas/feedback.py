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


class FeedbackCreate(FeedbackBase):
    """Schema for creating feedback."""

    user_id: UUID = Field(..., description="User ID")
    article_id: UUID = Field(..., description="Article ID")


class FeedbackUpdate(BaseModel):
    """Schema for updating feedback."""

    rating: int | None = Field(None, ge=1, le=5, description="Rating")
    comment: str | None = Field(None, max_length=500, description="Comment")


class FeedbackResponse(FeedbackBase):
    """Feedback response schema."""

    id: UUID = Field(..., description="Feedback ID")
    user_id: UUID = Field(..., description="User ID")
    article_id: UUID = Field(..., description="Article ID")
    created_at: datetime = Field(..., description="Creation time")

    model_config = {"from_attributes": True}


class FeedbackListResponse(BaseModel):
    """List of feedbacks with pagination."""

    feedbacks: list[FeedbackResponse] = Field(..., description="List of feedbacks")
    total: int = Field(..., description="Total number of feedbacks")
