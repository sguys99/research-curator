"""Daily digest orchestration - integrates builder, sender, and history."""

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


class DigestOrchestrator:
    """Orchestrates the daily digest workflow."""

    def __init__(self, email_sender: EmailSender | None = None):
        """
        Initialize digest orchestrator.

        Args:
            email_sender: Optional custom email sender (defaults to new instance)
        """
        self.builder = EmailBuilder()
        self.sender = email_sender or EmailSender()

    async def send_user_digest(
        self,
        session: AsyncSession,
        user_id: UUID | str,
        articles: list[CollectedArticle],
        subject: str | None = None,
    ) -> dict[str, Any]:
        """
        Send daily digest email to a single user.

        Args:
            session: Database session
            user_id: User UUID
            articles: List of collected articles
            subject: Optional custom subject (defaults to date-based)

        Returns:
            dict: Result with success status and digest_id

        Raises:
            ValueError: If user not found or has no preferences
        """
        try:
            # Convert user_id to UUID if string
            if isinstance(user_id, str):
                user_id = UUID(user_id)

            # Load user and preferences
            user = await self._load_user(session, user_id)
            if not user:
                raise ValueError(f"User {user_id} not found")

            preferences = await self._load_user_preferences(session, user_id)
            if not preferences:
                raise ValueError(f"User {user_id} has no preferences")

            # Get daily limit from preferences
            daily_limit = preferences.daily_limit or 5

            # Build email content
            html_content = self.builder.build_daily_digest(
                user_name=user.name,
                user_email=user.email,
                articles=articles,
                daily_limit=daily_limit,
            )

            # Generate subject
            if not subject:
                date_str = datetime.now().strftime("%Y년 %m월 %d일")
                subject = f"🔬 Research Curator - {date_str} AI 연구 동향"

            # Send email
            await self.sender.send_email(
                to_email=user.email,
                subject=subject,
                html_content=html_content,
            )

            # Save digest history
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
        Send daily digests to multiple users.

        Args:
            session: Database session
            user_articles: Dict mapping user_id to list of articles
            max_failures: Maximum number of failures before stopping

        Returns:
            dict: Summary with success_count, failure_count, results
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
        """Load user from database."""
        stmt = select(User).where(User.id == user_id)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    async def _load_user_preferences(
        self,
        session: AsyncSession,
        user_id: UUID,
    ) -> UserPreference | None:
        """Load user preferences from database."""
        stmt = select(UserPreference).where(UserPreference.user_id == user_id)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()


async def send_daily_digest(
    session: AsyncSession,
    user_id: UUID | str,
    articles: list[CollectedArticle],
    subject: str | None = None,
) -> dict[str, Any]:
    """
    Convenience function to send daily digest to a single user.

    Args:
        session: Database session
        user_id: User UUID
        articles: List of collected articles
        subject: Optional custom subject

    Returns:
        dict: Result with success status and digest_id
    """
    orchestrator = DigestOrchestrator()
    return await orchestrator.send_user_digest(session, user_id, articles, subject)


async def send_batch_daily_digests(
    session: AsyncSession,
    user_articles: dict[UUID | str, list[CollectedArticle]],
    max_failures: int = 5,
) -> dict[str, Any]:
    """
    Convenience function to send daily digests to multiple users.

    Args:
        session: Database session
        user_articles: Dict mapping user_id to list of articles
        max_failures: Maximum number of failures before stopping

    Returns:
        dict: Summary with success_count, failure_count, results
    """
    orchestrator = DigestOrchestrator()
    return await orchestrator.send_batch_digests(session, user_articles, max_failures)
