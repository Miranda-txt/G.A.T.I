from django.db import models
from django.db.models import F, Q

from gati.common.models import Registro


class Manutencao(Registro):
    ativo = models.ForeignKey("ativos.Ativo", on_delete=models.PROTECT, related_name="manutencoes")
    data_inicio = models.DateField("data de início")
    data_fim = models.DateField("data de conclusão", null=True, blank=True)
    fornecedor = models.CharField("fornecedor", max_length=160)
    nota_fiscal = models.CharField("nota fiscal / ordem de serviço", max_length=100, blank=True)
    defeito = models.TextField("defeito relatado", max_length=5000)
    servico = models.TextField("serviço realizado", blank=True, max_length=5000)
    custo = models.DecimalField("custo (R$)", max_digits=14, decimal_places=2, default=0)
    em_garantia = models.BooleanField("atendimento em garantia", default=False)

    class Meta:
        ordering = ["-data_inicio", "-id"]
        constraints = [
            models.CheckConstraint(
                condition=Q(data_fim__isnull=True) | Q(data_fim__gte=F("data_inicio")),
                name="manutencao_datas",
            ),
            models.CheckConstraint(condition=Q(custo__gte=0), name="manutencao_custo"),
        ]

    def __str__(self):
        return f"{self.ativo.patrimonio} · {self.fornecedor}"
