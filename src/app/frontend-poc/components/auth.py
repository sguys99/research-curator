"""Streamlit 앱 인증 컴포넌트."""

from collections.abc import Callable
from typing import Any

import streamlit as st

from app.frontend.utils.api_client import get_api_client
from app.frontend.utils.session import (
    clear_session,
    get_user_email,
    get_user_name,
    is_authenticated,
    set_user_session,
)


def show_login_page() -> None:
    """매직 링크 인증 로그인 페이지를 표시한다."""
    st.title("🔐 Research Curator")
    st.markdown("### AI 연구자를 위한 맞춤형 리서치 큐레이션")

    st.markdown("---")

    # 로그인 폼 중앙 배치
    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        st.markdown("#### 로그인")
        st.markdown("이메일 주소를 입력하시면 매직 링크를 보내드립니다.")

        email = st.text_input(
            "이메일 주소",
            placeholder="your-email@example.com",
            key="login_email",
        )

        if st.button("매직 링크 발송", type="primary", use_container_width=True):
            if not email:
                st.error("이메일 주소를 입력해주세요.")
            elif "@" not in email:
                st.error("유효한 이메일 주소를 입력해주세요.")
            else:
                with st.spinner("매직 링크를 발송하고 있습니다..."):
                    try:
                        api = get_api_client()
                        result = api.request_magic_link(email)

                        st.success("✅ 매직 링크가 발송되었습니다!")
                        st.info("이메일을 확인하시고 링크를 클릭해주세요.")

                        # 개발용 토큰 표시(프로덕션에서는 숨김)
                        if st.secrets.get("environment") == "development":
                            with st.expander("🔧 개발용 토큰 (프로덕션에서는 표시 안됨)"):
                                st.code(result.get("token", ""))
                                st.caption("위 토큰을 아래 '토큰으로 로그인'에 붙여넣으세요.")

                    except Exception as e:
                        st.error(f"❌ 오류가 발생했습니다: {str(e)}")

        st.markdown("---")

        # 토큰 기반 로그인(개발용)
        with st.expander("🔑 토큰으로 로그인 (개발용)"):
            st.caption("매직 링크 대신 토큰을 직접 입력할 수 있습니다.")

            token = st.text_input(
                "Access Token",
                type="password",
                placeholder="JWT token",
                key="login_token",
            )

            if st.button("토큰으로 로그인", use_container_width=True):
                if not token:
                    st.error("토큰을 입력해주세요.")
                else:
                    _handle_token_login(token)


def _handle_token_login(token: str) -> None:
    """토큰 기반 로그인을 처리한다."""
    with st.spinner("인증 중..."):
        try:
            api = get_api_client()

            # 매직 링크 토큰 검증 및 액세스 토큰 획득
            result = api.verify_magic_link(token)

            # 세션 설정
            set_user_session(
                user_id=result["user"]["id"],
                user_email=result["user"]["email"],
                user_name=result["user"].get("name", "User"),
                access_token=result["access_token"],
            )

            st.success("✅ 로그인 성공!")
            st.rerun()

        except Exception as e:
            st.error(f"❌ 로그인 실패: {str(e)}")
            clear_session()


def handle_magic_link_callback() -> None:
    """URL 파라미터의 매직 링크 콜백을 처리한다."""
    # URL 쿼리 파라미터에 토큰이 있는지 확인
    query_params = st.query_params

    if "token" in query_params:
        token = query_params["token"]

        with st.spinner("인증 중..."):
            try:
                api = get_api_client()

                # 매직 링크 토큰 검증
                result = api.verify_magic_link(token)

                # 세션 설정(user 객체에 사용자 데이터 포함)
                set_user_session(
                    user_id=result["user"]["id"],
                    user_email=result["user"]["email"],
                    user_name=result["user"].get("name", "User"),
                    access_token=result["access_token"],
                )

                # URL에서 토큰 제거
                st.query_params.clear()

                st.success("✅ 로그인 성공!")
                st.rerun()

            except Exception as e:
                st.error(f"❌ 인증 실패: {str(e)}")
                # URL에서 토큰 제거
                st.query_params.clear()


def show_logout_button() -> None:
    """사이드바에 로그아웃 버튼을 표시한다."""
    if st.sidebar.button("🚪 로그아웃", use_container_width=True):
        clear_session()
        st.success("로그아웃되었습니다.")
        st.rerun()


def show_user_info() -> None:
    """사이드바에 사용자 정보를 표시한다."""
    if is_authenticated():
        email = get_user_email()
        name = get_user_name()

        st.sidebar.markdown("---")
        st.sidebar.markdown("### 👤 사용자 정보")

        if name:
            st.sidebar.write(f"**이름:** {name}")
        st.sidebar.write(f"**이메일:** {email}")

        st.sidebar.markdown("---")


def require_auth(func: Callable[..., Any]) -> Callable[..., Any]:
    """페이지 접근 시 인증을 요구하는 데코레이터."""

    def wrapper(*args: Any, **kwargs: Any) -> Any:
        if not is_authenticated():
            st.warning("⚠️ 로그인이 필요한 페이지입니다.")
            show_login_page()
            st.stop()
        return func(*args, **kwargs)

    return wrapper
