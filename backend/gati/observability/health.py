"""Endpoints de vida e prontidao da aplicacao."""

import logging

from django.db import connection
from django.http import HttpResponse, JsonResponse

from gati.apps.usuarios.permissions import authorize

logger = logging.getLogger("gati.health")


def live(request):
    return JsonResponse({"status": "ok"})


def ready(request):
    try:
        with connection.cursor() as cur:
            cur.execute("SELECT 1")
        return JsonResponse({"status": "ready"})
    except Exception as exc:
        # Registrar apenas o tipo da falha, nunca a mensagem do driver,
        # que pode conter hostnames, nomes de usuarios ou dados sensiveis.
        logger.warning("Health check do banco falhou (%s)", type(exc).__name__)
        return JsonResponse({"status": "unavailable"}, status=503)


def metrics(request):
    authorize(request.user, admin=True)
    return HttpResponse("gati_application_up 1\n", content_type="text/plain; version=0.0.4")
