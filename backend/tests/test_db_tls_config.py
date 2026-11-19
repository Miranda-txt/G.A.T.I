"""Regressoes de seguranca para o transporte de dados PostgreSQL."""

import certifi
import pytest
from django.core.exceptions import ImproperlyConfigured

from config.settings.database import postgres_options


@pytest.mark.parametrize("host", ["127.0.0.1", "localhost", "::1"])
def test_postgresql_local_mantem_configuracao_sem_tls(host):
    assert postgres_options(host) == {"connect_timeout": 5, "sslmode": "disable"}


def test_postgresql_remoto_exige_certificado_e_hostname():
    options = postgres_options("ep-exemplo.sa-east-1.aws.neon.tech")
    assert options == {
        "connect_timeout": 5,
        "sslmode": "verify-full",
        "sslrootcert": certifi.where(),
    }


@pytest.mark.parametrize("mode", ["disable", "allow", "prefer", "require", "verify-ca", ""])
def test_postgresql_remoto_recusa_transporte_inseguro(mode):
    with pytest.raises(ImproperlyConfigured, match="PGSSLMODE=verify-full"):
        postgres_options("ep-exemplo.sa-east-1.aws.neon.tech", ssl_mode=mode)


def test_postgresql_remoto_aceita_certificado_explicitamente_confiavel():
    options = postgres_options(
        "ep-exemplo.sa-east-1.aws.neon.tech",
        ssl_mode="verify-full",
        ca_bundle="/etc/ssl/certs/ca-certificates.crt",
    )
    assert options["sslrootcert"] == "/etc/ssl/certs/ca-certificates.crt"


def test_postgresql_local_pode_habilitar_validacao_forte():
    options = postgres_options("127.0.0.1", ssl_mode="verify-full")
    assert options["sslmode"] == "verify-full"
    assert options["sslrootcert"] == certifi.where()
