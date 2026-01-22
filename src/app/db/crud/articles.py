"""CRUD operations for articles."""

from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from sqlalchemy import and_, desc, func, or_, select
from sqlalchemy.orm import Session

from app.db.models import CollectedArticle


def _commit_or_rollback(db: Session) -> None:
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise


def get_articles(
    db: Session,
    skip: int = 0,
    limit: int = 20,
    source_type: list[str] | None = None,
    category: list[str] | None = None,
    min_importance_score: float | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    order_by: str = "collected_at",
    order_desc: bool = True,
) -> tuple[list[CollectedArticle], int]:
    """
    Get list of articles with filtering, sorting, and pagination.

    Args:
        db: Database session
        skip: Number of records to skip
        limit: Maximum number of records to return
        source_type: Filter by source type (paper/news/report)
        category: Filter by category
        min_importance_score: Minimum importance score
        date_from: Filter articles from this date
        date_to: Filter articles until this date
        order_by: Field to order by (collected_at, importance_score)
        order_desc: Order descending if True

    Returns:
        Tuple of (articles list, total count)
    """
    # Apply filters
    filters = []
    if source_type:
        filters.append(CollectedArticle.source_type.in_(source_type))
    if category:
        filters.append(CollectedArticle.category.in_(category))
    if min_importance_score is not None:
        filters.append(CollectedArticle.importance_score >= min_importance_score)
    if date_from:
        filters.append(CollectedArticle.collected_at >= date_from)
    if date_to:
        filters.append(CollectedArticle.collected_at <= date_to)

    count_stmt = select(func.count()).select_from(CollectedArticle)
    if filters:
        count_stmt = count_stmt.where(and_(*filters))
    total = db.scalar(count_stmt) or 0

    stmt = select(CollectedArticle)
    if filters:
        stmt = stmt.where(and_(*filters))

    # Apply ordering
    if order_by == "importance_score":
        order_field = CollectedArticle.importance_score
    else:
        order_field = CollectedArticle.collected_at

    if order_desc:
        stmt = stmt.order_by(desc(order_field))
    else:
        stmt = stmt.order_by(order_field)

    # Apply pagination
    stmt = stmt.offset(skip).limit(limit)
    articles = list(db.scalars(stmt).all())

    return articles, total


def get_article_by_id(db: Session, article_id: UUID) -> CollectedArticle | None:
    """
    Get article by ID.

    Args:
        db: Database session
        article_id: Article UUID

    Returns:
        CollectedArticle object or None if not found
    """
    stmt = select(CollectedArticle).where(CollectedArticle.id == article_id)
    return db.scalar(stmt)


def get_article_by_url(db: Session, source_url: str) -> CollectedArticle | None:
    """
    Get article by source URL (for duplicate detection).

    Args:
        db: Database session
        source_url: Source URL

    Returns:
        CollectedArticle object or None if not found
    """
    stmt = select(CollectedArticle).where(CollectedArticle.source_url == source_url)
    return db.scalar(stmt)


def get_articles_by_ids(
    db: Session,
    article_ids: list[UUID],
) -> list[CollectedArticle]:
    """
    Get multiple articles by IDs (batch retrieval).

    Args:
        db: Database session
        article_ids: List of article UUIDs

    Returns:
        List of CollectedArticle objects
    """
    stmt = select(CollectedArticle).where(CollectedArticle.id.in_(article_ids))
    return list(db.scalars(stmt).all())


def create_article(
    db: Session,
    title: str,
    content: str,
    summary: str,
    source_url: str,
    source_type: str,
    category: str,
    importance_score: float,
    metadata: dict[str, Any] | None = None,
    vector_id: str | None = None,
) -> CollectedArticle:
    """
    Create a new article.

    Args:
        db: Database session
        title: Article title
        content: Article content
        summary: Article summary
        source_url: Source URL (must be unique)
        source_type: Source type (paper/news/report)
        category: Category
        importance_score: Importance score (0.0-1.0)
        metadata: Additional metadata
        vector_id: Qdrant vector ID (optional)

    Returns:
        Created CollectedArticle object
    """
    article = CollectedArticle(
        title=title,
        content=content,
        summary=summary,
        source_url=source_url,
        source_type=source_type,
        category=category,
        importance_score=importance_score,
        metadata=metadata or {},
        vector_id=vector_id,
        collected_at=datetime.now(UTC),
    )
    db.add(article)
    _commit_or_rollback(db)
    db.refresh(article)
    return article


def update_article(
    db: Session,
    article_id: UUID,
    title: str | None = None,
    content: str | None = None,
    summary: str | None = None,
    category: str | None = None,
    importance_score: float | None = None,
    metadata: dict[str, Any] | None = None,
    vector_id: str | None = None,
) -> CollectedArticle | None:
    """
    Update article fields.

    Args:
        db: Database session
        article_id: Article UUID
        title: New title (optional)
        content: New content (optional)
        summary: New summary (optional)
        category: New category (optional)
        importance_score: New importance score (optional)
        metadata: New metadata (optional)
        vector_id: New vector ID (optional)

    Returns:
        Updated CollectedArticle object or None if not found
    """
    article = get_article_by_id(db, article_id)
    if not article:
        return None

    if title is not None:
        article.title = title
    if content is not None:
        article.content = content
    if summary is not None:
        article.summary = summary
    if category is not None:
        article.category = category
    if importance_score is not None:
        article.importance_score = importance_score
    if metadata is not None:
        article.metadata = metadata
    if vector_id is not None:
        article.vector_id = vector_id

    _commit_or_rollback(db)
    db.refresh(article)
    return article


