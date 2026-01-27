"""일일 연구 다이제스트 이메일 콘텐츠 빌더."""

import os
from datetime import datetime
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, select_autoescape
from premailer import transform

from app.db.models import CollectedArticle


class EmailBuilder:
    """템플릿 기반 HTML 이메일 콘텐츠 생성 빌더."""

    # 진자 환경 초기화
    def __init__(self) -> None:
        """Jinja2 환경을 초기화한다."""
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
        일일 다이제스트 HTML 이메일 콘텐츠를 생성한다.

        Args:
            user_name: 개인화에 사용할 사용자 이름
            user_email: 사용자 이메일 주소
            articles: 수집된 아티클 목록
            daily_limit: 포함할 최대 아티클 수

        Returns:
            str: 렌더링된 HTML 이메일 콘텐츠
        """
        # 상위 아티클 선택
        selected_articles = self._select_top_articles(articles, daily_limit)

        # 카테고리별 그룹화
        papers, news, reports = self._group_by_category(selected_articles)

        # 템플릿 컨텍스트 준비
        context = {
            "service_name": os.getenv("SERVICE_NAME", "Research Curator"),
            "date": datetime.now().strftime("%Y년 %m월 %d일"),
            "current_year": datetime.now().year,
            "user_name": user_name,
            "user_email": user_email,
            "papers": [self._format_article(a) for a in papers],
            "news": [self._format_article(a) for a in news],
            "reports": [self._format_article(a) for a in reports],
            "settings_url": self._get_settings_url(),
            "feedback_url": self._get_feedback_url(),
            "unsubscribe_url": self._get_unsubscribe_url(user_email),
        }

        # 템플릿 렌더링
        html = self.render_template("daily_digest.html", context)

        # 이메일 클라이언트 호환성을 위해 CSS를 인라인으로 변환(특히 네이버)
        return self._inline_css(html)

    def _select_top_articles(
        self,
        articles: list[CollectedArticle],
        limit: int,
    ) -> list[CollectedArticle]:
        """
        중요도 점수 기준으로 상위 N개 아티클을 선택한다.

        전략:
        1. importance_score 내림차순 정렬
        2. 카테고리 균형을 고려
        3. 상위 N개 선택

        Args:
            articles: 수집된 아티클 목록
            limit: 선택할 최대 아티클 수

        Returns:
            list[CollectedArticle]: 선택된 상위 아티클
        """
        if not articles:
            return []

        # 중요도 점수 정렬
        sorted_articles = sorted(articles, key=lambda x: x.importance_score or 0.0, reverse=True)

        # 상위 N개 선택
        return sorted_articles[:limit]

    def _group_by_category(
        self,
        articles: list[CollectedArticle],
    ) -> tuple[list[CollectedArticle], list[CollectedArticle], list[CollectedArticle]]:
        """
        카테고리(paper/news/report)별로 아티클을 그룹화한다.

        Args:
            articles: 수집된 아티클 목록

        Returns:
            tuple: (papers, news, reports) 목록
        """
        papers = []
        news = []
        reports = []

        for article in articles:
            # source_type 대신 LLM 분류 카테고리 사용
            category = (article.category or "").lower()
            if category == "paper":
                papers.append(article)
            elif category == "news":
                news.append(article)
            elif category == "report":
                reports.append(article)

        return papers, news, reports

    def _format_article(self, article: CollectedArticle) -> dict[str, Any]:
        """
        템플릿 렌더링용 아티클 데이터를 가공한다.

        Args:
            article: CollectedArticle 객체

        Returns:
            dict: 가공된 아티클 데이터
        """
        # 중요도 등급과 별점 계산(임계값: 0.6/0.4)
        importance_score = article.importance_score or 0.0
        if importance_score >= 0.6:
            importance_level = "high"
            importance_stars = "⭐⭐⭐"
            importance_label = "높음"
        elif importance_score >= 0.4:
            importance_level = "medium"
            importance_stars = "⭐⭐"
            importance_label = "중간"
        else:
            importance_level = "low"
            importance_stars = "⭐"
            importance_label = "낮음"

        # 요약이 길면 자르기
        summary = article.summary or article.content or ""
        if len(summary) > 200:
            summary = summary[:197] + "..."

        # 메타데이터 추출
        metadata = article.article_metadata or {}

        # 발행일 포맷
        published_date = None
        if article.collected_at:
            published_date = article.collected_at.strftime("%Y-%m-%d")

        # 렌더링용 데이터 구성
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

        # 소스별 메타데이터 추가
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
        표시용 저자 목록을 포맷한다.

        Args:
            authors: 저자 이름 목록

        Returns:
            str | None: 포맷된 저자 문자열(최대 3명 + "외")
        """
        if not authors:
            return None

        if len(authors) <= 3:
            return ", ".join(authors)

        return f"{', '.join(authors[:3])} 외 {len(authors) - 3}명"

    def _get_settings_url(self) -> str:
        """설정 페이지 URL을 반환한다."""
        base_url = os.getenv("FRONTEND_URL", "http://localhost:8501")
        return f"{base_url}/settings"

    def _get_feedback_url(self) -> str:
        """피드백 페이지 URL을 반환한다."""
        base_url = os.getenv("FRONTEND_URL", "http://localhost:8501")
        return f"{base_url}/feedback"

    def _get_unsubscribe_url(self, user_email: str) -> str:
        """사용자 이메일을 포함한 구독 해지 URL을 반환한다."""
        base_url = os.getenv("FRONTEND_URL", "http://localhost:8501")
        return f"{base_url}/unsubscribe?email={user_email}"

    def render_template(self, template_name: str, context: dict[str, Any]) -> str:
        """
        Jinja2 템플릿을 렌더링한다.

        Args:
            template_name: 템플릿 파일 이름
            context: 템플릿 컨텍스트 데이터

        Returns:
            str: 렌더링된 HTML 콘텐츠
        """
        template = self.env.get_template(template_name)
        return template.render(**context)

    def build_magic_link_email(self, magic_link: str, user_email: str) -> str:
        """
        매직 링크 인증용 HTML 이메일을 생성한다.

        Args:
            magic_link: 인증용 매직 링크 URL
            user_email: 사용자 이메일 주소

        Returns:
            str: 인라인 CSS가 적용된 HTML 이메일
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

        # 이메일 클라이언트 호환성을 위해 CSS를 인라인으로 변환(특히 네이버)
        return self._inline_css(html)

    def _inline_css(self, html: str) -> str:
        """
        이메일 클라이언트 호환성을 위해 CSS를 인라인 스타일로 변환한다.

        특히 <style> 태그를 제거하는 클라이언트(예: 네이버)에서 중요하다.
        premailer로 CSS를 자동 인라인 변환한다.

        Args:
            html: <style> 태그가 포함된 HTML

        Returns:
            str: 인라인 스타일이 적용된 HTML
        """
        try:
            # cssutils 경고 로그 억제
            import logging

            cssutils_logger = logging.getLogger("CSSUTILS")
            original_level = cssutils_logger.level
            cssutils_logger.setLevel(logging.CRITICAL)

            # CSS를 인라인 스타일로 변환
            result = transform(html)

            # 로그 레벨 복원
            cssutils_logger.setLevel(original_level)

            return result
        except Exception as e:
            # 인라인 변환 실패 시 원본 HTML 반환
            import logging

            logging.warning(f"Failed to inline CSS: {e}")
            return html


# 빠른 이메일 빌드용 편의 함수
def build_daily_digest_email(
    user_name: str,
    user_email: str,
    articles: list[CollectedArticle],
    daily_limit: int = 5,
) -> str:
    """
    일일 다이제스트 이메일 HTML을 생성한다.

    Args:
        user_name: 사용자 이름
        user_email: 사용자 이메일
        articles: 수집된 아티클 목록
        daily_limit: 포함할 최대 아티클 수

    Returns:
        str: 렌더링된 HTML 이메일
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
