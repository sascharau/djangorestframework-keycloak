.PHONY: help quickstart install test-unit start-keycloak setup-keycloak \
	start-django token curl-test test-integration clean

COMPOSE = docker compose -f docker-compose.test.yml

help: ## Show this help message
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-20s %s\n", $$1, $$2}'

quickstart: ## Show the step-by-step testing guide
	@echo "Step-by-step integration test against Keycloak 26:"
	@echo "  1. make start-keycloak   # boot Keycloak in Docker (wait ~30-60s)"
	@echo "  2. make setup-keycloak   # create realm, clients, test user"
	@echo "  3. make start-django     # run the Django test server (separate terminal)"
	@echo "  4. make curl-test        # hit the API endpoints"
	@echo "  5. make clean            # stop containers and remove volumes"

install: ## Install the package (editable, with test extras)
	@pip install -e '..[test]'

test-unit: ## Run the package unit tests
	@cd .. && python -m pytest tests/ -q

start-keycloak: ## Start Keycloak (Docker)
	@$(COMPOSE) up -d keycloak
	@echo "Keycloak starting on http://localhost:8080 (admin/admin)."
	@echo "Wait ~30-60s for it to be ready, then run: make setup-keycloak"

start-django: ## Start the Django test server (local)
	@python manage.py migrate
	@python manage.py runserver 0.0.0.0:8000

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

test-integration: ## Run the integration test (needs Keycloak + Django running)
	@echo "🧪 Running integration test..."
	@python scripts/test-integration.py

clean: ## Stop containers and remove volumes
	@echo "🧹 Stopping containers and removing volumes..."
	@$(COMPOSE) down -v
