"""Transactional outbox foundation for term V2.

The handlers must enforce domain locks, revalidate state immediately before
external effects, and implement their own idempotency. A lease fences database
completion, not SMTP or object storage. No handlers are registered by default.
"""

import logging
from collections.abc import Callable
from datetime import timedelta
from secrets import randbelow
from uuid import UUID, uuid4

from django.conf import settings
from django.db import connection, transaction
from django.db.models import Count, Min, Q
from django.utils import timezone

from gati.apps.usuarios.permissions import authorize
from gati.common.errors import Conflict

from ..models import OutboxTask
from .outbox_policy import (
    KINDS,
    attempt_cap,
    aware_time,
    finish_values,
    lease_duration,
    lease_is_current,
    validate_identity,
)

logger = logging.getLogger(__name__)
HANDLERS: dict[str, Callable[[OutboxTask], str]] = {}


class Clock:
    @staticmethod
    def now():
        return timezone.now()


def enabled():
    return settings.GATI_TERMO_V2_ENABLED is True


def _require_enabled():
    if not enabled():
        raise Conflict("Modulo de termos V2 desabilitado")
    if connection.vendor != "postgresql":
        raise Conflict("Outbox exige PostgreSQL")


def _max_attempts():
    return attempt_cap(settings.GATI_TERM_OUTBOX_MAX_ATTEMPTS)


def _jitter():
    maximum = settings.GATI_TERM_OUTBOX_JITTER_SECONDS
    if type(maximum) is not int or not 0 <= maximum <= 5:
        raise ValueError("jitter invalido")
    return randbelow(maximum + 1)


def enqueue(kind, resource_id, dedupe_key, run_after):
    """Join caller transaction; conflict if a key represents a different event."""
    _require_enabled()
    validate_identity(kind, resource_id, dedupe_key)
    aware_time(run_after)
    with transaction.atomic():
        task, created = OutboxTask.objects.get_or_create(
            dedupe_key=dedupe_key,
            defaults={
                "kind": kind,
                "resource_id": resource_id,
                "scheduled_at": run_after,
                "run_after": run_after,
            },
        )
        if not created and (task.kind, task.resource_id, task.scheduled_at) != (kind, resource_id, run_after):
            raise Conflict("Chave de deduplicacao ja vinculada a outro evento")
        return task


def claim(now, lease_seconds, *, kinds=None):
    """Claim at most one task and quarantine a bounded batch of exhausted tasks."""
    _require_enabled()
    aware_time(now)
    lease_duration(lease_seconds)
    cap = _max_attempts()
    kinds = KINDS if kinds is None else tuple(kinds)
    if any(kind not in KINDS for kind in kinds):
        raise ValueError("tipo de tarefa invalido")
    if not kinds:
        return None
    with transaction.atomic():
        expired = Q(estado="PROCESSANDO", lease_until__lte=now)
        # A crashed notification worker may already have submitted to SMTP.
        # Quarantine rather than automatically repeating an ambiguous effect.
        uncertain = list(
            OutboxTask.objects.select_for_update(skip_locked=True)
            .filter(expired, kind="NOTIFICACAO", kind__in=kinds)
            .order_by("lease_until", "id")
            .values_list("pk", flat=True)[:100]
        )
        if uncertain:
            OutboxTask.objects.filter(pk__in=uncertain).update(
                estado="FALHA",
                lease_id=None,
                lease_until=None,
                error_code="OUTCOME_UNCERTAIN",
                updated_at=now,
            )
        ready = Q(estado="PENDENTE", run_after__lte=now) | (expired & ~Q(kind="NOTIFICACAO"))
        exhausted = list(
            OutboxTask.objects.select_for_update(skip_locked=True)
            .filter(ready, kind__in=kinds, attempts__gte=cap)
            .order_by("run_after", "id")
            .values_list("pk", flat=True)[:100]
        )
        if exhausted:
            OutboxTask.objects.filter(pk__in=exhausted).update(
                estado="FALHA", lease_id=None, lease_until=None, error_code="LEASE_EXHAUSTED", updated_at=now
            )
        task = (
            OutboxTask.objects.select_for_update(skip_locked=True)
            .filter(ready, kind__in=kinds, attempts__lt=cap)
            .order_by("run_after", "id")
            .first()
        )
        if task is None:
            return None
        task.estado = "PROCESSANDO"
        task.attempts += 1
        task.lease_id = uuid4()
        task.lease_until = now + timedelta(seconds=lease_seconds)
        task.error_code = ""
        task.save(update_fields=["estado", "attempts", "lease_id", "lease_until", "error_code", "updated_at"])
        return task


