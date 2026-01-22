"""데이터 수집 엔드포인트용 Pydantic 스키마."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class CollectionFilters(BaseModel):
    """데이터 수집 필터."""

    date_from: str | None = Field(None, description="시작 날짜 필터(YYYY-MM-DD)")
    date_to: str | None = Field(None, description="종료 날짜 필터(YYYY-MM-DD)")
    domains: list[str] | None = Field(None, description="뉴스 도메인 필터")
    categories: list[str] | None = Field(None, description="arXiv 카테고리")
    sort_by: str | None = Field("relevance", description="정렬 기준")
    sort_order: str | None = Field("descending", description="정렬 순서")

    class Config:
        json_schema_extra = {
            "example": {
                "date_from": "2024-01-01",
                "domains": ["techcrunch.com", "venturebeat.com"],
                "categories": ["cs.AI", "cs.LG"],
                "sort_by": "relevance",
                "sort_order": "descending",
            },
        }


class CollectionRequest(BaseModel):
    """데이터 수집 요청."""

    query: str = Field(..., description="검색 쿼리", min_length=1)
    sources: list[str] | None = Field(
        None,
        description="검색할 데이터 소스(arxiv, news). None이면 전체 검색",
    )
    limit: int = Field(10, ge=1, le=50, description="소스별 최대 결과 수")
    filters: CollectionFilters | None = Field(None, description="추가 필터")

    class Config:
        json_schema_extra = {
            "example": {
                "query": "transformer optimization",
                "sources": ["arxiv", "news"],
                "limit": 10,
                "filters": {
                    "categories": ["cs.AI", "cs.LG"],
                    "domains": ["techcrunch.com"],
                },
            },
        }


class CollectedItemResponse(BaseModel):
    """단일 수집 항목 응답."""

    title: str
    content: str
    url: str
    source_type: str
    source_name: str
    metadata: dict[str, Any]
    collected_at: datetime

    class Config:
        json_schema_extra = {
            "example": {
                "title": "Attention Is All You Need",
                "content": "The dominant sequence transduction models...",
                "url": "https://arxiv.org/abs/1706.03762",
                "source_type": "paper",
                "source_name": "arXiv",
                "metadata": {
                    "arxiv_id": "1706.03762",
                    "authors": ["Ashish Vaswani", "Noam Shazeer"],
                    "primary_category": "cs.CL",
                },
                "collected_at": "2024-11-29T10:00:00",
            },
        }


class CollectionResponse(BaseModel):
    """데이터 수집 응답."""

    total: int = Field(..., description="수집된 항목 총 수")
    results: list[CollectedItemResponse] = Field(..., description="수집 항목")
    errors: list[str] = Field(default_factory=list, description="수집 에러")

    class Config:
        json_schema_extra = {
            "example": {
                "total": 15,
                "results": [
                    {
                        "title": "Attention Is All You Need",
                        "content": "The dominant sequence transduction models...",
                        "url": "https://arxiv.org/abs/1706.03762",
                        "source_type": "paper",
                        "source_name": "arXiv",
                        "metadata": {"arxiv_id": "1706.03762"},
                        "collected_at": "2024-11-29T10:00:00",
                    },
                ],
                "errors": [],
            },
        }


class SourceInfo(BaseModel):
    """데이터 소스 정보."""

    name: str
    type: str
    description: str
    supported_filters: list[str]

    class Config:
        json_schema_extra = {
            "example": {
                "name": "arxiv",
                "type": "paper",
                "description": "Academic papers from arXiv.org",
                "supported_filters": ["categories", "sort_by", "sort_order"],
            },
        }


class SourcesResponse(BaseModel):
    """사용 가능한 소스 응답."""

    sources: list[SourceInfo]

    class Config:
        json_schema_extra = {
            "example": {
                "sources": [
                    {
                        "name": "arxiv",
                        "type": "paper",
                        "description": "Academic papers from arXiv.org",
                        "supported_filters": ["categories", "sort_by", "sort_order"],
                    },
                    {
                        "name": "news",
                        "type": "news",
                        "description": "Tech and AI news articles",
                        "supported_filters": ["domains", "date_filter"],
                    },
                ],
            },
        }
