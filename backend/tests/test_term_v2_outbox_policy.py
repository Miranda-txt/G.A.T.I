"""Pure policy tests: do not require Django or an active database."""

import importlib.util
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import UUID

import pytest

POLICY = Path(__file__).resolve().parents[1] / "gati/apps/termos/services/outbox_policy.py"
NOW = datetime(2026, 11, 28, 12, tzinfo=UTC)
RESOURCE = "42"
EVENT = "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"


def policy():
    assert POLICY.is_file(), "T02 outbox policy has not been implemented"
    spec = importlib.util.spec_from_file_location("outbox_policy", POLICY)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize("kind", ["EMISSAO", "PDF_FINAL", "NOTIFICACAO", "RECONCILIACAO"])
def test_canonical_identity(kind):
    module = policy()
    key = module.dedupe_key(kind, RESOURCE, UUID(EVENT))
    assert module.validate_identity(kind, RESOURCE, key) == (kind, RESOURCE, key)
    assert key == f"{kind}:{RESOURCE}:{EVENT}"


@pytest.mark.parametrize(
    "kind,resource,key",
    [
        ("UNKNOWN", RESOURCE, f"UNKNOWN:{RESOURCE}:{EVENT}"),
        ("EMISSAO", "email@example.invalid", f"EMISSAO:email@example.invalid:{EVENT}"),
        ("EMISSAO", "01", f"EMISSAO:01:{EVENT}"),
        ("EMISSAO", "0", f"EMISSAO:0:{EVENT}"),
        ("EMISSAO", "9223372036854775808", f"EMISSAO:9223372036854775808:{EVENT}"),
        ("EMISSAO", RESOURCE, "secret=not-for-storage"),
        ("EMISSAO", RESOURCE, f"PDF_FINAL:{RESOURCE}:{EVENT}"),
        ("EMISSAO", RESOURCE, f"EMISSAO:43:{EVENT}"),
        ("EMISSAO", RESOURCE, "EMISSAO:42:token"),
    ],
)
def test_invalid_identity_is_rejected(kind, resource, key):
    with pytest.raises(ValueError, match="identidade|deduplicacao"):
        policy().validate_identity(kind, resource, key)


def test_accepts_uuid_resource():
    module = policy()
    key = module.dedupe_key("EMISSAO", EVENT, UUID(EVENT))
    assert module.validate_identity("EMISSAO", EVENT, key)[1] == EVENT


@pytest.mark.parametrize("value", [None, "2026-11-28", datetime(2026, 11, 28)])
def test_rejects_naive_or_invalid_clock(value):
    with pytest.raises(ValueError, match="data"):
        policy().aware_time(value)


@pytest.mark.parametrize("value", [0, 3601, True, "30"])
def test_rejects_invalid_lease(value):
    with pytest.raises(ValueError, match="lease"):
        policy().lease_duration(value)


def test_retry_is_exponential_bounded_and_sanitized():
    module = policy()
    assert module.finish_values(1, "RETRY", NOW, 3, 2) == (
        "PENDENTE",
        "HANDLER_FAILED",
        NOW + timedelta(seconds=7),
    )
    assert module.finish_values(2, "RETRY", NOW, 3, 0) == (
        "PENDENTE",
        "HANDLER_FAILED",
        NOW + timedelta(seconds=10),
    )
    assert module.finish_values(3, "RETRY", NOW, 3, 0) == ("FALHA", "HANDLER_FAILED", NOW)
    assert module.finish_values(3, "SUCCESS", NOW, 3, 0) == ("CONCLUIDA", "", NOW)
    assert module.finish_values(2, "UNCERTAIN", NOW, 3, 0) == ("FALHA", "OUTCOME_UNCERTAIN", NOW)


@pytest.mark.parametrize(
    "attempts,outcome,cap,jitter",
    [(0, "RETRY", 3, 0), (1, "secret", 3, 0), (1, "RETRY", 0, 0), (1, "RETRY", 3, 6), (True, "RETRY", 3, 0)],
)
def test_invalid_outcomes_are_rejected(attempts, outcome, cap, jitter):
    with pytest.raises(ValueError):
        policy().finish_values(attempts, outcome, NOW, cap, jitter)


@pytest.mark.parametrize(
    "state,actual,deadline,expected,now,want",
    [
        ("PROCESSANDO", EVENT, NOW + timedelta(seconds=1), EVENT, NOW, True),
        ("PROCESSANDO", EVENT, NOW, EVENT, NOW, False),
        ("PROCESSANDO", EVENT, NOW - timedelta(seconds=1), EVENT, NOW, False),
        ("PROCESSANDO", EVENT, None, EVENT, NOW, False),
        (
            "PROCESSANDO",
            "bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb",
            NOW + timedelta(seconds=1),
            EVENT,
            NOW,
            False,
        ),
        ("PENDENTE", EVENT, NOW + timedelta(seconds=1), EVENT, NOW, False),
    ],
)
def test_current_lease_requires_matching_live_owner(state, actual, deadline, expected, now, want):
    assert policy().lease_is_current(state, UUID(actual), deadline, UUID(expected), now) is want
