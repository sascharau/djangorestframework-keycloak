"""Tests for the consolidated JWKS signing-key resolution."""

from unittest import mock

from django.test import TestCase
from django.test.utils import override_settings

import drf_keycloak.keys as keys_module
from drf_keycloak.exceptions import KeycloakAPIError, TokenBackendError
from drf_keycloak.keys import get_signing_key, reset_jwks_client

from .helpers import make_token


class FakeKey:
    def __init__(self, kid, key="KEYMATERIAL"):
        self.key_id = kid
        self.key = key


class FakeJWKClient:
    """Stand-in for PyJWKClient with controllable keys and a refresh counter."""

    instances = []

    def __init__(self, url, *args, **kwargs):
        self.url = url
        self.keys = [FakeKey("kid-1")]
        self.next_keys = None
        self.refresh_calls = 0
        self.connection_error = False
        FakeJWKClient.instances.append(self)

    def get_signing_keys(self, refresh=False):
        if self.connection_error:
            from jwt.exceptions import PyJWKClientConnectionError

            raise PyJWKClientConnectionError("JWKS endpoint unreachable", self.url)
        if refresh:
            self.refresh_calls += 1
            if self.next_keys is not None:
                self.keys = self.next_keys
        return self.keys


class TestSigningKeyResolution(TestCase):
    def setUp(self):
        reset_jwks_client()
        FakeJWKClient.instances = []
        patcher = mock.patch.object(keys_module, "PyJWKClient", FakeJWKClient)
        patcher.start()
        self.addCleanup(patcher.stop)
        self.addCleanup(reset_jwks_client)

    def test_cache_hit_does_not_refresh(self):
        token = make_token(kid="kid-1")
        key = get_signing_key(token)
        self.assertEqual(key, "KEYMATERIAL")
        self.assertEqual(FakeJWKClient.instances[0].refresh_calls, 0)

    def test_unknown_kid_triggers_one_refresh_and_resolves(self):
        token = make_token(kid="kid-2")
        # arrange: rotation — refresh yields the new key
        client = keys_module._get_client()
        client.next_keys = [FakeKey("kid-2", key="ROTATED")]
        key = get_signing_key(token)
        self.assertEqual(key, "ROTATED")
        self.assertEqual(client.refresh_calls, 1)

    def test_first_refresh_allowed_when_monotonic_below_cooldown(self):
        # Regression: time.monotonic()'s epoch is arbitrary, so on a freshly
        # booted CI host it can be < the cooldown. The first forced refresh must
        # still be allowed (a 0.0 sentinel wrongly blocked it -> "key not found").
        token = make_token(kid="kid-2")
        client = keys_module._get_client()
        client.next_keys = [FakeKey("kid-2", key="ROTATED")]
        with mock.patch.object(keys_module.time, "monotonic", return_value=5.0):
            key = get_signing_key(token)
        self.assertEqual(key, "ROTATED")
        self.assertEqual(client.refresh_calls, 1)

    def test_random_kid_flood_is_rate_limited(self):
        client = keys_module._get_client()
        # none of these kids will ever match
        for i in range(5):
            with self.assertRaises(TokenBackendError):
                get_signing_key(make_token(kid=f"bogus-{i}"))
        # cooldown gate: at most one forced refresh despite five distinct kids
        self.assertLessEqual(client.refresh_calls, 1)

    def test_connection_error_becomes_503(self):
        client = keys_module._get_client()
        client.connection_error = True
        with self.assertRaises(KeycloakAPIError):
            get_signing_key(make_token(kid="kid-1"))

    def test_malformed_header_is_401(self):
        with self.assertRaises(TokenBackendError):
            get_signing_key("not-a-jwt")

    @override_settings(
        KEYCLOAK_CONFIG={
            "SERVER_URL": "https://rotated.example/realms/x",
            "ISSUER": "https://rotated.example/realms/x",
        }
    )
    def test_settings_change_rebuilds_client_with_new_url(self):
        # override_settings fired reset via the setting_changed signal
        get_signing_key(make_token(kid="kid-1"))
        self.assertIn(
            "https://rotated.example/realms/x/protocol/openid-connect/certs",
            FakeJWKClient.instances[-1].url,
        )
