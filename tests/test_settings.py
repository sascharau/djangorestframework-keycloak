from django.test import TestCase
from django.test.utils import override_settings

from drf_keycloak.settings import keycloak_settings


class KeycloakSettingsTestCase(TestCase):
    def test_default_settings(self):
        # settings from conftest.py
        self.assertEqual(keycloak_settings.SERVER_URL, "https://my-server-url.com")
        self.assertEqual(keycloak_settings.REALM, "my-realm")
        # default settings
        self.assertEqual(keycloak_settings.CLIENT_ID, "account")
        self.assertIsNone(keycloak_settings.CLIENT_SECRET)
        self.assertIsNone(keycloak_settings.AUDIENCE)
        self.assertEqual(
            keycloak_settings.PERMISSION_PATH, "resource_access.account.roles"
        )
        self.assertEqual(keycloak_settings.USER_ID_FIELD, "username")
        self.assertEqual(keycloak_settings.USER_ID_CLAIM, "preferred_username")
        self.assertEqual(
            keycloak_settings.CLAIM_MAPPING,
            {
                "first_name": "given_name",
                "last_name": "family_name",
                "email": "email",
                "username": "preferred_username",
            },
        )

    @override_settings(
        KEYCLOAK_CONFIG={"SERVER_URL": "https://foo.com", "REALM": "bar"}
    )
    def test_reload_keycloak_settings(self):
        self.assertEqual(keycloak_settings.SERVER_URL, "https://foo.com")
        self.assertEqual(keycloak_settings.REALM, "bar")
