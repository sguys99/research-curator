"""End-to-end tests for users endpoints (requires running server)."""

import os

import httpx
import pytest

BASE_URL = "http://localhost:8000"
LIVE_SERVER = os.getenv("PYTEST_LIVE_SERVER") == "1"


@pytest.mark.e2e
@pytest.mark.skipif(not LIVE_SERVER, reason="Set PYTEST_LIVE_SERVER=1 to run live server tests")
def test_get_current_user():
    response = httpx.post(
        f"{BASE_URL}/auth/magic-link",
        json={"email": "test@example.com"},
        timeout=10.0,
    )
    assert response.status_code == 200
    token = response.json().get("token")
    assert token

    response = httpx.get(
        f"{BASE_URL}/auth/verify",
        params={"token": token},
        timeout=10.0,
    )
    assert response.status_code == 200
    access_token = response.json().get("access_token")
    user = response.json().get("user")
    assert access_token
    assert user

    response = httpx.get(
        f"{BASE_URL}/users/me",
        headers={"Authorization": f"Bearer {access_token}"},
        timeout=10.0,
    )
    assert response.status_code == 200


@pytest.mark.e2e
@pytest.mark.skipif(not LIVE_SERVER, reason="Set PYTEST_LIVE_SERVER=1 to run live server tests")
def test_get_and_update_preferences():
    response = httpx.post(
        f"{BASE_URL}/auth/magic-link",
        json={"email": "test@example.com"},
        timeout=10.0,
    )
    assert response.status_code == 200
    token = response.json().get("token")
    assert token

    response = httpx.get(
        f"{BASE_URL}/auth/verify",
        params={"token": token},
        timeout=10.0,
    )
    assert response.status_code == 200
    access_token = response.json().get("access_token")
    user_id = response.json().get("user")["id"]
    assert access_token
    assert user_id

    response = httpx.get(
        f"{BASE_URL}/users/{user_id}/preferences",
        headers={"Authorization": f"Bearer {access_token}"},
        timeout=10.0,
    )
    assert response.status_code in {200, 404}

    update_data = {
        "research_fields": ["Machine Learning", "Natural Language Processing", "Computer Vision"],
        "keywords": ["transformer", "GPT", "BERT", "attention", "neural networks"],
        "sources": ["arxiv.org", "techcrunch.com", "MIT Technology Review"],
        "info_types": {"paper": 0.5, "news": 0.3, "report": 0.2},
        "email_time": "09:00",
        "daily_limit": 10,
        "email_enabled": True,
    }

    response = httpx.put(
        f"{BASE_URL}/users/{user_id}/preferences",
        json=update_data,
        headers={"Authorization": f"Bearer {access_token}"},
        timeout=10.0,
    )

    assert response.status_code in {200, 201}


@pytest.mark.e2e
@pytest.mark.skipif(not LIVE_SERVER, reason="Set PYTEST_LIVE_SERVER=1 to run live server tests")
def test_get_digests():
    response = httpx.post(
        f"{BASE_URL}/auth/magic-link",
        json={"email": "test@example.com"},
        timeout=10.0,
    )
    assert response.status_code == 200
    token = response.json().get("token")
    assert token

    response = httpx.get(
        f"{BASE_URL}/auth/verify",
        params={"token": token},
        timeout=10.0,
    )
    assert response.status_code == 200
    access_token = response.json().get("access_token")
    user_id = response.json().get("user")["id"]
    assert access_token
    assert user_id

    response = httpx.get(
        f"{BASE_URL}/users/{user_id}/digests",
        params={"skip": 0, "limit": 10},
        headers={"Authorization": f"Bearer {access_token}"},
        timeout=10.0,
    )
    assert response.status_code == 200
