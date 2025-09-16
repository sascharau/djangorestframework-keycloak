# Changelog

All significant changes to the project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

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
