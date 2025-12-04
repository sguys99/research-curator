"""SQLAlchemy database models."""

from datetime import UTC, datetime
from typing import Any

from sqlalchemy import JSON, Boolean, DateTime, Float, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from uuid_extensions import uuid7


def utcnow() -> datetime:
    """Get current UTC time with timezone."""
    return datetime.now(UTC)


class Base(DeclarativeBase):
    """Base class for all database models."""

    pass


class User(Base):
    """User account model."""

    __tablename__ = "users"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid7)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    last_login: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utcnow,
        onupdate=utcnow,
    )

    def __repr__(self) -> str:
        return f"<User(id={self.id}, email={self.email})>"


class UserPreference(Base):
    """User preferences and settings."""

    __tablename__ = "user_preferences"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid7)
    user_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), nullable=False, unique=True, index=True)

    # Research interests
    research_fields: Mapped[list[str]] = mapped_column(JSON, default=list)
    keywords: Mapped[list[str]] = mapped_column(JSON, default=list)

    # Source configuration
    sources: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)

    # Content preferences
    info_types: Mapped[dict[str, int]] = mapped_column(
        JSON,
        default={"paper": 40, "news": 40, "report": 20},
    )

    # Email settings
    email_time: Mapped[str] = mapped_column(String(5), default="08:00")  # HH:MM format
    daily_limit: Mapped[int] = mapped_column(Integer, default=5)
    email_enabled: Mapped[bool] = mapped_column(Boolean, default=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utcnow,
        onupdate=utcnow,
    )

    def __repr__(self) -> str:
        return f"<UserPreference(user_id={self.user_id})>"


class CollectedArticle(Base):
    """Collected research articles, news, and reports."""

    __tablename__ = "collected_articles"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid7)
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=True)
    summary: Mapped[str] = mapped_column(Text, nullable=True)
    source_url: Mapped[str] = mapped_column(String(1024), nullable=False, unique=True)
    source_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )  # paper, news, report
    category: Mapped[str] = mapped_column(String(100), nullable=True, index=True)
    importance_score: Mapped[float] = mapped_column(Float, nullable=True, index=True)

    # Article metadata (authors, publish_date, citations, etc.)
    article_metadata: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)

    # Vector DB reference
    vector_id: Mapped[str] = mapped_column(String(255), nullable=True, unique=True)

    # Timestamps
    collected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)
    published_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)

    def __repr__(self) -> str:
        return f"<CollectedArticle(id={self.id}, title={self.title[:50]})>"


class SentDigest(Base):
    """Email digest sending history."""

    __tablename__ = "sent_digests"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid7)
    user_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)

    # Articles included in this digest
    article_ids: Mapped[list[str]] = mapped_column(JSON, default=list)

    # Email tracking
    sent_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)
    email_opened: Mapped[bool] = mapped_column(Boolean, default=False)
    opened_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)

    def __repr__(self) -> str:
        return f"<SentDigest(id={self.id}, user_id={self.user_id}, sent_at={self.sent_at})>"


class Feedback(Base):
    """User feedback on articles."""

    __tablename__ = "feedback"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid7)
    user_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    article_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)

    # Rating (1-5 stars)
    rating: Mapped[int] = mapped_column(Integer, nullable=True)

    # Optional comment
    comment: Mapped[str] = mapped_column(Text, nullable=True)

    # Timestamp
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    def __repr__(self) -> str:
        return f"<Feedback(id={self.id}, user_id={self.user_id}, rating={self.rating})>"
