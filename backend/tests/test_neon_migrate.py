"""Garantias da selecao do destino de homologacao Neon."""

from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from config.neon_migrate import (
    EXPECTED_DATABASE,
    EXPECTED_HOST,
    EXPECTED_USER,
    _check_client_tls,
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


def _fake_connection(*, ssl_mode="verify-full", ca_bundle="/tmp/trusted-ca.pem", ssl_in_use=True):
    pgconn = SimpleNamespace(ssl_in_use=ssl_in_use)
    native = SimpleNamespace(pgconn=pgconn)
    return SimpleNamespace(
        settings_dict={"OPTIONS": {"sslmode": ssl_mode, "sslrootcert": ca_bundle}},
        connection=native,
        ensure_connection=Mock(),
    )


def test_cliente_tls_valido_aceito():
    conn = _fake_connection()
    _check_client_tls(conn)
    conn.ensure_connection.assert_called_once_with()


@pytest.mark.parametrize("mode", ["disable", "require", "verify-ca", "prefer"])
def test_cliente_rejeita_configuracao_tls_sem_verificacao_completa(mode):
    with pytest.raises(RuntimeError, match="verify-full"):
        _check_client_tls(_fake_connection(ssl_mode=mode))


def test_cliente_rejeita_ca_ausente():
    with pytest.raises(RuntimeError, match="CA confiavel"):
        _check_client_tls(_fake_connection(ca_bundle=None))


def test_cliente_rejeita_conexao_que_nao_negociou_tls():
    with pytest.raises(RuntimeError, match="nao usa TLS"):
        _check_client_tls(_fake_connection(ssl_in_use=False))


def test_cliente_rejeita_conexao_sem_objeto_libpq():
    conn = _fake_connection()
    conn.connection = SimpleNamespace()
    with pytest.raises(RuntimeError, match="nao usa TLS"):
        _check_client_tls(conn)
