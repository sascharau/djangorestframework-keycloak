#!/usr/bin/env python3
"""
Test script for DRF Keycloak API calls
Tests the API methods from drf_keycloak.api module
"""
import sys
import os
import django
import requests

# Add the parent directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../'))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'test_project.settings')
django.setup()

from drf_keycloak.api import KeycloakApi
from drf_keycloak.settings import keycloak_settings

KEYCLOAK_URL = "http://localhost:8080"
REALM = "test-realm"
CLIENT_ID = "test-client"  # Use public client first
CLIENT_SECRET = "test-secret-123"
USERNAME = "testuser"
PASSWORD = "testpass"

# Create API instance after Django setup
keycloak_api = KeycloakApi()

def get_test_token():
    """Get a test token from Keycloak"""
    print("🔑 Getting test token...")
    
    token_url = f"{KEYCLOAK_URL}/realms/{REALM}/protocol/openid-connect/token"
    data = {
        'username': USERNAME,
        'password': PASSWORD,
        'grant_type': 'password',
        'client_id': CLIENT_ID,
        'scope': 'openid profile email'
    }
    
    try:
        response = requests.post(token_url, data=data)
        response.raise_for_status()
        token_data = response.json()
        print("✅ Test token obtained")
        return token_data['access_token']
    except Exception as e:
        print(f"❌ Failed to get test token: {e}")
        return None

def test_get_public_key():
    """Test get_public_key method"""
    print("\n🔐 Testing get_public_key()...")
    
    try:
        public_key = keycloak_api.get_public_key()
        print(f"✅ Public key retrieved successfully")
        print(f"   Key type: {type(public_key)}")
        if isinstance(public_key, str) and "BEGIN PUBLIC KEY" in public_key:
            print("   ✅ Key format looks correct")
        else:
            print(f"   ⚠️  Key format: {public_key[:100]}...")
        return True
    except Exception as e:
        print(f"❌ get_public_key failed: {e}")
        return False

def test_get_jwks(token):
    """Test get_jwks method"""
    print("\n🔑 Testing get_jwks()...")
    
    if not token:
        print("❌ No token available for JWKS test")
        return False
    
    try:
        jwks_key = keycloak_api.get_jwks(token)
        print(f"✅ JWKS key retrieved successfully")
        print(f"   Key type: {type(jwks_key)}")
        print(f"   Key preview: {str(jwks_key)[:100]}...")
        return True
    except Exception as e:
        print(f"❌ get_jwks failed: {e}")
        return False

def test_get_userinfo(token):
    """Test get_userinfo method"""
    print("\n👤 Testing get_userinfo()...")
    
    if not token:
        print("❌ No token available for userinfo test")
        return False
    
    print(f"   Using token: {token[:50]}...")
    print(f"   API base_url: {keycloak_api.base_url}")
    
    try:
        userinfo = keycloak_api.get_userinfo(token)
        print(f"✅ Userinfo retrieved successfully")
        print(f"   Response type: {type(userinfo)}")
        if isinstance(userinfo, dict):
            print(f"   Username: {userinfo.get('preferred_username', 'N/A')}")
            print(f"   Email: {userinfo.get('email', 'N/A')}")
        else:
            print(f"   Raw response: {userinfo}")
        return True
    except Exception as e:
        print(f"❌ get_userinfo failed: {e}")
        print(f"   Exception type: {type(e)}")
        if hasattr(e, 'status_code'):
            print(f"   Status code: {e.status_code}")
        if hasattr(e, 'detail'):
            print(f"   Detail: {e.detail}")
        print("   Full traceback:")
        import traceback
        traceback.print_exc()
        return False

def test_get_introspect(token):
    """Test get_introspect method"""
    print("\n🔍 Testing get_introspect()...")
    
    if not token:
        print("❌ No token available for introspect test")
        return False
    
    # Check if CLIENT_SECRET is configured
    if not keycloak_settings.CLIENT_SECRET:
        print("⚠️  CLIENT_SECRET not configured, skipping introspect test")
        return True
    
    try:
        introspect_data = keycloak_api.get_introspect(token)
        print(f"✅ Token introspection successful")
        print(f"   Response type: {type(introspect_data)}")
        if isinstance(introspect_data, dict):
            print(f"   Active: {introspect_data.get('active', 'N/A')}")
            print(f"   Username: {introspect_data.get('username', 'N/A')}")
            print(f"   Client ID: {introspect_data.get('client_id', 'N/A')}")
        return True
    except Exception as e:
        print(f"❌ get_introspect failed: {e}")
        return False

def test_keycloak_connectivity():
    """Test basic Keycloak connectivity"""
    print("\n🌐 Testing Keycloak connectivity...")
    
    try:
        response = requests.get(f"{KEYCLOAK_URL}/realms/{REALM}")
        response.raise_for_status()
        print("✅ Keycloak is reachable")
        return True
    except Exception as e:
        print(f"❌ Keycloak connectivity failed: {e}")
        return False

def main():
    """Run all API tests"""
    print("🧪 Testing DRF Keycloak API Methods")
    print("=" * 50)
    
    print(f"Keycloak Settings:")
    print(f"   SERVER_URL: {keycloak_settings.SERVER_URL}")
    print(f"   REALM: {keycloak_settings.REALM}")
    print(f"   CLIENT_ID: {keycloak_settings.CLIENT_ID}")
    print(f"   CLIENT_SECRET: {'***' if keycloak_settings.CLIENT_SECRET else 'None'}")
    print(f"   ISSUER: {keycloak_settings.ISSUER}")
    print(f"   VERIFY_TOKENS_WITH_KEYCLOAK: {keycloak_settings.VERIFY_TOKENS_WITH_KEYCLOAK}")
    print(f"   API base_url: {keycloak_api.base_url}")
    
    # Test userinfo URL manually
    print(f"\n🔍 Manual URL test:")
    expected_userinfo_url = f"{keycloak_api.base_url}/protocol/openid-connect/userinfo"
    print(f"   Expected userinfo URL: {expected_userinfo_url}")
    
    results = []
    
    # Test 1: Basic connectivity
    results.append(test_keycloak_connectivity())
    
    # Test 2: Get test token
    token = get_test_token()
    
    # Test 3: Public key (will fail if Keycloak doesn't have public_key endpoint)
    results.append(test_get_public_key())
    
    # Test 4: JWKS (requires token)
    results.append(test_get_jwks(token))
    
    # Test 5: Userinfo (requires token)
    results.append(test_get_userinfo(token))
    
    # Test 6: Introspect (requires token and CLIENT_SECRET)
    results.append(test_get_introspect(token))
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 API Test Summary:")
    passed = sum(results)
    total = len(results)
    
    print(f"   ✅ Passed: {passed}/{total}")
    
    if passed == total:
        print("🎉 All API tests passed!")
        sys.exit(0)
    else:
        print("❌ Some API tests failed!")
        print("\n💡 Tips:")
        print("   - Ensure Keycloak is running on localhost:8080")
        print("   - Run setup-keycloak.sh to create test realm and user")
        print("   - Check Keycloak configuration in Django settings")
        sys.exit(1)

if __name__ == "__main__":
    main()