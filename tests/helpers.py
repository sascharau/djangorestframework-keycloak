"""helpers for tests"""

from django.contrib.auth import get_user_model

User = get_user_model()

USERNAME = "foobar3000"
EMAIL = "foo@bar.de"
FIRST_NAME = "John"
LAST_NAME = "Doe"


def create_user():
    """
    helper function to create
    @return: user
    """
    user = User.objects.create_user(
        username=USERNAME,
        first_name=FIRST_NAME,
        last_name=LAST_NAME,
        email=EMAIL,
    )
    user.set_unusable_password()
    return user
