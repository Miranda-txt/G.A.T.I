"""Regressoes de prontidao em caso de falha de conexao ao PostgreSQL."""

import logging
from unittest.mock import patch

from django.test import RequestFactory

from gati.observability.health import ready


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
