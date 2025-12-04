"""Email sending history management."""

import logging
from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import SentDigest

logger = logging.getLogger(__name__)


async def save_sent_digest(
    session: AsyncSession,
    user_id: UUID | str,
    article_ids: list[str],
) -> SentDigest:
    """
    Save email digest sending history to database.

    Args:
        session: Database session
        user_id: User UUID
        article_ids: List of article IDs included in the digest

    Returns:
        SentDigest: Created digest record
    """
    try:
        # Convert user_id to UUID if string
        if isinstance(user_id, str):
            user_id = UUID(user_id)

        # Create digest record
        digest = SentDigest(
            user_id=user_id,
            article_ids=article_ids,
        )

        session.add(digest)
        await session.commit()
        await session.refresh(digest)

        logger.info(f"Saved digest history for user {user_id} with {len(article_ids)} articles")
        return digest

    except Exception as e:
        await session.rollback()
        logger.error(f"Failed to save digest history: {e}")
        raise


async def get_user_digest_history(
    session: AsyncSession,
    user_id: UUID | str,
    limit: int = 10,
) -> list[SentDigest]:
    """
    Get email digest history for a user.

    Args:
        session: Database session
        user_id: User UUID
        limit: Maximum number of records to return

    Returns:
        list[SentDigest]: List of digest records
    """
    try:
        # Convert user_id to UUID if string
        if isinstance(user_id, str):
            user_id = UUID(user_id)

        # Query digest history
        stmt = (
            select(SentDigest)
            .where(SentDigest.user_id == user_id)
            .order_by(SentDigest.sent_at.desc())
            .limit(limit)
        )

        result = await session.execute(stmt)
        digests = result.scalars().all()

        return list(digests)

    except Exception as e:
        logger.error(f"Failed to get digest history: {e}")
        raise


async def mark_email_opened(
    session: AsyncSession,
    digest_id: UUID | str,
    opened_at: datetime | None = None,
) -> SentDigest | None:
    """
    Mark an email as opened.

    Args:
        session: Database session
        digest_id: Digest UUID
        opened_at: Timestamp when email was opened (defaults to now)

    Returns:
        SentDigest | None: Updated digest record or None if not found
    """
    try:
        # Convert digest_id to UUID if string
        if isinstance(digest_id, str):
            digest_id = UUID(digest_id)

        # Get digest
        stmt = select(SentDigest).where(SentDigest.id == digest_id)
        result = await session.execute(stmt)
        digest = result.scalar_one_or_none()

        if not digest:
            logger.warning(f"Digest {digest_id} not found")
            return None

        # Update opened status
        digest.email_opened = True
        digest.opened_at = opened_at or datetime.utcnow()

        await session.commit()
        await session.refresh(digest)

        logger.info(f"Marked digest {digest_id} as opened")
        return digest

    except Exception as e:
        await session.rollback()
        logger.error(f"Failed to mark email as opened: {e}")
        raise


async def get_digest_stats(session: AsyncSession, user_id: UUID | str) -> dict[str, Any]:
    """
    Get email digest statistics for a user.

    Args:
        session: Database session
        user_id: User UUID

    Returns:
        dict: Statistics including total_sent, total_opened, open_rate
    """
    try:
        # Convert user_id to UUID if string
        if isinstance(user_id, str):
            user_id = UUID(user_id)

        # Get all digests for user
        stmt = select(SentDigest).where(SentDigest.user_id == user_id)
        result = await session.execute(stmt)
        digests = result.scalars().all()

        total_sent = len(digests)
        total_opened = sum(1 for d in digests if d.email_opened)
        open_rate = (total_opened / total_sent * 100) if total_sent > 0 else 0

        return {
            "total_sent": total_sent,
            "total_opened": total_opened,
            "open_rate": round(open_rate, 2),
        }

    except Exception as e:
        logger.error(f"Failed to get digest stats: {e}")
        raise
