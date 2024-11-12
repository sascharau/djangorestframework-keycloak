# Changelog

All significant changes to the project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [Unreleased]

### Added
- Support for `raw_token` as both `bytes` and `str` in `KeycloakAuthBackend`.
- New tests that cover both token types.

### Changed
- Conditional decoding of `raw_token` in `KeycloakAuthBackend` to handle both `bytes` and `str`.

### Fixed
- Removes unnecessary `.decode()` call for already decoded `str` tokens.

## [1.0.1] - 2024-11-12

### Added
- Support for different types of `raw_token` (byte strings and regular strings).
- Additional tests to ensure compatibility with both token types.

### Changed
- Adaptation of the `KeycloakAuthBackend` class for conditional decoding of `raw_token`.
- Updated the test cases to include both `bytes` and `str` tokens.

### Fixed
- Fixed comparison assertion bug in tests by comparing `validated_token` to `claims` instead of `raw_token`.

## [1.0.0] - 2023-09-12

### Added
- Initial release of the `drf_keycloak` package.
- Support for keycloak-based authentication in Django REST Framework.
