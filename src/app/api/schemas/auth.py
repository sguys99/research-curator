"""Authentication-related Pydantic schemas."""

from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class MagicLinkRequest(BaseModel):
    """Request schema for magic link generation."""

    email: EmailStr = Field(..., description="User email address")


class MagicLinkResponse(BaseModel):
    """Response schema for magic link request."""

    message: str = Field(..., description="Success message")
    token: str | None = Field(
        None,
        description="JWT token (only in development mode)",
    )


class TokenResponse(BaseModel):
    """JWT token response."""

    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field("bearer", description="Token type")
    user: dict = Field(..., description="User information")


class TokenPayload(BaseModel):
    """JWT token payload."""

    sub: str = Field(..., description="Subject (user email)")
    exp: datetime = Field(..., description="Expiration time")
    iat: datetime = Field(..., description="Issued at time")
