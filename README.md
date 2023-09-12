# Keycloak Authentication for Django Rest Framework

In this project, we implement authentication using the Authorization Code Flow with Keycloak as the identity and access management service. Here is how the authentication flow is structured:

1. **Frontend Responsibility**:
   - **User Registration and Login**: The frontend handles user registration and login through Keycloak, facilitating a seamless user experience.
   
2. **Backend Responsibility**:
   - **Token Validation**: Once a user is authenticated, the backend takes over by validating the JWT (JSON Web Token) from the header of each incoming request to ensure it is valid and secure.

This approach allows us to keep the backend implementation relatively simple, focusing mainly on token validation, while leveraging Keycloak's robust authentication and authorization features through the frontend.


### Environment variables

```
KEYCLOAK_CONFIG = {
    "CLIENT_ID": os.environ["KEYCLOAK_CLIENT_ID"],
    "CLIENT_SECRET": os.environ["KEYCLOAK_CLIENT_SECRET"],
    "SERVER_URL": os.environ["KEYCLOAK_SERVER_URL"],
    "REALM": os.environ["KEYCLOAK_REALM"],
}
```
You can find a selection of variables in `drf_keycloak.settings.py`, just overwrite them in the django settings.

By setting the variable 
```
KEYCLOAK_CONFIG = {
    ...
    "VERIFY_TOKENS_WITH_KEYCLOAK": True
    ...
}
```
This means that the token is validated with the Keycloak API and locally.
By default, the setting is based on `DEBUG` variable.

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
class UserApi(generics.RetrieveAPIView):
    permission_classes = [HasViewProfilePermission]
```

### Middleware
For security reasons, use the middleware in `drf_keycloak.middleware.HeaderMiddleware` at the top of the settings.

```
MIDDLEWARE = [
    "drf_keycloak.middleware.HeaderMiddleware",
    ....

]
```
You should also take a look at the [django-csp](https://github.com/mozilla/django-csp) package from Mozilla.

### Requirements

```
requests==2.28.1
PyJWT==2.6.0
Django==4.2.5
djangorestframework==3.14.0
```


Thanks to [`django-rest-framework-simplejwt`](https://github.com/jazzband/djangorestframework-simplejwt), the code was inspirational for this package.


