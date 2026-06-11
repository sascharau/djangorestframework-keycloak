from django.conf import settings

# Keep SERVER_URL and ISSUER coherent so tests that decode real tokens can
# validate the `iss` claim against the same realm the keys are "served" from.
TEST_SERVER_URL = "https://kc.test/realms/test"
TEST_ISSUER = "https://kc.test/realms/test"


def pytest_configure():
    settings.configure(
        DEBUG=True,
        ROOT_URLCONF="tests.urls",
        SECRET_KEY="notasecret",
        DATABASES={
            "default": {
                "ENGINE": "django.db.backends.sqlite3",
                "NAME": ":memory:",
            }
        },
        INSTALLED_APPS=[
            "django.contrib.auth",
            "django.contrib.contenttypes",
            "django.contrib.sessions",
            "django.contrib.messages",
            "drf_keycloak",
        ],
        KEYCLOAK_CONFIG={
            "SERVER_URL": TEST_SERVER_URL,
            "ISSUER": TEST_ISSUER,
        },
        MIDDLEWARE=(
            "django.middleware.security.SecurityMiddleware",
            "django.contrib.sessions.middleware.SessionMiddleware",
            "django.middleware.common.CommonMiddleware",
            "django.middleware.csrf.CsrfViewMiddleware",
            "django.contrib.auth.middleware.AuthenticationMiddleware",
            "django.contrib.messages.middleware.MessageMiddleware",
            "django.middleware.clickjacking.XFrameOptionsMiddleware",
        ),
    )
