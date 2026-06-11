"""Get User permissions from Keycloak token"""

from rest_framework.permissions import BasePermission

from .settings import keycloak_settings


class HasPermission(BasePermission):
    """
    Allows the User access if they have the expected permission.

    Use either as a configured instance ``HasPermission("view-profile")`` or as
    a subclass that sets the ``permission`` class attribute.
    """

    permission = None

    def __init__(self, permission=None):
        if permission:
            self.permission = permission

    def has_permission(self, request, view):
        if not request.auth:
            return False

        jwt_permission = request.auth
        try:
            for key in keycloak_settings.PERMISSION_PATH.split("."):
                jwt_permission = jwt_permission[key]
        except (KeyError, TypeError):
            # Path missing, or a segment was a list/str instead of a dict.
            return False

        if not isinstance(jwt_permission, list):
            return False
        return self.permission in jwt_permission

    def has_object_permission(self, request, view, obj):
        return self.has_permission(request, view)


class HasViewProfilePermission(HasPermission):
    """
    this is a default keycloak permission
    it is an example
    """

    permission = "view-profile"
