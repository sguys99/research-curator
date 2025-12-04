"""Sidebar navigation component for Streamlit app."""

import streamlit as st

from app.frontend.components.auth import show_logout_button
from app.frontend.utils.session import (
    get_user_email,
    get_user_name,
    is_authenticated,
    is_onboarding_completed,
)


def show_sidebar() -> str | None:
    """Display sidebar with navigation menu.

    Returns:
        Selected page name or None if not authenticated.
    """
    if not is_authenticated():
        return None

    # App title
    st.sidebar.title("🔬 Research Curator")

    # User info
    _show_user_info()

    # Navigation menu
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 📑 메뉴")

    pages = []

    # Show onboarding if not completed
    if not is_onboarding_completed():
        pages.append(("🎯 온보딩", "onboarding"))
    else:
        # Show main pages if onboarding is completed
        pages.extend(
            [
                ("📊 대시보드", "dashboard"),
                ("🔍 검색", "search"),
                ("⚙️ 설정", "settings"),
                ("💬 피드백", "feedback"),
            ],
        )

    # Navigation buttons
    selected_page = None
    for label, page_name in pages:
        if st.sidebar.button(label, key=f"nav_{page_name}", use_container_width=True):
            selected_page = page_name

    # Help & Info
    st.sidebar.markdown("---")
    with st.sidebar.expander("ℹ️ 도움말"):
        st.markdown(
            """
            **Research Curator 사용법**

            1. **대시보드**: 최근 받은 이메일 확인
            2. **검색**: 과거 자료 시맨틱 검색
            3. **설정**: 키워드, 소스, 발송 시간 변경
            4. **피드백**: 받은 아티클 평가

            문제가 있으신가요?
            👉 contact@research-curator.com
            """,
        )

    # Logout button
    st.sidebar.markdown("---")
    show_logout_button()

    return selected_page


def _show_user_info() -> None:
    """Display user info in sidebar."""
    name = get_user_name()
    email = get_user_email()

    st.sidebar.markdown("---")

    # User avatar and name
    col1, col2 = st.sidebar.columns([1, 3])
    with col1:
        st.markdown("### 👤")
    with col2:
        if name:
            st.markdown(f"**{name}**")
        st.caption(email)


def show_page_header(title: str, description: str = "") -> None:
    """Display page header with title and description.

    Args:
        title: Page title.
        description: Optional page description.
    """
    st.title(title)
    if description:
        st.markdown(description)
    st.markdown("---")


def show_stats_cards(stats: list[tuple[str, str, str]]) -> None:
    """Display statistics cards in columns.

    Args:
        stats: List of (label, value, icon) tuples.
    """
    cols = st.columns(len(stats))

    for col, (label, value, icon) in zip(cols, stats, strict=False):
        with col:
            st.metric(
                label=f"{icon} {label}",
                value=value,
            )
