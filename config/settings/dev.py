import sys

from .base import *  # noqa: F401,F403

DEBUG = True
ALLOWED_HOSTS = ["*"]

# This value is deliberately development-only. Production validates that an
# environment-provided secret exists and is strong enough before it starts.
if not SECRET_KEY:
    SECRET_KEY = "django-insecure-development-only-not-for-production"

if "test" in sys.argv:
    # PBKDF2 is intentionally slow; a weak hasher keeps `manage.py test` fast.
    # Never used outside test runs, so it doesn't weaken real local accounts.
    PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]

# Skip WhiteNoise's manifest requirement locally so `runserver`/`test` work
# without needing `collectstatic` first.
STORAGES = {
    **STORAGES,  # noqa: F405
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
    },
}
