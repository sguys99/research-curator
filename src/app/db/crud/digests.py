"""CRUD operations for sent digests."""

from uuid import UUID

from sqlalchemy.orm import Session

from app.db.models import SentDigest


def get_user_digests(
    db: Session,
    user_id: UUID,
    skip: int = 0,
    limit: int = 10,
) -> tuple[list[SentDigest], int]:
    """
    Get user's digest history with pagination.

    Args:
        db: Database session
        user_id: User UUID
        skip: Number of records to skip
        limit: Maximum number of records to return

    Returns:
        Tuple of (list of digests, total count)
    """
    query = db.query(SentDigest).filter(SentDigest.user_id == user_id)

    total = query.count()
    digests = query.order_by(SentDigest.sent_at.desc()).offset(skip).limit(limit).all()

    return digests, total


def get_latest_digest(db: Session, user_id: UUID) -> SentDigest | None:
    """
    Get user's most recent digest.

    Args:
        db: Database session
        user_id: User UUID

    Returns:
        Latest SentDigest object or None if no digests found
    """
    return (
        db.query(SentDigest)
        .filter(SentDigest.user_id == user_id)
        .order_by(SentDigest.sent_at.desc())
        .first()
    )


def create_digest(
    db: Session,
    user_id: UUID,
    article_ids: list[str],
) -> SentDigest:
    """
    Create a new digest record.

    Args:
        db: Database session
        user_id: User UUID
        article_ids: List of article IDs included in digest

    Returns:
        Created SentDigest object
    """
    digest = SentDigest(user_id=user_id, article_ids=article_ids)
    db.add(digest)
    db.commit()
    db.refresh(digest)
    return digest
