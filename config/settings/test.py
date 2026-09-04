from .base import *  # noqa

DEBUG = True

# Use fast in-memory SQLite for tests so the suite runs without Postgres
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

# Real Django cache backend so OTP storage works in tests
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
    }
}

# Speed up password hashing in tests
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]

SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False

# Suppress whitenoise during tests
STATICFILES_STORAGE = "django.contrib.staticfiles.storage.StaticFilesStorage"
