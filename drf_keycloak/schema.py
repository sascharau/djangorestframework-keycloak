try:
    from drf_spectacular.extensions import OpenApiAuthenticationExtension
    from drf_spectacular.plumbing import build_bearer_security_scheme_object
except ImportError as exc:
    # drf-spectacular is an optional dependency; only needed for OpenAPI schema.
    raise ImportError(
        "drf_keycloak.schema requires drf-spectacular. "
        "Install it with: pip install drf-spectacular"
    ) from exc


class TokenScheme(OpenApiAuthenticationExtension):
    target_class = "drf_keycloak.authentication.KeycloakAuthBackend"
    name = "KeycloakAuth"
    match_subclasses = True
    priority = -1

    def get_security_definition(self, auto_schema):  # pragma: no cover
        return build_bearer_security_scheme_object(
            header_name="AUTHORIZATION", token_prefix="Bearer", bearer_format="JWT"
        )
