# Keycloak Authentication for Django REST Framework

`drf-keycloak` validates Keycloak-issued JWTs in your Django REST Framework API.
It implements the backend half of the *Authorization Code Flow*:

- **The frontend** handles registration and login against Keycloak.
- **The backend** validates the JWT from the `Authorization` header of every
  incoming request.

That split keeps the backend small — it only verifies tokens — while Keycloak
provides the actual authentication and authorization features.

```bash
pip install drf-keycloak
```

<div class="grid cards" markdown>

- :material-rocket-launch: **[Getting started](getting-started.md)** — install,
  register the authentication backend, make your first authenticated request.
- :material-cog: **[Configuration](configuration.md)** — every `KEYCLOAK_CONFIG`
  key, and the two settings that quietly weaken security if you leave them at
  their defaults.
- :material-key: **[Permissions](permissions.md)** — map Keycloak roles onto DRF
  permission classes.
- :material-shield-lock: **[Security](security.md)** — behavior on invalid
  tokens, security headers, CSP.
- :material-api: **[OpenAPI schema](openapi.md)** — drf-spectacular integration.

</div>

## Requirements

| | |
|---|---|
| Python | 3.10 – 3.13 |
| Django | 4.2, 5.2, 6.0 |
| Django REST Framework | 3.14+ |

## Sponsor

<p markdown>
  <a href="https://fin3000.com">
    <img src="https://fin3000.com/static/images/logo.svg" alt="Fin3000" height="48">
  </a>
</p>

Development of this package is sponsored by
[**Fin3000**](https://fin3000.com) — accounting and invoicing for small
businesses in Germany.

## License

MIT. See [LICENSE.txt](https://github.com/sascharau/djangorestframework-keycloak/blob/main/LICENSE.txt).
