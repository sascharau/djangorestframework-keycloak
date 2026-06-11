"""default keycloak settings"""

from django.conf import settings
from django.test.signals import setting_changed
from rest_framework.settings import APISettings

# default settings from keycloak
#
# SERVER_URL is intentionally None by default so that a project may configure
# only ISSUER and have it used as the API base (resolved in KeycloakApi). The
# previous string default silently routed every request to localhost.
DEFAULT = {
    "SERVER_URL": None,
    "CLIENT_ID": "account",
    "CLIENT_SECRET": None,
    "AUDIENCE": None,
    "ALGORITHM": ["RS256"],
    "ISSUER": "http://localhost:8080/realms/master",
    "PERMISSION_PATH": "resource_access.account.roles",
    "USER_ID_FIELD": "username",
    # NOTE: preferred_username is mutable and can be reassigned in Keycloak.
    # For a stable, takeover-proof identity, point this at the immutable "sub"
    # claim and set USER_ID_FIELD to a dedicated field. See README.
    "USER_ID_CLAIM": "preferred_username",
    "VERIFY_SIGNATURE": True,
    "VERIFY_TOKENS_WITH_KEYCLOAK": False,
    "VERIFY_CERTIFICATE": True,
    # seconds of clock-skew tolerance for exp/nbf/iat checks
    "LEEWAY": 0,
    # django key, keycloak value
    "CLAIM_MAPPING": {
        "first_name": "given_name",
        "last_name": "family_name",
        "email": "email",
        "username": "preferred_username",
    },
}

# settings that, when changed, must invalidate the cached JWKS client because
# they determine which Keycloak the signing keys are fetched from.
_JWKS_RELEVANT = frozenset({"SERVER_URL", "ISSUER", "VERIFY_CERTIFICATE"})


class KeycloakSettings(APISettings):
    """We use the DRF settings logic"""

    def __init__(self, user_settings=None, defaults=None, import_strings=None):
        super().__init__(user_settings, defaults, import_strings)
        self.import_strings = ""

    @property
    def user_settings(self):
        if not hasattr(self, "_user_settings"):
            self._user_settings = getattr(settings, "KEYCLOAK_CONFIG", {})
        return self._user_settings

    @property
    def algorithms(self):
        """ALGORITHM normalized to a list for PyJWT's allowlist.

        A bare string would be iterated character-by-character by PyJWT, so a
        misconfigured short value could bypass the algorithm check. Always
        hand PyJWT an explicit list.
        """
        algorithm = self.ALGORITHM
        if isinstance(algorithm, list | tuple):
            return list(algorithm)
        return [algorithm]

    @property
    def base_url(self):
        """API base: explicit SERVER_URL, else fall back to ISSUER."""
        return self.SERVER_URL or self.ISSUER


keycloak_settings = KeycloakSettings(None, DEFAULT)


def reload_keycloak_settings(*args, **kwargs):  # pylint: disable=unused-argument
    """Reload when KEYCLOAK_CONFIG changes (e.g. override_settings in tests)."""
    setting = kwargs["setting"]
    if setting == "KEYCLOAK_CONFIG":
        keycloak_settings.reload()
        # The JWKS client snapshots its URL at construction; rebuild it so a
        # changed SERVER_URL/ISSUER is honored instead of hitting the old realm.
        from .keys import reset_jwks_client  # local import avoids import cycle

        reset_jwks_client()


# reload for unit test
setting_changed.connect(reload_keycloak_settings)
