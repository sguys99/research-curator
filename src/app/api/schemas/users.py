"""User and preference-related Pydantic schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field

# ========== User Schemas ==========


class UserBase(BaseModel):
    """Base user schema."""

    email: EmailStr = Field(..., description="User email address")
    name: str | None = Field(None, description="User name")


class UserCreate(UserBase):
    """Schema for creating a new user."""

    pass


class UserUpdate(BaseModel):
    """Schema for updating user."""

    name: str | None = Field(None, description="User name")


class UserResponse(UserBase):
    """User response schema."""

    id: UUID = Field(..., description="User ID")
    created_at: datetime = Field(..., description="Account creation time")
    last_login: datetime = Field(..., description="Last login time")

    model_config = {"from_attributes": True}


# ========== User Preference Schemas ==========


class UserPreferenceBase(BaseModel):
    """Base user preference schema."""

    research_fields: list[str] = Field(
        default_factory=list,
        description="Research fields of interest",
    )
    keywords: list[str] = Field(
        default_factory=list,
        description="Keywords to track",
    )
    sources: list[str] = Field(
        default_factory=list,
        description="Preferred data sources",
    )
    info_types: dict[str, float] = Field(
        default={"paper": 0.4, "news": 0.4, "report": 0.2},
        description="Information type preferences (paper/news/report ratio)",
    )
    email_time: str = Field(
        "08:00",
        pattern=r"^\d{2}:\d{2}$",
        description="Preferred email delivery time (HH:MM)",
    )
    daily_limit: int = Field(
        5,
        ge=1,
        le=20,
        description="Maximum articles per day",
    )
    email_enabled: bool = Field(
        True,
        description="Whether to send daily emails",
    )


class UserPreferenceCreate(UserPreferenceBase):
    """Schema for creating user preferences."""

    user_id: UUID = Field(..., description="User ID")


class UserPreferenceUpdate(BaseModel):
    """Schema for updating user preferences."""

    research_fields: list[str] | None = Field(None, description="Research fields")
    keywords: list[str] | None = Field(None, description="Keywords")
    sources: list[str] | None = Field(None, description="Data sources")
    info_types: dict[str, float] | None = Field(None, description="Information type preferences")
    email_time: str | None = Field(None, description="Email delivery time")
    daily_limit: int | None = Field(None, ge=1, le=20, description="Daily article limit")
    email_enabled: bool | None = Field(None, description="Enable/disable emails")


class UserPreferenceResponse(UserPreferenceBase):
    """User preference response schema."""

    id: UUID = Field(..., description="Preference ID")
    user_id: UUID = Field(..., description="User ID")
    created_at: datetime = Field(..., description="Creation time")
    updated_at: datetime = Field(..., description="Last update time")

    model_config = {"from_attributes": True}


# ========== Digest Schemas ==========


class DigestResponse(BaseModel):
    """Digest response schema."""

    id: UUID = Field(..., description="Digest ID")
    user_id: UUID = Field(..., description="User ID")
    article_ids: list[str] = Field(..., description="Article IDs in this digest")
    sent_at: datetime = Field(..., description="Send time")
    email_opened: bool = Field(..., description="Whether email was opened")
    opened_at: datetime | None = Field(None, description="Email open time")

    model_config = {"from_attributes": True}


class DigestListResponse(BaseModel):
    """List of digests with pagination."""

    digests: list[DigestResponse] = Field(..., description="List of digests")
    total: int = Field(..., description="Total number of digests")
