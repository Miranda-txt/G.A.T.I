from django.conf import settings
from django.db import models
from django.db.models import F, Q

from gati.common.models import AppendOnly, Registro


class ProcessoMovimentacao(Registro):
    TIPOS = [("ENTREGA", "Entrega"), ("DEVOLUCAO", "Devolução")]
    tipo = models.CharField(max_length=12, choices=TIPOS)
    responsavel = models.ForeignKey("pessoas.Pessoa", on_delete=models.PROTECT)
    localizacao = models.ForeignKey("cadastros.Localizacao", on_delete=models.PROTECT)
    data = models.DateField("data da movimentação")
    observacoes = models.TextField(blank=True, max_length=10000)
    estado = models.CharField(max_length=24, default="EM_EDICAO", db_index=True)
    criado_por = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    concluido_em = models.DateTimeField(null=True)

    class Meta:
        ordering = ["-id"]

    def __str__(self):
        return f"{self.get_tipo_display()} #{self.pk}"


class ProcessoItem(models.Model):
    processo = models.ForeignKey(ProcessoMovimentacao, on_delete=models.PROTECT, related_name="itens")
    ativo = models.ForeignKey("ativos.Ativo", on_delete=models.PROTECT)
    acessorios = models.TextField(blank=True, max_length=2000)
    condicoes = models.TextField(blank=True, max_length=4000)
    avaria = models.BooleanField(default=False)
    divergencias = models.TextField(blank=True, max_length=4000)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["processo", "ativo"], name="processo_ativo_unico")]


class ResponsabilidadeAtivo(models.Model):
    ativo = models.ForeignKey("ativos.Ativo", on_delete=models.PROTECT, related_name="responsabilidades")
    pessoa = models.ForeignKey("pessoas.Pessoa", on_delete=models.PROTECT, related_name="responsabilidades")
    inicio = models.DateTimeField()
    fim = models.DateTimeField(null=True, db_index=True)
    processo_inicio = models.ForeignKey(ProcessoMovimentacao, on_delete=models.PROTECT, related_name="+")
    processo_fim = models.ForeignKey(
        ProcessoMovimentacao, on_delete=models.PROTECT, related_name="+", null=True
    )

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=Q(fim__isnull=True) | Q(fim__gte=F("inicio")), name="responsabilidade_tempo"
            ),
            models.UniqueConstraint(
                fields=["ativo", "pessoa"],
                condition=Q(fim__isnull=True),
                name="responsabilidade_pessoa_unica",
            ),
        ]


class Movimentacao(AppendOnly):
    ativo = models.ForeignKey("ativos.Ativo", on_delete=models.PROTECT, related_name="historico")
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    processo = models.ForeignKey(ProcessoMovimentacao, on_delete=models.PROTECT, null=True)
    data = models.DateTimeField(auto_now_add=True)
    tipo = models.CharField(max_length=30)
    descricao = models.TextField(max_length=4000)
    antes = models.JSONField(default=dict)
    depois = models.JSONField(default=dict)

    class Meta:
        ordering = ["-data", "-id"]
        indexes = [models.Index(fields=["ativo", "-data"])]
