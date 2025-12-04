"""Session management utilities for Streamlit app."""

from datetime import datetime
from typing import Any

import streamlit as st


def init_session_state() -> None:
    """Initialize session state with default values."""
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
    """Set user session after successful authentication."""
    st.session_state.authenticated = True
    st.session_state.user_id = user_id
    st.session_state.user_email = user_email
    st.session_state.user_name = user_name
    st.session_state.access_token = access_token
    st.session_state.token_expires_at = expires_at


def clear_session() -> None:
    """Clear all session data (logout)."""
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
    """Check if user is authenticated."""
    return st.session_state.get("authenticated", False)


def get_user_id() -> str | None:
    """Get current user ID from session."""
    return st.session_state.get("user_id")


def get_user_email() -> str | None:
    """Get current user email from session."""
    return st.session_state.get("user_email")


def get_user_name() -> str | None:
    """Get current user name from session."""
    return st.session_state.get("user_name")


def get_access_token() -> str | None:
    """Get access token from session."""
    return st.session_state.get("access_token")


def set_preferences(preferences: dict[str, Any]) -> None:
    """Store user preferences in session."""
    st.session_state.preferences = preferences


def get_preferences() -> dict[str, Any] | None:
    """Get user preferences from session."""
    return st.session_state.get("preferences")


def is_token_valid() -> bool:
    """Check if access token is still valid."""
    if not st.session_state.get("access_token"):
        return False

    expires_at = st.session_state.get("token_expires_at")
    if expires_at and isinstance(expires_at, datetime):
        return datetime.now() < expires_at

    # If no expiration time set, assume token is valid
    return True


def mark_onboarding_completed() -> None:
    """Mark onboarding as completed."""
    st.session_state.onboarding_completed = True


def is_onboarding_completed() -> bool:
    """Check if onboarding is completed."""
    return st.session_state.get("onboarding_completed", False)


def set_current_page(page: str) -> None:
    """Set current page in session."""
    st.session_state.current_page = page


def get_current_page() -> str:
    """Get current page from session."""
    return st.session_state.get("current_page", "dashboard")
