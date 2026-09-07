from django.core.exceptions import ImproperlyConfigured

from .base import *  # noqa: F401,F403

DEBUG = False
CSRF_TRUSTED_ORIGINS = env.list("CSRF_TRUSTED_ORIGINS", default=[])

# Media can live outside the container on AWS S3, R2, or another S3 provider.
if env("AWS_STORAGE_BUCKET_NAME", default=""):
    STORAGES["default"] = {
        "BACKEND": "storages.backends.s3.S3Storage",
        "OPTIONS": {
            "bucket_name": env("AWS_STORAGE_BUCKET_NAME"),
            "endpoint_url": env("AWS_S3_ENDPOINT_URL", default=None) or None,
            "region_name": env("AWS_S3_REGION_NAME", default=None) or None,
            "default_acl": None,
            "file_overwrite": False,
            "querystring_auth": True,
        },
    }

if not ALLOWED_HOSTS:
    raise ValueError("ALLOWED_HOSTS must be set via env in production")

_INSECURE_SECRET_MARKERS = ("django-insecure-", "change-me", "placeholder", "example")
if (
    not SECRET_KEY
    or len(SECRET_KEY) < 50
    or any(marker in SECRET_KEY.lower() for marker in _INSECURE_SECRET_MARKERS)
):
    raise ImproperlyConfigured(
        "A strong SECRET_KEY of at least 50 characters must be supplied through the environment."
    )

SECURE_SSL_REDIRECT = env.bool("SECURE_SSL_REDIRECT", default=True)  # noqa: F405
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 60 * 60 * 24 * 30
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "same-origin"

_proxy_header = env("SECURE_PROXY_SSL_HEADER", default="")  # noqa: F405
if _proxy_header:
    header_name, separator, header_value = _proxy_header.partition(",")
    if not separator or not header_name or not header_value:
        raise ImproperlyConfigured("SECURE_PROXY_SSL_HEADER must be NAME,value.")
    SECURE_PROXY_SSL_HEADER = (header_name.strip(), header_value.strip())

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {"standard": {"format": "{asctime} {levelname} {name}: {message}", "style": "{"}},
    "handlers": {"console": {"class": "logging.StreamHandler", "formatter": "standard"}},
    "loggers": {
        "django": {"handlers": ["console"], "level": "INFO"},
        "apps": {"handlers": ["console"], "level": "INFO", "propagate": False},
    },
}
