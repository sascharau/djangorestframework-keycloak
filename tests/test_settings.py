from django.test import TestCase
from django.test.utils import override_settings

from drf_keycloak.settings import keycloak_settings


class KeycloakSettingsTestCase(TestCase):
    def test_default_settings(self):
        # settings from conftest.py
        self.assertEqual(keycloak_settings.SERVER_URL, "https://kc.test/realms/test")
        # default settings
        self.assertEqual(keycloak_settings.CLIENT_ID, "account")
        self.assertIsNone(keycloak_settings.CLIENT_SECRET)
        self.assertIsNone(keycloak_settings.AUDIENCE)
        self.assertEqual(
            keycloak_settings.PERMISSION_PATH, "resource_access.account.roles"
        )
        self.assertEqual(keycloak_settings.USER_ID_FIELD, "username")
        self.assertEqual(keycloak_settings.USER_ID_CLAIM, "preferred_username")
        self.assertEqual(keycloak_settings.LEEWAY, 0)
        self.assertTrue(keycloak_settings.VERIFY_CERTIFICATE)
        self.assertEqual(
            keycloak_settings.CLAIM_MAPPING,
            {
                "first_name": "given_name",
                "last_name": "family_name",
                "email": "email",
                "username": "preferred_username",
            },
        )

    def test_algorithms_normalized_to_list(self):
        # default is already a list
        self.assertEqual(keycloak_settings.algorithms, ["RS256"])

    @override_settings(KEYCLOAK_CONFIG={"ALGORITHM": "RS256"})
    def test_algorithms_coerces_string(self):
        # a bare string must become a single-element list, never iterated char-wise
        self.assertEqual(keycloak_settings.algorithms, ["RS256"])

    @override_settings(KEYCLOAK_CONFIG={"ISSUER": "https://only-issuer.example"})
    def test_base_url_falls_back_to_issuer(self):
        # SERVER_URL unset -> base_url resolves to ISSUER (the F4 fix)
        self.assertEqual(keycloak_settings.base_url, "https://only-issuer.example")

    @override_settings(
        KEYCLOAK_CONFIG={"SERVER_URL": "https://srv.example", "ISSUER": "https://iss"}
    )
    def test_base_url_prefers_server_url(self):
        self.assertEqual(keycloak_settings.base_url, "https://srv.example")

    @override_settings(
        KEYCLOAK_CONFIG={"SERVER_URL": "https://foo.com", "ISSUER": "https://foo.com"}
    )
    def test_reload_keycloak_settings(self):
        self.assertEqual(keycloak_settings.SERVER_URL, "https://foo.com")
        self.assertEqual(keycloak_settings.base_url, "https://foo.com")
