"""test keycloak api"""

from unittest import mock

import requests
from django.test import SimpleTestCase
from django.test.utils import override_settings
from django.utils.encoding import force_str
from rest_framework.exceptions import APIException

from drf_keycloak.api import KeycloakApi
from drf_keycloak.exceptions import KeycloakAPIError

from .conftest import TEST_ISSUER, TEST_SERVER_URL


def _config(**extra):
    base = {"SERVER_URL": TEST_SERVER_URL, "ISSUER": TEST_ISSUER}
    base.update(extra)
    return base


class TestKeycloakApi(SimpleTestCase):
    fake_response = {"key": "value"}

    def mock_response(self, status_code, content=None, json_data=None):
        response = mock.Mock()
        response.json.return_value = (
            json_data if json_data is not None else self.fake_response
        )
        response.status_code = status_code
        response.content = content
        return response

    @mock.patch("requests.Session.get")
    def test_get_userinfo_is_callable(self, mock_get):
        mock_get.return_value = self.mock_response(200)
        self.assertEqual(self.fake_response, KeycloakApi().get_userinfo("fake_token"))

    @override_settings(KEYCLOAK_CONFIG=_config(CLIENT_SECRET="foo"))
    @mock.patch("requests.Session.post")
    def test_get_introspect_is_callable(self, mock_post):
        mock_post.return_value = self.mock_response(200, "fake")
        self.assertEqual(self.fake_response, KeycloakApi().get_introspect("fake_token"))

    @override_settings(KEYCLOAK_CONFIG=_config(CLIENT_SECRET="foo"))
    @mock.patch("requests.Session.post")
    def test_introspect_server_error_is_503(self, mock_post):
        mock_post.return_value = self.mock_response(500, "boom")
        with self.assertRaises(KeycloakAPIError):
            KeycloakApi().get_introspect("fake_token")

    @override_settings(KEYCLOAK_CONFIG=_config(CLIENT_SECRET="foo"))
    @mock.patch("requests.Session.post")
    def test_introspect_network_failure_is_503(self, mock_post):
        mock_post.side_effect = requests.ConnectionError("refused")
        with self.assertRaises(KeycloakAPIError):
            KeycloakApi().get_introspect("fake_token")

    @override_settings(KEYCLOAK_CONFIG=_config())
    def test_introspect_without_client_secret_raises(self):
        with self.assertRaises(RuntimeError) as ctx:
            KeycloakApi().get_introspect("fake_token")
        self.assertEqual(
            'Please set KEYCLOAK_CONFIG["CLIENT_SECRET"] in your settings.',
            str(ctx.exception),
        )

    def test_clean_response_ok_json(self):
        self.assertEqual(
            self.fake_response, KeycloakApi().clean_response(self.mock_response(200))
        )

    def test_clean_response_ok_non_json_returns_content(self):
        response = requests.Response()
        response.status_code = 200
        response._content = b"Foo Bar"
        self.assertEqual("Foo Bar", force_str(KeycloakApi().clean_response(response)))

    def test_clean_response_client_error_preserves_status(self):
        response = self.mock_response(400, "error", json_data={"error": "bad"})
        with self.assertRaises(APIException) as ctx:
            KeycloakApi().clean_response(response)
        self.assertEqual(400, ctx.exception.status_code)
        self.assertEqual("bad", str(ctx.exception.detail))

    def test_clean_response_server_error_is_503(self):
        with self.assertRaises(KeycloakAPIError):
            KeycloakApi().clean_response(self.mock_response(500, "down"))

    @override_settings(KEYCLOAK_CONFIG=_config(CLIENT_ID="live-client"))
    def test_settings_read_live_via_property(self):
        # the singleton must reflect override_settings without re-instantiation
        from drf_keycloak.api import keycloak_api

        self.assertEqual("live-client", keycloak_api.client_id)
