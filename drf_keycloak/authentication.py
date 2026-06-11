"""Keycloak User Authentication"""

import logging

from django.contrib.auth import get_user_model
from django.db import IntegrityError
from rest_framework import authentication
from rest_framework.exceptions import AuthenticationFailed

from .exceptions import TokenBackendError, TokenBackendExpiredToken
from .settings import keycloak_settings
from .token import JWToken

logger = logging.getLogger("drf_keycloak")


class InvalidToken(AuthenticationFailed):
    """The token failed validation. Mirrors rest_framework_simplejwt."""

    default_detail = "Token is invalid or expired"
    default_code = "token_not_valid"


class ExpiredToken(InvalidToken):
    """The token is well-formed but expired.

    A distinct code so clients can tell "refresh me" apart from "re-login".
    """

    default_detail = "Token is expired"
    default_code = "token_expired"


class KeycloakAuthBackend(authentication.BaseAuthentication):
    """
    Validates the JWT locally (and optionally against the Keycloak API),
    then gets or creates the matching Django user.
    """

    raw_token = None
    user_model = get_user_model()

    def authenticate_header(self, request):
        return 'Bearer realm="api"'

    def get_raw_token(self, header):
        """
        Extract the bearer token from the Authorization header value.

        Returns None when the header is empty or not a bearer scheme (so other
        authenticators get a chance); raises when the scheme is bearer but
        malformed.
        """
        parts = header.split()
        if len(parts) == 0:
            # Empty AUTHORIZATION header sent
            return None

        if parts[0].lower() != "bearer":
            # Assume the header does not contain a JSON web token
            return None
        if len(parts) != 2:
            raise AuthenticationFailed(
                "Authorization header must contain two space-delimited values",
                code="bad_authorization_header",
            )

        return parts[1]

    def authenticate(self, request):
        header = request.headers.get("Authorization")
        if header is None:
            return None

        self.raw_token = self.get_raw_token(header)
        if self.raw_token is None:
            return None

        try:
            validated_token = JWToken(self.raw_token).payload
        except TokenBackendExpiredToken as exc:
            raise ExpiredToken() from exc
        except TokenBackendError as exc:
            raise InvalidToken() from exc
        # KeycloakAPIError (503) and config RuntimeError intentionally propagate:
        # an outage must fail closed and visibly, not silently downgrade to
        # anonymous.

        return self.get_user_or_create(validated_token), validated_token

    def get_user_or_create(self, validated_token):
        """
        Find or create the user identified by the token, and keep it in sync.
        """
        try:
            user_id = validated_token[keycloak_settings.USER_ID_CLAIM]
        except KeyError as exc:
            raise InvalidToken(
                "Token contained no recognizable user identification"
            ) from exc
        if not user_id:
            # Empty/blank claim (e.g. a service account without a username)
            # would otherwise create a broken user with an empty identifier.
            raise InvalidToken("Token contained no recognizable user identification")

        lookup = {keycloak_settings.USER_ID_FIELD: user_id}
        try:
            user, created = self.user_model.objects.get_or_create(**lookup)
        except IntegrityError:
            # Concurrent first request for the same user raced us to the insert.
            user, created = self.user_model.objects.get(**lookup), False

        if created:
            user.set_unusable_password()
        self.update_user(user, validated_token, force_save=created)

        if not self.user_can_authenticate(user):
            raise AuthenticationFailed("User is inactive", code="user_inactive")
        return user

    def user_can_authenticate(self, user):
        """
        Reject users with is_active=False. Custom user models without an
        is_active attribute are allowed (matching Django's ModelBackend).
        """
        is_active = getattr(user, "is_active", True)
        return is_active is None or is_active

    def update_user(self, user, claims, force_save=False):
        """
        Sync mapped fields from the token on every login, writing only when a
        value actually changed (or force_save is set, e.g. to persist a freshly
        created user). Values longer than the target column are truncated (and
        logged) so a long Keycloak value can't 500 the request.

        Security-relevant fields (is_staff, is_superuser, ...) are deliberately
        NOT in the default CLAIM_MAPPING and should not be added there.
        """
        dirty = force_save
        for field, claim in keycloak_settings.CLAIM_MAPPING.items():
            if claim not in claims:
                continue
            value = self._fit_to_field(user, field, claims[claim])
            if getattr(user, field, None) != value:
                setattr(user, field, value)
                dirty = True
        if dirty:
            user.save()
        return user

    @staticmethod
    def _fit_to_field(user, field, value):
        if isinstance(value, str):
            try:
                max_length = user._meta.get_field(field).max_length
            except Exception:  # noqa: BLE001 - unknown/virtual field, leave as-is
                max_length = None
            if max_length and len(value) > max_length:
                logger.warning(
                    "Truncating Keycloak claim for '%s' to %d chars during sync",
                    field,
                    max_length,
                )
                return value[:max_length]
        return value
