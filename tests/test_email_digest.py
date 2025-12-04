"""Tests for email digest orchestration."""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from app.db.models import CollectedArticle, User, UserPreference
from app.email.digest import DigestOrchestrator, send_daily_digest


@pytest.fixture
def mock_user():
    """Create mock user."""
    return User(
        id=uuid4(),
        email="test@example.com",
        name="Test User",
        created_at=datetime.now(),
    )


@pytest.fixture
def mock_preferences():
    """Create mock user preferences."""
    return UserPreference(
        id=uuid4(),
        user_id=uuid4(),
        research_fields=["AI", "Machine Learning"],
        keywords=["transformer", "GPT"],
        daily_limit=5,
        info_types={"paper": 50, "news": 30, "report": 20},
    )


@pytest.fixture
def sample_articles():
    """Create sample articles."""
    return [
        CollectedArticle(
            id=uuid4(),
            title=f"Article {i}",
            summary=f"Summary {i}",
            source_url=f"https://example.com/{i}",
            source_type="paper" if i % 3 == 0 else ("news" if i % 3 == 1 else "report"),
            importance_score=0.9 - (i * 0.1),
            collected_at=datetime.now(),
        )
        for i in range(10)
    ]


class TestDigestOrchestrator:
    """Test cases for DigestOrchestrator."""

    @pytest.mark.asyncio
    async def test_send_user_digest_success(self, mock_user, mock_preferences, sample_articles):
        """Test successful digest sending."""
        session = AsyncMock()
        # Create mock sender
        mock_sender = AsyncMock()
        mock_sender.send_email = AsyncMock(return_value=True)
        orchestrator = DigestOrchestrator(email_sender=mock_sender)

        # Mock database queries
        async def mock_execute(stmt):
            result = MagicMock()
            # First call returns user, second returns preferences
            if not hasattr(mock_execute, "call_count"):
                mock_execute.call_count = 0
            mock_execute.call_count += 1

            if mock_execute.call_count == 1:
                result.scalar_one_or_none.return_value = mock_user
            else:
                result.scalar_one_or_none.return_value = mock_preferences

            return result

        session.execute = mock_execute

        # Mock save_sent_digest
        with patch("app.email.digest.save_sent_digest", new_callable=AsyncMock) as mock_save:
            mock_digest = MagicMock()
            mock_digest.id = uuid4()
            mock_save.return_value = mock_digest

            result = await orchestrator.send_user_digest(session, mock_user.id, sample_articles)

            assert result["success"] is True
            assert result["user_email"] == "test@example.com"
            assert "digest_id" in result
            assert mock_sender.send_email.called
            assert mock_save.called

    @pytest.mark.asyncio
    async def test_send_user_digest_user_not_found(self, sample_articles):
        """Test digest sending when user not found."""
        session = AsyncMock()
        mock_sender = AsyncMock()
        orchestrator = DigestOrchestrator(email_sender=mock_sender)

        # Mock database to return None (user not found)
        async def mock_execute(stmt):
            result = MagicMock()
            result.scalar_one_or_none.return_value = None
            return result

        session.execute = mock_execute

        result = await orchestrator.send_user_digest(session, uuid4(), sample_articles)

        assert result["success"] is False
        assert "not found" in result["error"]

    @pytest.mark.asyncio
    async def test_send_user_digest_no_preferences(self, mock_user, sample_articles):
        """Test digest sending when user has no preferences."""
        session = AsyncMock()
        mock_sender = AsyncMock()
        orchestrator = DigestOrchestrator(email_sender=mock_sender)

        # Mock database: user exists, no preferences
        async def mock_execute(stmt):
            result = MagicMock()
            if not hasattr(mock_execute, "call_count"):
                mock_execute.call_count = 0
            mock_execute.call_count += 1

            if mock_execute.call_count == 1:
                result.scalar_one_or_none.return_value = mock_user
            else:
                result.scalar_one_or_none.return_value = None

            return result

        session.execute = mock_execute

        result = await orchestrator.send_user_digest(session, mock_user.id, sample_articles)

        assert result["success"] is False
        assert "no preferences" in result["error"]

    @pytest.mark.asyncio
    async def test_send_batch_digests_success(self, mock_user, mock_preferences, sample_articles):
        """Test successful batch digest sending."""
        session = AsyncMock()
        mock_sender = AsyncMock()
        orchestrator = DigestOrchestrator(email_sender=mock_sender)

        user_id_1 = uuid4()
        user_id_2 = uuid4()
        user_articles = {
            user_id_1: sample_articles[:5],
            user_id_2: sample_articles[5:],
        }

        # Mock send_user_digest
        async def mock_send_user_digest(sess, user_id, articles, subject=None):
            return {
                "success": True,
                "user_id": str(user_id),
                "user_email": f"user{user_id}@example.com",
                "digest_id": str(uuid4()),
                "article_count": len(articles),
            }

        with patch.object(
            orchestrator,
            "send_user_digest",
            side_effect=mock_send_user_digest,
        ):
            result = await orchestrator.send_batch_digests(session, user_articles)

            assert result["success_count"] == 2
            assert result["failure_count"] == 0
            assert len(result["results"]) == 2

    @pytest.mark.asyncio
    async def test_send_batch_digests_partial_failure(self, mock_user, sample_articles):
        """Test batch digest sending with some failures."""
        session = AsyncMock()
        mock_sender = AsyncMock()
        orchestrator = DigestOrchestrator(email_sender=mock_sender)

        user_id_1 = uuid4()
        user_id_2 = uuid4()
        user_id_3 = uuid4()
        user_articles = {
            user_id_1: sample_articles[:3],
            user_id_2: sample_articles[3:6],
            user_id_3: sample_articles[6:],
        }

        call_count = 0

        async def mock_send_user_digest(sess, user_id, articles, subject=None):
            nonlocal call_count
            call_count += 1

            if call_count == 2:
                # Second user fails
                return {
                    "success": False,
                    "user_id": str(user_id),
                    "error": "Email sending failed",
                }

            return {
                "success": True,
                "user_id": str(user_id),
                "user_email": f"user{user_id}@example.com",
                "digest_id": str(uuid4()),
            }

        with patch.object(
            orchestrator,
            "send_user_digest",
            side_effect=mock_send_user_digest,
        ):
            result = await orchestrator.send_batch_digests(session, user_articles)

            assert result["success_count"] == 2
            assert result["failure_count"] == 1
            assert len(result["results"]) == 3

    @pytest.mark.asyncio
    async def test_send_batch_digests_max_failures(self, sample_articles):
        """Test batch digest stops after max failures."""
        session = AsyncMock()
        mock_sender = AsyncMock()
        orchestrator = DigestOrchestrator(email_sender=mock_sender)

        user_articles = {uuid4(): sample_articles[:2] for _ in range(10)}

        async def mock_send_user_digest_fail(sess, user_id, articles, subject=None):
            return {
                "success": False,
                "user_id": str(user_id),
                "error": "Failed",
            }

        with patch.object(
            orchestrator,
            "send_user_digest",
            side_effect=mock_send_user_digest_fail,
        ):
            result = await orchestrator.send_batch_digests(session, user_articles, max_failures=3)

            assert result["success_count"] == 0
            assert result["failure_count"] == 3
            assert len(result["results"]) == 3

    @pytest.mark.asyncio
    async def test_convenience_send_daily_digest(self, mock_user, mock_preferences, sample_articles):
        """Test convenience function."""
        session = AsyncMock()

        async def mock_execute(stmt):
            result = MagicMock()
            if not hasattr(mock_execute, "call_count"):
                mock_execute.call_count = 0
            mock_execute.call_count += 1

            if mock_execute.call_count == 1:
                result.scalar_one_or_none.return_value = mock_user
            else:
                result.scalar_one_or_none.return_value = mock_preferences

            return result

        session.execute = mock_execute

        with patch("app.email.digest.EmailSender") as mock_sender_class:
            mock_sender = AsyncMock()
            mock_sender.send_email = AsyncMock(return_value=True)
            mock_sender_class.return_value = mock_sender

            with patch("app.email.digest.save_sent_digest", new_callable=AsyncMock) as mock_save:
                mock_digest = MagicMock()
                mock_digest.id = uuid4()
                mock_save.return_value = mock_digest

                result = await send_daily_digest(session, mock_user.id, sample_articles)

                assert result["success"] is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
