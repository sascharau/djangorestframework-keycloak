""" default keycloak settings """

from django.conf import settings
from django.test.signals import setting_changed
from rest_framework.settings import APISettings

# default settings from keycloak
DEFAULT = {
    "SERVER_URL": "http://localhost:8080/",
    "REALM": "master",
    "CLIENT_ID": "account",
    "CLIENT_SECRET": None,
    "AUDIENCE": "account",
    "ALGORITHM": "RS256",
    "ISSUER": "http://localhost:8080/realms/master",
    "VERIFY_TOKENS_WITH_KEYCLOAK": False,
    "PERMISSION_PATH": "resource_access.account.roles",
    "USER_ID_FIELD": "username",
    "USER_ID_CLAIM": "preferred_username",
    # django key, keycloak value
    "CLAIM_MAPPING": {
        "first_name": "given_name",
        "last_name": "family_name",
        "email": "email",
        "username": "preferred_username",
    },
}


class KeycloakSettings(APISettings):
    """We use the DRF settings logic"""

    def __init__(self, user_settings=None, defaults=None, import_strings=None):
        super().__init__(user_settings, defaults, import_strings)
        self.import_strings = ""

    def __check_user_settings(
        self, user_settings
    ):  # pragma: no cover # pylint: disable=unused-private-member
        # must be overwritten otherwise bottle error messages from DRF will appear
        return user_settings

    @property
    def user_settings(self):
        if not hasattr(self, "_user_settings"):
            self._user_settings = getattr(settings, "KEYCLOAK_CONFIG", {})
        return self._user_settings


keycloak_settings = KeycloakSettings(None, DEFAULT)


def reload_keycloak_settings(*args, **kwargs):  # pylint: disable=unused-argument
    """Reload if settings in the tests change"""
    setting = kwargs["setting"]
    if setting == "KEYCLOAK_CONFIG":
        keycloak_settings.reload()


# reload for unit test
setting_changed.connect(reload_keycloak_settings)
