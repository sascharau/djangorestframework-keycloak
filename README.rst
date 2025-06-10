=================================================
Keycloak Authentication for Django Rest Framework
=================================================

In this project, we implement authentication using the *Authorization Code Flow* with Keycloak as the identity and access management service. Here is how the authentication flow is structured:

1. **Frontend Responsibility**:

   - **User Registration and Login**: The frontend handles user registration and login through Keycloak, facilitating a seamless user experience.

2. **Backend Responsibility**:

   - **Token Validation**: Once a user is authenticated, the backend takes over by validating the JWT (JSON Web Token) from the header of each incoming request to ensure it is valid and secure.

This approach allows us to keep the backend implementation relatively simple, focusing mainly on token validation, while leveraging Keycloak's robust authentication and authorization features through the frontend.

Install
_______

.. code-block:: bash

   pip install drf-keycloak



Settings
--------

You can find a selection of variables in ``drf_keycloak.settings.py``, just overwrite them in the Django settings.

.. code-block:: python

   KEYCLOAK_CONFIG = {
       "SERVER_URL": "http://localhost:8080/realms/master",
       "REALM": "master",
       "CLIENT_ID": "account",
       "CLIENT_SECRET": None,
       "AUDIENCE": None,
       "ALGORITHM": "RS256",
       "ISSUER": "http://localhost:8080/realms/master",
       "PERMISSION_PATH": "resource_access.account.roles",
       "USER_ID_FIELD": "username",
       "USER_ID_CLAIM": "preferred_username",
       "VERIFY_SIGNATURE": True,
       # user mapping
       # django keys, keycloak keys
       "CLAIM_MAPPING": {
           "first_name": "given_name",
           "last_name": "family_name",
           "email": "email",
           "username": "preferred_username",
       },
   }


Enable
******

Add ``keycloak`` to ``INSTALLED_APPS``.

.. code-block:: python

   INSTALLED_APPS = [
       "django.contrib.auth",
       # ...
       "drf_keycloak"
   ]

Add ``drf_keycloak.authentication.KeycloakAuthBackend`` to DRF settings

.. code-block:: python

   REST_FRAMEWORK = {
       "DEFAULT_AUTHENTICATION_CLASSES": [
           # ...
           "drf_keycloak.authentication.KeycloakAuthBackend",
           # ...
       ],
   }

Permissions
***********

To create permissions for your API follow the example in ``HasViewProfilePermission`` in ``drf_keycloak.permissions.py``.

Use it as usual...

.. code-block:: python

   from drf_keycloak.permissions import HasPermission

   class ExamplePermission(HasPermission):
       permission = "view-profile"


   class UserApi(generics.RetrieveAPIView):
       permission_classes = [ExamplePermission]

Middleware
**********

For security reasons, use the optional middleware in ``drf_keycloak.middleware.HeaderMiddleware`` at the top of the settings.

.. code-block:: python

   MIDDLEWARE = [
       "drf_keycloak.middleware.HeaderMiddleware",
       # ...
   ]

You should also look at Mozilla's `django-csp <https://github.com/mozilla/django-csp>`_ package.

OpenAPI Schema with drf-spectacular
***********************************

In any ``apps.py`` or file that is loaded at startup

.. code-block:: python

   from django.apps import AppConfig

   class MyAppConfig(AppConfig):
       """app config"""

       default_auto_field = "django.db.models.BigAutoField"
       name = "myapp"

       def ready(self):
           import drf_keycloak.schema  # noqa: E402

Thanks
******

Thanks to `django-rest-framework-simplejwt <https://github.com/jazzband/djangorestframework-simplejwt>`_, the code was inspirational for this package.

