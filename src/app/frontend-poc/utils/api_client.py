"""Streamlit 프런트엔드용 FastAPI 클라이언트 래퍼."""

from typing import Any

import httpx
import streamlit as st


class APIClient:
    """FastAPI 백엔드와 통신하는 클라이언트."""

    def __init__(self, base_url: str = "http://localhost:8000") -> None:
        self.base_url = base_url
        self.timeout = 30.0

    def _get_headers(self) -> dict[str, str]:
        """액세스 토큰을 포함한 헤더를 반환한다."""
        headers = {"Content-Type": "application/json"}

        # 세션에 토큰이 있으면 추가
        if hasattr(st, "session_state"):
            token = st.session_state.get("access_token")
            if token:
                headers["Authorization"] = f"Bearer {token}"

        return headers

    def _handle_response(self, response: httpx.Response) -> dict[str, Any]:
        """API 응답과 오류를 처리한다."""
        try:
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            status_code = e.response.status_code
            error_detail = "Unknown error"

            try:
                error_data = e.response.json()
                error_detail = error_data.get("detail", str(e))
            except Exception:
                error_detail = str(e)

            # 상태 코드별 처리
            if status_code == 401:
                error_msg = "인증이 필요합니다. 다시 로그인해주세요."
                # 세션 토큰 제거
                if hasattr(st, "session_state"):
                    st.session_state.pop("access_token", None)
                    st.session_state.pop("user", None)
            elif status_code == 403:
                error_msg = f"권한이 없습니다: {error_detail}"
            elif status_code == 404:
                error_msg = f"리소스를 찾을 수 없습니다: {error_detail}"
            elif status_code == 500:
                error_msg = f"서버 오류가 발생했습니다: {error_detail}"
            else:
                error_msg = f"API 오류 ({status_code}): {error_detail}"

            raise Exception(error_msg) from e
        except httpx.TimeoutException as e:
            raise Exception("요청 시간이 초과되었습니다. 다시 시도해주세요.") from e
        except httpx.RequestError as e:
            raise Exception(f"네트워크 오류가 발생했습니다: {str(e)}") from e

    # ========== Authentication ==========

    def request_magic_link(self, email: str) -> dict[str, Any]:
        """인증용 매직 링크를 요청한다."""
        with httpx.Client(timeout=self.timeout) as client:
            response = client.post(f"{self.base_url}/auth/magic-link", json={"email": email})
            return self._handle_response(response)

    def verify_magic_link(self, token: str) -> dict[str, Any]:
        """매직 링크 토큰을 검증하고 액세스 토큰을 받는다."""
        with httpx.Client(timeout=self.timeout) as client:
            response = client.get(f"{self.base_url}/auth/verify?token={token}")
            return self._handle_response(response)

    # ========== User Management ==========

    def get_current_user(self) -> dict[str, Any]:
        """현재 인증된 사용자를 조회한다."""
        with httpx.Client(timeout=self.timeout) as client:
            response = client.get(f"{self.base_url}/users/me", headers=self._get_headers())
            return self._handle_response(response)

    def get_user_preferences(self, user_id: str) -> dict[str, Any]:
        """사용자 선호도를 조회한다."""
        with httpx.Client(timeout=self.timeout) as client:
            response = client.get(
                f"{self.base_url}/users/{user_id}/preferences",
                headers=self._get_headers(),
            )
            return self._handle_response(response)

    def update_user_preferences(self, user_id: str, preferences: dict[str, Any]) -> dict[str, Any]:
        """사용자 선호도를 업데이트한다."""
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
        limit: int = 20,
        source_type: list[str] | None = None,
        category: list[str] | None = None,
        min_importance_score: float | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
        order_by: str = "collected_at",
        order_desc: bool = True,
    ) -> dict[str, Any]:
        """페이지네이션/필터로 아티클을 조회한다."""
        params = {
            "skip": skip,
            "limit": limit,
            "order_by": order_by,
            "order_desc": order_desc,
        }
        if source_type:
            params["source_type"] = source_type
        if category:
            params["category"] = category
        if min_importance_score is not None:
            params["min_importance_score"] = min_importance_score
        if date_from:
            params["date_from"] = date_from
        if date_to:
            params["date_to"] = date_to

        with httpx.Client(timeout=self.timeout) as client:
            response = client.get(
                f"{self.base_url}/api/articles",
                params=params,
                headers=self._get_headers(),
            )
            return self._handle_response(response)

    def get_article(self, article_id: str) -> dict[str, Any]:
        """ID로 아티클을 조회한다."""
        with httpx.Client(timeout=self.timeout) as client:
            response = client.get(
                f"{self.base_url}/api/articles/{article_id}",
                headers=self._get_headers(),
            )
            return self._handle_response(response)

    def get_articles_batch(self, article_ids: list[str]) -> dict[str, Any]:
        """여러 ID로 아티클을 배치 조회한다."""
        payload = {"article_ids": article_ids}

        with httpx.Client(timeout=self.timeout) as client:
            response = client.post(
                f"{self.base_url}/api/articles/batch",
                json=payload,
                headers=self._get_headers(),
            )
            return self._handle_response(response)

    def get_article_statistics(
        self,
        date_from: str | None = None,
        date_to: str | None = None,
    ) -> dict[str, Any]:
        """아티클 통계를 조회한다."""
        params = {}
        if date_from:
            params["date_from"] = date_from
        if date_to:
            params["date_to"] = date_to

        with httpx.Client(timeout=self.timeout) as client:
            response = client.get(
                f"{self.base_url}/api/articles/statistics/summary",
                params=params,
                headers=self._get_headers(),
            )
            return self._handle_response(response)

    def delete_article(self, article_id: str) -> dict[str, Any]:
        """ID로 아티클을 삭제한다."""
        with httpx.Client(timeout=self.timeout) as client:
            response = client.delete(
                f"{self.base_url}/api/articles/{article_id}",
                headers=self._get_headers(),
            )
            return self._handle_response(response)

    # ========== Semantic Search ==========

    def search_articles_semantic(
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
        """시맨틱 검색(벡터 DB)으로 아티클을 조회한다."""
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
            response = client.post(
                f"{self.base_url}/api/articles/search",
                json=payload,
                headers=self._get_headers(),
            )
            return self._handle_response(response)

    def search_articles_keyword(
        self,
        query: str,
        skip: int = 0,
        limit: int = 20,
    ) -> dict[str, Any]:
        """키워드 검색(ILIKE 패턴 매칭)으로 아티클을 조회한다."""
        params = {
            "query": query,
            "skip": skip,
            "limit": limit,
        }

        with httpx.Client(timeout=self.timeout) as client:
            response = client.get(
                f"{self.base_url}/api/articles/keyword-search",
                params=params,
                headers=self._get_headers(),
            )
            return self._handle_response(response)

    def get_similar_articles(
        self,
        article_id: str,
        limit: int = 5,
    ) -> dict[str, Any]:
        """특정 아티클과 유사한 아티클을 찾는다."""
        params = {"limit": limit}

        with httpx.Client(timeout=self.timeout) as client:
            response = client.get(
                f"{self.base_url}/api/articles/{article_id}/similar",
                params=params,
                headers=self._get_headers(),
            )
            return self._handle_response(response)

    # ========== Digests ==========

    def get_user_digests(self, user_id: str, skip: int = 0, limit: int = 10) -> dict[str, Any]:
        """사용자 다이제스트 히스토리를 조회한다."""
        params = {"skip": skip, "limit": limit}

        with httpx.Client(timeout=self.timeout) as client:
            response = client.get(
                f"{self.base_url}/users/{user_id}/digests",
                params=params,
                headers=self._get_headers(),
            )
            return self._handle_response(response)

    def get_latest_digest(self, user_id: str) -> dict[str, Any]:
        """사용자의 최신 다이제스트를 조회한다."""
        with httpx.Client(timeout=self.timeout) as client:
            response = client.get(
                f"{self.base_url}/users/{user_id}/digests/latest",
                headers=self._get_headers(),
            )
            return self._handle_response(response)

    def send_test_digest(self, user_id: str) -> dict[str, Any]:
        """사용자에게 테스트 다이제스트를 보낸다."""
        with httpx.Client(timeout=self.timeout) as client:
            response = client.post(
                f"{self.base_url}/users/{user_id}/digests/test",
                headers=self._get_headers(),
            )
            return self._handle_response(response)

    # ========== Feedback ==========

    def create_feedback(
        self,
        article_id: str,
        rating: int,
        comment: str | None = None,
    ) -> dict[str, Any]:
        """아티클 피드백을 생성한다(JWT의 user_id 사용)."""
        payload = {
            "article_id": article_id,
            "rating": rating,
        }
        if comment:
            payload["comment"] = comment

        with httpx.Client(timeout=self.timeout) as client:
            response = client.post(
                f"{self.base_url}/api/feedback",
                json=payload,
                headers=self._get_headers(),
            )
            return self._handle_response(response)

    def get_feedback(self, feedback_id: str) -> dict[str, Any]:
        """ID로 피드백을 조회한다."""
        with httpx.Client(timeout=self.timeout) as client:
            response = client.get(
                f"{self.base_url}/api/feedback/{feedback_id}",
                headers=self._get_headers(),
            )
            return self._handle_response(response)

    def update_feedback(
        self,
        feedback_id: str,
        rating: int | None = None,
        comment: str | None = None,
    ) -> dict[str, Any]:
        """피드백을 업데이트한다."""
        payload = {}
        if rating is not None:
            payload["rating"] = rating
        if comment is not None:
            payload["comment"] = comment

        with httpx.Client(timeout=self.timeout) as client:
            response = client.put(
                f"{self.base_url}/api/feedback/{feedback_id}",
                json=payload,
                headers=self._get_headers(),
            )
            return self._handle_response(response)

    def delete_feedback(self, feedback_id: str) -> dict[str, Any]:
        """피드백을 삭제한다."""
        with httpx.Client(timeout=self.timeout) as client:
            response = client.delete(
                f"{self.base_url}/api/feedback/{feedback_id}",
                headers=self._get_headers(),
            )
            return self._handle_response(response)

    def get_user_feedback(self, user_id: str, skip: int = 0, limit: int = 20) -> dict[str, Any]:
        """사용자 피드백 목록을 조회한다."""
        params = {"skip": skip, "limit": limit}

        with httpx.Client(timeout=self.timeout) as client:
            response = client.get(
                f"{self.base_url}/api/feedback/user/{user_id}",
                params=params,
                headers=self._get_headers(),
            )
            return self._handle_response(response)

    def get_article_feedback(
        self,
        article_id: str,
        skip: int = 0,
        limit: int = 20,
    ) -> dict[str, Any]:
        """특정 아티클의 피드백을 조회한다."""
        params = {"skip": skip, "limit": limit}

        with httpx.Client(timeout=self.timeout) as client:
            response = client.get(
                f"{self.base_url}/api/feedback/article/{article_id}",
                params=params,
                headers=self._get_headers(),
            )
            return self._handle_response(response)

    def get_article_feedback_stats(self, article_id: str) -> dict[str, Any]:
        """아티클 피드백 통계를 조회한다."""
        with httpx.Client(timeout=self.timeout) as client:
            response = client.get(
                f"{self.base_url}/api/feedback/article/{article_id}/stats",
                headers=self._get_headers(),
            )
            return self._handle_response(response)

    # ========== LLM (for onboarding chatbot) ==========

    def chat_completion(
        self,
        messages: list[dict[str, str]],
        provider: str = "openai",
    ) -> dict[str, Any]:
        """LLM 채팅 완료 응답을 조회한다."""
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

    # ========== Scheduler ==========

    def get_scheduler_status(self) -> dict[str, Any]:
        """스케줄러 상태를 조회한다."""
        with httpx.Client(timeout=self.timeout) as client:
            response = client.get(
                f"{self.base_url}/api/scheduler/status",
                headers=self._get_headers(),
            )
            return self._handle_response(response)

    def start_scheduler(self) -> dict[str, Any]:
        """스케줄러를 시작한다."""
        with httpx.Client(timeout=self.timeout) as client:
            response = client.post(
                f"{self.base_url}/api/scheduler/control",
                json={"action": "start"},
                headers=self._get_headers(),
            )
            return self._handle_response(response)

    def stop_scheduler(self) -> dict[str, Any]:
        """스케줄러를 중지한다."""
        with httpx.Client(timeout=self.timeout) as client:
            response = client.post(
                f"{self.base_url}/api/scheduler/control",
                json={"action": "stop"},
                headers=self._get_headers(),
            )
            return self._handle_response(response)

    def trigger_job(self, job_id: str) -> dict[str, Any]:
        """스케줄된 잡을 수동 실행한다."""
        with httpx.Client(timeout=60.0) as client:  # 잡 실행용 긴 타임아웃
            response = client.post(
                f"{self.base_url}/api/scheduler/jobs/trigger",
                json={"job_id": job_id},
                headers=self._get_headers(),
            )
            return self._handle_response(response)


# 전역 API 클라이언트 인스턴스
@st.cache_resource
def get_api_client() -> APIClient:
    """캐시된 API 클라이언트를 반환한다."""
    # secrets에서 base URL을 가져오거나 기본값 사용
    base_url = st.secrets.get("api_base_url", "http://localhost:8000")
    return APIClient(base_url=base_url)
