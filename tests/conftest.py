from django.conf import settings

def pytest_configure():
    settings.configure(
        DEBUG=True,
        ROOT_URLCONF="tests.urls",
        SECRET_KEY="notasecret",
        DATABASES={
            'default': {
                'ENGINE': 'django.db.backends.sqlite3',
                'NAME': ':memory:',
            }
        },
        INSTALLED_APPS=[
            # Füge hier die Namen der Django-Apps hinzu, die für deine Tests benötigt werden
            'django.contrib.auth',
            'django.contrib.contenttypes',
            'django.contrib.sessions',
            'django.contrib.messages',
            'drf_keycloak',
        ],
        KEYCLOAK_CONFIG={
            "SERVER_URL": "https://my-server-url.com",
            "REALM": "my-realm",
        },
        MIDDLEWARE=(
            "drf_keycloak.middleware.HeaderMiddleware",
            "django.middleware.security.SecurityMiddleware",
            "django.contrib.sessions.middleware.SessionMiddleware",
            "django.middleware.common.CommonMiddleware",
            "django.middleware.csrf.CsrfViewMiddleware",
            "django.contrib.auth.middleware.AuthenticationMiddleware",
            "django.contrib.messages.middleware.MessageMiddleware",
            "django.middleware.clickjacking.XFrameOptionsMiddleware",
        ),
    )
