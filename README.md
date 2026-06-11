# Keycloak Authentication for Django Rest Framework

In this project, we implement authentication using the *Authorization Code Flow* with Keycloak as the identity and access management service. Here is how the authentication flow is structured:

1. **Frontend Responsibility**:

   - **User Registration and Login**: The frontend handles user registration and login through Keycloak, facilitating a seamless user experience.

2. **Backend Responsibility**:

   - **Token Validation**: Once a user is authenticated, the backend takes over by validating the JWT (JSON Web Token) from the header of each incoming request to ensure it is valid and secure.

This approach allows us to keep the backend implementation relatively simple, focusing mainly on token validation, while leveraging Keycloak's robust authentication and authorization features through the frontend.

## Install

```bash
pip install drf-keycloak
```

## Settings

You can find a selection of variables in `drf_keycloak.settings.py`, just overwrite them in the Django settings.

```python
KEYCLOAK_CONFIG = {
    # Base URL for Keycloak API calls (userinfo, introspection, JWKS). Must be
    # the full realm path. If unset, ISSUER is used.
    "SERVER_URL": "http://localhost:8080/realms/master",
    "CLIENT_ID": "account",
    # Required only when VERIFY_TOKENS_WITH_KEYCLOAK is True (introspection).
    "CLIENT_SECRET": None,
    # Expected "aud" claim. When None, audience is NOT verified (see note below).
    "AUDIENCE": None,
    # Allowed signing algorithm(s). A list is recommended.
    "ALGORITHM": ["RS256"],
    # Expected "iss" claim; also the full realm path.
    "ISSUER": "http://localhost:8080/realms/master",
    "PERMISSION_PATH": "resource_access.account.roles",
    # Which Django field / token claim identify the user. For a stable,
    # takeover-proof identity prefer the immutable "sub" claim (see note below).
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

> **Identity claim:** `preferred_username` is mutable and can be reassigned in
> Keycloak. If a username could ever be renamed and reused, point `USER_ID_CLAIM`
> at the immutable `sub` claim (and set `USER_ID_FIELD` to a dedicated field) to
> avoid account-takeover by username reuse.

> **Audience:** with `AUDIENCE` set to `None` the `aud` claim is not checked, so a
> token minted for another client in the same realm is accepted. Set `AUDIENCE`
> to your client to close that. `VERIFY_SIGNATURE: False` disables all validation
> and is for local debugging only — never use it in production.

### Behavior on invalid tokens

A missing `Authorization` header leaves the request anonymous (other
authenticators still get a chance). A present-but-invalid token is rejected with
`401`: code `token_not_valid`, or `token_expired` for an expired token so the
client knows to refresh. If `VERIFY_TOKENS_WITH_KEYCLOAK` is enabled and Keycloak
is unreachable, the request fails closed with `503` rather than silently becoming
anonymous.

The package logs under the `drf_keycloak` logger (warnings on Keycloak failures,
debug on token rejection); token and secret material are never logged.

## Enable

Add `drf_keycloak` to `INSTALLED_APPS`.

```python
INSTALLED_APPS = [
    "django.contrib.auth",
    # ...
    "drf_keycloak"
]
```

Add `drf_keycloak.authentication.KeycloakAuthBackend` to DRF settings

```python
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        # ...
        "drf_keycloak.authentication.KeycloakAuthBackend",
        # ...
    ],
}
```

By setting the variable:

```python
KEYCLOAK_CONFIG = {
    ...
    "VERIFY_TOKENS_WITH_KEYCLOAK": True
    ...
}
```

When enabled, each request is validated locally **and** against Keycloak's token
introspection endpoint, so tokens revoked in Keycloak (logout, session
termination, disabled user) are rejected before their `exp`. This requires
`CLIENT_SECRET` and adds one network round-trip per request: it couples your
API's latency and availability to Keycloak, and a Keycloak outage makes requests
fail with `503`. By default it is `False` (local validation only).

## Permissions

To create permissions for your API follow the example in `HasViewProfilePermission` in `drf_keycloak.permissions.py`.

Use it as usual...

```python
from drf_keycloak.permissions import HasPermission

class ExamplePermission(HasPermission):
    permission = "view-profile"


class UserApi(generics.RetrieveAPIView):
    permission_classes = [ExamplePermission]
```

## Security headers

This package does not ship its own header middleware — security headers are
Django's job, and it does them better. Enable Django's built-in
`SecurityMiddleware` and configure the `SECURE_*` settings for your deployment:

```python
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    # ...
]

# HSTS is only emitted over HTTPS; includeSubDomains is an explicit opt-in
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_SSL_REDIRECT = True
SECURE_CONTENT_TYPE_NOSNIFF = True
```

**Please read Django's security documentation** and apply what fits your setup —
it is the authoritative source and covers far more than this package could:

- Security overview: <https://docs.djangoproject.com/en/6.0/topics/security/>
- Deployment checklist (`manage.py check --deploy`): <https://docs.djangoproject.com/en/6.0/howto/deployment/checklist/>

### Content Security Policy

For XSS defense, set a Content-Security-Policy. Django **6.0+** ships CSP in
core: configure `SECURE_CSP` (or `SECURE_CSP_REPORT_ONLY`) and add
`django.middleware.csp.ContentSecurityPolicyMiddleware` — see the
[Django CSP docs](https://docs.djangoproject.com/en/6.0/howto/csp/). On Django
< 6, use Mozilla's [django-csp](https://github.com/mozilla/django-csp) package.

## OpenAPI Schema with drf-spectacular

Requires [drf-spectacular](https://github.com/tfranzel/drf-spectacular):
`pip install drf-spectacular`.

In any `apps.py` or file that is loaded at startup

```python
from django.apps import AppConfig

class MyAppConfig(AppConfig):
    """app config"""

    default_auto_field = "django.db.models.BigAutoField"
    name = "myapp"

    def ready(self):
        import drf_keycloak.schema  # noqa: E402
```
