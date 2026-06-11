"""keycloak tests permissions"""

from time import time

from django.test import TestCase
from rest_framework.test import APIRequestFactory

from drf_keycloak.permissions import HasPermission, HasViewProfilePermission

from .helpers import create_user


def base_claims(roles=None):
    """Fresh claims per call — never mutate a shared dict between tests."""
    now = int(time())
    return {
        "exp": now + 3600,
        "iat": now,
        "iss": "https://auth.uppercloud.io/auth/realms/zeus",
        "aud": "account",
        "sub": "316ab2d1-922e-48ed-9d75-25583dbc5b18",
        "resource_access": {"account": {"roles": roles if roles is not None else []}},
        "preferred_username": "Johny",
    }


class TestKeycloakPermissions(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()

    def _request(self, auth):
        request = self.factory.get("/")
        request.auth = auth
        return request

    def test_view_with_permission(self):
        request = self._request(base_claims(roles=["view-profile"]))
        self.assertTrue(HasPermission("view-profile").has_permission(request, None))

    def test_view_without_permission(self):
        request = self._request(base_claims(roles=[]))
        self.assertFalse(HasPermission("view-profile").has_permission(request, None))

    def test_view_other_permission(self):
        request = self._request(base_claims(roles=["view-profile"]))
        self.assertFalse(HasPermission("fake").has_permission(request, None))

    def test_missing_path_segment(self):
        claims = base_claims()
        del claims["resource_access"]
        self.assertFalse(
            HasPermission("view-profile").has_permission(self._request(claims), None)
        )

    def test_object_permission_delegates(self):
        user = create_user()
        request = self._request(base_claims(roles=["view-profile"]))
        check = HasPermission("view-profile")
        self.assertTrue(check.has_object_permission(request, None, user))
        check_fake = HasPermission("fake")
        self.assertFalse(check_fake.has_object_permission(request, None, user))

    def test_auth_is_none(self):
        self.assertFalse(
            HasPermission("view-profile").has_permission(self._request(None), None)
        )

    def test_roles_not_a_list(self):
        request = self._request(
            {"resource_access": {"account": {"roles": "view-profile"}}}
        )
        self.assertFalse(HasPermission("view-profile").has_permission(request, None))

    def test_path_segment_is_not_a_dict(self):
        # PERMISSION_PATH walks into a string -> TypeError must be handled, not 500
        request = self._request({"resource_access": "oops"})
        self.assertFalse(HasPermission("view-profile").has_permission(request, None))

    def test_instantiated_without_permission_denies(self):
        # permission_classes = [HasPermission] -> DRF calls HasPermission()
        request = self._request(base_claims(roles=["view-profile"]))
        self.assertFalse(HasPermission().has_permission(request, None))

    def test_subclass_permission(self):
        request = self._request(base_claims(roles=["view-profile"]))
        self.assertTrue(HasViewProfilePermission().has_permission(request, None))
