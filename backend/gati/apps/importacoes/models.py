import uuid

from django.conf import settings
from django.db import models


class ImportacaoExecucao(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    entidade = models.CharField(max_length=10)
    formato = models.CharField(max_length=5)
    sha256 = models.CharField(max_length=64)
    tamanho = models.PositiveIntegerField()
    quantidade = models.PositiveIntegerField(default=0)
    estado = models.CharField(max_length=20, default="PREVIEW")
    criado_em = models.DateTimeField(auto_now_add=True)
    concluido_em = models.DateTimeField(null=True)