def delete_article(db: Session, article_id: UUID) -> bool:
    """
    Delete article.

    Args:
        db: Database session
        article_id: Article UUID

    Returns:
        True if deleted, False if not found
    """
    article = get_article_by_id(db, article_id)
    if not article:
        return False

    db.delete(article)
    _commit_or_rollback(db)
    return True


def get_article_statistics(
    db: Session,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
) -> dict[str, Any]:
    """
    Get article statistics (counts by category, source type, etc.).

    Args:
        db: Database session
        date_from: Filter from this date (optional)
        date_to: Filter until this date (optional)

    Returns:
        Dictionary with statistics
    """
    filters = []
    if date_from:
        filters.append(CollectedArticle.collected_at >= date_from)
    if date_to:
        filters.append(CollectedArticle.collected_at <= date_to)

    total_stmt = select(func.count()).select_from(CollectedArticle)
    if filters:
        total_stmt = total_stmt.where(and_(*filters))
    total = db.scalar(total_stmt) or 0

    source_type_stmt = select(
        CollectedArticle.source_type,
        func.count(CollectedArticle.id).label("count"),
    ).select_from(CollectedArticle)
    category_stmt = select(
        CollectedArticle.category,
        func.count(CollectedArticle.id).label("count"),
    ).select_from(CollectedArticle)
    avg_score_stmt = select(func.avg(CollectedArticle.importance_score)).select_from(CollectedArticle)

    if filters:
        source_type_stmt = source_type_stmt.where(and_(*filters))
        category_stmt = category_stmt.where(and_(*filters))
        avg_score_stmt = avg_score_stmt.where(and_(*filters))

    source_type_counts = db.execute(
        source_type_stmt.group_by(CollectedArticle.source_type),
    ).all()
    category_counts = db.execute(
        category_stmt.group_by(CollectedArticle.category),
    ).all()
    avg_score = db.scalar(avg_score_stmt)

    return {
        "total": total,
        "by_source_type": dict(source_type_counts),
        "by_category": dict(category_counts),
        "average_importance_score": float(avg_score) if avg_score else 0.0,
    }


def search_articles(
    db: Session,
    search_query: str,
    skip: int = 0,
    limit: int = 20,
) -> tuple[list[CollectedArticle], int]:
    """
    Search articles by keyword in title, content, or summary.

    Note: For semantic search, use Vector DB operations instead.
    This is a simple keyword-based search.

    Args:
        db: Database session
        search_query: Search query string
        skip: Number of records to skip
        limit: Maximum number of records to return

    Returns:
        Tuple of (articles list, total count)
    """
    search_pattern = f"%{search_query}%"
    search_condition = or_(
        CollectedArticle.title.ilike(search_pattern),
        CollectedArticle.summary.ilike(search_pattern),
        CollectedArticle.content.ilike(search_pattern),
    )
    total_stmt = select(func.count()).select_from(CollectedArticle).where(search_condition)
    total = db.scalar(total_stmt) or 0
    stmt = (
        select(CollectedArticle)
        .where(search_condition)
        .order_by(desc(CollectedArticle.importance_score))
        .offset(skip)
        .limit(limit)
    )
    articles = list(db.scalars(stmt).all())

    return articles, total


def list_articles(
    db: Session,
    skip: int = 0,
    limit: int = 20,
    source_type: str | None = None,
    category: str | None = None,
    min_importance: float | None = None,
) -> list[CollectedArticle]:
    """
    List articles with filtering (simplified version of get_articles).

    Args:
        db: Database session
        skip: Number of records to skip
        limit: Maximum number of records to return
        source_type: Filter by source type (optional)
        category: Filter by category (optional)
        min_importance: Minimum importance score (optional)

    Returns:
        List of CollectedArticle objects
    """
    stmt = select(CollectedArticle)

    # Apply filters
    if source_type:
        stmt = stmt.where(CollectedArticle.source_type == source_type)
    if category:
        stmt = stmt.where(CollectedArticle.category == category)
    if min_importance is not None:
        stmt = stmt.where(CollectedArticle.importance_score >= min_importance)

    # Order by collection date (newest first)
    stmt = stmt.order_by(desc(CollectedArticle.collected_at))

    # Apply pagination
    stmt = stmt.offset(skip).limit(limit)
    return list(db.scalars(stmt).all())


def count_articles(
    db: Session,
    source_type: str | None = None,
) -> int:
    """
    Count total articles with optional filtering.

    Args:
        db: Database session
        source_type: Filter by source type (optional)

    Returns:
        Total count of articles
    """
    stmt = select(func.count()).select_from(CollectedArticle)
    if source_type:
        stmt = stmt.where(CollectedArticle.source_type == source_type)
    return db.scalar(stmt) or 0


def get_articles_since(
    db: Session,
    since: datetime,
) -> list[CollectedArticle]:
    """
    Get all articles collected after a specific datetime.

    Args:
        db: Database session
        since: Start datetime

    Returns:
        List of articles ordered by importance score
    """
    stmt = (
        select(CollectedArticle)
        .where(CollectedArticle.collected_at >= since)
        .order_by(desc(CollectedArticle.importance_score))
    )
    return list(db.scalars(stmt).all())


def get_top_articles_by_importance(
    db: Session,
    limit: int = 10,
    since: datetime | None = None,
) -> list[CollectedArticle]:
    """
    Get top N articles ordered by importance score.

    Args:
        db: Database session
        limit: Maximum number of articles to return
        since: Filter articles collected after this datetime (optional)

    Returns:
        List of top-rated articles
    """
    stmt = select(CollectedArticle)
    if since:
        stmt = stmt.where(CollectedArticle.collected_at >= since)
    stmt = stmt.order_by(desc(CollectedArticle.importance_score)).limit(limit)
    return list(db.scalars(stmt).all())
