"""Pure outbox identity, time and retry policy; no database or I/O."""

import re
from datetime import datetime, timedelta
from uuid import UUID

KINDS = ("EMISSAO", "PDF_FINAL", "NOTIFICACAO", "RECONCILIACAO")


def _canonical_uuid(value):
    if not isinstance(value, str) or len(value) != 36:
        return False
    try:
        return str(UUID(value)) == value
    except ValueError:
        return False


def _resource_id(value):
    if not isinstance(value, str):
        return False
    if _canonical_uuid(value):
        return True
    return bool(re.fullmatch(r"[1-9][0-9]{0,18}", value)) and int(value) <= 2**63 - 1


def dedupe_key(kind, resource_id, event_id):
    """Use a server-generated, stable event UUID; never accept free-form keys."""
    if kind not in KINDS or not _resource_id(resource_id) or type(event_id) is not UUID:
        raise ValueError("identidade de tarefa invalida")
    return f"{kind}:{resource_id}:{event_id}"


def validate_identity(kind, resource_id, key):
    if kind not in KINDS or not _resource_id(resource_id):
        raise ValueError("identidade de tarefa invalida")
    if not isinstance(key, str) or len(key) > 128:
        raise ValueError("chave de deduplicacao invalida")
    prefix = f"{kind}:{resource_id}:"
    if not key.startswith(prefix) or not _canonical_uuid(key[len(prefix) :]):
        raise ValueError("chave de deduplicacao invalida")
    return kind, resource_id, key


def aware_time(value):
    if not isinstance(value, datetime) or value.utcoffset() is None:
        raise ValueError("data com fuso obrigatoria")
    return value


def lease_duration(value):
    if type(value) is not int or not 1 <= value <= 3600:
        raise ValueError("duracao de lease invalida")
    return value


def attempt_cap(value):
    if type(value) is not int or not 1 <= value <= 10:
        raise ValueError("limite de tentativas invalido")
    return value


def finish_values(attempts, outcome, now, max_attempts, jitter_seconds):
    aware_time(now)
    attempt_cap(max_attempts)
    if type(attempts) is not int or not 1 <= attempts <= 10:
        raise ValueError("tentativa invalida")
    if type(jitter_seconds) is not int or not 0 <= jitter_seconds <= 5:
        raise ValueError("jitter invalido")
    if outcome == "SUCCESS":
        return "CONCLUIDA", "", now
    if outcome == "UNCERTAIN":
        return "FALHA", "OUTCOME_UNCERTAIN", now
    if outcome != "RETRY":
        raise ValueError("resultado invalido")
    if attempts >= max_attempts:
        return "FALHA", "HANDLER_FAILED", now
    delay = min(3600, 5 * 2 ** (attempts - 1) + jitter_seconds)
    return "PENDENTE", "HANDLER_FAILED", now + timedelta(seconds=delay)
