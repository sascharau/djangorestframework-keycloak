# Configuration

Everything lives in a single `KEYCLOAK_CONFIG` dict in your Django settings.
Only the keys you set are overridden; the rest fall back to the defaults in
`drf_keycloak/settings.py`.

```python
KEYCLOAK_CONFIG = {
    # Base URL for Keycloak API calls (userinfo, introspection, JWKS). Must be
    # the full realm path. If unset, ISSUER is used.
    "SERVER_URL": "http://localhost:8080/realms/master",
    "CLIENT_ID": "account",
    # Required only when VERIFY_TOKENS_WITH_KEYCLOAK is True (introspection).
    "CLIENT_SECRET": None,
    # Expected "aud" claim. When None, audience is NOT verified (see below).
    "AUDIENCE": None,
    # Allowed signing algorithm(s). A list is recommended.
    "ALGORITHM": ["RS256"],
    # Expected "iss" claim; also the full realm path.
    "ISSUER": "http://localhost:8080/realms/master",
    "PERMISSION_PATH": "resource_access.account.roles",
    # Which Django field / token claim identify the user. For a stable,
    # takeover-proof identity prefer the immutable "sub" claim (see below).
    "USER_ID_FIELD": "username",
    "USER_ID_CLAIM": "preferred_username",
    "VERIFY_SIGNATURE": True,
    # Also validate every request against Keycloak's introspection endpoint.
    "VERIFY_TOKENS_WITH_KEYCLOAK": False,
    # Verify TLS certificates for Keycloak calls.
    "VERIFY_CERTIFICATE": True,
    # Clock-skew tolerance (seconds) for exp/iat/nbf.
    "LEEWAY": 0,
    # user mapping — synced from the token on every login
    # django keys, keycloak keys
    "CLAIM_MAPPING": {
        "first_name": "given_name",
        "last_name": "family_name",
        "email": "email",
        "username": "preferred_username",
    },
}
```

## Reference

| Key | Default | Purpose |
|---|---|---|
| `SERVER_URL` | `None` | Base URL for Keycloak API calls (JWKS, userinfo, introspection). Full realm path. Falls back to `ISSUER` when unset. |
| `CLIENT_ID` | `"account"` | Client used for introspection calls. |
| `CLIENT_SECRET` | `None` | Required only when `VERIFY_TOKENS_WITH_KEYCLOAK` is enabled. |
| `AUDIENCE` | `None` | Expected `aud` claim. **Not verified while `None`** — see [Audience](#audience). |
| `ALGORITHM` | `["RS256"]` | Allowed signing algorithms. |
| `ISSUER` | `http://localhost:8080/realms/master` | Expected `iss` claim; full realm path. |
| `PERMISSION_PATH` | `resource_access.account.roles` | Dotted path to the role list inside the token. |
| `USER_ID_FIELD` | `"username"` | Django user field used to look the user up. |
| `USER_ID_CLAIM` | `"preferred_username"` | Token claim matched against `USER_ID_FIELD` — see [Identity claim](#identity-claim). |
| `VERIFY_SIGNATURE` | `True` | Verify the JWT signature. Never disable in production. |
| `VERIFY_TOKENS_WITH_KEYCLOAK` | `False` | Additionally introspect every token — see [Token introspection](#token-introspection). |
| `VERIFY_CERTIFICATE` | `True` | Verify TLS certificates on Keycloak calls. |
| `LEEWAY` | `0` | Clock-skew tolerance in seconds for `exp` / `iat` / `nbf`. |
| `CLAIM_MAPPING` | see above | Django field → Keycloak claim — see [`CLAIM_MAPPING`](#claim_mapping). |

!!! note "`ALGORITHM` should be a list"
    A bare string is normalized to a list internally, because PyJWT would
    otherwise iterate it character by character and a misconfigured short value
    could weaken the algorithm check.

## Identity claim

`preferred_username` is **mutable** and can be reassigned in Keycloak. If a
username could ever be renamed and then reused by someone else, that second
person inherits the first person's Django user.

For a stable identity, point `USER_ID_CLAIM` at the immutable `sub` claim and
`USER_ID_FIELD` at a dedicated field that stores it:

```python
KEYCLOAK_CONFIG = {
    "USER_ID_CLAIM": "sub",
    "USER_ID_FIELD": "keycloak_id",  # a field on your user model
}
```

## Audience

With `AUDIENCE` set to `None` the `aud` claim is not checked, so a token minted
for **another client in the same realm** is accepted by your API. Set `AUDIENCE`
to your client to close that:

```python
KEYCLOAK_CONFIG = {
    "AUDIENCE": "my-api",
}
```

!!! danger "`VERIFY_SIGNATURE: False`"
    This disables all validation and is for local debugging only. Never use it
    in production.

## Token introspection

```python
KEYCLOAK_CONFIG = {
    "VERIFY_TOKENS_WITH_KEYCLOAK": True,
}
```

When enabled, each request is validated locally **and** against Keycloak's
token introspection endpoint, so tokens revoked in Keycloak (logout, session
termination, disabled user) are rejected before their `exp`.

The trade-off: it requires `CLIENT_SECRET` and adds one network round-trip per
request. That couples your API's latency and availability to Keycloak — a
Keycloak outage makes requests fail with `503`. It is `False` by default (local
validation only).

## `CLAIM_MAPPING`

Maps Django user fields to Keycloak claims. The mapped fields are synced from
the token on **every** login, with a dirty-check so a database write only
happens when a value actually changed. Keycloak is the source of truth for
these fields — local edits to them are overwritten on the next request.
