"""Transactional PostgreSQL worker lease capability tests, using disposable test DB."""

import runpy
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from pathlib import Path

import pytest
from django.db import connection, connections, transaction
from django.utils import timezone

SPIKE = Path(__file__).parent / "fixtures" / "term_v2" / "worker_spike.py"
pytestmark = pytest.mark.django_db(transaction=True)


@pytest.fixture(autouse=True)
def postgres_spike_table():
    assert connection.vendor == "postgresql", "PostgreSQL real is required for T01 worker spike"
    assert str(connection.settings_dict["NAME"]).startswith("test_"), "Never create spike tables in real DB"
    with connection.cursor() as cur:
        cur.execute("""
            CREATE TABLE gati_t01_worker_spike (
                id BIGSERIAL PRIMARY KEY,
                dedupe_key VARCHAR(128) NOT NULL UNIQUE,
                kind VARCHAR(40) NOT NULL,
                resource_id UUID NOT NULL,
                run_after TIMESTAMPTZ NOT NULL,
                attempts INTEGER NOT NULL DEFAULT 0,
                state VARCHAR(12) NOT NULL DEFAULT 'PENDING',
                lease_id UUID,
                lease_until TIMESTAMPTZ,
                error_code VARCHAR(40) NOT NULL DEFAULT '',
                CONSTRAINT gati_t01_worker_state
                    CHECK (state IN ('PENDING', 'LEASED', 'DONE', 'DEAD'))
            )
        """)
        cur.execute("""
            CREATE INDEX gati_t01_worker_ready
            ON gati_t01_worker_spike (state, run_after, id)
        """)
    try:
        yield
    finally:
        with connection.cursor() as cur:
            cur.execute("DROP TABLE IF EXISTS gati_t01_worker_spike")


def _api():
    assert SPIKE.is_file(), "T01: PostgreSQL worker spike not implemented"
    return runpy.run_path(str(SPIKE))


def _worker():
    return _api()["WorkerSpike"](max_attempts=3, jitter_seconds=0)


def _enqueue(worker, now, suffix=None, after=None):
    ident = uuid.uuid4()
    key = "render:" + (suffix or str(ident))
    return worker.enqueue("render", ident, key, after or now)


def _state(task_id):
    with connection.cursor() as cur:
        cur.execute(
            "SELECT state, attempts, error_code FROM gati_t01_worker_spike WHERE id = %s",
            [task_id],
        )
        return cur.fetchone()


def test_worker_capability_reclaims_expired_lease_exactly_once():
    worker = _worker()
    now = timezone.now()
    task_id = _enqueue(worker, now)
    first = worker.claim(now, lease_seconds=10)
    assert first.id == task_id and first.attempts == 1
    assert worker.claim(now + timedelta(seconds=1), lease_seconds=10) is None
    recovered = worker.claim(now + timedelta(seconds=11), lease_seconds=10)
    assert recovered.id == task_id
    assert recovered.lease_id != first.lease_id
    assert recovered.attempts == 2
    assert worker.finish(task_id, first.lease_id, "SUCCESS", now + timedelta(seconds=12)) is False
    assert worker.finish(task_id, recovered.lease_id, "SUCCESS", now + timedelta(seconds=12))
    assert worker.claim(now + timedelta(seconds=30), lease_seconds=10) is None
    assert _state(task_id) == ("DONE", 2, "")


def test_worker_enqueue_rollback_is_atomic():
    worker = _worker()
    now = timezone.now()
    with pytest.raises(RuntimeError):
        with transaction.atomic():
            _enqueue(worker, now)
            raise RuntimeError("synthetic rollback")
    with connection.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM gati_t01_worker_spike")
        assert cur.fetchone()[0] == 0


def test_worker_enqueue_dedupe_key_rejects_conflicting_payload():
    worker = _worker()
    now = timezone.now()
    resource = uuid.uuid4()
    first = worker.enqueue("render", resource, "render:same", now)
    assert worker.enqueue("render", resource, "render:same", now) == first
    with pytest.raises(_api()["WorkerConflict"]):
        worker.enqueue("render", uuid.uuid4(), "render:same", now)
    with pytest.raises(_api()["WorkerConflict"]):
        worker.enqueue("notify", resource, "render:same", now)


