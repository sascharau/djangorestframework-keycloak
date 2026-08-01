# Security

## Behavior on invalid tokens

A missing `Authorization` header leaves the request **anonymous**, so other
authenticators in `DEFAULT_AUTHENTICATION_CLASSES` still get a chance to handle
it.

A present-but-invalid token is **rejected with `401`**:

| Situation | Status | Code |
|---|---|---|
| Malformed, wrongly signed, wrong issuer/audience | `401` | `token_not_valid` |
| Expired token | `401` | `token_expired` |
| Inactive or unknown user | `401` | `user_inactive` |
| Keycloak unreachable (with `VERIFY_TOKENS_WITH_KEYCLOAK`) | `503` | — |

The distinct `token_expired` code lets a client tell "refresh your token" apart
from "this token is bad", so it knows when a refresh is worth attempting.

The `503` case is deliberate: when introspection is enabled and Keycloak cannot
be reached, the request **fails closed** rather than silently degrading to
anonymous access.

!!! info "Logging"
    The package logs under the `drf_keycloak` logger — warnings on Keycloak
    failures, debug on token rejection. Token and secret material is never
    logged.

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

- [Security overview](https://docs.djangoproject.com/en/6.0/topics/security/)
- [Deployment checklist](https://docs.djangoproject.com/en/6.0/howto/deployment/checklist/)
  (`manage.py check --deploy`)

## Content Security Policy

For XSS defense, set a Content-Security-Policy.

Django **6.0+** ships CSP in core: configure `SECURE_CSP` (or
`SECURE_CSP_REPORT_ONLY`) and add
`django.middleware.csp.ContentSecurityPolicyMiddleware` — see the
[Django CSP docs](https://docs.djangoproject.com/en/6.0/howto/csp/).

On Django < 6, use Mozilla's [django-csp](https://github.com/mozilla/django-csp)
package.

## Reporting a vulnerability

Please report security issues privately via
[GitHub security advisories](https://github.com/sascharau/djangorestframework-keycloak/security/advisories/new)
rather than in a public issue.
