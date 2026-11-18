import os

from django.core.exceptions import ImproperlyConfigured

from .base import *  # noqa: F403

if not os.environ.get("GATI_ALLOWED_HOSTS") or not os.environ.get("GATI_CSRF_ORIGINS"):
    raise ImproperlyConfigured("Hosts e origens HTTPS explícitos são obrigatórios.")
if not PUBLIC_BASE_URL.startswith("https://"):  # noqa: F405
    raise ImproperlyConfigured("GATI_PUBLIC_URL precisa usar HTTPS.")
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_SSL_REDIRECT = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = os.environ.get("GATI_SMTP_HOST", "")
EMAIL_PORT = 465
EMAIL_USE_SSL = True
EMAIL_HOST_USER = os.environ.get("GATI_SMTP_USER", "")
EMAIL_HOST_PASSWORD = os.environ.get("GATI_SMTP_PASSWORD", "")
