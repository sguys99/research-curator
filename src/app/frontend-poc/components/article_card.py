"""연구 아티클 표시용 카드 컴포넌트."""

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
    """제목/요약/메타데이터를 포함한 아티클 카드를 표시한다.

    Args:
        title: 아티클 제목
        summary: 아티클 요약
        source_type: 소스 유형(paper, news, report)
        category: 아티클 카테고리(AI, NLP 등)
        importance_score: 중요도 점수(0-1)
        url: 아티클 URL
        collected_at: 수집 시각
        metadata: 추가 메타데이터
        show_similar_button: "유사 논문" 버튼 표시 여부
        article_id: 유사 검색용 아티클 ID
    """
    # 소스 유형 이모지 매핑
    source_emoji = {
        "paper": "📚",
        "news": "📰",
        "report": "📊",
        "blog": "📝",
    }

    # 중요도 별점
    stars = "⭐" * min(3, max(1, int(importance_score * 3)))

    # 카드 컨테이너
    with st.container():
        # 헤더 행
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

        # 요약
        st.markdown(summary)

        # 메타데이터 행
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

        # 추가 메타데이터
        if metadata:
            with st.expander("📋 상세 정보"):
                for key, value in metadata.items():
                    if key not in ["embedding", "vector_id"]:  # 대용량 필드 제외
                        st.text(f"{key}: {value}")

        # 액션 버튼
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
    """아티클 카드 목록을 표시한다.

    Args:
        articles: 아티클 dict 목록
        show_similar_button: "유사 논문" 버튼 표시 여부
        empty_message: 빈 목록일 때 표시할 메시지
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
    """컴팩트 아티클 카드를 표시한다(사이드바/작은 영역용).

    Args:
        title: 아티클 제목
        summary: 아티클 요약(자동 축약)
        source_type: 소스 유형
        importance_score: 중요도 점수
        url: 아티클 URL
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
