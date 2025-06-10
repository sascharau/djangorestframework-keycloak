# DRF Keycloak Testing

Quick testing setup for the DRF Keycloak package with real Keycloak integration.

⚠️ **Note**: This test project is **not shipped with the package** (excluded in `setup.py`).

## Quick Start

```bash
# Option 1: Complete automated test (recommended)
make test-integration

# Option 2: Step by step manual testing  
make start-keycloak      # Wait 1-2 minutes for Keycloak to start
make setup-keycloak      # Configure realm and test users
make start-django        # Start Django (in separate terminal)
make curl-test           # Test endpoints
```

## Available Commands

| Command | Dependencies | Description |
|---------|--------------|-------------|
| `make help` | none | Show all commands |
| `make quickstart` | none | Show detailed guide |
| `make test-unit` | none | Run unit tests |
| `make install` | none | Install package in venv |
| `make clean` | none | Stop containers and cleanup |
| `make start-keycloak` | Docker | Start Keycloak in Docker |
| `make setup-keycloak` | ↳ start-keycloak | Configure realm and test data |
| `make token` | ↳ setup-keycloak | Get test token from Keycloak |
| `make start-django` | ↳ setup-keycloak | Start Django test server |
| `make curl-test` | ↳ start-django | Test API endpoints |
| `make test-integration` | Docker | Full automated test |

## Test Endpoints

| Endpoint | Authentication | Description |
|----------|----------------|-------------|
| `/api/public/` | None | Public endpoint |
| `/api/protected/` | JWT Token | Requires authentication |
| `/api/profile/` | JWT + Permission | Requires 'view-profile' permission |

**Test Credentials:**
- Username: `testuser`
- Password: `testpass`
- Realm: `test-realm`
- Client: `test-client`

## Manual Testing

### 1. Get Access Token
```bash
make token
```

### 2. Test Endpoints
```bash
# Public endpoint (no auth)
curl http://localhost:8000/api/public/

# Protected endpoint without token (should return 401)
curl http://localhost:8000/api/protected/

# Protected endpoint with token
TOKEN=$(make token | tail -1)
curl -H "Authorization: $TOKEN" http://localhost:8000/api/protected/

# Permission endpoint
curl -H "Authorization: $TOKEN" http://localhost:8000/api/profile/
```

### 3. Keycloak Admin Console
- URL: http://localhost:8080
- Login: `admin` / `admin`

## Cleanup

```bash
# Stop all containers and remove volumes
make clean
```

This is a minimal setup for quick testing. For production use, refer to the main package documentation.
