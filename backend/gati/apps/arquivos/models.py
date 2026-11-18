import uuid

from django.conf import settings
from django.db import models

from gati.common.models import Cadastro


class Arquivo(Cadastro):
    storage_key = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    nome_original = models.CharField(max_length=200)
    mime = models.CharField(max_length=80)
    tamanho = models.PositiveBigIntegerField()
    sha256 = models.CharField(max_length=64)
    criado_por = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    ativo_vinculado = models.ForeignKey(
        "ativos.Ativo", null=True, on_delete=models.PROTECT, related_name="arquivos"
    )
    manutencao = models.ForeignKey(
        "manutencoes.Manutencao", null=True, on_delete=models.PROTECT, related_name="arquivos"
    )
    processo = models.ForeignKey(
        "movimentacoes.ProcessoMovimentacao", null=True, on_delete=models.PROTECT, related_name="arquivos"
    )

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=(
                    models.Q(ativo_vinculado__isnull=False, manutencao__isnull=True, processo__isnull=True)
                    | models.Q(ativo_vinculado__isnull=True, manutencao__isnull=False, processo__isnull=True)
                    | models.Q(ativo_vinculado__isnull=True, manutencao__isnull=True, processo__isnull=False)
                ),
                name="arquivo_um_vinculo",
            )
        ]
