"""이메일 발송 히스토리 관리."""

import logging
from datetime import UTC, datetime
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
    다이제스트 발송 히스토리를 DB에 저장한다.

    Args:
        session: DB 세션
        user_id: 사용자 UUID
        article_ids: 다이제스트에 포함된 아티클 ID 목록

    Returns:
        SentDigest: 생성된 다이제스트 기록
    """
    try:
        # 문자열이면 UUID로 변환
        if isinstance(user_id, str):
            user_id = UUID(user_id)

        # 다이제스트 레코드 생성
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
    사용자별 이메일 다이제스트 히스토리를 조회한다.

    Args:
        session: DB 세션
        user_id: 사용자 UUID
        limit: 반환할 최대 개수

    Returns:
        list[SentDigest]: 다이제스트 기록 목록
    """
    try:
        # 문자열이면 UUID로 변환
        if isinstance(user_id, str):
            user_id = UUID(user_id)

        # 히스토리 조회
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
    이메일 오픈 상태를 표시한다.

    Args:
        session: DB 세션
        digest_id: 다이제스트 UUID
        opened_at: 오픈 시각(기본값: 현재 시각)

    Returns:
        SentDigest | None: 업데이트된 레코드(없으면 None)
    """
    try:
        # 문자열이면 UUID로 변환
        if isinstance(digest_id, str):
            digest_id = UUID(digest_id)

        # 다이제스트 조회
        stmt = select(SentDigest).where(SentDigest.id == digest_id)
        result = await session.execute(stmt)
        digest = result.scalar_one_or_none()

        if not digest:
            logger.warning(f"Digest {digest_id} not found")
            return None

        # 오픈 상태 업데이트
        digest.email_opened = True
        digest.opened_at = opened_at or datetime.now(UTC)

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
    사용자별 이메일 다이제스트 통계를 반환한다.

    Args:
        session: DB 세션
        user_id: 사용자 UUID

    Returns:
        dict: total_sent, total_opened, open_rate 통계
    """
    try:
        # 문자열이면 UUID로 변환
        if isinstance(user_id, str):
            user_id = UUID(user_id)

        # 사용자 전체 다이제스트 조회
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
