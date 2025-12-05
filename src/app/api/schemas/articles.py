"""Article-related Pydantic schemas."""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field

# ========== Article Schemas ==========


class ArticleBase(BaseModel):
    """Base article schema."""

    title: str = Field(..., max_length=512, description="Article title")
    content: str | None = Field(None, description="Full article content")
    summary: str | None = Field(None, description="AI-generated summary")
    source_url: str = Field(..., max_length=1024, description="Source URL")
    source_type: str = Field(..., description="Source type (paper/news/report)")
    category: str | None = Field(None, description="Article category")
    importance_score: float | None = Field(
        None,
        ge=0.0,
        le=1.0,
        description="Importance score (0-1)",
    )
    article_metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata",
    )


class ArticleCreate(ArticleBase):
    """Schema for creating a new article."""

    vector_id: str | None = Field(None, description="Qdrant vector ID")
    published_at: datetime | None = Field(None, description="Publication date")


class ArticleUpdate(BaseModel):
    """Schema for updating an article."""

    title: str | None = Field(None, description="Article title")
    content: str | None = Field(None, description="Full content")
    summary: str | None = Field(None, description="Summary")
    importance_score: float | None = Field(None, description="Importance score")
    article_metadata: dict[str, Any] | None = Field(None, description="Metadata")


class ArticleResponse(ArticleBase):
    """Article response schema."""

    id: UUID = Field(..., description="Article ID")
    vector_id: str | None = Field(None, description="Qdrant vector ID")
    collected_at: datetime = Field(..., description="Collection time")
    published_at: datetime | None = Field(None, description="Publication date")

    model_config = {"from_attributes": True}


# ========== Search Schemas ==========


class ArticleSearchRequest(BaseModel):
    """Request schema for semantic article search."""

    query: str = Field(..., min_length=1, description="Search query")
    limit: int = Field(10, ge=1, le=100, description="Maximum results")
    score_threshold: float = Field(
        0.7,
        ge=0.0,
        le=1.0,
        description="Minimum similarity score",
    )
    source_type: list[str] | None = Field(
        None,
        description="Filter by source types",
    )
    category: list[str] | None = Field(
        None,
        description="Filter by categories",
    )
    min_importance_score: float | None = Field(
        None,
        ge=0.0,
        le=1.0,
        description="Minimum importance score",
    )
    date_from: str | None = Field(
        None,
        description="Filter from date (ISO format)",
    )
    date_to: str | None = Field(
        None,
        description="Filter to date (ISO format)",
    )


class ArticleSearchResult(ArticleResponse):
    """Search result with similarity score."""

    similarity_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Similarity score from vector search",
    )


class ArticleSearchResponse(BaseModel):
    """Response schema for article search."""

    results: list[ArticleSearchResult] = Field(
        default_factory=list,
        description="Search results",
    )
    total: int = Field(..., description="Total number of results")
    query: str = Field(..., description="Original query")


class SimilarArticlesRequest(BaseModel):
    """Request schema for finding similar articles."""

    limit: int = Field(5, ge=1, le=50, description="Maximum results")
    score_threshold: float = Field(
        0.7,
        ge=0.0,
        le=1.0,
        description="Minimum similarity score",
    )


class SimilarArticlesResponse(BaseModel):
    """Response schema for similar articles."""

    results: list[ArticleSearchResult] = Field(
        default_factory=list,
        description="Similar articles",
    )
    total: int = Field(..., description="Total number of results")
    article_id: UUID = Field(..., description="Reference article ID")


# ========== List Schemas ==========


class ArticleListRequest(BaseModel):
    """Request schema for listing articles."""

    skip: int = Field(0, ge=0, description="Number of items to skip")
    limit: int = Field(10, ge=1, le=100, description="Number of items to return")
    source_type: str | None = Field(None, description="Filter by source type")
    category: str | None = Field(None, description="Filter by category")
    sort_by: str = Field(
        "collected_at",
        description="Sort field (collected_at, importance_score, published_at)",
    )
    order: str = Field(
        "desc",
        pattern="^(asc|desc)$",
        description="Sort order (asc/desc)",
    )


class ArticleListResponse(BaseModel):
    """Response schema for article list."""

    articles: list[ArticleResponse] = Field(..., description="List of articles")
    total: int = Field(..., description="Total number of articles")
    skip: int = Field(0, description="Number of items skipped")
    limit: int = Field(10, description="Number of items returned")


# ========== Batch Schemas ==========


class BatchArticleRequest(BaseModel):
    """Request schema for batch article retrieval."""

    article_ids: list[UUID] = Field(..., min_length=1, max_length=50, description="Article IDs")


# ========== Statistics Schemas ==========


class ArticleStatisticsResponse(BaseModel):
    """Response schema for article statistics."""

    total: int = Field(..., description="Total number of articles")
    by_source_type: dict[str, int] = Field(
        default_factory=dict,
        description="Article count by source type",
    )
    by_category: dict[str, int] = Field(
        default_factory=dict,
        description="Article count by category",
    )
    average_importance_score: float = Field(..., description="Average importance score")
