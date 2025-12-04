"""CRUD operations for database models."""

from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import and_, desc, func, select
from sqlalchemy.orm import Session

from app.db.models import CollectedArticle, Feedback, SentDigest, User, UserPreference

# ============================================================================
# User CRUD Operations
# ============================================================================


def create_user(db: Session, email: str, name: str | None = None) -> User:
    """Create a new user."""
    user = User(email=email, name=name)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def get_user_by_id(db: Session, user_id: UUID) -> User | None:
    """Get user by ID."""
    return db.get(User, user_id)


def get_user_by_email(db: Session, email: str) -> User | None:
    """Get user by email."""
    stmt = select(User).where(User.email == email)
    return db.scalar(stmt)


def update_user(db: Session, user_id: UUID, **kwargs: Any) -> User | None:
    """Update user information."""
    user = db.get(User, user_id)
    if not user:
        return None

    for key, value in kwargs.items():
        if hasattr(user, key):
            setattr(user, key, value)

    db.commit()
    db.refresh(user)
    return user


def delete_user(db: Session, user_id: UUID) -> bool:
    """Delete a user (cascades to preferences, digests, and feedbacks)."""
    user = db.get(User, user_id)
    if not user:
        return False

    db.delete(user)
    db.commit()
    return True


def list_users(db: Session, skip: int = 0, limit: int = 100) -> list[User]:
    """List all users with pagination."""
    stmt = select(User).offset(skip).limit(limit)
    return list(db.scalars(stmt).all())


# ============================================================================
# UserPreference CRUD Operations
# ============================================================================


def create_user_preference(db: Session, user_id: UUID, **kwargs: Any) -> UserPreference:
    """Create user preferences."""
    preference = UserPreference(user_id=user_id, **kwargs)
    db.add(preference)
    db.commit()
    db.refresh(preference)
    return preference


def get_user_preference(db: Session, user_id: UUID) -> UserPreference | None:
    """Get user preferences by user_id."""
    stmt = select(UserPreference).where(UserPreference.user_id == user_id)
    return db.scalar(stmt)


def update_user_preference(db: Session, user_id: UUID, **kwargs: Any) -> UserPreference | None:
    """Update user preferences."""
    preference = get_user_preference(db, user_id)
    if not preference:
        return None

    for key, value in kwargs.items():
        if hasattr(preference, key):
            setattr(preference, key, value)

    db.commit()
    db.refresh(preference)
    return preference


def delete_user_preference(db: Session, user_id: UUID) -> bool:
    """Delete user preferences."""
    preference = get_user_preference(db, user_id)
    if not preference:
        return False

    db.delete(preference)
    db.commit()
    return True


# ============================================================================
# CollectedArticle CRUD Operations
# ============================================================================


def create_article(db: Session, **kwargs: Any) -> CollectedArticle:
    """Create a new article."""
    article = CollectedArticle(**kwargs)
    db.add(article)
    db.commit()
    db.refresh(article)
    return article


def get_article_by_id(db: Session, article_id: UUID) -> CollectedArticle | None:
    """Get article by ID."""
    return db.get(CollectedArticle, article_id)


def get_article_by_url(db: Session, source_url: str) -> CollectedArticle | None:
    """Get article by source URL."""
    stmt = select(CollectedArticle).where(CollectedArticle.source_url == source_url)
    return db.scalar(stmt)


def update_article(db: Session, article_id: UUID, **kwargs: Any) -> CollectedArticle | None:
    """Update article information."""
    article = db.get(CollectedArticle, article_id)
    if not article:
        return None

    for key, value in kwargs.items():
        if hasattr(article, key):
            setattr(article, key, value)

    db.commit()
    db.refresh(article)
    return article


def delete_article(db: Session, article_id: UUID) -> bool:
    """Delete an article."""
    article = db.get(CollectedArticle, article_id)
    if not article:
        return False

    db.delete(article)
    db.commit()
    return True


def list_articles(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    source_type: str | None = None,
    category: str | None = None,
    min_importance: float | None = None,
) -> list[CollectedArticle]:
    """
    List articles with optional filtering.

    Args:
        db: Database session
        skip: Number of records to skip
        limit: Maximum number of records to return
        source_type: Filter by source type (paper, news, report)
        category: Filter by category
        min_importance: Filter by minimum importance score

    Returns:
        List of articles
    """
    stmt = select(CollectedArticle)

    # Apply filters
    if source_type:
        stmt = stmt.where(CollectedArticle.source_type == source_type)
    if category:
        stmt = stmt.where(CollectedArticle.category == category)
    if min_importance is not None:
        stmt = stmt.where(CollectedArticle.importance_score >= min_importance)

    # Order by collected_at descending
    stmt = stmt.order_by(desc(CollectedArticle.collected_at)).offset(skip).limit(limit)

    return list(db.scalars(stmt).all())


def get_top_articles_by_importance(
    db: Session,
    limit: int = 10,
    source_type: str | None = None,
    since: datetime | None = None,
) -> list[CollectedArticle]:
    """
    Get top articles by importance score.

    Args:
        db: Database session
        limit: Number of articles to return
        source_type: Filter by source type
        since: Only include articles collected after this datetime

    Returns:
        List of top articles
    """
    stmt = select(CollectedArticle).where(CollectedArticle.importance_score.isnot(None))

    if source_type:
        stmt = stmt.where(CollectedArticle.source_type == source_type)
    if since:
        stmt = stmt.where(CollectedArticle.collected_at >= since)

    stmt = stmt.order_by(desc(CollectedArticle.importance_score)).limit(limit)

    return list(db.scalars(stmt).all())


