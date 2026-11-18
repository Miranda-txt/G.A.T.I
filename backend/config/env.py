import os
from pathlib import Path

from dotenv import load_dotenv


def configure():
    load_dotenv(Path(__file__).resolve().parents[1] / ".env")
    env = os.environ.get("GATI_ENV", "development")
    if env not in {"development", "test", "staging", "production"}:
        raise RuntimeError("GATI_ENV inválido.")
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", f"config.settings.{env}")
