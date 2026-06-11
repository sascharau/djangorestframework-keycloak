"""JWKS signing-key resolution.

This is the single source of signing keys for token validation. PyJWT's
``PyJWKClient`` already caches the JWKS and refreshes it on key rotation; we
wrap it only to:

  * rate-limit the *forced* refresh so an attacker spamming tokens with random
    ``kid`` values can't amplify into unbounded fetches against Keycloak, and
  * translate ``PyJWKClient`` errors into our 401/503 taxonomy (those classes
    subclass ``PyJWTError`` but NOT ``InvalidTokenError``, so without this they
    would surface as uncaught 500s).
"""

import ssl
import threading
import time

import jwt
from jwt import PyJWKClient
from jwt.exceptions import PyJWKClientError

try:  # PyJWT >= 2.8
    from jwt.exceptions import PyJWKClientConnectionError
except ImportError:  # pragma: no cover - older PyJWT
    PyJWKClientConnectionError = PyJWKClientError

from .exceptions import KeycloakAPIError, TokenBackendError
from .settings import keycloak_settings

_JWKS_LIFESPAN = 60 * 10
# Minimum seconds between two forced JWKS refreshes. Bounds the blast radius of
# an unknown-kid flood to one extra fetch per window.
_REFRESH_COOLDOWN = 60

_lock = threading.Lock()
_client = None
_client_url = None
# -inf (not 0.0): time.monotonic()'s epoch is arbitrary, so on a freshly booted
# host monotonic() can be < the cooldown and 0.0 would wrongly block the very
# first refresh. -inf means "never refreshed yet -> allow".
_last_refresh = float("-inf")


def _certs_url():
    return f"{keycloak_settings.base_url}/protocol/openid-connect/certs"


def _build_client(url):
    ssl_context = None
    if not keycloak_settings.VERIFY_CERTIFICATE:
        ssl_context = ssl._create_unverified_context()  # noqa: S323 - opt-in
    return PyJWKClient(
        url,
        cache_jwk_set=True,
        lifespan=_JWKS_LIFESPAN,
        ssl_context=ssl_context,
    )


def _get_client():
    """Return the cached client, rebuilding it if the JWKS URL changed."""
    global _client, _client_url
    url = _certs_url()
    with _lock:
        if _client is None or _client_url != url:
            _client = _build_client(url)
            _client_url = url
        return _client


def _refresh_allowed():
    """True at most once per cooldown window (anti-amplification gate)."""
    global _last_refresh
    now = time.monotonic()
    with _lock:
        if now - _last_refresh < _REFRESH_COOLDOWN:
            return False
        _last_refresh = now
        return True


def _match(signing_keys, kid):
    if kid is None:
        # A token without a kid is only unambiguous when there is exactly one
        # signing key. Otherwise we cannot safely pick one.
        return signing_keys[0] if len(signing_keys) == 1 else None
    for key in signing_keys:
        if key.key_id == kid:
            return key
    return None


def reset_jwks_client():
    """Drop the cached client so the next call rebuilds it.

    Called when JWKS-relevant settings change (e.g. override_settings in tests
    or a runtime reconfiguration), otherwise the client would keep fetching
    from the old realm URL.
    """
    global _client, _client_url, _last_refresh
    with _lock:
        _client = None
        _client_url = None
        _last_refresh = float("-inf")


def get_signing_key(token):
    """Resolve the signing key for ``token``.

    Raises ``TokenBackendError`` (401-class) for a malformed header or an
    unknown ``kid``, and ``KeycloakAPIError`` (503) when the JWKS endpoint is
    unreachable.
    """
    try:
        kid = jwt.get_unverified_header(token).get("kid")
    except jwt.PyJWTError as exc:
        raise TokenBackendError("Token header is invalid") from exc

    client = _get_client()

    # 1. Cache-first lookup. get_signing_keys() only hits the network on cold
    #    start or once the cached set has aged past its lifespan.
    try:
        signing_keys = client.get_signing_keys()
    except PyJWKClientConnectionError as exc:
        raise KeycloakAPIError() from exc
    except PyJWKClientError as exc:
        raise TokenBackendError("No signing keys available") from exc

    signing_key = _match(signing_keys, kid)
    if signing_key is not None:
        return signing_key.key

    # 2. Unknown kid. This may be a genuine rotation, so force one refresh —
    #    but only if the cooldown permits, to deny amplification.
    if not _refresh_allowed():
        raise TokenBackendError("Signing key not found")

    try:
        signing_keys = client.get_signing_keys(refresh=True)
    except PyJWKClientConnectionError as exc:
        raise KeycloakAPIError() from exc
    except PyJWKClientError as exc:
        raise TokenBackendError("Signing key not found") from exc

    signing_key = _match(signing_keys, kid)
    if signing_key is None:
        raise TokenBackendError("Signing key not found")
    return signing_key.key
