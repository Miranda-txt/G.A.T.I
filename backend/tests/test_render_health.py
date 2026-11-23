"""Regressoes de prontidao em caso de falha de conexao ao PostgreSQL."""

import logging
from unittest.mock import patch

import pytest
from django.db import OperationalError as DjangoOperationalError
from django.test import RequestFactory
from psycopg import OperationalError

from gati.observability.health import _database_failure_category, ready


def test_ready_falha_fechada_e_nao_registra_segredos(caplog):
    segredo = "senha-nao-deve-aparecer-em-log"
    with (
        patch(
            "gati.observability.health.connection.cursor",
            side_effect=RuntimeError(f"Conexao falhou com secret={segredo}"),
        ),
        caplog.at_level(logging.WARNING, logger="gati.health"),
    ):
        resposta = ready(RequestFactory().get("/health/ready/"))

    assert resposta.status_code == 503
    assert resposta.content == b'{"status": "unavailable"}'
    assert "RuntimeError" in caplog.text
    assert segredo not in caplog.text
    assert "secret=" not in caplog.text


def test_ready_com_banco_disponivel():
    with patch("gati.observability.health.connection.cursor") as cursor:
        resposta = ready(RequestFactory().get("/health/ready/"))

    assert resposta.status_code == 200
    assert resposta.content == b'{"status": "ready"}'
    cursor.return_value.__enter__.return_value.execute.assert_called_once_with("SELECT 1")


@pytest.mark.parametrize(
    ("message", "categoria"),
    [
        ("FATAL: password authentication failed for user gati_app", "authentication"),
        ("connection failed: certificate verify failed", "tls"),
        ("could not translate host name to address: Name or service not known", "dns"),
        ("connection failed: Connection timed out", "network"),
        ("database gati_homologacao does not exist", "database_missing"),
        ("connection rejected for unspecified reason", "unknown"),
    ],
)
def test_classificar_operational_error_sem_exposicao(message, categoria):
    assert _database_failure_category(OperationalError(message)) == categoria


def test_erro_operacional_nao_expoe_mensagem_no_log(caplog):
    segredo = "segredo-confidencial-de-teste"
    error = OperationalError("password authentication failed: " + segredo)
    with (
        patch("gati.observability.health.connection.cursor", side_effect=error),
        caplog.at_level(logging.WARNING, logger="gati.health"),
    ):
        resposta = ready(RequestFactory().get("/health/ready/"))

    assert resposta.status_code == 503
    assert "categoria=authentication" in caplog.text
    assert segredo not in caplog.text


@pytest.mark.parametrize(
    ("message", "expected"),
    [
        ("FATAL: password authentication failed for user gati_app", "authentication"),
        ("connection failed: certificate verify failed", "tls"),
        ("could not translate host name to address: Name or service not known", "dns"),
        ("connection failed: Connection timed out", "network"),
    ],
)
def test_classifica_causa_psycopg_encapsulada_pelo_django(message, expected):
    cause = OperationalError(message)
    wrapped = DjangoOperationalError("Mensagem de erro do Django")
    wrapped.__cause__ = cause

    assert _database_failure_category(wrapped) == expected


def test_classifica_erro_django_sem_causa():
    assert _database_failure_category(DjangoOperationalError("sem detalhes")) == "unknown"


def test_health_check_wrapped_preserva_sigilo(caplog):
    segredo = "token-sintetico-confidencial"
    cause = OperationalError(f"password authentication failed: {segredo}")
    wrapped = DjangoOperationalError("redacted")
    wrapped.__cause__ = cause

    with (
        patch("gati.observability.health.connection.cursor", side_effect=wrapped),
        caplog.at_level(logging.WARNING, logger="gati.health"),
    ):
        resposta = ready(RequestFactory().get("/health/ready/"))

    assert resposta.status_code == 503
    assert "categoria=authentication" in caplog.text
    assert segredo not in caplog.text
