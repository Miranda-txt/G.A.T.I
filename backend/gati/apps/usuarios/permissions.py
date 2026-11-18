from django.core.exceptions import PermissionDenied
from rest_framework.permissions import BasePermission


def profile(user):
    if not user.is_authenticated or not user.is_active:
        return None
    roles = list(user.groups.values_list("name", flat=True))
    return roles[0] if len(roles) == 1 and roles[0] in {"Administrador", "Operador"} else None


def is_admin(user):
    return profile(user) == "Administrador"


def authorize(user, admin=False):
    if not profile(user) or (admin and not is_admin(user)):
        raise PermissionDenied("Você não tem permissão para esta ação.")


class InternalPermission(BasePermission):
    def has_permission(self, request, view):
        return bool(profile(request.user))


class AdminPermission(BasePermission):
    def has_permission(self, request, view):
        return is_admin(request.user)
