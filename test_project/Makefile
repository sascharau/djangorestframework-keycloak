.PHONY: help setup-keycloak token curl-test test-integration

help: ## Show this help message
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-20s %s\n", $$1, $$2}'

setup-keycloak: ## Setup Keycloak realm and test data
	@echo "🔧 Setting up Keycloak configuration..."
	@./scripts/setup-keycloak.sh

token: ## Get a test token from Keycloak
	@echo "🔑 Getting test token..."
	@curl -s -X POST 'http://localhost:8080/realms/test-realm/protocol/openid-connect/token' \
		-H 'Content-Type: application/x-www-form-urlencoded' \
		-d 'username=testuser' \
		-d 'password=testpass' \
		-d 'grant_type=password' \
		-d 'client_id=test-client' | \
		python -c "import sys, json; data=json.load(sys.stdin); print('Bearer ' + data['access_token'])" 2>/dev/null || \
		echo "❌ Failed to get token"

curl-test: ## Test API endpoints with curl
	@echo "🧪 Testing API endpoints..."
	@echo "1. Public endpoint:"
	@curl -s http://localhost:8000/api/public/ | python -m json.tool 2>/dev/null || echo "❌ Django not running"
	@echo ""
	@echo "2. Protected endpoint (should fail):"
	@curl -s http://localhost:8000/api/protected/ 2>/dev/null || echo "✅ Expected 401/403"
	@echo ""
	@echo "3. Get token and test protected endpoint:"
	@TOKEN=$$($(MAKE) token 2>/dev/null | tail -1); \
	if [[ $$TOKEN == Bearer* ]]; then \
		echo "✅ Got token: $${TOKEN:0:50}..."; \
		echo "Testing protected endpoint:"; \
		curl -s -H "Authorization: $$TOKEN" http://localhost:8000/api/protected/ | python -m json.tool 2>/dev/null || echo "❌ Django not running"; \
	else \
		echo "❌ Failed to get token"; \
	fi

test-integration: ## Run complete integration test with docker
	@echo "🧪 Running integration test with docker..."
	@python scripts/test-integration.py