def count_articles(
    db: Session,
    source_type: str | None = None,
    since: datetime | None = None,
) -> int:
    """Count articles with optional filtering."""
    stmt = select(func.count()).select_from(CollectedArticle)

    if source_type:
        stmt = stmt.where(CollectedArticle.source_type == source_type)
    if since:
        stmt = stmt.where(CollectedArticle.collected_at >= since)

    return db.scalar(stmt) or 0


# ============================================================================
# SentDigest CRUD Operations
# ============================================================================


def create_digest(db: Session, user_id: UUID, article_ids: list[str]) -> SentDigest:
    """Create a digest record."""
    digest = SentDigest(user_id=user_id, article_ids=article_ids)
    db.add(digest)
    db.commit()
    db.refresh(digest)
    return digest


def get_digest_by_id(db: Session, digest_id: UUID) -> SentDigest | None:
    """Get digest by ID."""
    return db.get(SentDigest, digest_id)


def update_digest_opened(db: Session, digest_id: UUID, opened_at: datetime) -> SentDigest | None:
    """Mark digest as opened."""
    digest = db.get(SentDigest, digest_id)
    if not digest:
        return None

    digest.email_opened = True
    digest.opened_at = opened_at

    db.commit()
    db.refresh(digest)
    return digest


def list_user_digests(
    db: Session,
    user_id: UUID,
    skip: int = 0,
    limit: int = 100,
) -> list[SentDigest]:
    """List digests for a specific user."""
    stmt = (
        select(SentDigest)
        .where(SentDigest.user_id == user_id)
        .order_by(desc(SentDigest.sent_at))
        .offset(skip)
        .limit(limit)
    )
    return list(db.scalars(stmt).all())


def get_latest_digest(db: Session, user_id: UUID) -> SentDigest | None:
    """Get the most recent digest for a user."""
    stmt = (
        select(SentDigest)
        .where(SentDigest.user_id == user_id)
        .order_by(desc(SentDigest.sent_at))
        .limit(1)
    )
    return db.scalar(stmt)


def delete_digest(db: Session, digest_id: UUID) -> bool:
    """Delete a digest record."""
    digest = db.get(SentDigest, digest_id)
    if not digest:
        return False

    db.delete(digest)
    db.commit()
    return True


# ============================================================================
# Feedback CRUD Operations
# ============================================================================


def create_feedback(
    db: Session,
    user_id: UUID,
    article_id: UUID,
    rating: int | None = None,
    comment: str | None = None,
) -> Feedback:
    """Create user feedback on an article."""
    feedback = Feedback(user_id=user_id, article_id=article_id, rating=rating, comment=comment)
    db.add(feedback)
    db.commit()
    db.refresh(feedback)
    return feedback


def get_feedback_by_id(db: Session, feedback_id: UUID) -> Feedback | None:
    """Get feedback by ID."""
    return db.get(Feedback, feedback_id)


def get_user_feedback_for_article(
    db: Session,
    user_id: UUID,
    article_id: UUID,
) -> Feedback | None:
    """Get user's feedback for a specific article."""
    stmt = select(Feedback).where(
        and_(
            Feedback.user_id == user_id,
            Feedback.article_id == article_id,
        ),
    )
    return db.scalar(stmt)


def update_feedback(db: Session, feedback_id: UUID, **kwargs: Any) -> Feedback | None:
    """Update feedback."""
    feedback = db.get(Feedback, feedback_id)
    if not feedback:
        return None

    for key, value in kwargs.items():
        if hasattr(feedback, key):
            setattr(feedback, key, value)

    db.commit()
    db.refresh(feedback)
    return feedback


def delete_feedback(db: Session, feedback_id: UUID) -> bool:
    """Delete feedback."""
    feedback = db.get(Feedback, feedback_id)
    if not feedback:
        return False

    db.delete(feedback)
    db.commit()
    return True


def list_article_feedbacks(
    db: Session,
    article_id: UUID,
    skip: int = 0,
    limit: int = 100,
) -> list[Feedback]:
    """List all feedbacks for an article."""
    stmt = (
        select(Feedback)
        .where(Feedback.article_id == article_id)
        .order_by(desc(Feedback.created_at))
        .offset(skip)
        .limit(limit)
    )
    return list(db.scalars(stmt).all())


def list_user_feedbacks(
    db: Session,
    user_id: UUID,
    skip: int = 0,
    limit: int = 100,
) -> list[Feedback]:
    """List all feedbacks by a user."""
    stmt = (
        select(Feedback)
        .where(Feedback.user_id == user_id)
        .order_by(desc(Feedback.created_at))
        .offset(skip)
        .limit(limit)
    )
    return list(db.scalars(stmt).all())


def get_article_average_rating(db: Session, article_id: UUID) -> float | None:
    """Get average rating for an article."""
    stmt = select(func.avg(Feedback.rating)).where(
        and_(
            Feedback.article_id == article_id,
            Feedback.rating.isnot(None),
        ),
    )
    result = db.scalar(stmt)
    return float(result) if result is not None else None
