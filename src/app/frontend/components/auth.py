"""Authentication components for Streamlit app."""

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
    """Display login page with magic link authentication."""
    st.title("🔐 Research Curator")
    st.markdown("### AI 연구자를 위한 맞춤형 리서치 큐레이션")

    st.markdown("---")

    # Center the login form
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

                        # Show token for development (remove in production)
                        if st.secrets.get("environment") == "development":
                            with st.expander("🔧 개발용 토큰 (프로덕션에서는 표시 안됨)"):
                                st.code(result.get("token", ""))
                                st.caption("위 토큰을 아래 '토큰으로 로그인'에 붙여넣으세요.")

                    except Exception as e:
                        st.error(f"❌ 오류가 발생했습니다: {str(e)}")

        st.markdown("---")

        # Token-based login (for development)
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
    """Handle token-based login."""
    with st.spinner("인증 중..."):
        try:
            api = get_api_client()

            # Verify token (this would actually call verify endpoint)
            # For now, we'll set the token and try to get user info
            st.session_state.access_token = token

            # Get user info
            user_data = api.get_current_user()

            # Set session
            set_user_session(
                user_id=user_data["id"],
                user_email=user_data["email"],
                user_name=user_data.get("name", "User"),
                access_token=token,
            )

            st.success("✅ 로그인 성공!")
            st.rerun()

        except Exception as e:
            st.error(f"❌ 로그인 실패: {str(e)}")
            clear_session()


def handle_magic_link_callback() -> None:
    """Handle magic link callback from URL parameters."""
    # Check if token is in URL query params
    query_params = st.query_params

    if "token" in query_params:
        token = query_params["token"]

        with st.spinner("인증 중..."):
            try:
                api = get_api_client()

                # Verify magic link token
                result = api.verify_magic_link(token)

                # Set session
                set_user_session(
                    user_id=result["user_id"],
                    user_email=result["email"],
                    user_name=result.get("name", "User"),
                    access_token=result["access_token"],
                )

                # Clear token from URL
                st.query_params.clear()

                st.success("✅ 로그인 성공!")
                st.rerun()

            except Exception as e:
                st.error(f"❌ 인증 실패: {str(e)}")
                # Clear token from URL
                st.query_params.clear()


def show_logout_button() -> None:
    """Display logout button in sidebar."""
    if st.sidebar.button("🚪 로그아웃", use_container_width=True):
        clear_session()
        st.success("로그아웃되었습니다.")
        st.rerun()


def show_user_info() -> None:
    """Display user info in sidebar."""
    if is_authenticated():
        email = get_user_email()
        name = get_user_name()

        st.sidebar.markdown("---")
        st.sidebar.markdown("### 👤 사용자 정보")

        if name:
            st.sidebar.write(f"**이름:** {name}")
        st.sidebar.write(f"**이메일:** {email}")

        st.sidebar.markdown("---")


def require_auth(func):
    """Decorator to require authentication for a page."""

    def wrapper(*args, **kwargs):
        if not is_authenticated():
            st.warning("⚠️ 로그인이 필요한 페이지입니다.")
            show_login_page()
            st.stop()
        return func(*args, **kwargs)

    return wrapper
