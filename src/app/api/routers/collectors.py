"""API endpoints for data collection."""

import logging

from fastapi import APIRouter, HTTPException, status

from app.api.schemas.collectors import (
    CollectedItemResponse,
    CollectionRequest,
    CollectionResponse,
    SourceInfo,
    SourcesResponse,
)
from app.collectors.arxiv import ArxivCollector
from app.collectors.base import CollectedData, CollectorError
from app.collectors.news import NewsCollector

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/collectors", tags=["collectors"])


class CollectorRegistry:
    """Registry for all available collectors."""

    def __init__(self):
        """Initialize collector registry."""
        self._collectors = {
            "arxiv": ArxivCollector(),
            "news": NewsCollector(),
        }

    def get(self, name: str):
        """Get collector by name."""
        return self._collectors.get(name)

    def get_all_names(self) -> list[str]:
        """Get all registered collector names."""
        return list(self._collectors.keys())

    def get_source_info(self) -> list[SourceInfo]:
        """Get information about all sources."""
        sources = [
            SourceInfo(
                name="arxiv",
                type="paper",
                description="Academic papers from arXiv.org",
                supported_filters=["categories", "sort_by", "sort_order"],
            ),
            SourceInfo(
                name="news",
                type="news",
                description="Tech and AI news articles",
                supported_filters=["domains", "date_filter", "freshness"],
            ),
        ]
        return sources


registry = CollectorRegistry()


@router.post(
    "/search",
    response_model=CollectionResponse,
    summary="Search across multiple sources",
    description="Collect data from specified sources (arXiv, news, etc.)",
)
async def search_multiple_sources(request: CollectionRequest) -> CollectionResponse:
    """Search and collect data from multiple sources.

    Args:
        request: Collection request with query, sources, limit, and filters

    Returns:
        Collection response with results and errors

    Raises:
        HTTPException: If all collections fail
    """
    sources = request.sources or registry.get_all_names()

    all_results: list[CollectedData] = []
    errors: list[str] = []

    for source_name in sources:
        collector = registry.get(source_name)

        if not collector:
            errors.append(f"Unknown source: {source_name}")
            continue

        try:
            filters_dict = request.filters.model_dump() if request.filters else {}

            results = await collector.collect(
                query=request.query,
                limit=request.limit,
                filters=filters_dict,
            )

            all_results.extend(results)

            logger.info(f"Collected {len(results)} items from {source_name} for query '{request.query}'")

        except CollectorError as e:
            error_msg = f"Error collecting from {source_name}: {str(e)}"
            logger.error(error_msg)
            errors.append(error_msg)

        except Exception as e:
            error_msg = f"Unexpected error from {source_name}: {str(e)}"
            logger.error(error_msg, exc_info=True)
            errors.append(error_msg)

    if not all_results and errors:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"message": "All collections failed", "errors": errors},
        )

    response_items = [CollectedItemResponse(**item.to_dict()) for item in all_results]

    return CollectionResponse(
        total=len(response_items),
        results=response_items,
        errors=errors,
    )


@router.post(
    "/arxiv",
    response_model=CollectionResponse,
    summary="Search arXiv papers",
    description="Collect academic papers from arXiv.org",
)
async def search_arxiv(request: CollectionRequest) -> CollectionResponse:
    """Search arXiv for academic papers.

    Args:
        request: Collection request

    Returns:
        Collection response with arXiv papers

    Raises:
        HTTPException: If collection fails
    """
    try:
        collector = ArxivCollector()

        filters_dict = request.filters.model_dump() if request.filters else {}

        results = await collector.collect(
            query=request.query,
            limit=request.limit,
            filters=filters_dict,
        )

        response_items = [CollectedItemResponse(**item.to_dict()) for item in results]

        return CollectionResponse(
            total=len(response_items),
            results=response_items,
            errors=[],
        )

    except CollectorError as e:
        logger.error(f"arXiv collection failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to collect from arXiv: {str(e)}",
        ) from e
    except Exception as e:
        logger.error(f"Unexpected error in arXiv collection: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error: {str(e)}",
        ) from e


@router.post(
    "/news",
    response_model=CollectionResponse,
    summary="Search news articles",
    description="Collect tech and AI news from various sources",
)
async def search_news(request: CollectionRequest) -> CollectionResponse:
    """Search for news articles.

    Args:
        request: Collection request

    Returns:
        Collection response with news articles

    Raises:
        HTTPException: If collection fails
    """
    try:
        collector = NewsCollector()

        filters_dict = request.filters.model_dump() if request.filters else {}

        results = await collector.collect(
            query=request.query,
            limit=request.limit,
            filters=filters_dict,
        )

        response_items = [CollectedItemResponse(**item.to_dict()) for item in results]

        return CollectionResponse(
            total=len(response_items),
            results=response_items,
            errors=[],
        )

    except CollectorError as e:
        logger.error(f"News collection failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to collect news: {str(e)}",
        ) from e
    except Exception as e:
        logger.error(f"Unexpected error in news collection: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error: {str(e)}",
        ) from e


@router.get(
    "/sources",
    response_model=SourcesResponse,
    summary="List available sources",
    description="Get information about all available data sources",
)
async def list_sources() -> SourcesResponse:
    """List all available data sources.

    Returns:
        Information about all available sources
    """
    sources = registry.get_source_info()
    return SourcesResponse(sources=sources)
