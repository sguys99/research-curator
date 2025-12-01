"""Pydantic schemas for data collection endpoints."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class CollectionFilters(BaseModel):
    """Filters for data collection."""

    date_from: str | None = Field(None, description="Start date filter (YYYY-MM-DD)")
    date_to: str | None = Field(None, description="End date filter (YYYY-MM-DD)")
    domains: list[str] | None = Field(None, description="Domain filter for news")
    categories: list[str] | None = Field(None, description="arXiv categories")
    sort_by: str | None = Field("relevance", description="Sort criterion")
    sort_order: str | None = Field("descending", description="Sort order")

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
    """Request for data collection."""

    query: str = Field(..., description="Search query", min_length=1)
    sources: list[str] | None = Field(
        None,
        description="Data sources to search (arxiv, news). If None, search all sources",
    )
    limit: int = Field(10, ge=1, le=50, description="Maximum results per source")
    filters: CollectionFilters | None = Field(None, description="Additional filters")

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
    """Response for a single collected item."""

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
    """Response for data collection."""

    total: int = Field(..., description="Total number of collected items")
    results: list[CollectedItemResponse] = Field(..., description="Collected items")
    errors: list[str] = Field(default_factory=list, description="Collection errors")

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
    """Information about a data source."""

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
    """Response for available sources."""

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
