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

    # Uploaded test files (e.g. episode audio fixtures) must never land in the
    # real local media/ directory: FileSystemStorage silently appends a
    # collision-avoiding suffix ("episode_XXXXXXX.mp3") whenever a same-named
    # file already exists on disk, which made a test asserting the exact
    # upload URL flaky/failing depending on what a previous run had left
    # behind. A fresh temp dir per test run guarantees no collisions.
    import tempfile
    MEDIA_ROOT = Path(tempfile.mkdtemp(prefix="ytr-test-media-"))

# Skip WhiteNoise's manifest requirement locally so `runserver`/`test` work
# without needing `collectstatic` first.
STORAGES = {
    **STORAGES,  # noqa: F405
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
    },
}
