from django.db import models

from gati.common.models import Cadastro, Registro


class ModeloTermo(Cadastro):
    nome = models.CharField("nome", max_length=160)
    texto = models.TextField("texto do modelo", max_length=30000)

    class Meta:
        ordering = ["nome", "id"]

    def __str__(self):
        return self.nome


class Termo(Registro):
    substitui = models.OneToOneField(
        "self", null=True, blank=True, on_delete=models.PROTECT, related_name="substituto"
    )
    processo = models.ForeignKey(
        "movimentacoes.ProcessoMovimentacao", on_delete=models.PROTECT, related_name="termos"
    )
    modelo = models.ForeignKey(ModeloTermo, on_delete=models.PROTECT)
    texto = models.TextField(max_length=30000)
    estado = models.CharField(max_length=24, default="EM_EDICAO", db_index=True)
    payload = models.JSONField(default=dict)
    sha256 = models.CharField(max_length=64, blank=True)
    emitido_em = models.DateTimeField(null=True)
    cancelado_em = models.DateTimeField(null=True)
    motivo_cancelamento = models.TextField(blank=True, max_length=2000)

    class Meta:
        ordering = ["-id"]
        constraints = [
            models.UniqueConstraint(
                fields=["processo"], condition=~models.Q(estado="CANCELADO"), name="termo_vigente_processo"
            )
        ]

    def __str__(self):
        return f"Termo #{self.pk}"


class TermoItem(models.Model):
    termo = models.ForeignKey(Termo, on_delete=models.PROTECT, related_name="itens")
    ativo = models.ForeignKey("ativos.Ativo", on_delete=models.PROTECT)
    snapshot = models.JSONField()

    class Meta:
        constraints = [models.UniqueConstraint(fields=["termo", "ativo"], name="termo_item_unico")]


class AssinaturaTermo(models.Model):
    termo = models.ForeignKey(Termo, on_delete=models.PROTECT, related_name="assinaturas")
    pessoa = models.ForeignKey("pessoas.Pessoa", on_delete=models.PROTECT)
    papel = models.CharField(max_length=30, default="RESPONSAVEL")
    metodo = models.CharField(max_length=15, choices=[("PRESENCIAL", "Presencial"), ("EMAIL", "E-mail")])
    snapshot = models.JSONField(default=dict)
    token_hash = models.CharField(max_length=64, blank=True, db_index=True)
    expira_em = models.DateTimeField(null=True)
    tentativas = models.PositiveSmallIntegerField(default=0)
    assinado_em = models.DateTimeField(null=True)
    hash_assinado = models.CharField(max_length=64, blank=True)
    ip = models.GenericIPAddressField(null=True)
    user_agent = models.CharField(max_length=512, blank=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["termo", "pessoa"], name="signatario_unico")]


class SessaoAssinatura(models.Model):
    segredo_hash = models.CharField(max_length=64, unique=True)
    assinatura = models.ForeignKey(AssinaturaTermo, on_delete=models.PROTECT)
    criada_em = models.DateTimeField(auto_now_add=True)
    vista_em = models.DateTimeField(auto_now_add=True)
    identidade_confirmada = models.BooleanField(default=False)
    encerrada = models.BooleanField(default=False)


class OutboxTask(models.Model):
    """Persistent technical task; no personal data or reversible secrets."""

    kind = models.CharField(max_length=40)
    resource_id = models.CharField(max_length=36)
    dedupe_key = models.CharField(max_length=128, unique=True)
    scheduled_at = models.DateTimeField()
    run_after = models.DateTimeField()
    attempts = models.PositiveSmallIntegerField(default=0)
    lease_id = models.UUIDField(null=True, blank=True)
    lease_until = models.DateTimeField(null=True, blank=True)
    estado = models.CharField(max_length=12, default="PENDENTE")
    error_code = models.CharField(max_length=40, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["estado", "run_after", "id"], name="term_outbox_ready_idx"),
            models.Index(fields=["estado", "lease_until", "id"], name="term_outbox_lease_idx"),
        ]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(kind__in=["EMISSAO", "PDF_FINAL", "NOTIFICACAO", "RECONCILIACAO"]),
                name="term_outbox_kind_valid",
            ),
            models.CheckConstraint(
                condition=models.Q(estado__in=["PENDENTE", "PROCESSANDO", "CONCLUIDA", "FALHA"]),
                name="term_outbox_state_valid",
            ),
            models.CheckConstraint(
                condition=(
                    models.Q(estado="PROCESSANDO", lease_id__isnull=False, lease_until__isnull=False)
                    | (
                        ~models.Q(estado="PROCESSANDO")
                        & models.Q(lease_id__isnull=True, lease_until__isnull=True)
                    )
                ),
                name="term_outbox_lease_valid",
            ),
            models.CheckConstraint(condition=models.Q(attempts__lte=10), name="term_outbox_attempts_valid"),
            models.CheckConstraint(
                condition=models.Q(
                    error_code__in=["", "HANDLER_FAILED", "LEASE_EXHAUSTED", "OUTCOME_UNCERTAIN"]
                ),
                name="term_outbox_error_valid",
            ),
        ]
