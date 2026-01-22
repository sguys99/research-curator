"""데이터 수집을 위한 API 엔드포인트."""

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
    """사용 가능한 모든 수집기를 관리하는 레지스트리."""

    def __init__(self):
        """수집기 레지스트리를 초기화한다."""
        self._collectors = {
            "arxiv": ArxivCollector(),
            "news": NewsCollector(),
        }

    def get(self, name: str):
        """이름으로 수집기를 조회한다."""
        return self._collectors.get(name)

    def get_all_names(self) -> list[str]:
        """등록된 수집기 이름 목록을 반환한다."""
        return list(self._collectors.keys())

    def get_source_info(self) -> list[SourceInfo]:
        """모든 소스 정보를 반환한다."""
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
    summary="여러 소스에서 검색",
    description="지정된 소스(arXiv, 뉴스 등)에서 데이터를 수집합니다.",
)
async def search_multiple_sources(request: CollectionRequest) -> CollectionResponse:
    """여러 소스에서 데이터를 검색/수집한다.

    Args:
        request: 쿼리/소스/제한/필터가 포함된 수집 요청

    Returns:
        결과와 에러가 포함된 수집 응답

    Raises:
        HTTPException: 모든 수집이 실패한 경우
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
    summary="arXiv 논문 검색",
    description="arXiv.org에서 학술 논문을 수집합니다.",
)
async def search_arxiv(request: CollectionRequest) -> CollectionResponse:
    """arXiv에서 학술 논문을 검색한다.

    Args:
        request: 수집 요청

    Returns:
        arXiv 논문이 포함된 수집 응답

    Raises:
        HTTPException: 수집에 실패한 경우
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
    summary="뉴스 아티클 검색",
    description="여러 소스에서 기술/AI 뉴스를 수집합니다.",
)
async def search_news(request: CollectionRequest) -> CollectionResponse:
    """뉴스 아티클을 검색한다.

    Args:
        request: 수집 요청

    Returns:
        뉴스 아티클이 포함된 수집 응답

    Raises:
        HTTPException: 수집에 실패한 경우
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
    summary="사용 가능한 소스 목록",
    description="사용 가능한 모든 데이터 소스 정보를 반환합니다.",
)
async def list_sources() -> SourcesResponse:
    """사용 가능한 데이터 소스 목록을 조회한다.

    Returns:
        전체 소스 정보
    """
    sources = registry.get_source_info()
    return SourcesResponse(sources=sources)
