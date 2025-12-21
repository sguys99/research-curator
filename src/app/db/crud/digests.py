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


def get_digest_by_id(db: Session, digest_id: UUID) -> SentDigest | None:
    """
    Get digest by ID.

    Args:
        db: Database session
        digest_id: Digest UUID

    Returns:
        SentDigest object or None if not found
    """
    return db.query(SentDigest).filter(SentDigest.id == digest_id).first()


def update_digest_opened(
    db: Session,
    digest_id: UUID,
    opened_at,
) -> SentDigest | None:
    """
    Mark digest as opened and record timestamp.

    Args:
        db: Database session
        digest_id: Digest UUID
        opened_at: Timestamp when digest was opened

    Returns:
        Updated SentDigest object or None if not found
    """
    digest = get_digest_by_id(db, digest_id)
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
    limit: int = 10,
) -> list[SentDigest]:
    """
    List user's digests (simplified version of get_user_digests).

    Args:
        db: Database session
        user_id: User UUID
        skip: Number of records to skip
        limit: Maximum number of records to return

    Returns:
        List of SentDigest objects
    """
    return (
        db.query(SentDigest)
        .filter(SentDigest.user_id == user_id)
        .order_by(SentDigest.sent_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
