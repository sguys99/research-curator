"""데이터 수집 모듈을 위한 기본 수집기 인터페이스."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any


class SourceType(str, Enum):
    """콘텐츠 소스 유형."""

    PAPER = "paper"
    NEWS = "news"
    REPORT = "report"
    BLOG = "blog"
    OTHER = "other"


@dataclass
class CollectedData:
    """수집된 콘텐츠의 표준 데이터 구조."""

    title: str
    content: str
    url: str
    source_type: SourceType
    source_name: str
    metadata: dict[str, Any] = field(default_factory=dict)
    collected_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def to_dict(self) -> dict[str, Any]:
        """딕셔너리로 변환한다."""
        return {
            "title": self.title,
            "content": self.content,
            "url": self.url,
            "source_type": self.source_type.value,
            "source_name": self.source_name,
            "metadata": self.metadata,
            "collected_at": self.collected_at.isoformat(),
        }


class BaseCollector(ABC):
    """모든 수집기의 추상 베이스 클래스."""

    def __init__(self, source_name: str, source_type: SourceType) -> None:
        """수집기를 초기화한다.

        Args:
            source_name: 소스 이름(예: "arXiv", "TechCrunch")
            source_type: 소스 유형(paper, news 등)
        """
        self.source_name = source_name
        self.source_type = source_type

    @abstractmethod
    async def collect(
        self,
        query: str,
        limit: int = 10,
        filters: dict[str, Any] | None = None,
    ) -> list[CollectedData]:
        """소스에서 데이터를 수집한다.

        Args:
            query: 검색 쿼리 또는 키워드
            limit: 수집할 최대 항목 수
            filters: 추가 필터(기간, 카테고리 등)

        Returns:
            수집된 데이터 항목 목록

        Raises:
            CollectorError: 수집 실패 시
        """
        pass

    def _create_collected_data(
        self,
        title: str,
        content: str,
        url: str,
        metadata: dict[str, Any] | None = None,
    ) -> CollectedData:
        """CollectedData 인스턴스를 생성하는 헬퍼 메서드.

        Args:
            title: 콘텐츠 제목
            content: 본문 또는 요약
            url: 소스 URL
            metadata: 추가 메타데이터

        Returns:
            CollectedData 인스턴스
        """
        return CollectedData(
            title=title,
            content=content,
            url=url,
            source_type=self.source_type,
            source_name=self.source_name,
            metadata=metadata or {},
        )


class CollectorError(Exception):
    """수집기 에러의 기본 예외."""

    pass


class RateLimitError(CollectorError):
    """레이트 리밋을 초과했을 때 발생."""

    pass


class APIError(CollectorError):
    """API 호출 실패 시 발생."""

    pass
