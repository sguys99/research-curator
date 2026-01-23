"""검색 API를 사용한 뉴스 수집기."""

import logging
from typing import Any

from app.collectors.base import BaseCollector, CollectedData, CollectorError, SourceType
from app.collectors.search_client import SearchClient
from app.core.retry import retry_with_backoff

logger = logging.getLogger(__name__)


class NewsCollector(BaseCollector):
    """AI/기술 뉴스 아티클 수집기."""

    DEFAULT_DOMAINS = [
        "techcrunch.com",
        "venturebeat.com",
        "technologyreview.com",
        "theverge.com",
        "wired.com",
        "arstechnica.com",
        "zdnet.com",
    ]

    def __init__(self, search_provider: str = "serper") -> None:
        """뉴스 수집기를 초기화한다.

        Args:
            search_provider: 검색 API 제공자("serper" 또는 "brave")
        """
        super().__init__(source_name="News", source_type=SourceType.NEWS)
        self.search_client = SearchClient()
        self.search_provider = search_provider

    @retry_with_backoff(max_retries=3, initial_delay=1.0, exceptions=(CollectorError,))
    async def collect(
        self,
        query: str,
        limit: int = 10,
        filters: dict[str, Any] | None = None,
    ) -> list[CollectedData]:
        """뉴스 아티클을 수집한다.

        Args:
            query: 검색 쿼리
            limit: 수집할 최대 아티클 수
            filters: 추가 필터
                - domains: 포함할 도메인 목록(기본값: DEFAULT_DOMAINS)
                - date_filter: Serper 날짜 필터("d", "w", "m")
                - freshness: Brave 신선도 필터("pd", "pw", "pm")

        Returns:
            수집된 뉴스 아티클 목록

        Raises:
            CollectorError: 수집 실패 시
        """
        try:
            filters = filters or {}

            domains = filters.get("domains", self.DEFAULT_DOMAINS)
            domain_query = self._build_domain_query(query, domains)

            if self.search_provider == "serper":
                results = await self.search_client.serper_search(
                    query=domain_query,
                    num_results=limit,
                    search_type="news",
                    date_filter=filters.get("date_filter"),
                )
            else:
                results = await self.search_client.brave_search(
                    query=domain_query,
                    num_results=limit,
                    search_type="news",
                    freshness=filters.get("freshness"),
                )

            collected_data = [self._parse_news_result(result) for result in results]

            logger.info(f"NewsCollector: Collected {len(collected_data)} articles for query '{query}'")

            return collected_data

        except Exception as e:
            logger.error(f"NewsCollector error: {str(e)}")
            raise CollectorError(f"Failed to collect news: {str(e)}") from e

    def _build_domain_query(self, query: str, domains: list[str]) -> str:
        """도메인 필터가 포함된 검색 쿼리를 생성한다.

        Args:
            query: 기본 검색 쿼리
            domains: 포함할 도메인 목록

        Returns:
            도메인 필터가 포함된 쿼리
        """
        if not domains:
            return query

        domain_filter = " OR ".join([f"site:{domain}" for domain in domains])
        return f"{query} ({domain_filter})"

    def _parse_news_result(self, result: dict[str, Any]) -> CollectedData:
        """뉴스 검색 결과를 파싱한다.

        Args:
            result: 원본 검색 결과

        Returns:
            CollectedData 인스턴스
        """
        title = result.get("title", "")
        snippet = result.get("snippet", "")
        link = result.get("link", "")
        date_str = result.get("date")
        source = result.get("source")

        metadata = {
            "published_date": date_str,
            "source_name": source,
        }

        return self._create_collected_data(
            title=title,
            content=snippet,
            url=link,
            metadata=metadata,
        )


def get_ai_news_domains() -> list[str]:
    """인기 있는 AI/기술 뉴스 도메인 목록을 반환한다.

    Returns:
        도메인 이름 목록
    """
    return NewsCollector.DEFAULT_DOMAINS
