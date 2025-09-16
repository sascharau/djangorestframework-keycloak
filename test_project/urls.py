"""
URL configuration for test_project.
"""

from django.contrib import admin
from django.urls import path
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from drf_keycloak.permissions import HasPermission


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def protected_view(request):
    """A simple protected view that requires authentication"""
    return Response(
        {
            "message": "Hello, authenticated user!",
            "user": request.user.username,
            "user_data": {
                "id": request.user.id,
                "username": request.user.username,
                "email": request.user.email,
                "first_name": request.user.first_name,
                "last_name": request.user.last_name,
                "is_active": request.user.is_active,
            },
            "token_payload": request.auth if hasattr(request, "auth") else None,
        }
    )


class ViewProfilePermission(HasPermission):
    permission = "view-profile"


@api_view(["GET"])
@permission_classes([ViewProfilePermission])
def profile_view(request):
    """A view that requires the 'view-profile' permission"""
    return Response(
        {
            "message": "You have view-profile permission!",
            "user": request.user.username,
            "permissions": request.auth.get("resource_access", {})
            if request.auth
            else {},
        }
    )


@api_view(["GET"])
@permission_classes([])  # No permissions required
def public_view(request):
    """A public view that doesn't require authentication"""
    return Response(
        {
            "message": "This is a public endpoint",
            "authenticated": request.user.is_authenticated
            if hasattr(request, "user")
            else False,
        }
    )


urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/public/", public_view, name="public"),
    path("api/protected/", protected_view, name="protected"),
    path("api/profile/", profile_view, name="profile"),
]
