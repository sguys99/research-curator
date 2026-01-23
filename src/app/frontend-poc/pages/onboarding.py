"""AI 챗봇 온보딩 페이지."""

import streamlit as st

from app.frontend.components.chatbot import show_onboarding_chatbot
from app.frontend.utils.session import is_authenticated


def show_onboarding_page() -> None:
    """AI 챗봇 온보딩 페이지를 표시한다."""
    if not is_authenticated():
        st.warning("⚠️ 로그인이 필요합니다.")
        st.stop()

    # 페이지 헤더
    st.markdown(
        """
        <style>
        .onboarding-header {
            text-align: center;
            padding: 1rem 0;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border-radius: 10px;
            margin-bottom: 2rem;
        }
        </style>
        <div class="onboarding-header">
            <h1>🚀 환영합니다!</h1>
            <p>AI 어시스턴트가 맞춤형 설정을 도와드립니다</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # 안내 박스
    with st.container():
        col1, col2, col3 = st.columns(3)

        with col1:
            st.info("⏱️ **소요 시간**\n\n약 2-3분")

        with col2:
            st.info("💬 **질문 수**\n\n5가지 질문")

        with col3:
            st.info("🎯 **맞춤 설정**\n\n연구 분야 + 키워드")

    st.markdown("---")

    # 챗봇 표시
    show_onboarding_chatbot()

    # 도움말 섹션
    with st.sidebar:
        st.markdown("---")
        st.markdown("### 💡 도움말")
        st.markdown(
            """
            **온보딩 진행 방법:**

            1. AI 어시스턴트의 질문에 답변
            2. 연구 분야와 키워드 입력
            3. 정보 유형 선택
            4. 이메일 설정 선택
            5. 확인 후 저장

            **팁:**
            - 여러 키워드는 쉼표로 구분
            - 언제든 수정 가능
            """,
        )


if __name__ == "__main__":
    show_onboarding_page()
