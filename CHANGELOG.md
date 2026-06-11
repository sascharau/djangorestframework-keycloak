# Changelog

All significant changes to the project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [2.0.0] - 2026-06-11

This release fixes correctness and security defects in token validation. Several
fixes change runtime behavior, so it is a major release. Read the **Changed
(breaking)** and **Removed** sections before upgrading.

### Changed (breaking)
- **Invalid/expired tokens now return 401 instead of being silently treated as
  anonymous.** Previously a malformed, expired, or wrongly-signed token caused
  `authenticate()` to return `None`, so the request continued unauthenticated
  (and was allowed through on `AllowAny` views). It now raises
  `AuthenticationFailed` with code `token_not_valid`, or `token_expired` for an
  expired token so clients can trigger a refresh.
- **Inactive/unknown users now raise 401** (`user_inactive`) instead of returning
  `None`, which previously set `request.user = None` and could 500 downstream code.
- **A Keycloak outage now fails closed (503).** With
  `VERIFY_TOKENS_WITH_KEYCLOAK=True`, introspection/network failures raise
  `KeycloakAPIError` (503) instead of silently downgrading to anonymous access.
- **Mapped user fields are synced from the token on every login** (with a
  dirty-check so a write only happens on change), not just at user creation.
  Keycloak is the source of truth for the fields in `CLAIM_MAPPING`.
- **`SERVER_URL` default is now `None`** and resolves to `ISSUER` when unset, so
  configuring only `ISSUER` no longer silently talks to `localhost`.
- **`ALGORITHM` is normalized to a list** before being handed to PyJWT (a bare
  string could previously match by substring).
- **`WWW-Authenticate` realm now uses double quotes** (`Bearer realm="api"`) and
  the bearer scheme is matched case-insensitively (RFC 6750/7235).
- **Minimum supported versions raised:** Python >= 3.10, Django >= 4.2, DRF
  >= 3.14. EOL Python/Django versions are no longer supported.
