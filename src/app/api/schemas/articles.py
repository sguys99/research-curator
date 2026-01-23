"""아티클 관련 Pydantic 스키마."""

from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

# ========== 아티클 스키마 ==========


class ArticleBase(BaseModel):
    """아티클 기본 스키마."""

    title: str = Field(..., max_length=512, description="아티클 제목")
    content: str | None = Field(None, description="아티클 전체 내용")
    summary: str | None = Field(None, description="AI 생성 요약")
    source_url: str = Field(..., max_length=1024, description="소스 URL")
    source_type: str = Field(..., description="소스 유형(paper/news/report)")
    category: str | None = Field(None, description="아티클 카테고리")
    importance_score: float | None = Field(
        None,
        ge=0.0,
        le=1.0,
        description="중요도 점수(0-1)",
    )
    article_metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="추가 메타데이터",
    )


class ArticleCreate(ArticleBase):
    """새 아티클 생성 스키마."""

    vector_id: str | None = Field(None, description="Qdrant 벡터 ID")
    published_at: datetime | None = Field(None, description="발행일")


class ArticleUpdate(BaseModel):
    """아티클 업데이트 스키마."""

    title: str | None = Field(None, description="아티클 제목")
    content: str | None = Field(None, description="전체 내용")
    summary: str | None = Field(None, description="요약")
    importance_score: float | None = Field(None, description="중요도 점수")
    article_metadata: dict[str, Any] | None = Field(None, description="메타데이터")


class ArticleResponse(ArticleBase):
    """아티클 응답 스키마."""

    id: UUID = Field(..., description="아티클 ID")
    vector_id: str | None = Field(None, description="Qdrant 벡터 ID")
    collected_at: datetime = Field(..., description="수집 시각")
    published_at: datetime | None = Field(None, description="발행일")

    model_config = ConfigDict(from_attributes=True)


# ========== 검색 스키마 ==========


class ArticleSearchRequest(BaseModel):
    """시맨틱 아티클 검색 요청 스키마."""

    query: str = Field(..., min_length=1, description="검색 쿼리")
    limit: int = Field(10, ge=1, le=100, description="최대 결과 수")
    score_threshold: float = Field(
        0.7,
        ge=0.0,
        le=1.0,
        description="최소 유사도 점수",
    )
    source_type: list[str] | None = Field(
        None,
        description="소스 유형 필터",
    )
    category: list[str] | None = Field(
        None,
        description="카테고리 필터",
    )
    min_importance_score: float | None = Field(
        None,
        ge=0.0,
        le=1.0,
        description="최소 중요도 점수",
    )
    date_from: str | None = Field(
        None,
        description="시작 날짜 필터(ISO 형식)",
    )
    date_to: str | None = Field(
        None,
        description="종료 날짜 필터(ISO 형식)",
    )


class ArticleSearchResult(ArticleResponse):
    """유사도 점수가 포함된 검색 결과."""

    similarity_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="벡터 검색 유사도 점수",
    )


class ArticleSearchResponse(BaseModel):
    """아티클 검색 응답 스키마."""

    results: list[ArticleSearchResult] = Field(
        default_factory=list,
        description="검색 결과",
    )
    total: int = Field(..., description="전체 결과 수")
    query: str = Field(..., description="원본 쿼리")


class SimilarArticlesRequest(BaseModel):
    """유사 아티클 조회 요청 스키마."""

    limit: int = Field(5, ge=1, le=50, description="최대 결과 수")
    score_threshold: float = Field(
        0.7,
        ge=0.0,
        le=1.0,
        description="최소 유사도 점수",
    )


class SimilarArticlesResponse(BaseModel):
    """유사 아티클 응답 스키마."""

    results: list[ArticleSearchResult] = Field(
        default_factory=list,
        description="유사 아티클",
    )
    total: int = Field(..., description="전체 결과 수")
    article_id: UUID = Field(..., description="기준 아티클 ID")


# ========== 목록 스키마 ==========


class ArticleListRequest(BaseModel):
    """아티클 목록 요청 스키마."""

    skip: int = Field(0, ge=0, description="건너뛸 항목 수")
    limit: int = Field(10, ge=1, le=100, description="반환할 항목 수")
    source_type: str | None = Field(None, description="소스 유형 필터")
    category: str | None = Field(None, description="카테고리 필터")
    sort_by: Literal["collected_at", "importance_score", "published_at"] = Field(
        "collected_at",
        description="정렬 필드(collected_at, importance_score, published_at)",
    )
    order: str = Field(
        "desc",
        pattern="^(asc|desc)$",
        description="정렬 순서(asc/desc)",
    )


class ArticleListResponse(BaseModel):
    """아티클 목록 응답 스키마."""

    articles: list[ArticleResponse] = Field(..., description="아티클 목록")
    total: int = Field(..., description="전체 아티클 수")
    skip: int = Field(0, description="건너뛴 항목 수")
    limit: int = Field(10, description="반환된 항목 수")


# ========== 배치 스키마 ==========


class BatchArticleRequest(BaseModel):
    """아티클 배치 조회 요청 스키마."""

    article_ids: list[UUID] = Field(..., min_length=1, max_length=50, description="아티클 ID 목록")


# ========== 통계 스키마 ==========


class ArticleStatisticsResponse(BaseModel):
    """아티클 통계 응답 스키마."""

    total: int = Field(..., description="전체 아티클 수")
    by_source_type: dict[str, int] = Field(
        default_factory=dict,
        description="소스 유형별 아티클 수",
    )
    by_category: dict[str, int] = Field(
        default_factory=dict,
        description="카테고리별 아티클 수",
    )
    average_importance_score: float = Field(..., description="평균 중요도 점수")
