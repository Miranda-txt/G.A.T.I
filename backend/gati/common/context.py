import os

from gati.apps.usuarios.permissions import is_admin


def navigation(request):
    return {"admin_funcional": is_admin(request.user), "ambiente": os.environ.get("GATI_ENV", "development")}
