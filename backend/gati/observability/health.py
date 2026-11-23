"""Endpoints de vida e prontidao da aplicacao."""

import logging

from django.db import connection
from psycopg import OperationalError
from django.http import HttpResponse, JsonResponse

from gati.apps.usuarios.permissions import authorize

logger = logging.getLogger("gati.health")


def _database_failure_category(exc: Exception) -> str:
    """Classifica falhas sem registrar excecoes, strings de conexao ou segredos."""
    if not isinstance(exc, OperationalError):
        return "other"

    # SQLSTATE vem do protocolo PostgreSQL; quando presente, prevalece
    # sobre heuristicas no texto do driver.
    state = exc.sqlstate
    if state in {"28P01", "28000"}:
        return "authentication"
    if state == "3D000":
        return "database_missing"
    if state == "42501":
        return "permissions"

    # Mensagens libpq variam por idioma/plataforma. Leitura apenas em memoria:
    # nunca incluir exc nem qualquer trecho de str(exc) no logger.
    detail = str(exc).casefold()
    if any(x in detail for x in ("certificate verify failed", "certificate", "ssl", "tls")):
        return "tls"
    if any(
        x in detail
        for x in (
            "could not translate host name",
            "name or service not known",
            "getaddrinfo failed",
            "nodename nor servname provided",
        )
    ):
        return "dns"
    if any(
        x in detail
        for x in ("password authentication failed", "authentication failed", "no password supplied", "fe_sendauth")
    ):
        return "authentication"
    if "database" in detail and "does not exist" in detail:
        return "database_missing"
    if any(
        x in detail
        for x in (
            "connection timed out",
            "timeout expired",
            "connection refused",
            "network is unreachable",
            "no route to host",
        )
    ):
        return "network"
    return "unknown"



def live(request):
    return JsonResponse({"status": "ok"})


def ready(request):
    try:
        with connection.cursor() as cur:
            cur.execute("SELECT 1")
        return JsonResponse({"status": "ready"})
    except Exception as exc:
        # Nao registrar str(exc): o driver pode incluir nomes de usuarios,
        # hosts, URLs ou detalhes sensiveis da configuracao de conexao.
        logger.warning(
            "Health check do banco falhou (classe=%s, categoria=%s)",
            type(exc).__name__,
            _database_failure_category(exc),
        )
        return JsonResponse({"status": "unavailable"}, status=503)


def metrics(request):
    authorize(request.user, admin=True)
    return HttpResponse("gati_application_up 1\n", content_type="text/plain; version=0.0.4")
