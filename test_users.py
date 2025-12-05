"""Test script for users endpoints."""

import httpx

BASE_URL = "http://localhost:8000"


def get_access_token():
    """Get access token for testing."""
    # Request magic link
    response = httpx.post(
        f"{BASE_URL}/auth/magic-link",
        json={"email": "test@example.com"},
        timeout=10.0,
    )
    magic_token = response.json().get("token")

    # Verify magic link
    response = httpx.get(
        f"{BASE_URL}/auth/verify",
        params={"token": magic_token},
        timeout=10.0,
    )
    return response.json().get("access_token"), response.json().get("user")["id"]


def test_get_current_user(access_token):
    """Test GET /users/me endpoint."""
    print("\n=== Testing GET /users/me ===")

    response = httpx.get(
        f"{BASE_URL}/users/me",
        headers={"Authorization": f"Bearer {access_token}"},
        timeout=10.0,
    )

    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()}")

    if response.status_code == 200:
        print("✅ Current user info retrieved successfully")
        return True
    else:
        print(f"❌ Failed: {response.json()}")
        return False


def test_get_preferences(access_token, user_id):
    """Test GET /users/{user_id}/preferences endpoint."""
    print(f"\n=== Testing GET /users/{user_id}/preferences ===")

    response = httpx.get(
        f"{BASE_URL}/users/{user_id}/preferences",
        headers={"Authorization": f"Bearer {access_token}"},
        timeout=10.0,
    )

    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()}")

    if response.status_code == 200:
        print("✅ Preferences retrieved successfully")
        return response.json()
    else:
        print(f"❌ Failed: {response.json()}")
        return None


def test_update_preferences(access_token, user_id):
    """Test PUT /users/{user_id}/preferences endpoint."""
    print(f"\n=== Testing PUT /users/{user_id}/preferences ===")

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

    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()}")

    if response.status_code == 200:
        print("✅ Preferences updated successfully")
        return True
    else:
        print(f"❌ Failed: {response.json()}")
        return False


def test_get_digests(access_token, user_id):
    """Test GET /users/{user_id}/digests endpoint."""
    print(f"\n=== Testing GET /users/{user_id}/digests ===")

    response = httpx.get(
        f"{BASE_URL}/users/{user_id}/digests",
        params={"skip": 0, "limit": 10},
        headers={"Authorization": f"Bearer {access_token}"},
        timeout=10.0,
    )

    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()}")

    if response.status_code == 200:
        digests_data = response.json()
        print(f"✅ Digests retrieved: {digests_data['total']} digests found")
        return True
    else:
        print(f"❌ Failed: {response.json()}")
        return False


def main():
    """Run all users tests."""
    print("🚀 Starting Users Endpoint Tests")
    print(f"Base URL: {BASE_URL}")

    # Get access token
    print("\n--- Getting access token ---")
    access_token, user_id = get_access_token()
    print("✅ Access token obtained")
    print(f"✅ User ID: {user_id}")

    # Run tests
    results = []

    # Test 1: Get current user
    results.append(test_get_current_user(access_token))

    # Test 2: Get preferences
    preferences = test_get_preferences(access_token, user_id)
    results.append(preferences is not None)

    # Test 3: Update preferences
    results.append(test_update_preferences(access_token, user_id))

    # Test 4: Get updated preferences
    updated_prefs = test_get_preferences(access_token, user_id)
    if updated_prefs:
        print("\n--- Verifying updates ---")
        print(f"Research fields: {updated_prefs['research_fields']}")
        print(f"Keywords: {updated_prefs['keywords']}")
        print(f"Email time: {updated_prefs['email_time']}")
        print(f"Daily limit: {updated_prefs['daily_limit']}")

    # Test 5: Get digests
    results.append(test_get_digests(access_token, user_id))

    # Summary
    print("\n" + "=" * 60)
    if all(results):
        print("✅ All tests passed!")
    else:
        print(f"⚠️ {sum(results)}/{len(results)} tests passed")
    print("=" * 60)


if __name__ == "__main__":
    main()
