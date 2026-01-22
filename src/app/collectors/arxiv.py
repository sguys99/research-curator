"""공식 arXiv API를 사용한 논문 수집기."""

import logging
from typing import Any

import arxiv

from app.collectors.base import BaseCollector, CollectedData, CollectorError, SourceType
from app.core.retry import retry_with_backoff

logger = logging.getLogger(__name__)


class ArxivCollector(BaseCollector):
    """arXiv 논문 수집기."""

    def __init__(self):
        """arXiv 수집기를 초기화한다."""
        super().__init__(source_name="arXiv", source_type=SourceType.PAPER)
        self.client = arxiv.Client()

    @retry_with_backoff(max_retries=3, initial_delay=1.0, exceptions=(CollectorError,))
    async def collect(
        self,
        query: str,
        limit: int = 10,
        filters: dict[str, Any] | None = None,
    ) -> list[CollectedData]:
        """arXiv에서 논문을 수집한다.

        Args:
            query: 검색 쿼리(arXiv 쿼리 문법 지원)
            limit: 수집할 최대 논문 수
            filters: 추가 필터
                - sort_by: 정렬 기준(relevance, lastUpdatedDate, submittedDate)
                - sort_order: 정렬 순서(ascending, descending)
                - categories: arXiv 카테고리 목록(예: ["cs.AI", "cs.LG"])

        Returns:
            수집된 논문 목록

        Raises:
            CollectorError: 수집 실패 시
        """
        try:
            filters = filters or {}

            sort_by_map = {
                "relevance": arxiv.SortCriterion.Relevance,
                "last_updated": arxiv.SortCriterion.LastUpdatedDate,
                "submitted": arxiv.SortCriterion.SubmittedDate,
            }

            sort_order_map = {
                "ascending": arxiv.SortOrder.Ascending,
                "descending": arxiv.SortOrder.Descending,
            }

            sort_by = sort_by_map.get(
                filters.get("sort_by", "relevance"),
                arxiv.SortCriterion.Relevance,
            )
            sort_order = sort_order_map.get(
                filters.get("sort_order", "descending"),
                arxiv.SortOrder.Descending,
            )

            search_query = query
            if "categories" in filters and filters["categories"]:
                categories = filters["categories"]
                category_query = " OR ".join([f"cat:{cat}" for cat in categories])
                search_query = f"({query}) AND ({category_query})"

            search = arxiv.Search(
                query=search_query,
                max_results=limit,
                sort_by=sort_by,
                sort_order=sort_order,
            )

            results = []
            for paper in self.client.results(search):
                collected_data = self._parse_paper(paper)
                results.append(collected_data)

            logger.info(f"ArxivCollector: Collected {len(results)} papers for query '{query}'")

            return results

        except Exception as e:
            logger.error(f"ArxivCollector error: {str(e)}")
            raise CollectorError(f"Failed to collect from arXiv: {str(e)}") from e

    def _parse_paper(self, paper: arxiv.Result) -> CollectedData:
        """arXiv 논문 결과를 파싱한다.

        Args:
            paper: arXiv Result 객체

        Returns:
            CollectedData 인스턴스
        """
        authors = [author.name for author in paper.authors]

        primary_category = paper.primary_category
        categories = paper.categories

        metadata = {
            "arxiv_id": paper.entry_id.split("/")[-1],
            "authors": authors,
            "primary_category": primary_category,
            "categories": categories,
            "published": paper.published.isoformat() if paper.published else None,
            "updated": paper.updated.isoformat() if paper.updated else None,
            "pdf_url": paper.pdf_url,
            "comment": paper.comment,
            "journal_ref": paper.journal_ref,
            "doi": paper.doi,
        }

        content = paper.summary.strip()

        return self._create_collected_data(
            title=paper.title.strip(),
            content=content,
            url=paper.entry_id,
            metadata=metadata,
        )


def get_popular_ai_categories() -> list[str]:
    """인기 있는 AI 관련 arXiv 카테고리 목록을 반환한다.

    Returns:
        카테고리 코드 목록
    """
    return [
        "cs.AI",
        "cs.LG",
        "cs.CL",
        "cs.CV",
        "cs.NE",
        "cs.RO",
        "stat.ML",
    ]
