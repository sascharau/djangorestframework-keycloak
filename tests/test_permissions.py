""" keycloak tests permissions """
from time import time

from django.test import TestCase
from rest_framework.test import APIRequestFactory

from drf_keycloak.permissions import HasPermission
from .helpers import create_user

TOKEN_CLAIMS = {
    "exp": time(),
    "iat": time() + 3600,
    "auth_time": 1667857235,
    "jti": "e3bc9dd9-fdc0-47da-90f9-fe3b87f0d2ff",
    "iss": "https://auth.uppercloud.io/auth/realms/zeus",
    "aud": "account",
    "sub": "316ab2d1-922e-48ed-9d75-25583dbc5b18",
    "typ": "Bearer",
    "azp": "fda",
    "nonce": "627e46ef-f995-4b01-87c3-3807c9e6be18",
    "session_state": "10105ce8-25be-43c9-9a58-416a11a36711",
    "acr": "0",
    "allowed-origins": ["*"],
    "realm_access": {"roles": ["offline_access", "default-roles-zeus", "uma_authorization"]},
    "resource_access": {"account": {"roles": []}},
    "scope": "openid profile email",
    "sid": "10105ce8-25be-43c9-9a58-416a11a36711",
    "name": "John Doe",
    "preferred_username": "Johny",
    "given_name": "John",
    "family_name": "Doe",
    "email": "j.doe@clients.eee",
}

PERMISSION_TOKEN_CLAIMS = {
    **TOKEN_CLAIMS,
    "resource_access": {
        "account": {"roles": ["manage-account", "manage-account-links", "view-profile"]}
    },
}


class TestKeycloakPermissions(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()

    def test_view_withs_permissions(self):
        request = self.factory.get("/")
        request.auth = PERMISSION_TOKEN_CLAIMS
        permission_check = HasPermission("view-profile")
        permission = permission_check.has_permission(request, None)
        self.assertTrue(permission)

    def test_view_without_permissions(self):
        request = self.factory.get("/")
        request.auth = TOKEN_CLAIMS
        permission_check = HasPermission("view-profile")
        permission = permission_check.has_permission(request, None)
        self.assertFalse(permission)

    def test_view_another_permissions(self):
        request = self.factory.get("/")
        request.auth = PERMISSION_TOKEN_CLAIMS
        permission_check = HasPermission("fake")
        permission = permission_check.has_permission(request, None)
        self.assertFalse(permission)

    def test_key_error_permissions(self):
        del TOKEN_CLAIMS["resource_access"]
        request = self.factory.get("/")
        request.auth = TOKEN_CLAIMS
        permission_check = HasPermission("view-profile")
        permission = permission_check.has_permission(request, None)
        self.assertFalse(permission)

    def test_has_object_permissions(self):
        user = create_user()
        request = self.factory.get("/")
        request.auth = PERMISSION_TOKEN_CLAIMS
        permission_check = HasPermission("view-profile")
        permission = permission_check.has_object_permission(request, None, user)
        self.assertTrue(permission)

    def test_has_not_object_permissions(self):
        user = create_user()
        request = self.factory.get("/")
        request.auth = PERMISSION_TOKEN_CLAIMS
        permission_check = HasPermission("fake")
        permission = permission_check.has_object_permission(request, None, user)
        self.assertFalse(permission)

    def test_jwt_permission_is_none(self):
        request = self.factory.get("/")
        request.auth = None
        permission_check = HasPermission("view-profile")
        permission = permission_check.has_permission(request, None)
        self.assertFalse(permission)

    def test_jwt_permission_is_not_list(self):
        request = self.factory.get("/")
        request.auth = {"resource_access": {"account": {"roles": "view-profile"}}}
        permission_check = HasPermission("view-profile")
        permission = permission_check.has_permission(request, None)
        self.assertFalse(permission)
