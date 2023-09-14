from django.test import TestCase
from drf_keycloak.schema import TokenScheme
from drf_keycloak.authentication import KeycloakAuthBackend

class TestTokenScheme(TestCase):

    def test_get_security_definition(self):
        token_scheme = TokenScheme(target=KeycloakAuthBackend)
        auto_schema = {}
        security_definition = token_scheme.get_security_definition(auto_schema)
        self.assertEqual(security_definition, {
            'type': 'http',
            'scheme': 'bearer',
            'bearerFormat': 'JWT',
        })

