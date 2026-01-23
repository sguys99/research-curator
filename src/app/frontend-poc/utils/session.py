"""Streamlit 앱 세션 관리 유틸리티."""

import os
from datetime import datetime
from typing import Any

import streamlit as st


def init_session_state() -> None:
    """기본값으로 세션 상태를 초기화한다."""
    defaults = {
        "authenticated": False,
        "user_id": None,
        "user_email": None,
        "user_name": None,
        "access_token": None,
        "token_expires_at": None,
        "current_page": "dashboard",
        "preferences": None,
        "onboarding_completed": False,
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def set_user_session(
    user_id: str,
    user_email: str,
    user_name: str,
    access_token: str,
    expires_at: datetime | None = None,
) -> None:
    """인증 성공 후 사용자 세션을 설정한다."""
    st.session_state.authenticated = True
    st.session_state.user_id = user_id
    st.session_state.user_email = user_email
    st.session_state.user_name = user_name
    st.session_state.access_token = access_token
    st.session_state.token_expires_at = expires_at


def clear_session() -> None:
    """세션 데이터를 모두 지운다(로그아웃)."""
    keys_to_clear = [
        "authenticated",
        "user_id",
        "user_email",
        "user_name",
        "access_token",
        "token_expires_at",
        "preferences",
    ]

    for key in keys_to_clear:
        if key in st.session_state:
            st.session_state[key] = None

    st.session_state.authenticated = False


def is_authenticated() -> bool:
    """사용자 인증 여부를 확인한다."""
    return st.session_state.get("authenticated", False)


def get_user_id() -> str | None:
    """세션에서 사용자 ID를 가져온다."""
    return st.session_state.get("user_id")


def get_user_email() -> str | None:
    """세션에서 사용자 이메일을 가져온다."""
    return st.session_state.get("user_email")


def get_user_name() -> str | None:
    """세션에서 사용자 이름을 가져온다."""
    return st.session_state.get("user_name")


def get_access_token() -> str | None:
    """세션에서 액세스 토큰을 가져온다."""
    return st.session_state.get("access_token")


def set_preferences(preferences: dict[str, Any]) -> None:
    """사용자 선호도를 세션에 저장한다."""
    st.session_state.preferences = preferences


def get_preferences() -> dict[str, Any] | None:
    """세션에서 사용자 선호도를 가져온다."""
    return st.session_state.get("preferences")


def is_token_valid() -> bool:
    """액세스 토큰 유효 여부를 확인한다."""
    if not st.session_state.get("access_token"):
        return False

    expires_at = st.session_state.get("token_expires_at")
    if expires_at and isinstance(expires_at, datetime):
        return datetime.now() < expires_at

    # 만료 시간이 없으면 유효하다고 가정
    return True


def mark_onboarding_completed() -> None:
    """온보딩 완료 상태로 표시한다."""
    st.session_state.onboarding_completed = True


def is_onboarding_completed() -> bool:
    """온보딩 완료 여부를 확인한다."""
    return st.session_state.get("onboarding_completed", False)


def set_current_page(page: str) -> None:
    """세션에 현재 페이지를 설정한다."""
    st.session_state.current_page = page


def get_current_page() -> str:
    """세션에서 현재 페이지를 가져온다."""
    return st.session_state.get("current_page", "dashboard")


def is_admin_user() -> bool:
    """현재 사용자가 관리자 인지 확인한다(환경 변수 기준)."""
    # 환경 변수 또는 Streamlit secrets에서 관리자 이메일 조회
    admin_emails_str = os.getenv("ADMIN_EMAILS", "")

    # Streamlit secrets도 폴백으로 확인
    if not admin_emails_str and hasattr(st, "secrets"):
        admin_emails_str = st.secrets.get("ADMIN_EMAILS", "")

    # 쉼표로 구분된 이메일 파싱
    admin_emails = [email.strip() for email in admin_emails_str.split(",") if email.strip()]

    # 현재 사용자 이메일이 관리자 목록에 있는지 확인
    user_email = get_user_email()
    return user_email in admin_emails if user_email else False
