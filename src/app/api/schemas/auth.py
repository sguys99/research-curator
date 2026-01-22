"""인증 관련 Pydantic 스키마."""

from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class MagicLinkRequest(BaseModel):
    """매직 링크 생성 요청 스키마."""

    email: EmailStr = Field(..., description="사용자 이메일 주소")


class MagicLinkResponse(BaseModel):
    """매직 링크 요청 응답 스키마."""

    message: str = Field(..., description="성공 메시지")
    token: str | None = Field(
        None,
        description="JWT 토큰(개발 모드에서만 반환)",
    )


class TokenResponse(BaseModel):
    """JWT 토큰 응답."""

    access_token: str = Field(..., description="JWT 액세스 토큰")
    token_type: str = Field("bearer", description="토큰 타입")
    user: dict = Field(..., description="사용자 정보")


class TokenPayload(BaseModel):
    """JWT 토큰 페이로드."""

    sub: str = Field(..., description="주체(사용자 이메일)")
    exp: datetime = Field(..., description="만료 시각")
    iat: datetime = Field(..., description="발급 시각")
