"""tests for token functions"""

from unittest import mock

import jwt
from cryptography.hazmat.primitives.asymmetric import rsa
from django.test import TestCase
from django.test.utils import override_settings

from drf_keycloak.exceptions import TokenBackendError, TokenBackendExpiredToken
from drf_keycloak.token import JWToken

from .conftest import TEST_ISSUER, TEST_SERVER_URL
from .helpers import USERNAME, make_token, public_key


def _config(**extra):
    base = {"SERVER_URL": TEST_SERVER_URL, "ISSUER": TEST_ISSUER}
    base.update(extra)
    return base


class TestKeycloakToken(TestCase):
    def setUp(self):
        patcher = mock.patch(
            "drf_keycloak.token.get_signing_key", return_value=public_key()
        )
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_decode_valid(self):
        payload = JWToken(make_token()).payload
        self.assertEqual(payload["preferred_username"], USERNAME)

    def test_decode_expired_raises_expired(self):
        with self.assertRaises(TokenBackendExpiredToken):
            JWToken(make_token(exp_delta=-10))

    def test_decode_malformed_raises_invalid(self):
        with self.assertRaises(TokenBackendError) as ctx:
            JWToken("invalid.token.here")
        self.assertEqual("Token is invalid", str(ctx.exception))

    def test_decode_bad_signature_raises_invalid(self):
        other_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        forged = jwt.encode(
            {"iss": TEST_ISSUER, "preferred_username": USERNAME},
            other_key,
            algorithm="RS256",
            headers={"kid": "test-kid"},
        )
        with self.assertRaises(TokenBackendError):
            JWToken(forged)

    def test_decode_wrong_issuer_raises_invalid(self):
        with self.assertRaises(TokenBackendError):
            JWToken(make_token(claims={"iss": "https://evil.example/realms/x"}))

    @override_settings(KEYCLOAK_CONFIG=_config(LEEWAY=30))
    def test_leeway_allows_recently_expired(self):
        # expired 5s ago, but 30s of leeway tolerates it
        payload = JWToken(make_token(exp_delta=-5)).payload
        self.assertEqual(payload["preferred_username"], USERNAME)

    @override_settings(
        KEYCLOAK_CONFIG=_config(VERIFY_TOKENS_WITH_KEYCLOAK=True, CLIENT_SECRET="s")
    )
    @mock.patch("drf_keycloak.token.keycloak_api.get_introspect")
    def test_introspection_active_passes(self, mock_introspect):
        mock_introspect.return_value = {"active": True}
        payload = JWToken(make_token()).payload
        self.assertEqual(payload["preferred_username"], USERNAME)
        mock_introspect.assert_called_once()

    @override_settings(
        KEYCLOAK_CONFIG=_config(VERIFY_TOKENS_WITH_KEYCLOAK=True, CLIENT_SECRET="s")
    )
    @mock.patch("drf_keycloak.token.keycloak_api.get_introspect")
    def test_introspection_inactive_rejected(self, mock_introspect):
        mock_introspect.return_value = {"active": False}
        with self.assertRaises(TokenBackendError):
            JWToken(make_token())

    @override_settings(
        KEYCLOAK_CONFIG=_config(VERIFY_TOKENS_WITH_KEYCLOAK=True, CLIENT_SECRET="s")
    )
    @mock.patch("drf_keycloak.token.keycloak_api.get_introspect")
    def test_introspection_non_dict_fails_closed(self, mock_introspect):
        mock_introspect.return_value = b"not json"
        with self.assertRaises(TokenBackendError):
            JWToken(make_token())
