"""test keycloak api"""

from unittest import mock

import requests
from django.test import SimpleTestCase
from django.test.utils import override_settings
from django.utils.encoding import force_str
from rest_framework.exceptions import APIException

from drf_keycloak.api import KeycloakApi


class TestKeycloakApi(SimpleTestCase):
    fake_response = {"key": "value"}

    def mock_response(self, status_code, content=None):
        """Mock Response to test responses"""
        response = mock.Mock()
        response.json.return_value = self.fake_response
        response.status_code = status_code
        response.content = content
        return response

    @mock.patch("requests.Session.get")
    def test_public_key_return_none(self, mock_public_key):
        mock_public_key.return_value = self.mock_response(200)
        public_key = KeycloakApi().get_public_key()
        self.assertIsNone(public_key)

    @mock.patch("requests.Session.get")
    def test_public_key(self, mock_public_key):
        mock_response = mock.Mock()
        mock_response.json.return_value = {"public_key": "test"}
        mock_response.status_code = 200
        mock_public_key.return_value = mock_response
        public_key = KeycloakApi().get_public_key()
        expected_result = (
            "-----BEGIN PUBLIC KEY-----\n" + "test" + "\n-----END PUBLIC KEY-----"
        )
        self.assertEqual(public_key, expected_result)

    @mock.patch("requests.Session.get")
    def test_get_userinfo_is_callable(self, mock_get_userinfo):
        mock_get_userinfo.return_value = self.mock_response(200)
        userinfo = KeycloakApi().get_userinfo("fake_token")
        self.assertEqual(self.fake_response, userinfo)

    @override_settings(KEYCLOAK_CONFIG={"CLIENT_SECRET": "foo"})
    @mock.patch("requests.Session.post")
    def test_get_introspect_is_callable(self, mock_get_introspect):
        mock_get_introspect.return_value = self.mock_response(200, "fake")
        introspect = KeycloakApi().get_introspect("fake_token")
        self.assertEqual(self.fake_response, introspect)

    @override_settings(KEYCLOAK_CONFIG={"CLIENT_SECRET": "foo"})
    @mock.patch("requests.Session.post")
    def test_fail_get_introspect(self, mock_get_introspect):
        mock_get_introspect.return_value = self.mock_response(500, "fake")
        with self.assertRaises(APIException) as error:
            KeycloakApi().get_introspect("fake_token")
        self.assertEqual("fake", str(error.exception))

    def test_fail_get_no_client_secret(self):
        api_instance = KeycloakApi()
        api_instance.client_secret_key = None
        with self.assertRaises(RuntimeError) as error:
            api_instance.get_introspect("fake_token")
        self.assertEqual(
            'Please set KEYCLOAK_CONFIG["CLIENT_SECRET"] in your settings.',
            str(error.exception),
        )

    def test_clean_response(self):
        # all good
        http_200_ok = KeycloakApi().clean_response(self.mock_response(200))
        self.assertEqual(self.fake_response, http_200_ok)
        # response massage
        with self.assertRaises(APIException) as error:
            KeycloakApi().clean_response(self.mock_response(400, "error"))
        self.assertEqual("error", str(error.exception))
        # default Exception massage
        with self.assertRaises(APIException) as error:
            KeycloakApi().clean_response(self.mock_response(500))
        self.assertEqual("A server error occurred.", str(error.exception))
        # status ok only content
        response = requests.Response()
        response.status_code = 200
        content = "Foo Bar"
        response._content = content.encode()  # pylint: disable=protected-access
        http_200_ok_no_json = KeycloakApi().clean_response(response)
        self.assertEqual("Foo Bar", force_str(http_200_ok_no_json))
