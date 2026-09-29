"""Django settings for the folio project.

Deployment-specific values are read from environment variables (or a `.env`
file at the project root). See `.env.example` for every supported variable.

https://docs.djangoproject.com/en/6.1/topics/settings/
https://docs.djangoproject.com/en/6.1/ref/settings/
"""

from pathlib import Path
from typing import Any

import environ

BASE_DIR = Path(__file__).resolve().parent.parent

env = environ.Env()
environ.Env.read_env(BASE_DIR / ".env")


def _mailer_from_url(url: str) -> dict[str, Any]:
    """Build a `MAILERS` entry from a django-environ email URL.

    django-environ only emits the deprecated `EMAIL_*` settings, and Django's
    mail backends reject OPTIONS they don't understand, so only the options the
    chosen backend accepts are passed through.

    Args:
        url: Email URL such as `smtp+tls://user:pass@host:587`.

    Returns:
        A mailer configuration with `BACKEND` and backend-specific `OPTIONS`.
    """
    config = environ.Env.email_url_config(url)
    backend = config["EMAIL_BACKEND"]
    options: dict[str, Any] = {}
    if backend == environ.Env.EMAIL_SCHEMES["smtp"]:
        options = {
            "host": config["EMAIL_HOST"],
            "port": config["EMAIL_PORT"],
            "username": config["EMAIL_HOST_USER"],
            "password": config["EMAIL_HOST_PASSWORD"],
            "use_tls": config.get("EMAIL_USE_TLS", False),
            "use_ssl": config.get("EMAIL_USE_SSL", False),
            "timeout": config.get("OPTIONS", {}).get("TIMEOUT"),
        }
    elif backend == environ.Env.EMAIL_SCHEMES["filemail"]:
        options = {"file_path": config["EMAIL_FILE_PATH"]}
    return {
        "BACKEND": backend,
        "OPTIONS": {key: value for key, value in options.items() if value is not None},
    }


# Core

SECRET_KEY = env.str("SECRET_KEY")
SECRET_KEY_FALLBACKS = env.list("SECRET_KEY_FALLBACKS", default=[])

DEBUG = env.bool("DEBUG", default=False)

ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=[])
CSRF_TRUSTED_ORIGINS = env.list("CSRF_TRUSTED_ORIGINS", default=[])

ADMIN_URL = env.str("ADMIN_URL", default="admin/")


# Application definition

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "simple_history",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "simple_history.middleware.HistoryRequestMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"


# Database
# https://docs.djangoproject.com/en/6.1/ref/settings/#databases

DATABASES = {
    "default": env.db("DATABASE_URL", default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}"),
}


# Cache
# https://docs.djangoproject.com/en/6.1/topics/cache/

CACHES = {
    "default": env.cache("CACHE_URL", default="locmemcache://"),
}


# Password validation
# https://docs.djangoproject.com/en/6.1/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


# Security
# https://docs.djangoproject.com/en/6.1/howto/deployment/checklist/

SECURE_SSL_REDIRECT = env.bool("SECURE_SSL_REDIRECT", default=False)
if env.bool("USE_X_FORWARDED_PROTO", default=False):
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

SESSION_COOKIE_SECURE = env.bool("SESSION_COOKIE_SECURE", default=not DEBUG)
CSRF_COOKIE_SECURE = env.bool("CSRF_COOKIE_SECURE", default=not DEBUG)

SECURE_HSTS_SECONDS = env.int("SECURE_HSTS_SECONDS", default=0)
SECURE_HSTS_INCLUDE_SUBDOMAINS = env.bool(
    "SECURE_HSTS_INCLUDE_SUBDOMAINS", default=False
)
SECURE_HSTS_PRELOAD = env.bool("SECURE_HSTS_PRELOAD", default=False)


# Internationalization
# https://docs.djangoproject.com/en/6.1/topics/i18n/

LANGUAGE_CODE = env.str("LANGUAGE_CODE", default="en-us")

TIME_ZONE = env.str("TIME_ZONE", default="UTC")

USE_I18N = True

USE_TZ = True


# Static and media files
# https://docs.djangoproject.com/en/6.1/howto/static-files/

STATIC_URL = env.str("STATIC_URL", default="static/")
STATIC_ROOT = env.path("STATIC_ROOT", default=BASE_DIR / "staticfiles")

MEDIA_URL = env.str("MEDIA_URL", default="media/")
MEDIA_ROOT = env.path("MEDIA_ROOT", default=BASE_DIR / "media")


# Email
# https://docs.djangoproject.com/en/6.1/topics/email/#topic-email-configuration

MAILERS = {
    "default": _mailer_from_url(env.str("EMAIL_URL", default="consolemail://")),
}

DEFAULT_FROM_EMAIL = env.str("DEFAULT_FROM_EMAIL", default="webmaster@localhost")
SERVER_EMAIL = env.str("SERVER_EMAIL", default="root@localhost")
ADMINS = env.list("ADMINS", default=[])
MANAGERS = ADMINS


# Logging
# https://docs.djangoproject.com/en/6.1/topics/logging/

LOG_LEVEL = env.str("LOG_LEVEL", default="INFO")

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {"class": "logging.StreamHandler"},
    },
    "root": {
        "handlers": ["console"],
        "level": LOG_LEVEL,
    },
}
