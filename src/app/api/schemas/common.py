"""API 공통 Pydantic 스키마."""

from typing import Any, Generic, TypeVar

from pydantic import BaseModel, Field

# 페이지네이션 응답용 제네릭 타입
T = TypeVar("T")


class PaginationParams(BaseModel):
    """목록 엔드포인트용 페이지네이션 파라미터."""

    skip: int = Field(0, ge=0, description="건너뛸 항목 수")
    limit: int = Field(10, ge=1, le=100, description="반환할 항목 수")


class PaginatedResponse(BaseModel, Generic[T]):
    """페이지네이션 응답 스키마."""

    items: list[T] = Field(default_factory=list, description="항목 목록")
    total: int = Field(..., description="전체 항목 수")
    skip: int = Field(..., description="건너뛴 항목 수")
    limit: int = Field(..., description="반환된 항목 수")


class MessageResponse(BaseModel):
    """간단한 메시지 응답."""

    message: str = Field(..., description="응답 메시지")
    detail: dict[str, Any] | None = Field(None, description="추가 상세")


class ErrorResponse(BaseModel):
    """에러 응답."""

    detail: str = Field(..., description="에러 상세 메시지")
    error_code: str | None = Field(None, description="에러 코드")
