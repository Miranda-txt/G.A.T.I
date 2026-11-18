from django.db import connection
from django.http import HttpResponse, JsonResponse

from gati.apps.usuarios.permissions import authorize


def live(request):
    return JsonResponse({"status": "ok"})


def ready(request):
    try:
        with connection.cursor() as cur:
            cur.execute("SELECT 1")
        return JsonResponse({"status": "ready"})
    except Exception:
        return JsonResponse({"status": "unavailable"}, status=503)


def metrics(request):
    authorize(request.user, admin=True)
    return HttpResponse("gati_application_up 1\n", content_type="text/plain; version=0.0.4")
