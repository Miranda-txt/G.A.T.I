"""Opcoes PostgreSQL: conexao remota obrigatoriamente autenticada por TLS."""

import certifi
from django.core.exceptions import ImproperlyConfigured

_LOOPBACK_HOSTS = frozenset({"localhost", "127.0.0.1", "::1"})


def postgres_options(
    host: str, ssl_mode: str | None = None, ca_bundle: str | None = None
) -> dict[str, object]:
    """Mantem o PostgreSQL local sem TLS e exige verify-full fora do loopback."""
    is_local = host in _LOOPBACK_HOSTS
    mode = ssl_mode if ssl_mode is not None else ("disable" if is_local else "verify-full")
    if not is_local and mode != "verify-full":
        raise ImproperlyConfigured(
            "PostgreSQL remoto exige PGSSLMODE=verify-full; "
            "nao utilize require, prefer, allow ou disable."
        )

    options: dict[str, object] = {"connect_timeout": 5, "sslmode": mode}
    if mode in {"verify-full", "verify-ca"}:
        options["sslrootcert"] = ca_bundle or certifi.where()
    return options
