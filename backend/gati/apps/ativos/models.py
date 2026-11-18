from django.db import models
from django.db.models import Q
from django.db.models.functions import Lower

from gati.common.models import Cadastro


class Ativo(Cadastro):
    patrimonio = models.CharField("patrimônio", max_length=80, db_index=True)
    service_tag = models.CharField("Service Tag", max_length=80, blank=True, db_index=True)
    numero_serie = models.CharField("número de série", max_length=120, blank=True, db_index=True)
    categoria = models.ForeignKey("cadastros.CategoriaAtivo", on_delete=models.PROTECT, related_name="ativos")
    fabricante = models.CharField("fabricante", max_length=120, blank=True)
    modelo = models.CharField("modelo", max_length=160)
    localizacao = models.ForeignKey("cadastros.Localizacao", on_delete=models.PROTECT, related_name="ativos")
    status = models.ForeignKey("cadastros.StatusAtivo", on_delete=models.PROTECT, related_name="ativos")
    data_aquisicao = models.DateField("data de aquisição", null=True, blank=True)
    valor_aquisicao = models.DecimalField(
        "valor de aquisição (R$)", max_digits=14, decimal_places=2, null=True, blank=True
    )
    nota_fiscal = models.CharField("nota fiscal", max_length=100, blank=True)
    garantia_fim = models.DateField("garantia até", null=True, blank=True, db_index=True)
    observacoes = models.TextField("observações", blank=True, max_length=10000)

    class Meta:
        ordering = ["patrimonio", "id"]
        constraints = [
            models.UniqueConstraint(
                Lower("patrimonio"), condition=Q(ativo=True), name="ativo_patrimonio_ativo"
            ),
            models.UniqueConstraint(
                Lower("service_tag"),
                condition=Q(ativo=True) & ~Q(service_tag=""),
                name="ativo_service_tag_ativo",
            ),
            models.CheckConstraint(
                condition=Q(valor_aquisicao__isnull=True) | Q(valor_aquisicao__gte=0),
                name="ativo_valor_positivo",
            ),
        ]

    def __str__(self):
        return f"{self.patrimonio} · {self.modelo}"


class AtivoTecnico(models.Model):
    ativo = models.OneToOneField(Ativo, on_delete=models.PROTECT, related_name="tecnico")
    hostname = models.CharField(max_length=253, blank=True, db_index=True)
    sistema_operacional = models.CharField(max_length=160, blank=True)
    processador = models.CharField(max_length=200, blank=True)
    memoria_gb = models.PositiveIntegerField(null=True)
    origem = models.CharField(max_length=20, default="MANUAL")


class InterfaceRede(models.Model):
    ativo = models.ForeignKey(Ativo, on_delete=models.PROTECT, related_name="interfaces")
    nome = models.CharField(max_length=100)
    mac = models.CharField(max_length=17, blank=True, db_index=True)
    ip = models.GenericIPAddressField(null=True, blank=True, db_index=True)
