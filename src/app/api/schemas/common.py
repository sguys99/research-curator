"""Common Pydantic schemas for API."""

from typing import Any, Generic, TypeVar

from pydantic import BaseModel, Field

# Generic type for paginated responses
T = TypeVar("T")


class PaginationParams(BaseModel):
    """Pagination parameters for list endpoints."""

    skip: int = Field(0, ge=0, description="Number of items to skip")
    limit: int = Field(10, ge=1, le=100, description="Number of items to return")


class PaginatedResponse(BaseModel, Generic[T]):
    """Generic paginated response."""

    items: list[T] = Field(default_factory=list, description="List of items")
    total: int = Field(..., description="Total number of items")
    skip: int = Field(..., description="Number of items skipped")
    limit: int = Field(..., description="Number of items returned")


class MessageResponse(BaseModel):
    """Simple message response."""

    message: str = Field(..., description="Response message")
    detail: dict[str, Any] | None = Field(None, description="Additional details")


class ErrorResponse(BaseModel):
    """Error response."""

    detail: str = Field(..., description="Error detail message")
    error_code: str | None = Field(None, description="Error code")
