"""Serper/Brave 검색 API 클라이언트."""

import logging
from typing import Any

import httpx

from app.collectors.base import APIError, RateLimitError
from app.core.config import settings
from app.core.retry import RateLimiter, retry_with_backoff

logger = logging.getLogger(__name__)


class SearchClient:
    """Serper와 Brave 검색 API를 통합하는 클라이언트."""

    def __init__(self):
        """검색 클라이언트를 초기화한다."""
        self.serper_api_key = settings.SERPER_API_KEY
        self.brave_api_key = settings.BRAVE_API_KEY
        self.rate_limiter = RateLimiter(max_calls=10, time_window=60.0)

    @retry_with_backoff(
        max_retries=3,
        initial_delay=1.0,
        exceptions=(httpx.HTTPError, APIError, RateLimitError),
    )
    async def serper_search(
        self,
        query: str,
        num_results: int = 10,
        search_type: str = "search",
        date_filter: str | None = None,
    ) -> list[dict[str, Any]]:
        """Serper API로 검색한다.

        Args:
            query: 검색 쿼리
            num_results: 반환할 결과 수
            search_type: 검색 유형(search, news, scholar)
            date_filter: 날짜 필터(예: "d"=일, "w"=주, "m"=월)

        Returns:
            검색 결과 목록

        Raises:
            APIError: API 호출 실패 시
            RateLimitError: 레이트 리밋 초과 시
        """
        if not self.serper_api_key:
            raise APIError("Serper API key not configured")

        await self.rate_limiter.acquire()

        url = f"https://google.serper.dev/{search_type}"
        headers = {
            "X-API-KEY": self.serper_api_key,
            "Content-Type": "application/json",
        }

        payload: dict[str, Any] = {
            "q": query,
            "num": num_results,
        }

        if date_filter:
            payload["tbs"] = f"qdr:{date_filter}"

        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.post(url, json=payload, headers=headers)
                response.raise_for_status()
                data = response.json()

                logger.info(
                    f"Serper search successful: query='{query}', results={len(data.get('organic', []))}",
                )

                return self._parse_serper_results(data, search_type)

            except httpx.HTTPStatusError as e:
                if e.response.status_code == 429:
                    raise RateLimitError("Serper API rate limit exceeded") from e
                elif e.response.status_code == 401:
                    raise APIError("Invalid Serper API key") from e
                else:
                    raise APIError(f"Serper API error: {e.response.status_code}") from e
            except httpx.HTTPError as e:
                raise APIError(f"HTTP error during Serper search: {str(e)}") from e

    def _parse_serper_results(
        self,
        data: dict[str, Any],
        search_type: str,
    ) -> list[dict[str, Any]]:
        """Serper API 응답을 파싱한다.

        Args:
            data: 원본 API 응답
            search_type: 수행한 검색 유형

        Returns:
            파싱된 결과 목록
        """
        results = []

        if search_type == "news":
            raw_results = data.get("news", [])
        elif search_type == "scholar":
            raw_results = data.get("organic", [])
        else:
            raw_results = data.get("organic", [])

        for item in raw_results:
            result = {
                "title": item.get("title", ""),
                "snippet": item.get("snippet", ""),
                "link": item.get("link", ""),
                "date": item.get("date"),
                "source": item.get("source"),
            }

            if search_type == "scholar":
                result.update(
                    {
                        "publication": item.get("publication"),
                        "cited_by": item.get("inline_links", {}).get("cited_by"),
                        "year": item.get("year"),
                    },
                )

            results.append(result)

        return results

    @retry_with_backoff(
        max_retries=3,
        initial_delay=1.0,
        exceptions=(httpx.HTTPError, APIError, RateLimitError),
    )
    async def brave_search(
        self,
        query: str,
        num_results: int = 10,
        search_type: str = "web",
        freshness: str | None = None,
    ) -> list[dict[str, Any]]:
        """Brave Search API로 검색한다.

        Args:
            query: 검색 쿼리
            num_results: 반환할 결과 수
            search_type: 검색 유형(web, news)
            freshness: 신선도 필터(예: "pd"=하루, "pw"=1주)

        Returns:
            검색 결과 목록

        Raises:
            APIError: API 호출 실패 시
            RateLimitError: 레이트 리밋 초과 시
        """
        if not self.brave_api_key:
            raise APIError("Brave API key not configured")

        await self.rate_limiter.acquire()

        url = "https://api.search.brave.com/res/v1/web/search"
        headers = {
            "X-Subscription-Token": self.brave_api_key,
            "Accept": "application/json",
        }

        params: dict[str, Any] = {
            "q": query,
            "count": num_results,
        }

        if freshness:
            params["freshness"] = freshness

        if search_type == "news":
            params["search_lang"] = "en"
            params["result_filter"] = "news"

        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.get(url, params=params, headers=headers)
                response.raise_for_status()
                data = response.json()

                results_count = len(data.get("web", {}).get("results", []))
                logger.info(f"Brave search successful: query='{query}', results={results_count}")

                return self._parse_brave_results(data)

            except httpx.HTTPStatusError as e:
                if e.response.status_code == 429:
                    raise RateLimitError("Brave API rate limit exceeded") from e
                elif e.response.status_code == 401:
                    raise APIError("Invalid Brave API key") from e
                else:
                    raise APIError(f"Brave API error: {e.response.status_code}") from e
            except httpx.HTTPError as e:
                raise APIError(f"HTTP error during Brave search: {str(e)}") from e

    def _parse_brave_results(self, data: dict[str, Any]) -> list[dict[str, Any]]:
        """Brave API 응답을 파싱한다.

        Args:
            data: 원본 API 응답

        Returns:
            파싱된 결과 목록
        """
        results = []
        raw_results = data.get("web", {}).get("results", [])

        for item in raw_results:
            result = {
                "title": item.get("title", ""),
                "snippet": item.get("description", ""),
                "link": item.get("url", ""),
                "date": item.get("age"),
                "source": item.get("profile", {}).get("name"),
            }
            results.append(result)

        return results

    async def search(
        self,
        query: str,
        num_results: int = 10,
        provider: str = "serper",
        **kwargs: Any,
    ) -> list[dict[str, Any]]:
        """통합 검색 메서드.

        Args:
            query: 검색 쿼리
            num_results: 결과 수
            provider: 검색 제공자("serper" 또는 "brave")
            **kwargs: 제공자별 추가 인자

        Returns:
            검색 결과 목록

        Raises:
            ValueError: 제공자가 유효하지 않은 경우
            APIError: 검색 실패 시
        """
        if provider == "serper":
            return await self.serper_search(query, num_results, **kwargs)
        elif provider == "brave":
            return await self.brave_search(query, num_results, **kwargs)
        else:
            raise ValueError(f"Invalid search provider: {provider}")
