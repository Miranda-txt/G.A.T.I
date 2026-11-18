from .production import *  # noqa: F403

EMAIL_BACKEND = "django.core.mail.backends.filebased.EmailBackend"
EMAIL_FILE_PATH = RUNTIME / "emails"  # noqa: F405
