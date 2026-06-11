"""test keycloak auth"""

from unittest import mock

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.test.utils import override_settings
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.test import APIRequestFactory

from drf_keycloak.authentication import (
    ExpiredToken,
    InvalidToken,
    KeycloakAuthBackend,
)
from drf_keycloak.exceptions import KeycloakAPIError
from drf_keycloak.settings import keycloak_settings

from .conftest import TEST_ISSUER, TEST_SERVER_URL
from .helpers import (
    EMAIL,
    FIRST_NAME,
    LAST_NAME,
    USERNAME,
    create_user,
    make_token,
    public_key,
)

User = get_user_model()
_MAP = keycloak_settings.CLAIM_MAPPING


def make_claims(**overrides):
    """Fresh claims dict per call (never mutate a shared global)."""
    claims = {
        _MAP["username"]: USERNAME,
        _MAP["first_name"]: FIRST_NAME,
        _MAP["last_name"]: LAST_NAME,
        _MAP["email"]: EMAIL,
    }
    claims.update(overrides)
    return claims


def _config(**extra):
    base = {"SERVER_URL": TEST_SERVER_URL, "ISSUER": TEST_ISSUER}
    base.update(extra)
    return base


class TestGetUserOrCreate(TestCase):
    backend = KeycloakAuthBackend()

    def test_creates_and_returns_user(self):
        user = self.backend.get_user_or_create(make_claims())
        self.assertEqual(user.email, EMAIL)
        self.assertTrue(user.is_active)
        self.assertFalse(user.has_usable_password())

    def test_missing_user_id_claim_raises(self):
        with self.assertRaises(InvalidToken):
            self.backend.get_user_or_create({"foo": "bar"})

    def test_blank_user_id_claim_raises(self):
        # service account with an empty preferred_username must not create a
        # user with a blank identifier
        with self.assertRaises(InvalidToken):
            self.backend.get_user_or_create(make_claims(**{_MAP["username"]: ""}))

    def test_inactive_user_raises(self):
        user = create_user()
        user.is_active = False
        user.save()
        with self.assertRaises(AuthenticationFailed) as ctx:
            self.backend.get_user_or_create(make_claims())
        self.assertEqual("user_inactive", ctx.exception.detail.code)

    def test_active_user_returned(self):
        user = create_user()
        self.assertEqual(self.backend.get_user_or_create(make_claims()).id, user.id)


class TestUpdateUser(TestCase):
    backend = KeycloakAuthBackend()

    def test_sync_updates_changed_field(self):
        user = self.backend.get_user_or_create(make_claims(given_name="Updated"))
        self.assertEqual(user.first_name, "Updated")

    def test_dirty_check_skips_write_when_unchanged(self):
        user = create_user()
        with mock.patch.object(user, "save") as mock_save:
            self.backend.update_user(user, make_claims())
            mock_save.assert_not_called()

    def test_dirty_check_writes_once_on_change(self):
        user = create_user()
        with mock.patch.object(user, "save") as mock_save:
            self.backend.update_user(user, make_claims(given_name="New"))
            mock_save.assert_called_once()

    def test_long_value_is_truncated_not_500(self):
        user = create_user()
        long_name = "x" * 500
        self.backend.update_user(user, make_claims(given_name=long_name))
        max_length = User._meta.get_field("first_name").max_length
        self.assertEqual(len(user.first_name), max_length)


class TestUserCanAuthenticate(TestCase):
    backend = KeycloakAuthBackend()

    def test_missing_is_active_attr_allowed(self):
        class CustomUser:
            pass

        self.assertTrue(self.backend.user_can_authenticate(CustomUser()))


class TestHeaderParsing(TestCase):
    backend = KeycloakAuthBackend()

    def test_authenticate_header_uses_double_quotes(self):
        factory = APIRequestFactory()
        self.assertEqual(
            self.backend.authenticate_header(factory.request()), 'Bearer realm="api"'
        )

    def test_get_raw_token(self):
        self.assertIsNone(self.backend.get_raw_token(""))
        self.assertIsNone(self.backend.get_raw_token("is_not_bearer"))
        self.assertEqual(self.backend.get_raw_token("Bearer CoolToken"), "CoolToken")
        # case-insensitive scheme (RFC 6750)
        self.assertEqual(self.backend.get_raw_token("bearer CoolToken"), "CoolToken")
        with self.assertRaises(AuthenticationFailed):
            self.backend.get_raw_token("Bearer one two")
        with self.assertRaises(AuthenticationFailed):
            self.backend.get_raw_token("Bearer")

    def test_no_header_returns_none(self):
        request = APIRequestFactory().get("/")
        self.assertIsNone(self.backend.authenticate(request))

    def test_non_bearer_header_returns_none(self):
        request = APIRequestFactory().get("/")
        request.META["HTTP_AUTHORIZATION"] = "Basic abc"
        self.assertIsNone(self.backend.authenticate(request))


class TestAuthenticateFlow(TestCase):
    backend = KeycloakAuthBackend()

    def setUp(self):
        patcher = mock.patch(
            "drf_keycloak.token.get_signing_key", return_value=public_key()
        )
        patcher.start()
        self.addCleanup(patcher.stop)

    def _request(self, token):
        request = APIRequestFactory().get("/")
        request.META["HTTP_AUTHORIZATION"] = f"Bearer {token}"
        return request

    def test_valid_token_authenticates(self):
        user, claims = self.backend.authenticate(self._request(make_token()))
        self.assertEqual(user, User.objects.get(username=USERNAME))
        self.assertEqual(claims["preferred_username"], USERNAME)

    def test_invalid_token_raises_401(self):
        with self.assertRaises(InvalidToken):
            self.backend.authenticate(self._request("garbage.token.here"))

    def test_expired_token_raises_expired(self):
        with self.assertRaises(ExpiredToken):
            self.backend.authenticate(self._request(make_token(exp_delta=-10)))

    @override_settings(
        KEYCLOAK_CONFIG=_config(VERIFY_TOKENS_WITH_KEYCLOAK=True, CLIENT_SECRET="s")
    )
    @mock.patch("drf_keycloak.token.keycloak_api.get_introspect")
    def test_keycloak_outage_propagates_503(self, mock_introspect):
        mock_introspect.side_effect = KeycloakAPIError()
        # must NOT be swallowed into anonymous access
        with self.assertRaises(KeycloakAPIError):
            self.backend.authenticate(self._request(make_token()))
