"""Gera apenas configuração local; nunca sobrescreve segredos existentes."""
import secrets
from pathlib import Path

root = Path(__file__).resolve().parents[1]
target = root / "backend" / ".env"
if target.exists():
    raise SystemExit("backend/.env já existe e foi preservado.")
target.write_text(
    "GATI_ENV=development\n"
    f"GATI_SECRET_KEY={secrets.token_urlsafe(64)}\n"
    "GATI_ALLOWED_HOSTS=localhost,127.0.0.1\n"
    "GATI_PUBLIC_URL=http://127.0.0.1:8765\n"
    "PGDATABASE=gati\nPGUSER=gati\nPGHOST=127.0.0.1\nPGPORT=5432\n"
    f"PGPASSWORD={secrets.token_urlsafe(32)}\n"
    "GATI_CLAMAV_HOST=127.0.0.1\nGATI_CLAMAV_PORT=3310\n",
    encoding="utf-8",
)
print("backend/.env criado. Preserve em local privado; não versione este arquivo.")
