"""Unit tests for email builder functionality."""

from datetime import datetime
from pathlib import Path

import pytest

from app.db.models import CollectedArticle
from app.email.builder import EmailBuilder, build_daily_digest_email


@pytest.mark.unit
@pytest.fixture
def sample_articles():
    """Create sample articles for testing."""
    return [
        CollectedArticle(
            id="1",
            title="Attention Is All You Need",
            content="This paper introduces the Transformer architecture...",
            summary="트랜스포머 아키텍처를 소개하는 획기적인 논문입니다.",
            source_url="https://arxiv.org/abs/1706.03762",
            source_type="paper",
            category="Deep Learning",
            importance_score=0.95,
            article_metadata={
                "authors": ["Vaswani", "Shazeer", "Parmar", "Uszkoreit"],
                "citations": 50000,
            },
            collected_at=datetime(2024, 1, 15),
        ),
        CollectedArticle(
            id="2",
            title="GPT-4 Released by OpenAI",
            content="OpenAI has released GPT-4, the latest version...",
            summary="OpenAI가 GPT-4를 공개했습니다. 멀티모달 기능을 포함합니다.",
            source_url="https://techcrunch.com/gpt4",
            source_type="news",
            category="AI News",
            importance_score=0.88,
            article_metadata={"source": "TechCrunch"},
            collected_at=datetime(2024, 3, 14),
        ),
        CollectedArticle(
            id="3",
            title="State of AI Report 2024",
            content="Annual report on AI trends and predictions...",
            summary="2024년 AI 산업 트렌드와 예측을 담은 연례 리포트입니다.",
            source_url="https://www.stateof.ai/",
            source_type="report",
            category="Industry Report",
            importance_score=0.82,
            article_metadata={"organization": "State of AI"},
            collected_at=datetime(2024, 10, 1),
        ),
        CollectedArticle(
            id="4",
            title="Low Importance Paper",
            content="A minor improvement on existing methods...",
            summary="기존 방법론에 대한 소폭 개선을 제안합니다.",
            source_url="https://arxiv.org/abs/9999.99999",
            source_type="paper",
            category="Machine Learning",
            importance_score=0.45,
            article_metadata={"authors": ["Smith", "Jones"], "citations": 5},
            collected_at=datetime(2024, 11, 20),
        ),
        CollectedArticle(
            id="5",
            title="Medium Importance News",
            content="AI startup raises funding...",
            summary="AI 스타트업이 시리즈 A 펀딩을 받았습니다.",
            source_url="https://venturebeat.com/funding",
            source_type="news",
            category="Funding",
            importance_score=0.65,
            article_metadata={"source": "VentureBeat"},
            collected_at=datetime(2024, 11, 22),
        ),
    ]