- **`HeaderMiddleware` has been removed.** It overlapped with Django's
  `SecurityMiddleware` and set HSTS unconditionally with a hardcoded
  `includeSubDomains`. Use Django's `SecurityMiddleware` and the `SECURE_*`
  settings for security headers — see the README and
  [Django's security docs](https://docs.djangoproject.com/en/6.0/topics/security/).

### Added
- `VERIFY_TOKENS_WITH_KEYCLOAK` now actually performs token introspection (after
  local validation) — previously the setting only changed key lookup.
- `LEEWAY` setting (default `0`) for clock-skew tolerance on `exp`/`iat`/`nbf`.
- `VERIFY_CERTIFICATE` is now a documented default setting and is honored for the
  JWKS fetch as well.
- A `drf_keycloak` logger emits warnings on Keycloak failures and debug lines on
  token rejection (never logging token or secret material).
- `KeycloakAPIError` (503) exception for upstream availability failures.
- `SECURITY.md` with a vulnerability disclosure policy.

### Fixed
- OpenAPI schema: corrected `TokenScheme.target_class` (`keycloak.…` →
  `drf_keycloak.…`) so drf-spectacular actually emits the `securitySchemes` entry.
- JWKS handling consolidated into a single cached client with native key
  rotation; an unreachable JWKS endpoint now yields 503 (was an uncaught 500),
  and a missing realm public key no longer crashes.
- Forced JWKS refreshes are rate-limited so a flood of tokens with random `kid`
  values can't amplify into unbounded requests against Keycloak.
- `HasPermission` no longer raises when used as a bare class
  (`permission_classes = [HasPermission]`) and tolerates non-dict segments in
  `PERMISSION_PATH`.
- Keycloak HTTP errors surface with the correct status (5xx → 503) instead of a
  generic 500; long Keycloak claim values are truncated during sync instead of
  500-ing the request; empty `USER_ID_CLAIM` no longer creates a blank user.
- `KeycloakApi` reads settings live, so `override_settings` and runtime
  reconfiguration take effect.
- Test suite no longer mutates module globals (order-independent).

### Removed
- `KeycloakApi.get_public_key` and `KeycloakApi.get_jwks` (replaced by the
  internal `drf_keycloak.keys` module).
- `drf_keycloak.token.PUBLIC_KEYCLOAK_KEY_CACHE` and `drf_keycloak.token.TokenError`
  (unused).
- `REALM` setting (the realm is part of `SERVER_URL`/`ISSUER`).
- `drf_keycloak.middleware.HeaderMiddleware` (use Django's `SecurityMiddleware`
  and the `SECURE_*` settings instead).
- `python-jose` optional dependency (unused; had known CVEs).

### Security
- The README previously claimed tokens were validated against the Keycloak API
  even though introspection was never invoked. Token revocation checking now
  works when `VERIFY_TOKENS_WITH_KEYCLOAK=True`, and the documentation reflects
  the actual behavior.

## [1.0.3] - 2025-09-16

### Added
- **GitHub Actions CI/CD:** Complete CI pipeline with ruff linting, formatting checks, and automated testing using uv
- **Dependabot Integration:** Automatic dependency updates for Python packages and GitHub Actions
- **Pre-commit Hooks:** Code quality enforcement with ruff formatting and linting on commit
- **Automated PR Labeling:** Smart labeling system for pull requests based on changed files

### Changed
- **Development Tooling:** Migrated from traditional pip to modern uv package manager for faster dependency resolution
- **Code Style:** Refactored codebase for improved consistency and readability across all modules
- **CI Strategy:** Replaced pre-commit.ci with GitHub Actions for more control over CI processes

### Improved
- **Developer Experience:** Streamlined setup with uv and comprehensive pre-commit configuration
- **Code Quality:** Enhanced linting and formatting with updated ruff configuration
- **Project Maintenance:** Automated dependency management and PR organization

## [1.0.2] - 2025-06-11

### Added
- **Docker Test Environment:** Complete Docker setup with Keycloak integration for testing
- **Integration Tests:** Comprehensive test scripts to validate authentication flow
- **SERVER_URL Configuration:** New `SERVER_URL` setting to separate API calls from JWT issuer validation
- **Custom Exception Classes:** Added `TokenBackendError` and `TokenBackendExpiredToken` for better error handling

### Changed
- **Simplified Configuration:** Replaced `JWKS_URL` with automatic generation from `SERVER_URL`
- **Removed Keycloak API Verification:** Eliminated `VERIFY_TOKENS_WITH_KEYCLOAK` setting for simplified token validation
- **Enhanced Error Handling:** Improved exception handling in authentication backend
- **PyJWT Crypto Support:** Added `PyJWT[crypto]` dependency for RS256 algorithm support

### Fixed
- **Docker Network Communication:** Fixed internal vs external URL handling for Docker environments
- **JWT Algorithm Support:** Resolved "Algorithm 'RS256' could not be found" error
- **Token Issuer Validation:** Fixed issuer mismatch in Docker environments

### Removed
- **VERIFY_TOKENS_WITH_KEYCLOAK:** Removed complex dual-validation approach
- **JWKS_URL:** Auto-generated from SERVER_URL to reduce configuration complexity

## [1.0.1] - 2024-11-12

### Added
- Support for different types of `raw_token` (byte strings and regular strings)
- Additional tests to ensure compatibility with both token types

### Changed
- Adaptation of the `KeycloakAuthBackend` class for conditional decoding of `raw_token`
- Updated the test cases to include both `bytes` and `str` tokens

### Fixed
- Fixed comparison assertion bug in tests by comparing `validated_token` to `claims` instead of `raw_token`

## [1.0.0] - 2023-09-12

### Added
- Initial release of the `drf_keycloak` package
- Support for keycloak-based authentication in Django REST Framework
