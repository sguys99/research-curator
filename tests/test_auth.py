"""End-to-end tests for auth endpoints (requires running server)."""

import os

import httpx
import pytest

BASE_URL = "http://localhost:8000"
LIVE_SERVER = os.getenv("PYTEST_LIVE_SERVER") == "1"


@pytest.mark.e2e
@pytest.mark.skipif(not LIVE_SERVER, reason="Set PYTEST_LIVE_SERVER=1 to run live server tests")
def test_magic_link():
    response = httpx.post(
        f"{BASE_URL}/auth/magic-link",
        json={"email": "test@example.com"},
        timeout=10.0,
    )

    assert response.status_code == 200
    data = response.json()
    token = data.get("token")
    assert token


@pytest.mark.e2e
@pytest.mark.skipif(not LIVE_SERVER, reason="Set PYTEST_LIVE_SERVER=1 to run live server tests")
def test_verify_magic_link():
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
    data = response.json()
    assert data.get("access_token")
    assert data.get("user")
