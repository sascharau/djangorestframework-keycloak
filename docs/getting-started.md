# Getting started

## Install

```bash
pip install drf-keycloak
```

## Enable the app

Add `drf_keycloak` to `INSTALLED_APPS`:

```python
INSTALLED_APPS = [
    "django.contrib.auth",
    # ...
    "drf_keycloak",
]
```

## Register the authentication backend

Add `KeycloakAuthBackend` to the DRF settings:

```python
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        # ...
        "drf_keycloak.authentication.KeycloakAuthBackend",
        # ...
    ],
}
```

## Point it at your realm

The minimum configuration is the realm URL. Everything else has a default —
see [Configuration](configuration.md) for the full list.

```python
KEYCLOAK_CONFIG = {
    "ISSUER": "https://keycloak.example.com/realms/myrealm",
    "CLIENT_ID": "my-api",
    "AUDIENCE": "my-api",
}
```

!!! warning "Set `AUDIENCE`"
    With `AUDIENCE` left at `None` the `aud` claim is not checked, so a token
    minted for *any* client in the same realm is accepted by your API. See
    [Audience](configuration.md#audience).

## Make a request

Send the access token as a bearer token:

```bash
curl -H "Authorization: Bearer $ACCESS_TOKEN" https://api.example.com/profile/
```

On success the token's claims are mapped onto a Django user (created on first
login, and re-synced from the token on every subsequent login — see
[`CLAIM_MAPPING`](configuration.md#claim_mapping)), which is then available as
`request.user`.

A missing `Authorization` header leaves the request anonymous so other
authenticators still get their turn; a present-but-invalid token is rejected
with `401`. The details are in [Behavior on invalid
tokens](security.md#behavior-on-invalid-tokens).
