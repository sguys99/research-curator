"""Research Curator Streamlit 앱 진입점."""

import streamlit as st
from dotenv import load_dotenv

from app.frontend.components.auth import (
    handle_magic_link_callback,
    show_login_page,
)
from app.frontend.components.sidebar import show_sidebar
from app.frontend.utils.session import (
    init_session_state,
    is_authenticated,
    is_onboarding_completed,
)

# .env에서 환경 변수 로드
load_dotenv()

# 페이지 설정
st.set_page_config(
    page_title="Research Curator",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded",
)


def main():
    """메인 애플리케이션 로직."""
    # 세션 상태 초기화
    init_session_state()

    # URL의 매직 링크 콜백 처리
    handle_magic_link_callback()

    # 인증 여부 확인
    if not is_authenticated():
        show_login_page()
        return

    # 사이드바 표시 및 페이지 선택
    selected_page = show_sidebar()

    # 선택 페이지로 라우팅
    if selected_page:
        _navigate_to_page(selected_page)
    else:
        # 온보딩 완료 여부에 따른 기본 페이지
        if not is_onboarding_completed():
            _show_onboarding_page()
        else:
            _show_dashboard_page()


def _navigate_to_page(page_name: str) -> None:
    """선택된 페이지로 이동한다.

    Args:
        page_name: 이동할 페이지 이름
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
    elif page_name == "admin":
        _show_admin_page()
    else:
        st.error(f"Unknown page: {page_name}")


def _show_onboarding_page() -> None:
    """온보딩 페이지를 표시한다."""
    from app.frontend.pages.onboarding import show_onboarding_page

    show_onboarding_page()


def _show_dashboard_page() -> None:
    """대시보드 페이지를 표시한다."""
    from app.frontend.pages.dashboard import show_dashboard_page

    show_dashboard_page()


def _show_search_page() -> None:
    """검색 페이지를 표시한다."""
    from app.frontend.pages.search import show_search_page

    show_search_page()


def _show_settings_page() -> None:
    """설정 페이지를 표시한다."""
    from app.frontend.pages.settings import show_settings_page

    show_settings_page()


def _show_feedback_page() -> None:
    """피드백 페이지를 표시한다."""
    from app.frontend.pages.feedback import show_feedback_page

    show_feedback_page()


def _show_admin_page() -> None:
    """관리자 페이지를 표시한다."""
    from app.frontend.pages.admin import show_admin_page

    show_admin_page()


if __name__ == "__main__":
    main()
