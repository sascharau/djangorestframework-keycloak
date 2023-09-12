""" tests for token functions """
from unittest import mock

import jwt
from django.test import SimpleTestCase, TestCase
from django.test.utils import override_settings
from rest_framework.exceptions import APIException

import drf_keycloak.token as token_model
from drf_keycloak.token import JWToken, TokenError


class TestKeycloakToken(TestCase):
    def setUp(self):
        token_model.PUBLIC_KEYCLOAK_KEY_CACHE = None

    @override_settings(KEYCLOAK_CONFIG={"VERIFY_TOKENS_WITH_KEYCLOAK": False})
    @mock.patch("drf_keycloak.api.KeycloakApi.get_public_key")
    def test_get_public_key(self, mock_get_public_key):
        mock_get_public_key.return_value = "test"
        token_instance = JWToken()
        self.assertEqual("test", token_instance.get_jwt_key())

    @override_settings(KEYCLOAK_CONFIG={"VERIFY_TOKENS_WITH_KEYCLOAK": False})
    def test_get_public_key_from_cache(self):
        token_model.PUBLIC_KEYCLOAK_KEY_CACHE = "test"
        token_instance = JWToken()
        self.assertEqual("test", token_instance.get_jwt_key())

    @override_settings(KEYCLOAK_CONFIG={"VERIFY_TOKENS_WITH_KEYCLOAK": False})
    @mock.patch("drf_keycloak.api.KeycloakApi.get_public_key")
    @mock.patch("drf_keycloak.api.KeycloakApi.get_jwks")
    def test_decode(self, mock_get_jwt_key, mock_public_key):
        mock_public_key.return_value = "super"
        mock_get_jwt_key.return_value = "abc"
        token = jwt.encode(
            payload={
                "iss": "test",
            },
            key="abc",
        )
        with self.assertRaises(TokenError) as error:
            JWToken(token)
        self.assertEqual("Invalid algorithm specified", str(error.exception))
        token = (
            "eyJhbGciOiJSUzI1NiIsInR5cCIgOiAiSldUIiwia2lkIiA6ICJ6bEtLcFJmU2FBY"
            "lhrakl0cmhZMnFSMEZLZFVsbTZMSjh1Q3Rzb3VyV1JFIn0"
        )
        with self.assertRaises(TokenError) as error:
            JWToken(token)
        self.assertEqual("Token is invalid or expired", str(error.exception))


class TestKeycloakTokenVerifyTokensWithKeycloak(SimpleTestCase):
    @override_settings(KEYCLOAK_CONFIG={"VERIFY_TOKENS_WITH_KEYCLOAK": True})
    @mock.patch("drf_keycloak.token.JWToken.decode")
    @mock.patch("drf_keycloak.api.KeycloakApi.get_introspect")
    @mock.patch("drf_keycloak.api.KeycloakApi.get_jwks")
    def test_verify_token_with_keycloak(self, mock_get_jwks, mock_get_introspect, mock_decode):
        mock_get_jwks.return_value = "key"
        mock_decode.return_value = {"key": "value"}
        mock_get_introspect.return_value = {"active": True}
        token_instance = JWToken("test")
        self.assertEqual(token_instance.payload, {"key": "value"})

        mock_get_introspect.return_value = {"active": False}
        with self.assertRaises(APIException) as error:
            JWToken("test")
        self.assertIn("False", str(error.exception))

    @override_settings(KEYCLOAK_CONFIG={"VERIFY_TOKENS_WITH_KEYCLOAK": True})
    @mock.patch("drf_keycloak.api.KeycloakApi.get_jwks")
    def test_get_jwks(self, mock_get_jwks):
        mock_get_jwks.return_value = "test"
        token_instance = JWToken()
        self.assertEqual("test", token_instance.get_jwt_key())