def test_worker_claim_skips_row_locked_by_other_transaction():
    worker = _worker()
    now = timezone.now()
    locked_id = _enqueue(worker, now)
    free_id = _enqueue(worker, now)
    with transaction.atomic():
        with connection.cursor() as cur:
            cur.execute(
                "SELECT id FROM gati_t01_worker_spike WHERE id = %s FOR UPDATE",
                [locked_id],
            )

        def claim_from_other_connection():
            try:
                return worker.claim(now, lease_seconds=10)
            finally:
                connections.close_all()

        with ThreadPoolExecutor(max_workers=1) as pool:
            candidate = pool.submit(claim_from_other_connection).result(timeout=15)
        assert candidate is not None and candidate.id == free_id
    other = worker.claim(now, lease_seconds=10)
    assert other is not None and other.id == locked_id
    assert candidate.lease_id != other.lease_id


def test_worker_concurrent_claims_have_distinct_ids():
    worker = _worker()
    now = timezone.now()
    ids = {_enqueue(worker, now) for _ in range(3)}

    def claim_thread(_):
        try:
            return worker.claim(now, lease_seconds=20)
        finally:
            connections.close_all()

    with ThreadPoolExecutor(max_workers=3) as pool:
        claimed = list(pool.map(claim_thread, range(3)))
    assert all(task is not None for task in claimed)
    assert {task.id for task in claimed} == ids
    assert len({task.lease_id for task in claimed}) == 3


def test_worker_retry_backoff_is_bounded_and_sanitized():
    worker = _worker()
    now = timezone.now()
    task_id = _enqueue(worker, now)
    first = worker.claim(now, lease_seconds=10)
    assert worker.finish(task_id, first.lease_id, "RETRY", now)
    assert _state(task_id) == ("PENDING", 1, "HANDLER_FAILED")
    assert worker.claim(now + timedelta(seconds=4), lease_seconds=10) is None
    second = worker.claim(now + timedelta(seconds=5), lease_seconds=10)
    assert second.id == task_id and second.attempts == 2
    assert worker.finish(task_id, second.lease_id, "RETRY", now + timedelta(seconds=5))
    assert worker.claim(now + timedelta(seconds=14), lease_seconds=10) is None
    third = worker.claim(now + timedelta(seconds=15), lease_seconds=10)
    assert third.id == task_id and third.attempts == 3
    assert worker.finish(task_id, third.lease_id, "RETRY", now + timedelta(seconds=15))
    assert _state(task_id) == ("DEAD", 3, "HANDLER_FAILED")


def test_worker_expired_last_attempt_goes_dead_without_reexecution():
    worker = _worker()
    now = timezone.now()
    task_id = _enqueue(worker, now)
    for attempt in range(3):
        claimed = worker.claim(now + timedelta(seconds=attempt * 11), lease_seconds=10)
        assert claimed is not None
    assert worker.claim(now + timedelta(seconds=33), lease_seconds=10) is None
    assert _state(task_id) == ("DEAD", 3, "LEASE_EXHAUSTED")


def test_worker_handler_exception_fails_closed_without_logging_secrets():
    worker = _worker()
    now = timezone.now()
    task_id = _enqueue(worker, now)

    def failing_handler(_):
        raise RuntimeError("sensitive-token=never-log-me")

    assert worker.run_one(now, {"render": failing_handler}) is True
    assert _state(task_id) == ("PENDING", 1, "HANDLER_FAILED")
    assert worker.run_one(now, {"render": failing_handler}) is False


def test_worker_successful_handler_marks_done_once():
    worker = _worker()
    now = timezone.now()
    task_id = _enqueue(worker, now)
    seen = []
    assert worker.run_one(now, {"render": lambda ident: seen.append(ident)}) is True
    assert len(seen) == 1
    assert _state(task_id) == ("DONE", 1, "")
    assert worker.run_one(now, {"render": lambda _: seen.append("duplicate")}) is False
    assert len(seen) == 1


def test_worker_rejects_unsafe_tasks_and_parameters():
    worker = _worker()
    now = timezone.now()
    for kwargs in [
        ("render", "personal@example.invalid", "render:key", now),
        ("invalid_kind", uuid.uuid4(), "render:key", now),
        ("render", uuid.uuid4(), "secret=abc", now),
        ("render", uuid.uuid4(), "render:key", now.replace(tzinfo=None)),
    ]:
        with pytest.raises(ValueError):
            worker.enqueue(*kwargs)
    with pytest.raises(ValueError):
        worker.claim(now, lease_seconds=0)
    with pytest.raises(ValueError):
        worker.finish(42, uuid.uuid4(), "INVALID", now)
