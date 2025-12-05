"""Search page with semantic search and filters."""

import streamlit as st

from app.frontend.components.article_card import show_article_list
from app.frontend.components.sidebar import show_page_header
from app.frontend.utils.api_client import get_api_client
from app.frontend.utils.session import is_authenticated


def show_search_page():
    """Display search page with semantic search functionality."""
    if not is_authenticated():
        st.warning("⚠️ 로그인이 필요합니다.")
        st.stop()

    show_page_header("🔍 시맨틱 검색", "과거 자료를 자연어로 검색하세요")

    api = get_api_client()

    # Check if searching for similar articles
    if st.session_state.get("search_similar_id"):
        _show_similar_search(api)
        return

    # Search input
    st.markdown("### 🔎 검색")

    query = st.text_input(
        "검색어를 입력하세요",
        placeholder="예: transformer 모델 최적화 기법",
        key="search_query",
    )

    # Filters in expander
    with st.expander("🔧 필터 옵션", expanded=False):
        col1, col2, col3 = st.columns(3)

        with col1:
            source_types = st.multiselect(
                "Source Type",
                ["paper", "news", "report", "blog"],
                default=[],
                help="아티클 유형 선택",
            )

        with col2:
            categories = st.multiselect(
                "Category",
                ["AI", "NLP", "ML", "CV", "Robotics", "Other"],
                default=[],
                help="카테고리 선택",
            )

        with col3:
            min_importance = st.slider(
                "최소 중요도",
                0.0,
                1.0,
                0.5,
                0.1,
                help="중요도 점수 최소값",
            )

        # Advanced filters
        col4, col5 = st.columns(2)

        with col4:
            date_from = st.date_input("시작 날짜 (선택)", value=None)

        with col5:
            date_to = st.date_input("종료 날짜 (선택)", value=None)

        score_threshold = st.slider(
            "유사도 임계값",
            0.0,
            1.0,
            0.7,
            0.05,
            help="검색 결과의 최소 유사도",
        )

        limit = st.number_input(
            "최대 결과 수",
            min_value=1,
            max_value=50,
            value=10,
            help="표시할 최대 결과 수",
        )

    # Search button
    col1, col2, col3 = st.columns([2, 1, 1])

    with col1:
        search_button = st.button("🔍 검색", type="primary", use_container_width=True)

    with col2:
        if st.button("🔄 초기화", use_container_width=True):
            st.session_state.search_query = ""
            st.rerun()

    # Perform search
    if search_button and query:
        with st.spinner("검색 중..."):
            try:
                # Prepare search parameters
                search_params = {
                    "query": query,
                    "limit": limit,
                    "score_threshold": score_threshold,
                }

                if source_types:
                    search_params["source_type"] = source_types

                if categories:
                    search_params["category"] = categories

                if min_importance > 0:
                    search_params["min_importance_score"] = min_importance

                if date_from:
                    search_params["date_from"] = date_from.isoformat()

                if date_to:
                    search_params["date_to"] = date_to.isoformat()

                # Call search API
                response = api.search_articles(**search_params)

                articles = response.get("results", [])

                st.markdown("---")
                st.markdown("### 📋 검색 결과")

                if articles:
                    st.success(f"✅ {len(articles)}개의 아티클을 찾았습니다.")

                    # Display results
                    show_article_list(articles, show_similar_button=True)

                else:
                    st.warning("검색 결과가 없습니다. 다른 키워드를 시도하거나 필터를 조정해보세요.")

            except Exception as e:
                st.error(f"❌ 검색 중 오류가 발생했습니다: {str(e)}")

    elif search_button and not query:
        st.warning("⚠️ 검색어를 입력해주세요.")

    # Show example queries
    st.markdown("---")
    st.markdown("### 💡 검색 예시")

    example_queries = [
        "transformer 아키텍처 최적화",
        "GPT-4 성능 평가",
        "BERT 모델 파인튜닝 방법",
        "attention mechanism 개선",
        "few-shot learning 기법",
    ]

    st.markdown("다음 예시 중 하나를 클릭해보세요:")

    cols = st.columns(len(example_queries))
    for idx, example in enumerate(example_queries):
        with cols[idx]:
            if st.button(f"💬 {example}", key=f"example_{idx}", use_container_width=True):
                st.session_state.search_query = example
                st.rerun()


def _show_similar_search(api):
    """Show similar article search results."""
    article_id = st.session_state.get("search_similar_id")

    st.markdown("### 🔍 유사 문서 검색")

    # Back button
    if st.button("← 검색으로 돌아가기"):
        st.session_state.pop("search_similar_id", None)
        st.rerun()

    st.markdown(f"**참조 아티클 ID:** `{article_id}`")

    # Search parameters
    col1, col2 = st.columns(2)

    with col1:
        limit = st.number_input("최대 결과 수", min_value=1, max_value=20, value=5)

    with col2:
        score_threshold = st.slider("유사도 임계값", 0.0, 1.0, 0.7, 0.05)

    if st.button("🔍 유사 문서 검색", type="primary"):
        with st.spinner("유사 문서를 찾는 중..."):
            try:
                response = api.find_similar_articles(
                    article_id=article_id,
                    limit=limit,
                    score_threshold=score_threshold,
                )

                articles = response.get("results", [])

                st.markdown("---")
                st.markdown("### 📋 유사 문서")

                if articles:
                    st.success(f"✅ {len(articles)}개의 유사 문서를 찾았습니다.")
                    show_article_list(articles, show_similar_button=False)
                else:
                    st.warning("유사한 문서를 찾을 수 없습니다.")

            except Exception as e:
                st.error(f"❌ 오류: {str(e)}")


if __name__ == "__main__":
    show_search_page()
