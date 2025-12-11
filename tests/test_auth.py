"""Test script for authentication endpoints."""

import httpx

BASE_URL = "http://localhost:8000"


def test_magic_link():
    """Test magic link request endpoint."""
    print("\n=== Testing Magic Link Request ===")

    # Request magic link
    response = httpx.post(
        f"{BASE_URL}/auth/magic-link",
        json={"email": "test@example.com"},
        timeout=10.0,
    )

    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()}")

    if response.status_code == 200:
        data = response.json()
        token = data.get("token")
        if token:
            print(f"\n✅ Magic link token received: {token[:50]}...")
            return token
        else:
            print("\n⚠️ No token in response (production mode?)")
            return None
    else:
        print(f"\n❌ Failed: {response.json()}")
        return None


def test_verify_magic_link(token):
    """Test magic link verification endpoint."""
    print("\n=== Testing Magic Link Verification ===")

    if not token:
        print("⚠️ No token available to verify")
        return None

    # Verify magic link
    response = httpx.get(
        f"{BASE_URL}/auth/verify",
        params={"token": token},
        timeout=10.0,
    )

    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()}")

    if response.status_code == 200:
        data = response.json()
        access_token = data.get("access_token")
        user = data.get("user")

        print(f"\n✅ Access token received: {access_token[:50]}...")
        print(f"✅ User info: {user}")
        return access_token
    else:
        print(f"\n❌ Failed: {response.json()}")
        return None


def main():
    """Run all auth tests."""
    print("🚀 Starting Auth Endpoint Tests")
    print(f"Base URL: {BASE_URL}")

    # Test 1: Request magic link
    magic_token = test_magic_link()

    # Test 2: Verify magic link and get access token
    if magic_token:
        access_token = test_verify_magic_link(magic_token)

        if access_token:
            print("\n" + "=" * 60)
            print("✅ All tests passed!")
            print("=" * 60)
            print("\nYou can use this access token for authenticated requests:")
            print(f"Authorization: Bearer {access_token}")
        else:
            print("\n" + "=" * 60)
            print("❌ Verification test failed")
            print("=" * 60)
    else:
        print("\n" + "=" * 60)
        print("❌ Magic link test failed")
        print("=" * 60)


if __name__ == "__main__":
    main()
