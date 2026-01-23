"""Streamlit 앱 사이드바 네비게이션 컴포넌트."""

import streamlit as st

from app.frontend.components.auth import show_logout_button
from app.frontend.utils.session import (
    get_user_email,
    get_user_name,
    is_admin_user,
    is_authenticated,
    is_onboarding_completed,
)


def show_sidebar() -> str | None:
    """네비게이션 메뉴가 있는 사이드바를 표시한다.

    Returns:
        선택된 페이지 이름(미인증이면 None)
    """
    if not is_authenticated():
        return None

    # 앱 타이틀
    st.sidebar.title("🔬 Research Curator")

    # 사용자 정보
    _show_user_info()

    # 네비게이션 메뉴
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 📑 메뉴")

    pages = []

    # 온보딩 미완료 시 온보딩 표시
    if not is_onboarding_completed():
        pages.append(("🎯 온보딩", "onboarding"))
    else:
        # 온보딩 완료 시 메인 페이지 표시
        pages.extend(
            [
                ("📊 대시보드", "dashboard"),
                ("🔍 검색", "search"),
                ("⚙️ 설정", "settings"),
                ("💬 피드백", "feedback"),
            ],
        )

    # 네비게이션 버튼
    selected_page = None
    for label, page_name in pages:
        if st.sidebar.button(label, key=f"nav_{page_name}", use_container_width=True):
            selected_page = page_name

    # 관리자 섹션(관리자 전용)
    if is_admin_user():
        st.sidebar.markdown("---")
        st.sidebar.markdown("### 🛠️ Admin")
        if st.sidebar.button("Admin Dashboard", key="nav_admin", use_container_width=True):
            selected_page = "admin"

    # 도움말/정보
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

    # 로그아웃 버튼
    st.sidebar.markdown("---")
    show_logout_button()

    return selected_page


def _show_user_info() -> None:
    """사이드바에 사용자 정보를 표시한다."""
    name = get_user_name()
    email = get_user_email()

    st.sidebar.markdown("---")

    # 사용자 아바타와 이름
    col1, col2 = st.sidebar.columns([1, 3])
    with col1:
        st.markdown("### 👤")
    with col2:
        if name:
            st.markdown(f"**{name}**")
        st.caption(email)


def show_page_header(title: str, description: str = "") -> None:
    """제목/설명 포함 페이지 헤더를 표시한다.

    Args:
        title: 페이지 제목
        description: 페이지 설명(선택)
    """
    st.title(title)
    if description:
        st.markdown(description)
    st.markdown("---")


def show_stats_cards(stats: list[tuple[str, str, str]]) -> None:
    """통계 카드들을 컬럼으로 표시한다.

    Args:
        stats: (label, value, icon) 튜플 목록
    """
    cols = st.columns(len(stats))

    for col, (label, value, icon) in zip(cols, stats, strict=False):
        with col:
            st.metric(
                label=f"{icon} {label}",
                value=value,
            )
