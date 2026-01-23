"""일일 다이제스트 오케스트레이션(빌더/발송/히스토리 통합)."""

import logging
from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import CollectedArticle, User, UserPreference
from app.email.builder import EmailBuilder
from app.email.history import save_sent_digest
from app.email.sender import EmailSender

logger = logging.getLogger(__name__)


# 빌더/발송/히스토리를 통합해 실제 이메일 발송 워크플로우 관리
class DigestOrchestrator:
    """일일 다이제스트 워크플로우를 오케스트레이션한다."""

    def __init__(self, email_sender: EmailSender | None = None):
        """
        다이제스트 오케스트레이터를 초기화한다.

        Args:
            email_sender: 커스텀 이메일 발송기(기본값: 새 인스턴스)
        """
        self.builder = EmailBuilder()
        self.sender = email_sender or EmailSender()

    # 단일 사용자 다이제스트 발송
    async def send_user_digest(
        self,
        session: AsyncSession,
        user_id: UUID | str,
        articles: list[CollectedArticle],
        subject: str | None = None,
    ) -> dict[str, Any]:
        """
        단일 사용자에게 일일 다이제스트 이메일을 발송한다.

        Args:
            session: DB 세션
            user_id: 사용자 UUID
            articles: 수집된 아티클 목록
            subject: 커스텀 제목(기본값: 날짜 기반)

        Returns:
            dict: 성공 여부와 digest_id를 포함한 결과

        Raises:
            ValueError: 사용자가 없거나 선호도가 없는 경우
        """
        try:
            # 문자열이면 UUID로 변환
            if isinstance(user_id, str):
                user_id = UUID(user_id)

            # 사용자 및 선호도 로드(1단계)
            user = await self._load_user(session, user_id)
            if not user:
                raise ValueError(f"User {user_id} not found")

            preferences = await self._load_user_preferences(session, user_id)
            if not preferences:
                raise ValueError(f"User {user_id} has no preferences")

            # 선호도에서 일일 제한 수 확인
            daily_limit = preferences.daily_limit or 5

            # 이메일 콘텐츠 생성(2단계)
            html_content = self.builder.build_daily_digest(
                user_name=user.name,
                user_email=user.email,
                articles=articles,
                daily_limit=daily_limit,
            )

            # 제목 생성(3단계)
            if not subject:
                date_str = datetime.now().strftime("%Y년 %m월 %d일")
                subject = f"🔬 Research Curator - {date_str} AI 연구 동향"

            # 이메일 발송(4단계)
            await self.sender.send_email(
                to_email=user.email,
                subject=subject,
                html_content=html_content,
            )

            # 다이제스트 히스토리 저장
            article_ids = [str(article.id) for article in articles[:daily_limit]]
            digest = await save_sent_digest(session, user_id, article_ids)

            logger.info(f"Successfully sent digest to user {user_id}")

            return {
                "success": True,
                "user_id": str(user_id),
                "user_email": user.email,
                "digest_id": str(digest.id),
                "article_count": len(article_ids),
            }

        except Exception as e:
            logger.error(f"Failed to send digest to user {user_id}: {e}")
            return {
                "success": False,
                "user_id": str(user_id),
                "error": str(e),
            }

    async def send_batch_digests(
        self,
        session: AsyncSession,
        user_articles: dict[UUID | str, list[CollectedArticle]],
        max_failures: int = 5,
    ) -> dict[str, Any]:
        """
        여러 사용자에게 일일 다이제스트를 발송한다.

        Args:
            session: DB 세션
            user_articles: user_id -> 아티클 목록 매핑
            max_failures: 중단 전 허용 실패 횟수

        Returns:
            dict: 성공/실패 개수와 결과 요약
        """
        success_count = 0
        failure_count = 0
        results = []

        for user_id, articles in user_articles.items():
            if failure_count >= max_failures:
                logger.warning(f"Stopping batch digest send: reached max failures ({max_failures})")
                break

            result = await self.send_user_digest(session, user_id, articles)
            results.append(result)

            if result["success"]:
                success_count += 1
            else:
                failure_count += 1

        logger.info(f"Batch digest send complete: {success_count} succeeded, {failure_count} failed")

        return {
            "success_count": success_count,
            "failure_count": failure_count,
            "results": results,
        }

    async def _load_user(self, session: AsyncSession, user_id: UUID) -> User | None:
        """DB에서 사용자를 로드한다."""
        stmt = select(User).where(User.id == user_id)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    async def _load_user_preferences(
        self,
        session: AsyncSession,
        user_id: UUID,
    ) -> UserPreference | None:
        """DB에서 사용자 선호도를 로드한다."""
        stmt = select(UserPreference).where(UserPreference.user_id == user_id)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()


# 간단한 케이스에서 오케스트레이터 인스턴스 없이 바로 사용
async def send_daily_digest(
    session: AsyncSession,
    user_id: UUID | str,
    articles: list[CollectedArticle],
    subject: str | None = None,
) -> dict[str, Any]:
    """
    단일 사용자 다이제스트 발송용 편의 함수.

    Args:
        session: DB 세션
        user_id: 사용자 UUID
        articles: 수집된 아티클 목록
        subject: 커스텀 제목(선택)

    Returns:
        dict: 성공 여부와 digest_id를 포함한 결과
    """
    orchestrator = DigestOrchestrator()
    return await orchestrator.send_user_digest(session, user_id, articles, subject)


async def send_batch_daily_digests(
    session: AsyncSession,
    user_articles: dict[UUID | str, list[CollectedArticle]],
    max_failures: int = 5,
) -> dict[str, Any]:
    """
    다수 사용자 다이제스트 발송용 편의 함수.

    Args:
        session: DB 세션
        user_articles: user_id -> 아티클 목록 매핑
        max_failures: 중단 전 허용 실패 횟수

    Returns:
        dict: 성공/실패 개수와 결과 요약
    """
    orchestrator = DigestOrchestrator()
    return await orchestrator.send_batch_digests(session, user_articles, max_failures)
