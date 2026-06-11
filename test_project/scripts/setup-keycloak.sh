#!/bin/bash

# Script to setup Keycloak for testing
set -e

KEYCLOAK_URL="http://localhost:8080"
ADMIN_USER="admin"
ADMIN_PASS="admin"
REALM_NAME="test-realm"
CLIENT_ID="test-client"
CONFIDENTIAL_CLIENT_ID="test-client-confidential"
CONFIDENTIAL_CLIENT_SECRET="test-secret-123"

echo "🔧 Setting up Keycloak for testing..."

# Wait for Keycloak to be ready
echo "⏳ Waiting for Keycloak to start..."
timeout=60
counter=0
until curl -f "$KEYCLOAK_URL/realms/master" > /dev/null 2>&1; do
    sleep 3
    counter=$((counter + 3))
    if [ $counter -gt $timeout ]; then
        echo "❌ Timeout waiting for Keycloak after ${timeout}s"
        exit 1
    fi
    echo "... still waiting (${counter}s)"
done
echo "✅ Keycloak is ready!"

# Get admin token
echo "🔑 Getting admin token..."
TOKEN_RESPONSE=$(curl -s -X POST "$KEYCLOAK_URL/realms/master/protocol/openid-connect/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=$ADMIN_USER" \
  -d "password=$ADMIN_PASS" \
  -d "grant_type=password" \
  -d "client_id=admin-cli" 2>/dev/null)

# Check if response contains access_token
if echo "$TOKEN_RESPONSE" | grep -q "access_token"; then
    ADMIN_TOKEN=$(echo "$TOKEN_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])")
    echo "✅ Admin token obtained"
else
    echo "❌ Failed to get admin token. Response: $TOKEN_RESPONSE"
    exit 1
fi

# Create realm
echo "🏗️  Creating realm: $REALM_NAME"
curl -s -X POST "$KEYCLOAK_URL/admin/realms" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "realm": "'$REALM_NAME'",
    "enabled": true,
    "displayName": "Test Realm for DRF Keycloak"
  }' || echo "Realm might already exist"

# Create client
echo "🔧 Creating client: $CLIENT_ID"
curl -s -X POST "$KEYCLOAK_URL/admin/realms/$REALM_NAME/clients" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "clientId": "'$CLIENT_ID'",
    "enabled": true,
    "publicClient": true,
    "directAccessGrantsEnabled": true,
    "protocol": "openid-connect",
    "standardFlowEnabled": false,
    "implicitFlowEnabled": false,
    "directAccessGrantsEnabled": true,
    "serviceAccountsEnabled": false,
    "defaultClientScopes": ["profile", "email"],
    "optionalClientScopes": ["address", "phone"],
    "attributes": {
      "jwt.credential": "true"
    }
  }' || echo "Client might already exist"

# Create confidential client for introspection
echo "🔧 Creating confidential client: $CONFIDENTIAL_CLIENT_ID"
curl -s -X POST "$KEYCLOAK_URL/admin/realms/$REALM_NAME/clients" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "clientId": "'$CONFIDENTIAL_CLIENT_ID'",
    "enabled": true,
    "publicClient": false,
    "directAccessGrantsEnabled": true,
    "protocol": "openid-connect",
    "standardFlowEnabled": false,
    "implicitFlowEnabled": false,
    "serviceAccountsEnabled": true,
    "secret": "'$CONFIDENTIAL_CLIENT_SECRET'",
    "defaultClientScopes": ["profile", "email"],
    "optionalClientScopes": ["address", "phone"],
    "attributes": {
      "jwt.credential": "true"
    }
  }' || echo "Confidential client might already exist"

# Create test user
echo "👤 Creating test user..."
curl -s -X POST "$KEYCLOAK_URL/admin/realms/$REALM_NAME/users" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "enabled": true,
    "firstName": "Test",
    "lastName": "User",
    "email": "test@example.com",
    "credentials": [{
      "type": "password",
      "value": "testpass",
      "temporary": false
    }]
  }' || echo "User might already exist"

# Create roles
echo "🛡️  Creating roles..."
curl -s -X POST "$KEYCLOAK_URL/admin/realms/$REALM_NAME/roles" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "view-profile",
    "description": "Can view profile"
  }' || echo "Role might already exist"

echo "✅ Keycloak setup complete!"
echo ""
echo "📋 Test Configuration:"
echo "Realm: $REALM_NAME"
echo "Client ID: $CLIENT_ID"
echo "Test User: testuser / testpass"
echo "JWKS URL: $KEYCLOAK_URL/realms/$REALM_NAME/protocol/openid-connect/certs"
echo ""
echo "🧪 To get a test token:"
echo "curl -X POST '$KEYCLOAK_URL/realms/$REALM_NAME/protocol/openid-connect/token' \\"
echo "     -H 'Content-Type: application/x-www-form-urlencoded' \\"
echo "     -d 'username=testuser' \\"
echo "     -d 'password=testpass' \\"
echo "     -d 'grant_type=password' \\"
echo "     -d 'client_id=$CLIENT_ID'"
