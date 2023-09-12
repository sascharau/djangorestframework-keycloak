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
            jwt_permission = request.auth["resource_access"][keycloak_settings.AUDIENCE]["roles"]
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