def finish(task_id, lease_id, outcome, *, now=None, clock=Clock.now):
    """Fence completion with the current lease and a fresh time under row lock."""
    _require_enabled()
    if type(task_id) is not int or task_id <= 0 or type(lease_id) is not UUID:
        raise ValueError("identidade do lease invalida")
    with transaction.atomic():
        task = OutboxTask.objects.select_for_update().filter(pk=task_id).first()
        current = aware_time(clock() if now is None else now)
        if task is None or not lease_is_current(
            task.estado, task.lease_id, task.lease_until, lease_id, current
        ):
            raise Conflict("Lease ausente, expirado ou substituido")
        task.estado, task.error_code, task.run_after = finish_values(
            task.attempts, outcome, current, _max_attempts(), _jitter()
        )
        task.lease_id = None
        task.lease_until = None
        task.save(
            update_fields=["estado", "error_code", "run_after", "lease_id", "lease_until", "updated_at"]
        )


def run_one(now, *, handlers=None, clock=Clock.now):
    """Run one registered handler outside the claim transaction.

    Only an explicit RETRY indicates a safely retryable failure. Unclassified
    exceptions or invalid outcomes are quarantined as ambiguous; never log the
    exception content. A stale finish cannot mutate a recovered task.
    """
    _require_enabled()
    if connection.in_atomic_block:
        raise Conflict("Worker nao pode executar dentro de uma transacao externa")
    handlers = HANDLERS if handlers is None else handlers
    if any(kind not in KINDS or not callable(handler) for kind, handler in handlers.items()):
        raise ValueError("registro de handlers invalido")
    if not handlers:
        return False
    task = claim(now, settings.GATI_TERM_OUTBOX_LEASE_SECONDS, kinds=handlers)
    if task is None:
        return False
    task_id, lease_id, kind = task.pk, task.lease_id, task.kind
    # Recheck ownership with the fresh clock before dispatch; this is not an
    # external-effect fence. The domain handler must still revalidate its state.
    with transaction.atomic():
        current = OutboxTask.objects.select_for_update().filter(pk=task_id).first()
        if current is None or not lease_is_current(
            current.estado, current.lease_id, current.lease_until, lease_id, clock()
        ):
            logger.warning("term_outbox_lease_lost_before_dispatch task_id=%s", task_id)
            return True
    try:
        outcome = handlers[kind](current)
    except Exception:  # External outcomes may be ambiguous; do not retry or leak exception text.
        outcome = "UNCERTAIN"
    if outcome not in ("SUCCESS", "RETRY", "UNCERTAIN"):
        outcome = "UNCERTAIN"
    if outcome != "SUCCESS":
        logger.warning("term_outbox_handler_result task_id=%s outcome=%s", task_id, outcome)
    try:
        finish(task_id, lease_id, outcome, clock=clock)
    except Conflict:
        logger.warning("term_outbox_lease_lost task_id=%s", task_id)
    return True


def queue_snapshot(user, now, *, failure_limit=50, before_id=None):
    """Admin-only read-only operational snapshot, including while V2 is disabled."""
    authorize(user, admin=True)
    aware_time(now)
    if type(failure_limit) is not int or not 1 <= failure_limit <= 100:
        raise ValueError("limite de falhas invalido")
    if before_id is not None and (type(before_id) is not int or before_id <= 0):
        raise ValueError("cursor invalido")
    tasks = OutboxTask.objects.all()
    oldest = tasks.filter(estado="PENDENTE", run_after__lte=now).aggregate(oldest=Min("run_after"))["oldest"]
    counts = list(tasks.values("kind", "estado").annotate(total=Count("id")).order_by("kind", "estado"))
    failures = tasks.filter(estado="FALHA")
    if before_id is not None:
        failures = failures.filter(id__lt=before_id)
    failure_rows = failures.order_by("-id").values("id", "kind", "attempts", "error_code", "updated_at")
    return {
        "observed_at": now,
        "enabled": enabled(),
        "counts": counts,
        "oldest_ready_seconds": int((now - oldest).total_seconds()) if oldest is not None else None,
        "expired_leases": tasks.filter(estado="PROCESSANDO", lease_until__lte=now).count(),
        "failures": list(failure_rows[:failure_limit]),
    }
