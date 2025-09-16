"""Tests Keycloak Middleware"""

from django.test import TestCase
from rest_framework.test import APIClient


class TestKeycloakMiddleware(TestCase):
    def test_header(self):
        response = APIClient().get("/")
        headers = response.headers
        self.assertFalse(int(headers["Expires"]))
        self.assertEqual(
            headers["Cache-Control"],
            "max-age=0, no-cache, no-store, must-revalidate, private",
        )
        self.assertFalse(int(headers["X-XSS-Protection"]))
        self.assertEqual(
            headers["Strict-Transport-Security"], "max-age=31536000; includeSubDomains"
        )
