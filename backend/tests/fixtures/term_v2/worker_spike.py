"""T01 worker capability spike: PostgreSQL row-locked, leased outbox.

This is NOT a production Django worker or migration. It operates only on
gati_t01_worker_spike, a transient table created by the test fixture.
"""

import re
import uuid
from dataclasses import dataclass
from datetime import timedelta

from django.db import connection, transaction
from django.utils import timezone


class WorkerConflict(Exception):
    """An existing deduplication key belongs to a different task."""


@dataclass(frozen=True)
class ClaimedTask:
    id: int
    kind: str
    resource_id: uuid.UUID
    attempts: int
    lease_id: uuid.UUID
    lease_until: object


class WorkerSpike:
    """Small proof for at-least-once processing with fencing, not exactly-once."""

    def __init__(self, max_attempts=3, jitter_seconds=0):
        if type(max_attempts) is not int or not 1 <= max_attempts <= 10:
            raise ValueError("Invalid attempt cap")
        if type(jitter_seconds) is not int or not 0 <= jitter_seconds <= 5:
            raise ValueError("Invalid jitter")
        self.max_attempts = max_attempts
        self.jitter_seconds = jitter_seconds

    @staticmethod
    def _time(now):
        if not hasattr(now, "tzinfo") or not timezone.is_aware(now):
            raise ValueError("Timezone-aware datetime required")

    def enqueue(self, kind, resource_id, dedupe_key, run_after):
        if kind not in {"render", "notify"} or type(resource_id) is not uuid.UUID:
            raise ValueError("Invalid task identity")
        if (
            not isinstance(dedupe_key, str)
            or len(dedupe_key) > 128
            or re.fullmatch(r"[A-Za-z0-9:_-]+", dedupe_key) is None
        ):
            raise ValueError("Invalid deduplication key")
        self._time(run_after)
        with transaction.atomic():
            with connection.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO gati_t01_worker_spike
                        (kind, resource_id, dedupe_key, run_after)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (dedupe_key) DO NOTHING
                    RETURNING id
                    """,
                    [kind, resource_id, dedupe_key, run_after],
                )
                inserted = cur.fetchone()
                if inserted is not None:
                    return inserted[0]
                cur.execute(
                    """
                    SELECT id, kind, resource_id, run_after
                    FROM gati_t01_worker_spike
                    WHERE dedupe_key = %s
                    """,
                    [dedupe_key],
                )
                existing = cur.fetchone()
                if existing is None:
                    raise WorkerConflict("Deduplication conflict without visible task")
                if existing[1:] != (kind, resource_id, run_after):
                    raise WorkerConflict("Deduplication key reused for another intent")
                return existing[0]

    def claim(self, now, lease_seconds):
        self._time(now)
        if type(lease_seconds) is not int or not 1 <= lease_seconds <= 3600:
            raise ValueError("Invalid lease duration")
        with transaction.atomic():
            with connection.cursor() as cur:
                # Expired final attempts must be quarantined before new claims.
                cur.execute(
                    """
                    UPDATE gati_t01_worker_spike
                    SET state = 'DEAD', lease_id = NULL, lease_until = NULL,
                        error_code = 'LEASE_EXHAUSTED'
                    WHERE id IN (
                        SELECT id FROM gati_t01_worker_spike
                        WHERE state = 'LEASED' AND lease_until <= %s
                          AND attempts >= %s
                        FOR UPDATE SKIP LOCKED
                    )
                    """,
                    [now, self.max_attempts],
                )
                cur.execute(
                    """
                    SELECT id, kind, resource_id, attempts
                    FROM gati_t01_worker_spike
                    WHERE (
                        (state = 'PENDING' AND run_after <= %s)
                        OR (state = 'LEASED' AND lease_until <= %s)
                    ) AND attempts < %s
                    ORDER BY run_after, id
                    LIMIT 1
                    FOR UPDATE SKIP LOCKED
                    """,
                    [now, now, self.max_attempts],
                )
                row = cur.fetchone()
                if row is None:
                    return None
                task_id, kind, resource, attempts = row
                lease_id = uuid.uuid4()
                until = now + timedelta(seconds=lease_seconds)
                cur.execute(
                    """
                    UPDATE gati_t01_worker_spike
                    SET state = 'LEASED', lease_id = %s, lease_until = %s,
                        attempts = attempts + 1, error_code = ''
                    WHERE id = %s
                    """,
                    [lease_id, until, task_id],
                )
                return ClaimedTask(task_id, kind, resource, attempts + 1, lease_id, until)

    def finish(self, task_id, lease_id, outcome, now):
        self._time(now)
        if type(task_id) is not int or task_id <= 0 or type(lease_id) is not uuid.UUID:
            raise ValueError("Invalid lease identity")
        if outcome not in ("SUCCESS", "RETRY"):
            raise ValueError("Invalid outcome")
        with transaction.atomic():
            with connection.cursor() as cur:
                cur.execute(
                    """
                    SELECT attempts FROM gati_t01_worker_spike
                    WHERE id = %s AND state = 'LEASED' AND lease_id = %s
                      AND lease_until > %s
                    FOR UPDATE
                    """,
                    [task_id, lease_id, now],
                )
                row = cur.fetchone()
                if row is None:
                    return False
                attempts = row[0]
                if outcome == "SUCCESS":
                    state, error_code, next_run = "DONE", "", now
                elif attempts >= self.max_attempts:
                    state, error_code, next_run = "DEAD", "HANDLER_FAILED", now
                else:
                    state = "PENDING"
                    error_code = "HANDLER_FAILED"
                    delay = min(3600, 5 * (2 ** (attempts - 1)) + self.jitter_seconds)
                    next_run = now + timedelta(seconds=delay)
                cur.execute(
                    """
                    UPDATE gati_t01_worker_spike
                    SET state = %s, error_code = %s, run_after = %s,
                        lease_id = NULL, lease_until = NULL
                    WHERE id = %s
                    """,
                    [state, error_code, next_run, task_id],
                )
                return True

    def run_one(self, now, handlers, lease_seconds=30):
        task = self.claim(now, lease_seconds)
        if task is None:
            return False
        try:
            handler = handlers[task.kind]
            handler(task.resource_id)
        except Exception:
            # Never persist handler exception strings: they may contain secrets.
            self.finish(task.id, task.lease_id, "RETRY", now)
        else:
            self.finish(task.id, task.lease_id, "SUCCESS", now)
        return True
