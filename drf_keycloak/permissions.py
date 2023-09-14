""" Get User permissions from Keycloak token  """
from rest_framework.permissions import BasePermission

from .settings import keycloak_settings


class HasPermission(BasePermission):
    """
    Allows the User access if they have the expected permission
    """

    def __init__(self, permission=None):
        if permission:
            self.permission = permission

    def has_permission(self, request, view):
        try:
            # Get the JWT permission path from the environment variable
            jwt_permission_path = keycloak_settings.PERMISSION_PATH
            # Split the path into individual keys
            keys = jwt_permission_path.split('.')

            # Get the JWT permission list using the keys
            jwt_permission = request.auth
            if not jwt_permission:
                return False

            for key in keys:
                jwt_permission = jwt_permission[key]

            # If the final value is not a list, set it to an empty list
            if not isinstance(jwt_permission, list):
                jwt_permission = []
        except KeyError:
            jwt_permission = []

        return request.auth and self.permission in jwt_permission

    def has_object_permission(self, request, view, obj):
        return self.has_permission(request, view)


class HasViewProfilePermission(HasPermission):
    """
    this is a default keycloak permission
    it is an example
    """

    permission = "view-profile"
