""" Keycloak User Authentication """
from django.contrib.auth import get_user_model
from rest_framework import authentication
from rest_framework.exceptions import AuthenticationFailed

from .api import keycloak_api
from .settings import keycloak_settings
from .token import JWToken


class InvalidToken(AuthenticationFailed):
    """
    Base on REST framework exceptions.
    Only the description is changed.
    """

    default_detail = "Token is invalid or expired"
    default_code = "token_not_valid"


class KeycloakAuthBackend(authentication.BaseAuthentication):
    """
    checks the jwt token local and with the keycloak API.
    get or create user and updates the user
    this is inspired from rest_framework_simplejwt
    """

    raw_token = None
    user_model = get_user_model()

    def authenticate_header(self, request):
        return "Bearer realm='api'"

    def get_raw_token(self, header):
        """
        Extracts an unvalidated JSON web token from the given "Authorization"
        header value.
        """
        parts = header.split()
        if len(parts) == 0:
            # Empty AUTHORIZATION header sent
            return None

        if not parts[0] == "Bearer":
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
        validated_token = JWToken(self.raw_token).payload
        return self.get_user_or_create(validated_token), validated_token

    def get_user_or_create(self, validated_token):
        """
        Attempts to find and return a user using the given validated token.
        """
        try:
            user_id = validated_token[keycloak_settings.USER_ID_CLAIM]
        except KeyError as exc:
            raise InvalidToken("Token contained no recognizable user identification") from exc

        user, created = self.user_model.objects.get_or_create(
            **{keycloak_settings.USER_ID_FIELD: user_id}
        )
        if created:
            if keycloak_settings.VERIFY_TOKENS_WITH_KEYCLOAK:
                validated_token = keycloak_api.get_userinfo(self.raw_token.decode())
            user.set_unusable_password()
            self.update_user(user, validated_token)

        return user if self.user_can_authenticate(user) else None

    def user_can_authenticate(self, user):
        """
        Reject users with is_active=False. Custom user models that don't have
        that attribute are allowed.
        """
        is_active = getattr(user, "is_active", None)
        return is_active or is_active is None

    def update_user(self, user, claims):
        """
        The user object will be updated with all fields in mappings.
        If security relevant fields like is_superuser should not be updated here
        """
        for field, claim in keycloak_settings.CLAIM_MAPPING.items():
            if claim in claims:
                setattr(user, field, claims[claim])
        return user.save()
