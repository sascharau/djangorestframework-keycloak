"""tests for token functions"""

from unittest import mock

from django.test import TestCase

import drf_keycloak.token as token_model
from drf_keycloak.exceptions import TokenBackendError
from drf_keycloak.token import JWToken


class TestKeycloakToken(TestCase):
    def setUp(self):
        token_model.PUBLIC_KEYCLOAK_KEY_CACHE = None

    @mock.patch("drf_keycloak.api.KeycloakApi.get_public_key")
    def test_get_public_key(self, mock_get_public_key):
        mock_get_public_key.return_value = "test"
        token_instance = JWToken()
        self.assertEqual("test", token_instance.get_jwt_key())

    def test_get_public_key_from_cache(self):
        token_model.PUBLIC_KEYCLOAK_KEY_CACHE = "test"
        token_instance = JWToken()
        self.assertEqual("test", token_instance.get_jwt_key())

    @mock.patch("drf_keycloak.api.KeycloakApi.get_public_key")
    @mock.patch("drf_keycloak.api.KeycloakApi.get_jwks")
    def test_decode(self, mock_get_jwt_key, mock_public_key):
        mock_public_key.return_value = "super"
        mock_get_jwt_key.return_value = "abc"
        # Test with invalid token (malformed)
        token = "invalid.token.here"
        with self.assertRaises(TokenBackendError) as error:
            JWToken(token)
        self.assertEqual("Token is invalid", str(error.exception))
        token = (
            "eyJhbGciOiJSUzI1NiIsInR5cCIgOiAiSldUIiwia2lkIiA6ICJ6bEtLcFJmU2FBY"
            "lhrakl0cmhZMnFSMEZLZFVsbTZMSjh1Q3Rzb3VyV1JFIn0"
        )
        with self.assertRaises(TokenBackendError) as error:
            JWToken(token)
        self.assertEqual("Token is invalid", str(error.exception))