@pytest.mark.unit
class TestEmailBuilder:
    """Test cases for EmailBuilder class."""

    def test_init(self):
        """Test EmailBuilder initialization."""
        builder = EmailBuilder()
        assert builder.env is not None
        assert "daily_digest.html" in builder.env.list_templates()

    def test_select_top_articles(self, sample_articles):
        """Test article selection logic."""
        builder = EmailBuilder()

        # Select top 3
        top_3 = builder._select_top_articles(sample_articles, 3)
        assert len(top_3) == 3
        assert top_3[0].importance_score == 0.95
        assert top_3[1].importance_score == 0.88
        assert top_3[2].importance_score == 0.82

        # Select all
        all_articles = builder._select_top_articles(sample_articles, 10)
        assert len(all_articles) == 5

        # Select from empty list
        empty = builder._select_top_articles([], 5)
        assert len(empty) == 0

    def test_group_by_category(self, sample_articles):
        """Test article grouping by category."""
        builder = EmailBuilder()
        papers, news, reports = builder._group_by_category(sample_articles)

        assert len(papers) == 2
        assert len(news) == 2
        assert len(reports) == 1
        assert all(a.source_type == "paper" for a in papers)
        assert all(a.source_type == "news" for a in news)
        assert all(a.source_type == "report" for a in reports)

    def test_format_article_high_importance(self, sample_articles):
        """Test article formatting for high importance."""
        builder = EmailBuilder()
        formatted = builder._format_article(sample_articles[0])

        assert formatted["title"] == "Attention Is All You Need"
        assert formatted["importance_level"] == "high"
        assert formatted["importance_stars"] == "⭐⭐⭐"
        assert formatted["importance_label"] == "높음"
        assert "Vaswani" in formatted["authors"]
        assert formatted["citations"] == 50000

    def test_format_article_medium_importance(self, sample_articles):
        """Test article formatting for medium importance."""
        builder = EmailBuilder()
        formatted = builder._format_article(sample_articles[4])

        assert formatted["importance_level"] == "medium"
        assert formatted["importance_stars"] == "⭐⭐"
        assert formatted["importance_label"] == "중간"

    def test_format_article_low_importance(self, sample_articles):
        """Test article formatting for low importance."""
        builder = EmailBuilder()
        formatted = builder._format_article(sample_articles[3])

        assert formatted["importance_level"] == "low"
        assert formatted["importance_stars"] == "⭐"
        assert formatted["importance_label"] == "낮음"

    def test_format_article_summary_truncation(self):
        """Test summary truncation for long content."""
        builder = EmailBuilder()
        long_article = CollectedArticle(
            id="long",
            title="Long Article",
            summary="A" * 300,  # 300 characters
            source_url="https://example.com",
            source_type="paper",
            importance_score=0.7,
        )

        formatted = builder._format_article(long_article)
        assert len(formatted["summary"]) <= 200
        assert formatted["summary"].endswith("...")

    def test_format_authors_short_list(self):
        """Test author formatting for short lists."""
        builder = EmailBuilder()
        authors = ["Author A", "Author B"]
        formatted = builder._format_authors(authors)
        assert formatted == "Author A, Author B"

    def test_format_authors_long_list(self):
        """Test author formatting for long lists."""
        builder = EmailBuilder()
        authors = ["A", "B", "C", "D", "E", "F"]
        formatted = builder._format_authors(authors)
        assert formatted == "A, B, C 외 3명"

    def test_format_authors_empty(self):
        """Test author formatting for empty list."""
        builder = EmailBuilder()
        formatted = builder._format_authors([])
        assert formatted is None

    def test_build_daily_digest(self, sample_articles):
        """Test full daily digest building."""
        builder = EmailBuilder()
        html = builder.build_daily_digest(
            user_name="테스트 사용자",
            user_email="test@example.com",
            articles=sample_articles,
            daily_limit=3,
        )

        # Check HTML structure
        assert "<!DOCTYPE html>" in html
        assert "테스트 사용자" in html
        assert "test@example.com" in html

        # Check sections are present
        assert "📚" in html or "논문" in html
        assert "📰" in html or "뉴스" in html

        # Check article content
        assert "Attention Is All You Need" in html
        assert "GPT-4 Released by OpenAI" in html
        assert "State of AI Report 2024" in html

        # Low importance article should not be included (limited to 3)
        assert "Low Importance Paper" not in html

    def test_build_daily_digest_empty_articles(self):
        """Test daily digest with no articles."""
        builder = EmailBuilder()
        html = builder.build_daily_digest(
            user_name="테스트 사용자",
            user_email="test@example.com",
            articles=[],
        )

        assert "<!DOCTYPE html>" in html
        assert "테스트 사용자" in html
        assert "새로운 자료가 없습니다" in html

    def test_render_template_with_context(self):
        """Test template rendering with custom context."""
        builder = EmailBuilder()
        context = {
            "service_name": "Test Service",
            "date": "2024-01-01",
            "user_name": "John",
            "user_email": "john@example.com",
            "papers": [],
            "news": [],
            "reports": [],
            "settings_url": "https://example.com/settings",
            "feedback_url": "https://example.com/feedback",
            "unsubscribe_url": "https://example.com/unsubscribe",
        }

        html = builder.render_template("daily_digest.html", context)

        assert "Test Service" in html
        assert "John" in html
        assert "john@example.com" in html
        assert "https://example.com/settings" in html

    def test_convenience_function(self, sample_articles):
        """Test the convenience function."""
        html = build_daily_digest_email(
            user_name="테스트",
            user_email="test@test.com",
            articles=sample_articles,
            daily_limit=2,
        )

        assert "<!DOCTYPE html>" in html
        assert "테스트" in html
        assert "test@test.com" in html


def test_template_file_exists():
    """Test that the template file exists."""
    template_path = (
        Path(__file__).parent.parent / "src" / "app" / "email" / "templates" / "daily_digest.html"
    )
    assert template_path.exists(), "Template file should exist"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
