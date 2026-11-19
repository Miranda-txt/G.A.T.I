"""Regressoes de configuracao e dos limites do Render Free."""

import os
import subprocess
import sys

import pytest
import yaml
from django.core.mail import EmailMessage
from django.test import override_settings


def _render_env():
    env = dict(os.environ)
    env.update(
        GATI_ENV="staging",
        DJANGO_SETTINGS_MODULE="config.settings.render",
        RENDER_SERVICE_ID="srv-validacao-ci",
        GATI_SECRET_KEY="chave-apenas-para-testes-sem-credenciais-" * 2,
        GATI_ALLOWED_HOSTS="gati-example.onrender.com",
        GATI_CSRF_ORIGINS="https://gati-example.onrender.com",
        GATI_PUBLIC_URL="https://gati-example.onrender.com",
        PGDATABASE="gati_homologacao",
        PGUSER="gati_app",
        PGHOST="ep-exemplo.c-2.sa-east-1.aws.neon.tech",
        PGPORT="5432",
        PGSSLMODE="verify-full",
        PGPASSWORD="senha-falsa-nao-e-credencial",
    )
    return env


def _inspect_render(overrides):
    env = _render_env()
    env.update(overrides)
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            "from django.conf import settings; print(settings.SECURE_PROXY_SSL_HEADER); "
            "print(settings.SECURE_HSTS_SECONDS); print(settings.EMAIL_BACKEND)",
        ],
        env=env,
        check=False,
        text=True,
        capture_output=True,
        timeout=20,
    )
    return result


def test_render_reconhece_proxy_com_https_e_sem_hsts_permanente():
    result = _inspect_render({})
    assert result.returncode == 0, result.stderr
    assert "('HTTP_X_FORWARDED_PROTO', 'https')" in result.stdout
    assert "\n0\n" in result.stdout
    assert "gati.common.email.FailClosedEmailBackend" in result.stdout


@pytest.mark.parametrize(
    "overrides",
    [
        {"RENDER_SERVICE_ID": ""},
        {"GATI_ENV": "production"},
        {"PGUSER": "gati_homologacao_owner"},
        {"PGDATABASE": "gati"},
        {"PGHOST": "127.0.0.1"},
        {"PGSSLMODE": "disable"},
    ],
)
def test_render_recusa_configuracoes_inseguras(overrides):
    result = _inspect_render(overrides)
    assert result.returncode != 0
    assert "ImproperlyConfigured" in result.stderr


@override_settings(EMAIL_BACKEND="gati.common.email.FailClosedEmailBackend")
def test_render_nao_finge_enviar_email_com_token():
    with pytest.raises(RuntimeError, match="indisponivel"):
        EmailMessage(
            "Assinatura", "token-sintetico", "gati@example.invalid", ["teste@example.invalid"]
        ).send()


def test_blueprint_nao_cria_servicos_pagos_ou_migra_banco():
    from pathlib import Path

    blueprint = yaml.safe_load((Path(__file__).resolve().parents[2] / "render.yaml").read_text())
    assert "databases" not in blueprint
    assert len(blueprint["services"]) == 1
    service = blueprint["services"][0]
    assert service["plan"] == "free"
    assert service["autoDeployTrigger"] == "off"
    assert service["runtime"] == "docker"
    assert service["healthCheckPath"] == "/health/ready/"
    assert "preDeployCommand" not in service
    values = {item["key"]: item for item in service["envVars"]}
    assert values["GATI_SECRET_KEY"]["sync"] is False
    assert values["PGPASSWORD"]["sync"] is False
    assert values["PGHOST"]["sync"] is False
    assert values["PGUSER"]["value"] == "gati_app"
    assert values["DJANGO_SETTINGS_MODULE"]["value"] == "config.settings.render"
