"""Email content builder for daily research digest."""

import os
from datetime import datetime
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, select_autoescape

from src.app.db.models import CollectedArticle


class EmailBuilder:
    """Builder class for generating HTML email content from templates."""

    def __init__(self):
        """Initialize the email builder with Jinja2 environment."""
        template_dir = Path(__file__).parent / "templates"
        self.env = Environment(
            loader=FileSystemLoader(str(template_dir)),
            autoescape=select_autoescape(["html", "xml"]),
        )

    def build_daily_digest(
        self,
        user_name: str,
        user_email: str,
        articles: list[CollectedArticle],
        daily_limit: int = 5,
    ) -> str:
        """
        Build HTML email content for daily digest.

        Args:
            user_name: User's name for personalization
            user_email: User's email address
            articles: List of collected articles
            daily_limit: Maximum number of articles to include

        Returns:
            str: Rendered HTML email content
        """
        # Select top articles
        selected_articles = self._select_top_articles(articles, daily_limit)

        # Group by category
        papers, news, reports = self._group_by_category(selected_articles)

        # Prepare template context
        context = {
            "service_name": os.getenv("SERVICE_NAME", "Research Curator"),
            "date": datetime.now().strftime("%Y년 %m월 %d일"),
            "user_name": user_name,
            "user_email": user_email,
            "papers": [self._format_article(a) for a in papers],
            "news": [self._format_article(a) for a in news],
            "reports": [self._format_article(a) for a in reports],
            "settings_url": self._get_settings_url(),
            "feedback_url": self._get_feedback_url(),
            "unsubscribe_url": self._get_unsubscribe_url(user_email),
        }

        # Render template
        return self.render_template("daily_digest.html", context)

    def _select_top_articles(
        self,
        articles: list[CollectedArticle],
        limit: int,
    ) -> list[CollectedArticle]:
        """
        Select top N articles based on importance score.

        Strategy:
        1. Sort all articles by importance_score (descending)
        2. Try to maintain balance across categories
        3. Select top N articles

        Args:
            articles: List of collected articles
            limit: Maximum number of articles to select

        Returns:
            list[CollectedArticle]: Selected top articles
        """
        if not articles:
            return []

        # Sort by importance score
        sorted_articles = sorted(articles, key=lambda x: x.importance_score or 0.0, reverse=True)

        # Select top N
        return sorted_articles[:limit]

    def _group_by_category(
        self,
        articles: list[CollectedArticle],
    ) -> tuple[list[CollectedArticle], list[CollectedArticle], list[CollectedArticle]]:
        """
        Group articles by source type (paper/news/report).

        Args:
            articles: List of collected articles

        Returns:
            tuple: (papers, news, reports) lists
        """
        papers = []
        news = []
        reports = []

        for article in articles:
            if article.source_type == "paper":
                papers.append(article)
            elif article.source_type == "news":
                news.append(article)
            elif article.source_type == "report":
                reports.append(article)

        return papers, news, reports

    def _format_article(self, article: CollectedArticle) -> dict[str, Any]:
        """
        Format article data for template rendering.

        Args:
            article: CollectedArticle object

        Returns:
            dict: Formatted article data
        """
        # Calculate importance level and stars
        importance_score = article.importance_score or 0.0
        if importance_score >= 0.8:
            importance_level = "high"
            importance_stars = "⭐⭐⭐"
            importance_label = "높음"
        elif importance_score >= 0.6:
            importance_level = "medium"
            importance_stars = "⭐⭐"
            importance_label = "중간"
        else:
            importance_level = "low"
            importance_stars = "⭐"
            importance_label = "낮음"

        # Truncate summary if too long
        summary = article.summary or article.content or ""
        if len(summary) > 200:
            summary = summary[:197] + "..."

        # Extract metadata
        metadata = article.metadata or {}

        # Format published date
        published_date = None
        if article.collected_at:
            published_date = article.collected_at.strftime("%Y-%m-%d")

        # Build formatted data
        formatted = {
            "title": article.title,
            "summary": summary,
            "source_url": article.source_url,
            "importance_level": importance_level,
            "importance_stars": importance_stars,
            "importance_label": importance_label,
            "importance_score": importance_score,
            "published_date": published_date,
        }

        # Add source-specific metadata
        if article.source_type == "paper":
            formatted["authors"] = self._format_authors(metadata.get("authors", []))
            formatted["citations"] = metadata.get("citations")
        elif article.source_type == "news":
            formatted["source"] = metadata.get("source")
        elif article.source_type == "report":
            formatted["organization"] = metadata.get("organization")

        return formatted

    def _format_authors(self, authors: list[str]) -> str | None:
        """
        Format authors list for display.

        Args:
            authors: List of author names

        Returns:
            str | None: Formatted authors string (max 3 authors + "외")
        """
        if not authors:
            return None

        if len(authors) <= 3:
            return ", ".join(authors)

        return f"{', '.join(authors[:3])} 외 {len(authors) - 3}명"

    def _get_settings_url(self) -> str:
        """Get settings page URL."""
        base_url = os.getenv("FRONTEND_URL", "http://localhost:8501")
        return f"{base_url}/settings"

    def _get_feedback_url(self) -> str:
        """Get feedback page URL."""
        base_url = os.getenv("FRONTEND_URL", "http://localhost:8501")
        return f"{base_url}/feedback"

    def _get_unsubscribe_url(self, user_email: str) -> str:
        """Get unsubscribe URL with user email."""
        base_url = os.getenv("FRONTEND_URL", "http://localhost:8501")
        return f"{base_url}/unsubscribe?email={user_email}"

    def render_template(self, template_name: str, context: dict[str, Any]) -> str:
        """
        Render a Jinja2 template with given context.

        Args:
            template_name: Name of the template file
            context: Template context data

        Returns:
            str: Rendered HTML content
        """
        template = self.env.get_template(template_name)
        return template.render(**context)


# Convenience function for quick email building
def build_daily_digest_email(
    user_name: str,
    user_email: str,
    articles: list[CollectedArticle],
    daily_limit: int = 5,
) -> str:
    """
    Build daily digest email HTML content.

    Args:
        user_name: User's name
        user_email: User's email
        articles: List of collected articles
        daily_limit: Maximum articles to include

    Returns:
        str: Rendered HTML email
    """
    builder = EmailBuilder()
    return builder.build_daily_digest(user_name, user_email, articles, daily_limit)
