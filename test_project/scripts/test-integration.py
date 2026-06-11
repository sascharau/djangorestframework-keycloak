#!/usr/bin/env python3
"""
Integration test script for DRF Keycloak package
"""

import json
import sys
import time

import requests

KEYCLOAK_URL = "http://localhost:8080"
DJANGO_URL = "http://localhost:8000"
REALM = "test-realm"
CLIENT_ID = "test-client"
USERNAME = "testuser"
PASSWORD = "testpass"


def get_access_token():
    """Get access token from Keycloak"""
    print("Getting access token from Keycloak...")

    token_url = f"{KEYCLOAK_URL}/realms/{REALM}/protocol/openid-connect/token"
    data = {
        "username": USERNAME,
        "password": PASSWORD,
        "grant_type": "password",
        "client_id": CLIENT_ID,
    }

    try:
        response = requests.post(token_url, data=data)
        response.raise_for_status()
        token_data = response.json()
        print("Token obtained successfully")
        return token_data["access_token"]
    except Exception as e:
        print(
            f"Failed to get token: {e} Ensure Keycloak is running and credentials und User are correct?"
        )
        return None


def test_public_endpoint():
    """Test public endpoint (no auth required)"""
    print("\nTesting public endpoint...")

    try:
        response = requests.get(f"{DJANGO_URL}/api/public/")
        response.raise_for_status()
        data = response.json()
        print(f"Public endpoint response: {data}")
        return True
    except Exception as e:
        print(f"Public endpoint failed: {e}")
        return False


def test_protected_endpoint(token):
    """Test protected endpoint (auth required)"""
    print("\nTesting protected endpoint...")

    headers = {"Authorization": f"Bearer {token}"}

    try:
        response = requests.get(f"{DJANGO_URL}/api/protected/", headers=headers)
        response.raise_for_status()
        data = response.json()
        print(f"Protected endpoint response: {json.dumps(data, indent=2)}")
        return True
    except Exception as e:
        print(f"Protected endpoint failed: {e}")
        return False


def test_protected_endpoint_without_token():
    """Test protected endpoint without token (should fail)"""
    print("\nTesting protected endpoint without token...")

    try:
        response = requests.get(f"{DJANGO_URL}/api/protected/")
        if response.status_code == 401:
            print("Correctly rejected request without token")
            return True
        else:
            print(f"Expected 401, got {response.status_code}")
            return False
    except Exception as e:
        print(f"Unexpected error: {e}")
        return False


def test_permission_endpoint(token):
    """Test endpoint requiring specific permission"""
    print("\nTesting permission-protected endpoint...")

    headers = {"Authorization": f"Bearer {token}"}

    try:
        response = requests.get(f"{DJANGO_URL}/api/profile/", headers=headers)
        print(f"Profile endpoint status: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print(f"Profile endpoint response: {json.dumps(data, indent=2)}")
            return True
        elif response.status_code == 403:
            print("Access denied - user doesn't have 'view-profile' permission")
            print("   This is expected if the user role hasn't been assigned")
            return True
        else:
            print(f"Unexpected status: {response.status_code}")
            return False
    except Exception as e:
        print(f"Permission endpoint failed: {e}")
        return False


def main():
    """Run all integration tests"""
    print("Starting DRF Keycloak Integration Tests")
    print("=" * 50)

    # Wait for services to be ready
    print("⏳ Waiting for services to be ready...")
    time.sleep(2)

    results = []

    # Test 1: Public endpoint
    results.append(test_public_endpoint())

    # Test 2: Get token
    token = get_access_token()
    if not token:
        print("Cannot continue without token")
        sys.exit(1)

    # Test 3: Protected endpoint with token
    results.append(test_protected_endpoint(token))

    # Test 4: Protected endpoint without token
    results.append(test_protected_endpoint_without_token())

    # Test 5: Permission endpoint
    results.append(test_permission_endpoint(token))

    # Summary
    print("\n" + "=" * 50)
    print("Test Summary:")
    passed = sum(results)
    total = len(results)

    print(f"   Passed: {passed}/{total}")

    if passed == total:
        print("All tests passed!")
        sys.exit(0)
    else:
        print("Some tests failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()
