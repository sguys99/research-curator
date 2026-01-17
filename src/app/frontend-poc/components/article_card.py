"""Article card component for displaying research articles."""

from datetime import datetime

import streamlit as st


def show_article_card(
    title: str,
    summary: str,
    source_type: str,
    category: str,
    importance_score: float,
    url: str,
    collected_at: str | None = None,
    metadata: dict | None = None,
    show_similar_button: bool = False,
    article_id: str | None = None,
):
    """Display an article card with title, summary, and metadata.

    Args:
        title: Article title
        summary: Article summary
        source_type: Type of source (paper, news, report)
        category: Article category (AI, NLP, etc.)
        importance_score: Importance score (0-1)
        url: Article URL
        collected_at: Collection timestamp
        metadata: Additional metadata
        show_similar_button: Whether to show "Find Similar" button
        article_id: Article ID for similar search
    """
    # Source type emoji mapping
    source_emoji = {
        "paper": "📚",
        "news": "📰",
        "report": "📊",
        "blog": "📝",
    }

    # Importance stars
    stars = "⭐" * min(3, max(1, int(importance_score * 3)))

    # Card container
    with st.container():
        # Header row
        col1, col2, col3 = st.columns([2, 1, 1])

        with col1:
            st.markdown(f"### {title}")

        with col2:
            st.markdown(
                f"<div style='text-align: right'>{stars}</div>",
                unsafe_allow_html=True,
            )

        with col3:
            badge_color = "#4F46E5" if source_type == "paper" else "#10B981"
            st.markdown(
                f"<div style='text-align: right'>"
                f"<span style='background: {badge_color}; color: white; "
                f"padding: 2px 8px; border-radius: 4px; font-size: 12px;'>"
                f"{source_emoji.get(source_type, '📄')} {source_type.upper()}"
                f"</span></div>",
                unsafe_allow_html=True,
            )

        # Summary
        st.markdown(summary)

        # Metadata row
        meta_col1, meta_col2, meta_col3 = st.columns(3)

        with meta_col1:
            st.caption(f"🏷️ {category}")

        with meta_col2:
            st.caption(f"📈 중요도: {importance_score:.2f}")

        with meta_col3:
            if collected_at:
                try:
                    dt = datetime.fromisoformat(collected_at.replace("Z", "+00:00"))
                    st.caption(f"📅 {dt.strftime('%Y-%m-%d')}")
                except Exception:
                    st.caption("📅 N/A")

        # Additional metadata
        if metadata:
            with st.expander("📋 상세 정보"):
                for key, value in metadata.items():
                    if key not in ["embedding", "vector_id"]:  # Skip large fields
                        st.text(f"{key}: {value}")

        # Action buttons
        btn_col1, btn_col2, btn_col3 = st.columns([2, 1, 1])

        with btn_col1:
            if st.button(
                "🔗 원문 보기",
                key=f"view_{url}_{collected_at}",
                use_container_width=True,
            ):
                st.markdown(f"[{title}]({url})")

        with btn_col2:
            if show_similar_button and article_id:
                if st.button(
                    "🔍 유사 논문",
                    key=f"similar_{article_id}_{collected_at}",
                    use_container_width=True,
                ):
                    st.session_state["search_similar_id"] = article_id
                    st.rerun()

        st.markdown("---")


def show_article_list(
    articles: list[dict],
    show_similar_button: bool = False,
    empty_message: str = "표시할 아티클이 없습니다.",
):
    """Display a list of article cards.

    Args:
        articles: List of article dictionaries
        show_similar_button: Whether to show "Find Similar" button
        empty_message: Message to show when list is empty
    """
    if not articles:
        st.info(empty_message)
        return

    st.markdown(f"**총 {len(articles)}개의 아티클**")

    for article in articles:
        show_article_card(
            title=article.get("title", "제목 없음"),
            summary=article.get("summary", "요약 없음"),
            source_type=article.get("source_type", "other"),
            category=article.get("category", "기타"),
            importance_score=article.get("importance_score", 0.5),
            url=article.get("url", article.get("source_url", "#")),
            collected_at=article.get("collected_at"),
            metadata=article.get("metadata"),
            show_similar_button=show_similar_button,
            article_id=article.get("id", article.get("article_id")),
        )


def show_compact_article_card(
    title: str,
    summary: str,
    source_type: str,
    importance_score: float,
    url: str,
):
    """Display a compact version of article card (for sidebar or small spaces).

    Args:
        title: Article title
        summary: Article summary (will be truncated)
        source_type: Type of source
        importance_score: Importance score
        url: Article URL
    """
    source_emoji = {"paper": "📚", "news": "📰", "report": "📊", "blog": "📝"}
    stars = "⭐" * min(3, max(1, int(importance_score * 3)))

    with st.container():
        st.markdown(
            f"**{source_emoji.get(source_type, '📄')} {title[:50]}{'...' if len(title) > 50 else ''}**",
        )
        st.caption(summary[:100] + ("..." if len(summary) > 100 else ""))
        st.caption(f"{stars} | [원문]({url})")
        st.markdown("")
