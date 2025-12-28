"""Email content builder for daily research digest."""

import os
from datetime import datetime
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, select_autoescape
from premailer import transform

from app.db.models import CollectedArticle


class EmailBuilder:
    """Builder class for generating HTML email content from templates."""

    # 진자 환경 초기화
    def __init__(self):
        """Initialize the email builder with Jinja2 environment."""
        template_dir = Path(__file__).parent / "templates"
        self.env = Environment(
            loader=FileSystemLoader(str(template_dir)),
            autoescape=select_autoescape(["html", "xml"]),
        )

    # 일일 다이제스트 HTML 생성
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
        html = self.render_template("daily_digest.html", context)

        # Convert CSS to inline styles for better email client compatibility (especially Naver)
        return self._inline_css(html)

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
        metadata = article.article_metadata or {}

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

    def build_magic_link_email(self, magic_link: str, user_email: str) -> str:
        """
        Build HTML email content for magic link authentication.

        Args:
            magic_link: The magic link URL for authentication
            user_email: User's email address

        Returns:
            str: Rendered HTML email content with inline CSS
        """
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .button {{
                    display: inline-block;
                    padding: 12px 24px;
                    background-color: #007bff;
                    color: white;
                    text-decoration: none;
                    border-radius: 5px;
                    margin: 20px 0;
                }}
                .footer {{ margin-top: 30px; font-size: 12px; color: #666; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h2>🔬 Research Curator 로그인</h2>
                <p>안녕하세요!</p>
                <p>로그인을 위해 아래 버튼을 클릭해주세요:</p>
                <a href="{magic_link}" class="button">로그인하기</a>
                <p>또는 아래 링크를 복사하여 브라우저에 붙여넣으세요:</p>
                <p style="word-break: break-all; background: #f5f5f5; padding: 10px;">{magic_link}</p>
                <p>이 링크는 15분 동안 유효합니다.</p>
                <div class="footer">
                    <p>이 이메일은 Research Curator 로그인 요청에 따라 발송되었습니다.</p>
                    <p>요청하지 않으셨다면 이 이메일을 무시하셔도 됩니다.</p>
                </div>
            </div>
        </body>
        </html>
        """

        # Convert CSS to inline styles for better email client compatibility (especially Naver)
        return self._inline_css(html)

    def _inline_css(self, html: str) -> str:
        """
        Convert CSS styles to inline styles for better email client compatibility.

        This is especially important for email clients like Naver that strip <style> tags.
        Uses premailer to automatically convert all CSS to inline style attributes.

        Args:
            html: HTML content with <style> tags

        Returns:
            str: HTML content with inline styles
        """
        try:
            # Suppress cssutils warnings about modern CSS properties
            import logging

            cssutils_logger = logging.getLogger("CSSUTILS")
            original_level = cssutils_logger.level
            cssutils_logger.setLevel(logging.CRITICAL)

            # Transform CSS to inline styles
            result = transform(html)

            # Restore original log level
            cssutils_logger.setLevel(original_level)

            return result
        except Exception as e:
            # If inlining fails, return original HTML
            import logging

            logging.warning(f"Failed to inline CSS: {e}")
            return html


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


# 동작 구조
# 입력: 아티클 리스트 (from Vector DB or PostgreSQL)
#    ↓
# [_select_top_articles] - importance_score 기준 정렬 및 상위 N개 선택
#    ↓
# [_group_by_category] - paper/news/report 그룹화
#    ↓
# [_format_article] - 각 아티클을 템플릿 포맷으로 변환
#    - 중요도 별 stars 생성 (⭐⭐⭐)
#    - 날짜 포맷팅
#    - 요약문 길이 제한
#    ↓
# [render_template] - Jinja2로 HTML 렌더링
#    - 사용자 이름 삽입
#    - 날짜 삽입
#    - 아티클 섹션 생성
#    - Footer 링크 생성
#    ↓
# 출력: 완전한 HTML 이메일 (String)
