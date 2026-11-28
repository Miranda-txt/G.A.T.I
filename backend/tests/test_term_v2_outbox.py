"""T02 PostgreSQL integration tests; only disposable test database."""

import logging
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from threading import Barrier
from uuid import uuid4

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError
from django.db import connection, connections, transaction
from django.utils import timezone

from gati.apps.termos.models import OutboxTask
from gati.apps.termos.services import outbox
from gati.apps.termos.services.outbox_policy import dedupe_key
from gati.common.errors import Conflict

pytestmark = pytest.mark.django_db(transaction=True)


@pytest.fixture(autouse=True)
def isolated_db(settings):
    assert connection.vendor == "postgresql"
    assert str(connection.settings_dict["NAME"]).startswith("test_")
    settings.GATI_TERMO_V2_ENABLED = True
    settings.GATI_TERM_OUTBOX_MAX_ATTEMPTS = 3
    settings.GATI_TERM_OUTBOX_LEASE_SECONDS = 30
    settings.GATI_TERM_OUTBOX_JITTER_SECONDS = 0


def schedule(now, resource="42", key=None, kind="EMISSAO"):
    return outbox.enqueue(kind, resource, key or dedupe_key(kind, resource, uuid4()), now)


def test_enqueue_rollback():
    now = timezone.now()
    key = dedupe_key("EMISSAO", "42", uuid4())
    with pytest.raises(RuntimeError):
        with transaction.atomic():
            schedule(now, key=key)
            raise RuntimeError("rollback sintetico")
    assert not OutboxTask.objects.filter(dedupe_key=key).exists()


def test_duplicate_enqueue():
    now = timezone.now()
    first = schedule(now)
    assert schedule(now, key=first.dedupe_key).pk == first.pk
    with pytest.raises(Conflict):
        schedule(now + timedelta(seconds=1), key=first.dedupe_key)
    lease = outbox.claim(now, 10)
    outbox.finish(lease.pk, lease.lease_id, "RETRY", now=now)
    assert schedule(now, key=first.dedupe_key).pk == first.pk


def test_concurrent_claim_and_stale_lease():
    now = timezone.now()
    tasks = [schedule(now) for _ in range(2)]
    barrier = Barrier(2)

    def claim_other(_):
        try:
            barrier.wait(timeout=10)
            return outbox.claim(now, 10)
        finally:
            connections.close_all()

    with ThreadPoolExecutor(max_workers=2) as pool:
        claimed = list(pool.map(claim_other, range(2)))
    assert all(claimed)
    assert {task.pk for task in claimed} == {task.pk for task in tasks}
    assert len({task.lease_id for task in claimed}) == 2
    recovered = outbox.claim(now + timedelta(seconds=11), 10)
    old = next(task for task in claimed if task.pk == recovered.pk)
    assert recovered.lease_id != old.lease_id
    with pytest.raises(Conflict):
        outbox.finish(old.pk, old.lease_id, "SUCCESS", now=now + timedelta(seconds=12))
    outbox.finish(recovered.pk, recovered.lease_id, "SUCCESS", now=now + timedelta(seconds=12))
    recovered.refresh_from_db()
    assert recovered.estado == "CONCLUIDA"


def test_retry_and_terminal_failure():
    now = timezone.now()
    task = schedule(now)
    for delay in (5, 10, 0):
        lease = outbox.claim(now, 10)
        assert lease.pk == task.pk
        outbox.finish(lease.pk, lease.lease_id, "RETRY", now=now)
        task.refresh_from_db()
        if delay:
            assert task.estado == "PENDENTE"
            assert task.run_after == now + timedelta(seconds=delay)
            assert outbox.claim(task.run_after - timedelta(microseconds=1), 10) is None
            now = task.run_after
    assert task.estado == "FALHA"
    assert task.attempts == 3
    assert task.lease_id is None and task.lease_until is None
    assert outbox.claim(now, 10) is None


def test_expired_last_lease_is_quarantined():
    now = timezone.now()
    task = schedule(now)
    for _ in range(3):
        assert outbox.claim(now, 10).pk == task.pk
        now += timedelta(seconds=11)
    assert outbox.claim(now, 10) is None
    task.refresh_from_db()
    assert task.estado == "FALHA"
    assert task.error_code == "LEASE_EXHAUSTED"


def test_no_secrets_in_payload_or_logs(caplog):
    now = timezone.now()
    task = schedule(now)
    secret = "synthetic-confidential-value"

    def fail(_):
        raise RuntimeError(secret)

    with caplog.at_level(logging.WARNING):
        assert outbox.run_one(now, handlers={"EMISSAO": fail}, clock=lambda: now)
    task.refresh_from_db()
    assert secret not in str(OutboxTask.objects.filter(pk=task.pk).values().get())
    assert secret not in caplog.text
    assert task.error_code == "OUTCOME_UNCERTAIN"
    assert task.estado == "FALHA"


def test_finish_rechecks_current_time():
    now = timezone.now()
    task = schedule(now)

    def finish_late(_):
        return "SUCCESS"

    assert outbox.run_one(now, handlers={"EMISSAO": finish_late}, clock=lambda: now + timedelta(seconds=31))
    task.refresh_from_db()
    assert task.estado == "PROCESSANDO"
    assert outbox.claim(now + timedelta(seconds=31), 10).pk == task.pk


def test_worker_does_not_claim_without_handler():
    now = timezone.now()
    task = schedule(now)
    assert not outbox.run_one(now, handlers={}, clock=lambda: now)
    task.refresh_from_db()
    assert task.attempts == 0


def test_disabled_by_default_or_without_handlers(settings):
    settings.GATI_TERMO_V2_ENABLED = False
    with pytest.raises(Conflict):
        schedule(timezone.now())
    with pytest.raises(CommandError):
        call_command("processar_tarefas_termos", once=True)
    settings.GATI_TERMO_V2_ENABLED = True
    with pytest.raises(CommandError):
        call_command("processar_tarefas_termos", once=True)
