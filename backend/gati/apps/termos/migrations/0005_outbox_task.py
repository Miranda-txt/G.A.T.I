"""Expand schema for term V2 technical tasks; leave all legacy tables intact."""

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("termos", "0004_seg_term_001")]
    operations = [
        migrations.CreateModel(
            name="OutboxTask",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
                    ),
                ),
                ("kind", models.CharField(max_length=40)),
                ("resource_id", models.CharField(max_length=36)),
                ("dedupe_key", models.CharField(max_length=128, unique=True)),
                ("scheduled_at", models.DateTimeField()),
                ("run_after", models.DateTimeField()),
                ("attempts", models.PositiveSmallIntegerField(default=0)),
                ("lease_id", models.UUIDField(blank=True, null=True)),
                ("lease_until", models.DateTimeField(blank=True, null=True)),
                ("estado", models.CharField(default="PENDENTE", max_length=12)),
                ("error_code", models.CharField(blank=True, default="", max_length=40)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "indexes": [
                    models.Index(fields=["estado", "run_after", "id"], name="term_outbox_ready_idx"),
                    models.Index(fields=["estado", "lease_until", "id"], name="term_outbox_lease_idx"),
                ],
                "constraints": [
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
                    models.CheckConstraint(
                        condition=models.Q(attempts__lte=10), name="term_outbox_attempts_valid"
                    ),
                    models.CheckConstraint(
                        condition=models.Q(
                            error_code__in=["", "HANDLER_FAILED", "LEASE_EXHAUSTED", "OUTCOME_UNCERTAIN"]
                        ),
                        name="term_outbox_error_valid",
                    ),
                ],
            },
        ),
    ]
