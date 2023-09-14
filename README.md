# Keycloak Authentication for Django Rest Framework

In this project, we implement authentication using the **Authorization Code Flow** with Keycloak as the identity and access management service. Here is how the authentication flow is structured:

1. **Frontend Responsibility**:
   - **User Registration and Login**: The frontend handles user registration and login through Keycloak, facilitating a seamless user experience.
   
2. **Backend Responsibility**:
   - **Token Validation**: Once a user is authenticated, the backend takes over by validating the JWT (JSON Web Token) from the header of each incoming request to ensure it is valid and secure.

This approach allows us to keep the backend implementation relatively simple, focusing mainly on token validation, while leveraging Keycloak's robust authentication and authorization features through the frontend.


### Settings

You can find a selection of variables in `drf_keycloak.settings.py`, just overwrite them in the django settings.
```
KEYCLOAK_CONFIG = {
    "SERVER_URL": "http://localhost:8080/",
    "REALM": "master",
    "CLIENT_ID": "account",
    "CLIENT_SECRET": None,
    "AUDIENCE": None,
    "ALGORITHM": "RS256",
    "ISSUER": "http://localhost:8080/realms/master",
    "VERIFY_TOKENS_WITH_KEYCLOAK": False,
    "PERMISSION_PATH": "resource_access.account.roles",
    "USER_ID_FIELD": "username",
    "USER_ID_CLAIM": "preferred_username",
    
    # user mapping
    # django keys, keycloak keys
    "CLAIM_MAPPING": {
        "first_name": "given_name",
        "last_name": "family_name",
        "email": "email",
        "username": "preferred_username",
    },
}
```
By setting the variable 
```
KEYCLOAK_CONFIG = {
    ...
    "VERIFY_TOKENS_WITH_KEYCLOAK": True
    ...
}
```
This means that the token is validated with the Keycloak API and locally.

### Enable
Add `keycloak` to INSTALLED_APPS.
```
INSTALLED_APPS = [
    "django.contrib.auth",
    ...
    "drf_keycloak"
]
```
 Add `drf_keycloak.authentication.KeycloakAuthBackend` to DRF settings
```
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        ...
        "drf_keycloak.authentication.KeycloakAuthBackend",
        ...
    ],
```

### Permissions
To create permissions for your API follow the example in `HasViewProfilePermission` in `drf_keycloak.permissions.py`.

use it as usual...
```
from drf_keycloak.permissions import HasPermission

class ExamplePermission(HasPermission):
    permission = "view-profile"
    

class UserApi(generics.RetrieveAPIView):
    permission_classes = [ExamplePermission]
```

### Middleware
For security reasons, use the optional middleware in `drf_keycloak.middleware.HeaderMiddleware` at the top of the settings.

```
MIDDLEWARE = [
    "drf_keycloak.middleware.HeaderMiddleware",
    ....

]
```
You should also look at Mozilla's [django-csp](https://github.com/mozilla/django-csp) package.



### Thanks
Thanks to [`django-rest-framework-simplejwt`](https://github.com/jazzband/djangorestframework-simplejwt), the code was inspirational for this package.


