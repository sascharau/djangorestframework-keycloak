# OpenAPI schema

`drf_keycloak.schema` registers the authentication class with
[drf-spectacular](https://github.com/tfranzel/drf-spectacular), so the generated
OpenAPI schema documents the bearer-token security scheme instead of leaving
endpoints looking unauthenticated.

```bash
pip install drf-spectacular
```

Import the module once at startup — for example from an `AppConfig.ready()`:

```python
from django.apps import AppConfig


class MyAppConfig(AppConfig):
    """app config"""

    default_auto_field = "django.db.models.BigAutoField"
    name = "myapp"

    def ready(self):
        import drf_keycloak.schema  # noqa: E402
```

Any module that is loaded at startup works; `ready()` is simply the idiomatic
place for import-for-side-effect registrations.
