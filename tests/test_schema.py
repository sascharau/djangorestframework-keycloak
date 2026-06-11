import importlib
import sys
from unittest import mock

from django.test import TestCase
from django.urls import path
from drf_spectacular.openapi import AutoSchema
from rest_framework.response import Response
from rest_framework.views import APIView

import drf_keycloak.schema  # noqa: F401 - registers the OpenAPI extension
from drf_keycloak.authentication import KeycloakAuthBackend
from drf_keycloak.schema import TokenScheme


class _ProtectedView(APIView):
    authentication_classes = [KeycloakAuthBackend]
    permission_classes = []
    schema = AutoSchema()

    def get(self, request):
        return Response({})


class TestTokenScheme(TestCase):
    def test_get_security_definition(self):
        token_scheme = TokenScheme(target=KeycloakAuthBackend)
        self.assertEqual(
            token_scheme.get_security_definition(None),
            {"type": "http", "scheme": "bearer", "bearerFormat": "JWT"},
        )

    def test_scheme_resolves_through_generator(self):
        # This is the test that would have caught the wrong target_class:
        # exercising the real generator, not get_security_definition directly.
        from drf_spectacular.generators import SchemaGenerator

        generator = SchemaGenerator(patterns=[path("x/", _ProtectedView.as_view())])
        schema = generator.get_schema(request=None, public=True)
        schemes = schema.get("components", {}).get("securitySchemes")
        self.assertIsNotNone(schemes, "authenticator was not resolved by spectacular")
        self.assertIn("KeycloakAuth", schemes)
        self.assertEqual(schemes["KeycloakAuth"]["scheme"], "bearer")


class TestSchemaImportGuard(TestCase):
    def test_missing_drf_spectacular_raises_actionable_error(self):
        # Simulate drf-spectacular not being installed and re-import the module.
        blocked = dict.fromkeys(
            (
                "drf_spectacular",
                "drf_spectacular.extensions",
                "drf_spectacular.plumbing",
            )
        )
        with mock.patch.dict(sys.modules, blocked):
            sys.modules.pop("drf_keycloak.schema", None)
            with self.assertRaises(ImportError) as ctx:
                importlib.import_module("drf_keycloak.schema")
        # patch.dict restores sys.modules (incl. drf_keycloak.schema) on exit
        self.assertIn("drf-spectacular", str(ctx.exception))
