"""FastAPI client wrapper for Streamlit frontend."""

from typing import Any

import httpx
import streamlit as st


class APIClient:
    """Client for interacting with FastAPI backend."""

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.timeout = 30.0

    def _get_headers(self) -> dict[str, str]:
        """Get headers with access token if available."""
        headers = {"Content-Type": "application/json"}

        # Add access token if available in session
        if hasattr(st, "session_state"):
            token = st.session_state.get("access_token")
            if token:
                headers["Authorization"] = f"Bearer {token}"

        return headers

    def _handle_response(self, response: httpx.Response) -> dict[str, Any]:
        """Handle API response and errors."""
        try:
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            error_detail = "Unknown error"
            try:
                error_data = e.response.json()
                error_detail = error_data.get("detail", str(e))
            except Exception:
                error_detail = str(e)

            raise Exception(f"API Error: {error_detail}") from e

    # ========== Authentication ==========

    def request_magic_link(self, email: str) -> dict[str, Any]:
        """Request magic link for authentication."""
        with httpx.Client(timeout=self.timeout) as client:
            response = client.post(f"{self.base_url}/auth/magic-link", json={"email": email})
            return self._handle_response(response)

    def verify_magic_link(self, token: str) -> dict[str, Any]:
        """Verify magic link token and get access token."""
        with httpx.Client(timeout=self.timeout) as client:
            response = client.get(f"{self.base_url}/auth/verify?token={token}")
            return self._handle_response(response)

    # ========== User Management ==========

    def get_current_user(self) -> dict[str, Any]:
        """Get current authenticated user."""
        with httpx.Client(timeout=self.timeout) as client:
            response = client.get(f"{self.base_url}/users/me", headers=self._get_headers())
            return self._handle_response(response)

    def get_user_preferences(self, user_id: str) -> dict[str, Any]:
        """Get user preferences."""
        with httpx.Client(timeout=self.timeout) as client:
            response = client.get(
                f"{self.base_url}/users/{user_id}/preferences",
                headers=self._get_headers(),
            )
            return self._handle_response(response)

    def update_user_preferences(self, user_id: str, preferences: dict[str, Any]) -> dict[str, Any]:
        """Update user preferences."""
        with httpx.Client(timeout=self.timeout) as client:
            response = client.put(
                f"{self.base_url}/users/{user_id}/preferences",
                json=preferences,
                headers=self._get_headers(),
            )
            return self._handle_response(response)

    # ========== Articles ==========

    def get_articles(
        self,
        skip: int = 0,
        limit: int = 10,
        source_type: str | None = None,
        category: str | None = None,
        sort_by: str = "collected_at",
        order: str = "desc",
    ) -> dict[str, Any]:
        """Get articles with pagination and filters."""
        params = {
            "skip": skip,
            "limit": limit,
            "sort_by": sort_by,
            "order": order,
        }
        if source_type:
            params["source_type"] = source_type
        if category:
            params["category"] = category

        with httpx.Client(timeout=self.timeout) as client:
            response = client.get(
                f"{self.base_url}/articles",
                params=params,
                headers=self._get_headers(),
            )
            return self._handle_response(response)

    def get_article(self, article_id: str) -> dict[str, Any]:
        """Get single article by ID."""
        with httpx.Client(timeout=self.timeout) as client:
            response = client.get(f"{self.base_url}/articles/{article_id}", headers=self._get_headers())
            return self._handle_response(response)

    # ========== Semantic Search ==========

    def search_articles(
        self,
        query: str,
        limit: int = 10,
        score_threshold: float = 0.7,
        source_type: list[str] | None = None,
        category: list[str] | None = None,
        min_importance_score: float | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
    ) -> dict[str, Any]:
        """Search articles using semantic search."""
        payload = {
            "query": query,
            "limit": limit,
            "score_threshold": score_threshold,
        }
        if source_type:
            payload["source_type"] = source_type
        if category:
            payload["category"] = category
        if min_importance_score is not None:
            payload["min_importance_score"] = min_importance_score
        if date_from:
            payload["date_from"] = date_from
        if date_to:
            payload["date_to"] = date_to

        with httpx.Client(timeout=self.timeout) as client:
            response = client.post(f"{self.base_url}/search", json=payload, headers=self._get_headers())
            return self._handle_response(response)

    def find_similar_articles(
        self,
        article_id: str,
        limit: int = 5,
        score_threshold: float = 0.7,
    ) -> dict[str, Any]:
        """Find similar articles to a given article."""
        params = {
            "limit": limit,
            "score_threshold": score_threshold,
        }

        with httpx.Client(timeout=self.timeout) as client:
            response = client.get(
                f"{self.base_url}/articles/{article_id}/similar",
                params=params,
                headers=self._get_headers(),
            )
            return self._handle_response(response)

    # ========== Digests ==========

    def get_user_digests(self, user_id: str, skip: int = 0, limit: int = 10) -> dict[str, Any]:
        """Get user's digest history."""
        params = {"skip": skip, "limit": limit}

        with httpx.Client(timeout=self.timeout) as client:
            response = client.get(
                f"{self.base_url}/users/{user_id}/digests",
                params=params,
                headers=self._get_headers(),
            )
            return self._handle_response(response)

    def get_latest_digest(self, user_id: str) -> dict[str, Any]:
        """Get user's latest digest."""
        with httpx.Client(timeout=self.timeout) as client:
            response = client.get(
                f"{self.base_url}/users/{user_id}/digests/latest",
                headers=self._get_headers(),
            )
            return self._handle_response(response)

    def send_test_digest(self, user_id: str) -> dict[str, Any]:
        """Send test digest to user."""
        with httpx.Client(timeout=self.timeout) as client:
            response = client.post(
                f"{self.base_url}/users/{user_id}/digests/test",
                headers=self._get_headers(),
            )
            return self._handle_response(response)

    # ========== Feedback ==========

    def submit_feedback(
        self,
        user_id: str,
        article_id: str,
        rating: int,
        comment: str = "",
    ) -> dict[str, Any]:
        """Submit feedback for an article."""
        payload = {
            "user_id": user_id,
            "article_id": article_id,
            "rating": rating,
            "comment": comment,
        }

        with httpx.Client(timeout=self.timeout) as client:
            response = client.post(
                f"{self.base_url}/feedback",
                json=payload,
                headers=self._get_headers(),
            )
            return self._handle_response(response)

    def get_user_feedback(self, user_id: str, skip: int = 0, limit: int = 10) -> dict[str, Any]:
        """Get user's feedback history."""
        params = {"skip": skip, "limit": limit}

        with httpx.Client(timeout=self.timeout) as client:
            response = client.get(
                f"{self.base_url}/users/{user_id}/feedback",
                params=params,
                headers=self._get_headers(),
            )
            return self._handle_response(response)

    # ========== LLM (for onboarding chatbot) ==========

    def chat_completion(
        self,
        messages: list[dict[str, str]],
        provider: str = "openai",
    ) -> dict[str, Any]:
        """Get LLM chat completion."""
        payload = {
            "messages": messages,
            "provider": provider,
            "temperature": 0.7,
        }

        with httpx.Client(timeout=self.timeout) as client:
            response = client.post(
                f"{self.base_url}/llm/chat/completions",
                json=payload,
                headers=self._get_headers(),
            )
            return self._handle_response(response)


# Global API client instance
@st.cache_resource
def get_api_client() -> APIClient:
    """Get cached API client instance."""
    return APIClient()
