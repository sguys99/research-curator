"""News collector using search APIs."""

import logging
from typing import Any

from app.collectors.base import BaseCollector, CollectedData, CollectorError, SourceType
from app.collectors.search_client import SearchClient
from app.core.retry import retry_with_backoff

logger = logging.getLogger(__name__)


class NewsCollector(BaseCollector):
    """Collector for AI and tech news articles."""

    DEFAULT_DOMAINS = [
        "techcrunch.com",
        "venturebeat.com",
        "technologyreview.com",
        "theverge.com",
        "wired.com",
        "arstechnica.com",
        "zdnet.com",
    ]

    def __init__(self, search_provider: str = "serper"):
        """Initialize news collector.

        Args:
            search_provider: Search API provider ("serper" or "brave")
        """
        super().__init__(source_name="News", source_type=SourceType.NEWS)
        self.search_client = SearchClient()
        self.search_provider = search_provider

    @retry_with_backoff(max_retries=3, initial_delay=1.0, exceptions=(Exception,))
    async def collect(
        self,
        query: str,
        limit: int = 10,
        filters: dict[str, Any] | None = None,
    ) -> list[CollectedData]:
        """Collect news articles.

        Args:
            query: Search query
            limit: Maximum number of articles to collect
            filters: Additional filters
                - domains: List of domains to include (default: DEFAULT_DOMAINS)
                - date_filter: Date filter for Serper ("d", "w", "m")
                - freshness: Freshness filter for Brave ("pd", "pw", "pm")

        Returns:
            List of collected news articles

        Raises:
            CollectorError: If collection fails
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
        """Build search query with domain filters.

        Args:
            query: Base search query
            domains: List of domains to include

        Returns:
            Enhanced query with domain filters
        """
        if not domains:
            return query

        domain_filter = " OR ".join([f"site:{domain}" for domain in domains])
        return f"{query} ({domain_filter})"

    def _parse_news_result(self, result: dict[str, Any]) -> CollectedData:
        """Parse news search result.

        Args:
            result: Raw search result

        Returns:
            CollectedData instance
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
    """Get list of popular AI/tech news domains.

    Returns:
        List of domain names
    """
    return NewsCollector.DEFAULT_DOMAINS
