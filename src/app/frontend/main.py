"""Main entry point for Research Curator Streamlit application."""

import streamlit as st

from app.frontend.components.auth import (
    handle_magic_link_callback,
    show_login_page,
)
from app.frontend.components.sidebar import show_sidebar
from app.frontend.utils.session import init_session_state, is_authenticated, is_onboarding_completed

# Page configuration
st.set_page_config(
    page_title="Research Curator",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded",
)


def main():
    """Main application logic."""
    # Initialize session state
    init_session_state()

    # Handle magic link callback from URL
    handle_magic_link_callback()

    # Check authentication
    if not is_authenticated():
        show_login_page()
        return

    # Show sidebar and get selected page
    selected_page = show_sidebar()

    # Route to selected page
    if selected_page:
        _navigate_to_page(selected_page)
    else:
        # Default page based on onboarding status
        if not is_onboarding_completed():
            _show_onboarding_page()
        else:
            _show_dashboard_page()


def _navigate_to_page(page_name: str) -> None:
    """Navigate to selected page.

    Args:
        page_name: Name of the page to navigate to.
    """
    if page_name == "onboarding":
        _show_onboarding_page()
    elif page_name == "dashboard":
        _show_dashboard_page()
    elif page_name == "search":
        _show_search_page()
    elif page_name == "settings":
        _show_settings_page()
    elif page_name == "feedback":
        _show_feedback_page()
    else:
        st.error(f"Unknown page: {page_name}")


def _show_onboarding_page() -> None:
    """Display onboarding page."""
    from app.frontend.pages.onboarding import show_onboarding_page

    show_onboarding_page()


def _show_dashboard_page() -> None:
    """Display dashboard page (placeholder)."""
    from app.frontend.components.sidebar import show_page_header, show_stats_cards

    show_page_header("📊 대시보드", "최근 받은 연구 자료를 확인하세요")

    # Placeholder stats
    show_stats_cards(
        [
            ("총 아티클", "0", "📚"),
            ("오늘 받은 이메일", "0", "📧"),
            ("평균 피드백", "0.0", "⭐"),
        ],
    )

    st.info("⚠️ 대시보드 페이지는 Checkpoint 3에서 구현됩니다.")


def _show_search_page() -> None:
    """Display search page (placeholder)."""
    from app.frontend.components.sidebar import show_page_header

    show_page_header("🔍 시맨틱 검색", "과거 자료를 자연어로 검색하세요")

    st.text_input("검색어를 입력하세요", placeholder="예: transformer 모델 최적화")
    st.button("검색", type="primary")

    st.info("⚠️ 검색 페이지는 Checkpoint 3에서 구현됩니다.")


def _show_settings_page() -> None:
    """Display settings page (placeholder)."""
    from app.frontend.components.sidebar import show_page_header

    show_page_header("⚙️ 설정", "연구 분야, 키워드, 발송 시간 등을 변경하세요")

    st.info("⚠️ 설정 페이지는 Checkpoint 3에서 구현됩니다.")


def _show_feedback_page() -> None:
    """Display feedback page (placeholder)."""
    from app.frontend.components.sidebar import show_page_header

    show_page_header("💬 피드백", "받은 아티클을 평가해주세요")

    st.info("⚠️ 피드백 페이지는 Checkpoint 4에서 구현됩니다.")


if __name__ == "__main__":
    main()
