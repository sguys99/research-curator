"""시맨틱 검색과 필터를 제공하는 검색 페이지."""

import streamlit as st

from app.frontend.components.article_card import show_article_list
from app.frontend.components.sidebar import show_page_header
from app.frontend.utils.api_client import get_api_client
from app.frontend.utils.session import is_authenticated


def show_search_page():
    """시맨틱 검색 기능이 있는 검색 페이지를 표시한다."""
    if not is_authenticated():
        st.warning("⚠️ 로그인이 필요합니다.")
        st.stop()

    show_page_header("🔍 시맨틱 검색", "과거 자료를 자연어로 검색하세요")

    api = get_api_client()

    # 유사 아티클 검색 여부 확인
    if st.session_state.get("search_similar_id"):
        _show_similar_search(api)
        return

    # 검색 모드 탭
    st.markdown("### 🔎 검색")

    search_tab1, search_tab2 = st.tabs(["🧠 시맨틱 검색", "🔤 키워드 검색"])

    # 탭 1: 시맨틱 검색
    with search_tab1:
        query = st.text_input(
            "검색어를 입력하세요 (자연어)",
            placeholder="예: transformer 모델 최적화 기법",
            key="semantic_search_query",
        )
        search_mode = "semantic"

    # 탭 2: 키워드 검색
    with search_tab2:
        query = st.text_input(
            "키워드를 입력하세요",
            placeholder="예: GPT-4, BERT, attention mechanism",
            key="keyword_search_query",
            help="제목, 요약, 내용에서 키워드를 검색합니다",
        )
        search_mode = "keyword"

    # 선택된 탭 기준으로 검색어 선택
    if search_mode == "semantic":
        query = st.session_state.get("semantic_search_query", "")
    else:
        query = st.session_state.get("keyword_search_query", "")

    # 필터 옵션(확장 섹션)
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

        # 고급 필터
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

    # 검색 버튼
    col1, col2, col3 = st.columns([2, 1, 1])

    with col1:
        search_button = st.button("🔍 검색", type="primary", use_container_width=True)

    with col2:
        if st.button("🔄 초기화", use_container_width=True):
            st.session_state.semantic_search_query = ""
            st.session_state.keyword_search_query = ""
            st.rerun()

    # 검색 실행
    if search_button and query:
        with st.spinner("검색 중..."):
            try:
                if search_mode == "semantic":
                    # 시맨틱 검색 파라미터 준비
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

                    # 시맨틱 검색 API 호출
                    response = api.search_articles_semantic(**search_params)
                    articles = response.get("results", [])

                else:  # 키워드 검색
                    # 키워드 검색 API 호출(고급 필터 없음)
                    response = api.search_articles_keyword(
                        query=query,
                        skip=0,
                        limit=limit,
                    )
                    articles = response.get("articles", [])

                st.markdown("---")
                st.markdown("### 📋 검색 결과")

                if articles:
                    st.success(f"✅ {len(articles)}개의 아티클을 찾았습니다.")

                    # 결과 표시
                    show_article_list(articles, show_similar_button=True)

                else:
                    st.warning("검색 결과가 없습니다. 다른 키워드를 시도하거나 필터를 조정해보세요.")

            except Exception as e:
                st.error(f"❌ 검색 중 오류가 발생했습니다: {str(e)}")

    elif search_button and not query:
        st.warning("⚠️ 검색어를 입력해주세요.")

    # 예시 쿼리 표시
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
                st.session_state.semantic_search_query = example
                st.rerun()


def _show_similar_search(api):
    """유사 아티클 검색 결과를 표시한다."""
    article_id = st.session_state.get("search_similar_id")

    st.markdown("### 🔍 유사 문서 검색")

    # 뒤로 가기 버튼
    if st.button("← 검색으로 돌아가기"):
        st.session_state.pop("search_similar_id", None)
        st.rerun()

    st.markdown(f"**참조 아티클 ID:** `{article_id}`")

    # 검색 파라미터
    limit = st.number_input("최대 결과 수", min_value=1, max_value=20, value=5)

    if st.button("🔍 유사 문서 검색", type="primary"):
        with st.spinner("유사 문서를 찾는 중..."):
            try:
                response = api.get_similar_articles(
                    article_id=article_id,
                    limit=limit,
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
