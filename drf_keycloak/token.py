"""Verify an access token: local signature/claims, optional introspection."""

import logging

import jwt

from .api import keycloak_api
from .exceptions import TokenBackendError, TokenBackendExpiredToken
from .keys import get_signing_key
from .settings import keycloak_settings

logger = logging.getLogger("drf_keycloak")


class JWToken:
    """Validate an existing JWT access token and expose its payload."""

    def __init__(self, token=None):
        self.token = token
        self.audience = keycloak_settings.AUDIENCE
        if self.token:
            self.payload = self.decode(self.token)
            if keycloak_settings.VERIFY_TOKENS_WITH_KEYCLOAK:
                self.verify_token_with_keycloak()

    def verify_token_with_keycloak(self):
        """Confirm the token is still active via Keycloak introspection.

        Runs only after local signature/claim validation has passed, so the
        network round-trip is reserved for tokens that are already locally
        valid. Fails closed: a non-dict or inactive response is rejected.
        Network/5xx failures raise KeycloakAPIError (503) from the API layer.
        """
        result = keycloak_api.get_introspect(self.token)
        if isinstance(result, dict) and result.get("active", False):
            return None
        logger.debug("Introspection reported token inactive")
        raise TokenBackendError("Token is not active")

    def decode(self, token):
        """Validate the token and return its payload.

        Raises ``TokenBackendExpiredToken`` if expired, ``TokenBackendError``
        if malformed or badly signed. Key-resolution failures propagate from
        ``keys.get_signing_key`` (TokenBackendError = 401, KeycloakAPIError =
        503).
        """
        try:
            return jwt.decode(
                token,
                get_signing_key(token),
                algorithms=keycloak_settings.algorithms,
                audience=self.audience,
                issuer=keycloak_settings.ISSUER,
                leeway=keycloak_settings.LEEWAY,
                options={
                    "verify_aud": self.audience is not None,
                    "verify_signature": keycloak_settings.VERIFY_SIGNATURE,
                    "verify_exp": True,
                },
            )
        except jwt.ExpiredSignatureError as exc:
            logger.debug("Token expired")
            raise TokenBackendExpiredToken("Token is expired") from exc
        except jwt.InvalidAlgorithmError as exc:
            raise TokenBackendError("Algorithm is invalid") from exc
        except jwt.InvalidTokenError as exc:
            logger.debug("Token invalid: %s", exc)
            raise TokenBackendError("Token is invalid") from exc
