""" test keycloak auth """
from unittest import mock

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.test.utils import override_settings
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.test import APIRequestFactory

from drf_keycloak.authentication import KeycloakAuthBackend, InvalidToken
from drf_keycloak.settings import keycloak_settings
from .helpers import create_user, USERNAME, EMAIL, FIRST_NAME, LAST_NAME

User = get_user_model()
keycloak_mapping = keycloak_settings.CLAIM_MAPPING
USER_CLAIMS = {
    keycloak_mapping["username"]: USERNAME,
    keycloak_mapping["first_name"]: FIRST_NAME,
    keycloak_mapping["last_name"]: LAST_NAME,
    keycloak_mapping["email"]: EMAIL,
}


class TestKeycloakAuthentication(TestCase):
    backend = KeycloakAuthBackend()

    @override_settings(KEYCLOAK_CONFIG={"VERIFY_TOKENS_WITH_KEYCLOAK": False})
    def test_backend_get_user(self):
        user = self.backend.get_user_or_create(USER_CLAIMS)
        self.assertEqual(user.email, EMAIL)

    def test_backend_user_raise(self):
        claims = {"foo": "bar"}
        with self.assertRaises(InvalidToken):
            self.backend.get_user_or_create(claims)

    def test_user_is_inactive(self):
        user = create_user()
        user.is_active = False  # nosemgrep
        user.save()
        self.assertIsNone(self.backend.get_user_or_create(USER_CLAIMS))
        user.is_active = True  # nosemgrep
        user.save()
        self.assertEqual(self.backend.get_user_or_create(USER_CLAIMS).id, user.id)

    @override_settings(KEYCLOAK_CONFIG={"VERIFY_TOKENS_WITH_KEYCLOAK": False})
    def test_update_user(self):
        USER_CLAIMS["given_name"] = "foo"
        self.assertEqual(self.backend.get_user_or_create(USER_CLAIMS).first_name, "foo")

    @override_settings(KEYCLOAK_CONFIG={"VERIFY_TOKENS_WITH_KEYCLOAK": False})
    def test_create_user_from_claims(self):
        claims = {
            keycloak_mapping["username"]: "FooBar",
            keycloak_mapping["first_name"]: "Foo",
            keycloak_mapping["last_name"]: "Bar",
            keycloak_mapping["email"]: "foo@bar.io",
        }
        self.assertFalse(User.objects.filter(username__iexact="FooBar").exists())
        user = self.backend.get_user_or_create(validated_token=claims)
        self.assertEqual(user.username, "FooBar")
        self.assertEqual(user.email, "foo@bar.io")
        self.assertTrue(user.is_active)  # nosemgrep

    @override_settings(KEYCLOAK_CONFIG={"VERIFY_TOKENS_WITH_KEYCLOAK": True})
    @mock.patch("drf_keycloak.api.KeycloakApi.get_userinfo")
    def test_create_user_from_keycloak_mock(self, userinfo):
        token_payload = {
            keycloak_mapping["username"]: "ZOIDBERG",
            keycloak_mapping["first_name"]: "John A.",
            keycloak_mapping["last_name"]: "Zoidberg",
            keycloak_mapping["email"]: "zoidberg@bar.io",
        }
        mock_claims = token_payload.copy()
        mock_claims[keycloak_mapping["first_name"]] = "first_name_is_different"
        userinfo.return_value = mock_claims
        self.assertFalse(User.objects.filter(username__iexact="ZOIDBERG").exists())
        self.backend.raw_token = b"test_token"
        user = self.backend.get_user_or_create(validated_token=token_payload)
        # now user will be updated with keycloak api,
        self.assertEqual(user.username, "ZOIDBERG")
        self.assertTrue(user.is_active)  # nosemgrep
        self.assertEqual(user.first_name, "first_name_is_different")

    def test_authenticate_header(self):
        factory = APIRequestFactory()
        self.assertEqual(self.backend.authenticate_header(factory.request()), "Bearer realm='api'")

    def test_get_raw_token(self):
        fake_token = "CoolToken"
        fake_header = f"Bearer {fake_token}"
        self.assertIsNone(self.backend.get_raw_token(""))
        self.assertIsNone(self.backend.get_raw_token("is_not_bearer"))
        self.assertEqual(self.backend.get_raw_token(fake_header), fake_token)
        with self.assertRaises(AuthenticationFailed):
            self.backend.get_raw_token("Bearer one two")
        with self.assertRaises(AuthenticationFailed):
            self.backend.get_raw_token("Bearer")

    def test_authenticate_return_none(self):
        request = APIRequestFactory().get("/")
        self.assertIsNone(self.backend.authenticate(request))
        request.META["HTTP_AUTHORIZATION"] = "test"
        self.assertIsNone(self.backend.authenticate(request))

    @override_settings(KEYCLOAK_CONFIG={"VERIFY_TOKENS_WITH_KEYCLOAK": False})
    @mock.patch("drf_keycloak.authentication.KeycloakAuthBackend.get_raw_token")
    @mock.patch("drf_keycloak.token.JWToken.decode")
    def test_authenticate_get_user(self, mock_token, mock_decode_token):
        request = APIRequestFactory().get("/")
        request.META["HTTP_AUTHORIZATION"] = "test"
        claims = {
            keycloak_mapping["username"]: "ZOIDBERG",
            keycloak_mapping["first_name"]: "John A.",
            keycloak_mapping["last_name"]: "Zoidberg",
            keycloak_mapping["email"]: "zoidberg@bar.io",
        }
        token_value = {"preferred_username": "ZOIDBERG"}
        mock_token.return_value = token_value
        mock_decode_token.return_value = claims
        user, validated_token = self.backend.authenticate(request)
        self.assertEqual(user, User.objects.get(username="ZOIDBERG"))
        self.assertEqual(validated_token, token_value)

    def test_authenticate_get_raw_token_is_none(self):
        request = APIRequestFactory().get("/")
        request.META["HTTP_AUTHORIZATION"] = "test"
        self.assertIsNone(self.backend.authenticate(request))
