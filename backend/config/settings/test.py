import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[2] / ".env")
os.environ.setdefault("GATI_SECRET_KEY", "test-only-key-not-for-deployment-" * 3)
from .base import *  # noqa: E402,F403

DATABASES["default"]["CONN_MAX_AGE"] = 0  # noqa: F405
EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
