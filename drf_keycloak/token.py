"""Verify AccessToken"""

import jwt
from rest_framework.exceptions import APIException

from .api import keycloak_api
from .exceptions import TokenBackendError, TokenBackendExpiredToken
from .settings import keycloak_settings


class TokenError(Exception):
    """Name for the Exception"""


PUBLIC_KEYCLOAK_KEY_CACHE = None


class JWToken:
    """
    A class which validates and wraps an existing JWT or can be used to build a
    new JWT.
    """

    def __init__(self, token=None):
        self.token = token
        self.audience = keycloak_settings.AUDIENCE
        if self.token:
            self.payload = self.decode(self.token)

    def verify_token_with_keycloak(self):
        """
        validates header token with Keycloak API
        """
        if keycloak_api.get_introspect(self.token).get("active", False):
            return None
        raise APIException("Verify token with keycloak return False")

    def get_jwt_key(self):
        """
        So that we don't have to make an API call every time,
        we cash the result.
        @return: jwt key
        """
        global PUBLIC_KEYCLOAK_KEY_CACHE  # pylint: disable=global-statement
        if keycloak_settings.VERIFY_TOKENS_WITH_KEYCLOAK:
            return keycloak_api.get_jwks(self.token)
        if PUBLIC_KEYCLOAK_KEY_CACHE:
            return PUBLIC_KEYCLOAK_KEY_CACHE
        PUBLIC_KEYCLOAK_KEY_CACHE = keycloak_api.get_public_key()
        return PUBLIC_KEYCLOAK_KEY_CACHE

    def decode(self, token):
        """
        Performs a validation of the given token and returns its payload
        dictionary.

        Raises a `AuthenticationFailed` if the token is malformed, if its
        signature check fails, or if its 'exp' claim indicates it has expired.
        """

        try:
            return jwt.decode(
                token,
                self.get_jwt_key(),
                algorithms=keycloak_settings.ALGORITHM,
                audience=self.audience,
                issuer=keycloak_settings.ISSUER,
                options={
                    "verify_aud": self.audience is not None,
                    "verify_signature": keycloak_settings.VERIFY_SIGNATURE,
                    "verify_exp": True,
                },
            )
        except jwt.InvalidAlgorithmError as e:
            raise TokenBackendError("Algorithm is invalid") from e
        except jwt.ExpiredSignatureError as e:
            raise TokenBackendExpiredToken("Token is expired") from e
        except jwt.InvalidTokenError as e:
            raise TokenBackendError("Token is invalid") from e
