# Permissions

Keycloak roles are carried inside the token. `HasPermission` reads the role list
at `PERMISSION_PATH` (default `resource_access.account.roles`) and checks
whether the required role is in it.

## As a subclass

The usual way — one permission class per role:

```python
from drf_keycloak.permissions import HasPermission
from rest_framework import generics


class ExamplePermission(HasPermission):
    permission = "view-profile"


class UserApi(generics.RetrieveAPIView):
    permission_classes = [ExamplePermission]
```

## As a configured instance

For one-offs you can skip the subclass:

```python
class UserApi(generics.RetrieveAPIView):
    permission_classes = [HasPermission("view-profile")]
```

`drf_keycloak.permissions.HasViewProfilePermission` ships as a worked example of
the subclass form, using Keycloak's built-in `view-profile` role.

## Where the roles come from

`PERMISSION_PATH` is a dotted path into the decoded token. The default points at
the roles of the `account` client:

```json
{
  "resource_access": {
    "account": {
      "roles": ["view-profile", "manage-account"]
    }
  }
}
```

Point it at your own client — or at realm roles — to match how you model roles
in Keycloak:

```python
KEYCLOAK_CONFIG = {
    # client roles of "my-api"
    "PERMISSION_PATH": "resource_access.my-api.roles",
    # ...or realm-wide roles
    # "PERMISSION_PATH": "realm_access.roles",
}
```

Access is denied (rather than erroring) when the request is unauthenticated, the
path does not exist in the token, or the value at that path is not a list.

`has_object_permission` applies the same check, so object-level access behaves
like view-level access.
