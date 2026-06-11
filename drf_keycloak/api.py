"""Manage Keycloak HTTP calls (userinfo and token introspection)."""

import logging

import requests
from django.utils.encoding import force_str
from rest_framework import status
from rest_framework.exceptions import APIException

from .exceptions import KeycloakAPIError
from .settings import keycloak_settings

logger = logging.getLogger("drf_keycloak")


class KeycloakApi:
    """Thin client for the Keycloak endpoints this package needs.

    Configuration is read live from ``keycloak_settings`` on every call so that
    ``override_settings`` / runtime reconfiguration is honored (the previous
    implementation snapshotted settings at import time).
    """

    timeout = 30

    def __init__(self):
        self.connection = requests.Session()

    @property
    def base_url(self):
        return keycloak_settings.base_url

    @property
    def client_id(self):
        return keycloak_settings.CLIENT_ID

    @property
    def client_secret_key(self):
        return keycloak_settings.CLIENT_SECRET or None

    @property
    def _verify(self):
        return keycloak_settings.VERIFY_CERTIFICATE

    def get_userinfo(self, token):
        """Fetch the userinfo document for a token."""
        return self.get(
            path="protocol/openid-connect/userinfo",
            headers={"Authorization": "Bearer " + token},
        )

    def get_introspect(self, token):
        """Validate a token via Keycloak's introspection endpoint.

        Returns the introspection document (a dict). Network failures and
        Keycloak server errors raise ``KeycloakAPIError`` (503) so they fail
        closed and visibly.
        """
        if not self.client_secret_key:
            raise RuntimeError(
                'Please set KEYCLOAK_CONFIG["CLIENT_SECRET"] in your settings.'
            )
        post_data = {
            "client_id": self.client_id,
            "client_secret": self.client_secret_key,
            "token": token,
        }
        return self.post("protocol/openid-connect/token/introspect", data=post_data)

    def clean_response(self, response):
        """Return parsed JSON/body for 2xx, else raise a typed error.

        - 5xx  -> KeycloakAPIError (503): upstream is unavailable, fail closed.
        - 4xx  -> APIException carrying the upstream status (config/request bug).
        """
        if response.status_code < status.HTTP_400_BAD_REQUEST:
            try:
                return response.json()
            except ValueError:
                return response.content

        message = self._error_message(response)
        if response.status_code >= status.HTTP_500_INTERNAL_SERVER_ERROR:
            logger.warning("Keycloak returned %s: %s", response.status_code, message)
            raise KeycloakAPIError(message)
        logger.error("Keycloak request failed %s: %s", response.status_code, message)
        exc = APIException(message)
        exc.status_code = response.status_code
        raise exc

    @staticmethod
    def _error_message(response):
        try:
            error_json = response.json()
            message = (
                error_json.get("message")
                or error_json.get("error_description")
                or error_json.get("error")
            )
        except (AttributeError, ValueError):
            message = None
        if not message:
            message = response.content
        return force_str(message)

    def get(self, path=None, headers=None):
        """GET helper. Network failures fail closed as 503."""
        url = f"{self.base_url}/{path}" if path else self.base_url
        try:
            response = self.connection.get(
                url, headers=headers, timeout=self.timeout, verify=self._verify
            )
        except requests.RequestException as exc:
            logger.warning("Keycloak GET %s failed: %s", url, exc)
            raise KeycloakAPIError() from exc
        return self.clean_response(response)

    def post(self, path, data):
        """POST helper. Network failures fail closed as 503."""
        url = f"{self.base_url}/{path}"
        try:
            response = self.connection.post(
                url, data=data, timeout=self.timeout, verify=self._verify
            )
        except requests.RequestException as exc:
            logger.warning("Keycloak POST %s failed: %s", url, exc)
            raise KeycloakAPIError() from exc
        return self.clean_response(response)


keycloak_api = KeycloakApi()
