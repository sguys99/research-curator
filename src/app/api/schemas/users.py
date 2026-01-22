"""사용자 및 선호도 관련 Pydantic 스키마."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field

# ========== 사용자 스키마 ==========


class UserBase(BaseModel):
    """사용자 기본 스키마."""

    email: EmailStr = Field(..., description="사용자 이메일 주소")
    name: str | None = Field(None, description="사용자 이름")


class UserCreate(UserBase):
    """새 사용자 생성 스키마."""

    pass


class UserUpdate(BaseModel):
    """사용자 업데이트 스키마."""

    name: str | None = Field(None, description="사용자 이름")


class UserResponse(UserBase):
    """사용자 응답 스키마."""

    id: UUID = Field(..., description="사용자 ID")
    created_at: datetime = Field(..., description="계정 생성 시각")
    last_login: datetime = Field(..., description="마지막 로그인 시각")

    model_config = {"from_attributes": True}


# ========== 사용자 선호도 스키마 ==========


class UserPreferenceBase(BaseModel):
    """사용자 선호도 기본 스키마."""

    research_fields: list[str] = Field(
        default_factory=list,
        description="관심 연구 분야",
    )
    keywords: list[str] = Field(
        default_factory=list,
        description="추적할 키워드",
    )
    sources: list[str] = Field(
        default_factory=list,
        description="선호 데이터 소스",
    )
    info_types: dict[str, float] = Field(
        default={"paper": 0.4, "news": 0.4, "report": 0.2},
        description="정보 유형 선호도(paper/news/report 비율)",
    )
    email_time: str = Field(
        "08:00",
        pattern=r"^\d{2}:\d{2}$",
        description="이메일 발송 시간(HH:MM)",
    )
    daily_limit: int = Field(
        5,
        ge=1,
        le=20,
        description="하루 최대 아티클 수",
    )
    email_enabled: bool = Field(
        True,
        description="일일 이메일 발송 여부",
    )


class UserPreferenceCreate(UserPreferenceBase):
    """사용자 선호도 생성 스키마."""

    user_id: UUID = Field(..., description="사용자 ID")


class UserPreferenceUpdate(BaseModel):
    """사용자 선호도 업데이트 스키마."""

    research_fields: list[str] | None = Field(None, description="연구 분야")
    keywords: list[str] | None = Field(None, description="키워드")
    sources: list[str] | None = Field(None, description="데이터 소스")
    info_types: dict[str, float] | None = Field(None, description="정보 유형 선호도")
    email_time: str | None = Field(None, description="이메일 발송 시간")
    daily_limit: int | None = Field(None, ge=1, le=20, description="일일 아티클 제한")
    email_enabled: bool | None = Field(None, description="이메일 발송 여부")


class UserPreferenceResponse(UserPreferenceBase):
    """사용자 선호도 응답 스키마."""

    id: UUID = Field(..., description="선호도 ID")
    user_id: UUID = Field(..., description="사용자 ID")
    created_at: datetime = Field(..., description="생성 시각")
    updated_at: datetime = Field(..., description="마지막 수정 시각")

    model_config = {"from_attributes": True}


# ========== 다이제스트 스키마 ==========


class DigestResponse(BaseModel):
    """다이제스트 응답 스키마."""

    id: UUID = Field(..., description="다이제스트 ID")
    user_id: UUID = Field(..., description="사용자 ID")
    article_ids: list[str] = Field(..., description="다이제스트 포함 아티클 ID")
    sent_at: datetime = Field(..., description="발송 시각")
    email_opened: bool = Field(..., description="이메일 열람 여부")
    opened_at: datetime | None = Field(None, description="이메일 열람 시각")

    model_config = {"from_attributes": True}


class DigestListResponse(BaseModel):
    """페이지네이션이 포함된 다이제스트 목록."""

    digests: list[DigestResponse] = Field(..., description="다이제스트 목록")
    total: int = Field(..., description="전체 다이제스트 수")
