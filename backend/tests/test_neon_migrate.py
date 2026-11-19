"""Garantias da selecao do destino de homologacao Neon."""

import pytest

from config.neon_migrate import (
    EXPECTED_DATABASE,
    EXPECTED_HOST,
    EXPECTED_USER,
    parse_migration_url,
)


def test_url_neon_direta_e_tls_verificado():
    url = (
        f"postgresql://{EXPECTED_USER}:senha%40de%23teste@{EXPECTED_HOST}/"
        f"{EXPECTED_DATABASE}?sslmode=require&channel_binding=require"
    )
    config = parse_migration_url(url)
    assert config["PGPASSWORD"] == "senha@de#teste"
    assert config["PGSSLMODE"] == "verify-full"
    assert config["PGDATABASE"] == EXPECTED_DATABASE
    assert config["PGUSER"] == EXPECTED_USER
    assert config["PGHOST"] == EXPECTED_HOST


@pytest.mark.parametrize(
    "url",
    [
        "postgresql://gati:senha@localhost/gati",
        f"postgresql://gati_app:senha@{EXPECTED_HOST}/{EXPECTED_DATABASE}",
        f"postgresql://{EXPECTED_USER}:senha@outro.neon.tech/{EXPECTED_DATABASE}",
        f"postgresql://{EXPECTED_USER}:senha@{EXPECTED_HOST}/gati",
        f"postgresql://{EXPECTED_USER}:senha@{EXPECTED_HOST}:5433/{EXPECTED_DATABASE}",
        f"postgresql://{EXPECTED_USER}@{EXPECTED_HOST}/{EXPECTED_DATABASE}",
        f"postgresql://{EXPECTED_USER}:senha@{EXPECTED_HOST}/{EXPECTED_DATABASE}#fragmento",
        "",
    ],
)
def test_destinos_inesperados_sao_rejeitados(url):
    with pytest.raises(ValueError):
        parse_migration_url(url)
