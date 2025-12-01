"""Base collector interface for all data collection modules."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class SourceType(str, Enum):
    """Types of content sources."""

    PAPER = "paper"
    NEWS = "news"
    REPORT = "report"
    BLOG = "blog"
    OTHER = "other"


@dataclass
class CollectedData:
    """Standard data structure for collected content."""

    title: str
    content: str
    url: str
    source_type: SourceType
    source_name: str
    metadata: dict[str, Any] = field(default_factory=dict)
    collected_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
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
    """Abstract base class for all collectors."""

    def __init__(self, source_name: str, source_type: SourceType):
        """Initialize the collector.

        Args:
            source_name: Name of the source (e.g., "arXiv", "TechCrunch")
            source_type: Type of source (paper, news, etc.)
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
        """Collect data from the source.

        Args:
            query: Search query or keywords
            limit: Maximum number of items to collect
            filters: Additional filters (date range, categories, etc.)

        Returns:
            List of collected data items

        Raises:
            CollectorError: If collection fails
        """
        pass

    def _create_collected_data(
        self,
        title: str,
        content: str,
        url: str,
        metadata: dict[str, Any] | None = None,
    ) -> CollectedData:
        """Helper method to create CollectedData instance.

        Args:
            title: Content title
            content: Main content or summary
            url: Source URL
            metadata: Additional metadata

        Returns:
            CollectedData instance
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
    """Base exception for collector errors."""

    pass


class RateLimitError(CollectorError):
    """Raised when rate limit is exceeded."""

    pass


class APIError(CollectorError):
    """Raised when API call fails."""

    pass
