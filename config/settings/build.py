"""Offline asset collection: production static storage, no runtime secrets."""
from .base import *  # noqa: F401,F403

SECRET_KEY = "build-only-never-used-to-serve-requests"
DEBUG = False
DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}}
