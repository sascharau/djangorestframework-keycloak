"""helpers for tests"""

import time

import jwt
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from django.contrib.auth import get_user_model

from .conftest import TEST_ISSUER

User = get_user_model()

USERNAME = "foobar3000"
EMAIL = "foo@bar.de"
FIRST_NAME = "John"
LAST_NAME = "Doe"

# A throwaway RSA keypair shared by the test suite. The public key stands in
# for what keys.get_signing_key would return for a real JWKS key.
_PRIVATE_KEY = rsa.generate_private_key(public_exponent=65537, key_size=2048)
TEST_KID = "test-kid"


def public_key():
    """The public key object jwt.decode expects (matches PyJWK.key)."""
    return _PRIVATE_KEY.public_key()


def public_key_pem():
    return public_key().public_bytes(
        serialization.Encoding.PEM,
        serialization.PublicFormat.SubjectPublicKeyInfo,
    )


def make_token(claims=None, exp_delta=3600, kid=TEST_KID, **header_overrides):
    """Build a real RS256-signed token with sensible Keycloak-like claims."""
    now = int(time.time())
    payload = {
        "iss": TEST_ISSUER,
        "preferred_username": USERNAME,
        "given_name": FIRST_NAME,
        "family_name": LAST_NAME,
        "email": EMAIL,
        "iat": now,
        "exp": now + exp_delta,
    }
    if claims:
        payload.update(claims)
    headers = {"kid": kid}
    headers.update(header_overrides)
    return jwt.encode(payload, _PRIVATE_KEY, algorithm="RS256", headers=headers)


def create_user():
    """
    helper function to create
    @return: user
    """
    user = User.objects.create_user(
        username=USERNAME,
        first_name=FIRST_NAME,
        last_name=LAST_NAME,
        email=EMAIL,
    )
    user.set_unusable_password()
    return user
