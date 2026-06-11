"""Exceptions raised by drf-keycloak."""

from rest_framework import status
from rest_framework.exceptions import APIException


class TokenBackendError(Exception):
    """The token is malformed, has a bad signature, or otherwise invalid."""


class TokenBackendExpiredToken(TokenBackendError):
    """The token is well-formed and correctly signed but expired."""


class KeycloakAPIError(APIException):
    """Keycloak could not be reached or returned a server error.

    Surfaced as 503 so an outage fails closed and visibly instead of being
    swallowed into an anonymous request.
    """

    status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    default_detail = "Authentication service unavailable."
    default_code = "keycloak_unavailable"
