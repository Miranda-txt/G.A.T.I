from django.conf import settings
from django.db import models

from gati.common.models import AppendOnly


class LogAuditoria(AppendOnly):
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.PROTECT)
    data = models.DateTimeField(auto_now_add=True, db_index=True)
    acao = models.CharField(max_length=80)
    entidade = models.CharField(max_length=80)
    objeto_id = models.CharField(max_length=80, blank=True)
    ip = models.GenericIPAddressField(null=True)
    detalhes = models.JSONField(default=dict)

    class Meta:
        ordering = ["-data", "-id"]
