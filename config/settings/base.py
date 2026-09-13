"""
Base settings shared by every environment.
"""
from pathlib import Path

import environ

BASE_DIR = Path(__file__).resolve().parent.parent.parent

env = environ.Env(
    DEBUG=(bool, False),
)
environ.Env.read_env(BASE_DIR / ".env")

SECRET_KEY = env("SECRET_KEY", default="")
DEBUG = env.bool("DEBUG", default=False)
ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=[])

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    "apps.core",
    "apps.accounts",
    "apps.dashboard",
    "apps.devotions",
    "apps.articles",
    "apps.podcasts",
    "apps.videos",
    "apps.morning_devotions",
    "apps.library",
    "apps.about",
    "apps.faq",
    "apps.engagement",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "apps.core.context_processors.site_settings",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

_database_url = env("DATABASE_URL", default="") or f"sqlite:///{BASE_DIR / 'db.sqlite3'}"
DATABASES = {"default": env.db_url_config(_database_url)}

if DATABASES["default"]["ENGINE"] == "django.db.backends.sqlite3":
    # WAL lets readers and the writer run concurrently; IMMEDIATE grabs the
    # write lock at BEGIN instead of at first write, so two racing writers
    # fail fast with "database is locked" rather than deadlocking later.
    DATABASES["default"]["OPTIONS"] = {
        "init_command": "PRAGMA journal_mode=WAL; PRAGMA synchronous=NORMAL;",
        "transaction_mode": "IMMEDIATE",
        "timeout": 20,
    }

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = env("TIME_ZONE", default="Africa/Kigali")
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"
STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

LOGIN_URL = "accounts:login"
LOGIN_REDIRECT_URL = "dashboard:home"
LOGOUT_REDIRECT_URL = "core:home"

# ---- YTR site config ----
SITE_NAME = "Youth Time Revival"
CONTACT_FALLBACK_EMAIL = env("CONTACT_FALLBACK_EMAIL", default="hello@youthtimerevival.rw")

EMAIL_BACKEND = env("EMAIL_BACKEND", default="django.core.mail.backends.console.EmailBackend")
EMAIL_HOST = env("EMAIL_HOST", default="")
EMAIL_PORT = env.int("EMAIL_PORT", default=587)
EMAIL_HOST_USER = env("EMAIL_HOST_USER", default="")
EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD", default="")
EMAIL_USE_TLS = env.bool("EMAIL_USE_TLS", default=True)
DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL", default=CONTACT_FALLBACK_EMAIL)

# Local-memory throttling protects a single application instance. Production should
# use a shared cache/proxy limit as documented in docs/security.md.
RATELIMIT_WINDOW_SECONDS = env.int("RATELIMIT_WINDOW_SECONDS", default=60 * 60)
RATELIMIT_REGISTRATION_LIMIT = env.int("RATELIMIT_REGISTRATION_LIMIT", default=5)
RATELIMIT_CONTACT_LIMIT = env.int("RATELIMIT_CONTACT_LIMIT", default=5)
RATELIMIT_NEWSLETTER_LIMIT = env.int("RATELIMIT_NEWSLETTER_LIMIT", default=10)
