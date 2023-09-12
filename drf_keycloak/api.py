""" Manage Keycloak """
import requests
from jwt import PyJWKClient
from rest_framework import status
from rest_framework.exceptions import APIException

from .settings import keycloak_settings


class KeycloakApi:
    """
    call KeycloakApi
    it contains userinfo, introspect, and public_key only
    """

    timeout = 30

    def __init__(self):
        self.connection = requests.Session()
        self.base_url = keycloak_settings.ISSUER
        self.client_id = keycloak_settings.CLIENT_ID
        self.realm_name = keycloak_settings.REALM
        self.client_secret_key = keycloak_settings.CLIENT_SECRET

    @classmethod
    def get_jwks(cls, token):  # pragma: no cover
        """To decode the JWT token, we need a key. We get this from the API"""
        url = f"{keycloak_settings.ISSUER}/protocol/openid-connect/certs"
        jwks_client = PyJWKClient(url, lifespan=60 * 10)
        signing_key = jwks_client.get_signing_key_from_jwt(token)
        return signing_key.key

    def get_userinfo(self, token):
        """Used to keep the user up to date."""
        response = self.get(
            path="protocol/openid-connect/userinfo", headers={"Authorization": "Bearer " + token}
        )
        return response

    def get_introspect(self, token):
        """Is used to validate the token."""
        if not self.client_secret_key:
            raise RuntimeError('Please set KEYCLOAK_CONFIG["CLIENT_SECRET"] in your settings.')
        post_data = {
            "client_id": self.client_id,
            "client_secret": self.client_secret_key,
            "token": token,
        }
        response = self.post("protocol/openid-connect/token/introspect", data=post_data)
        return response

    def get_public_key(self):
        """
        public key as key to decode JWT
        """
        response = self.get().get("public_key")
        try:
            return "-----BEGIN PUBLIC KEY-----\n" + response + "\n-----END PUBLIC KEY-----"
        except TypeError:
            return response

    def clean_response(self, response):
        """checks the status_code and tries to return json or content"""
        if not response.status_code >= status.HTTP_400_BAD_REQUEST:
            try:
                return response.json()
            except ValueError:
                return response.content
        try:
            message = response.json()["message"]
        except (KeyError, ValueError):
            message = response.content
        raise APIException(message, response.status_code)

    def get(self, path=None, headers=None):
        """get only"""
        if path:
            url = f"{self.base_url}/{path}"
        else:
            url = self.base_url
        response = self.connection.get(
            url,
            headers=headers,
            timeout=self.timeout,
            verify=keycloak_settings.user_settings.get("VERIFY_CERTIFICATE", True),
        )
        return self.clean_response(response)

    def post(self, path, data):
        """post only"""
        response = self.connection.post(
            f"{self.base_url}/{path}",
            data=data,
            verify=keycloak_settings.user_settings.get("VERIFY_CERTIFICATE", True),
            timeout=self.timeout,
        )
        return self.clean_response(response)


keycloak_api = KeycloakApi()
