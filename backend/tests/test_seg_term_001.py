"""Regression coverage for SEG-TERM-001 (requires a dedicated pytest database)."""

import pytest
from conftest import process_for
from django.db import IntegrityError, connection, transaction

from gati.apps.termos.services import accept, confirm_identity, exchange_token, invitation, issue


@pytest.mark.django_db
def test_seg_term_001_rejects_signed_without_signers(domain):
    process = process_for(domain)
    term = process.termos.get()
    # A draft may have its signers edited; ensure the empty-set case is covered.
    term.assinaturas.all().delete()
    with pytest.raises(IntegrityError):
        with transaction.atomic(), connection.cursor() as cursor:
            cursor.execute("UPDATE termos_termo SET estado='ASSINADO' WHERE id=%s", [term.pk])
    term.refresh_from_db()
    assert term.estado == "EM_EDICAO"
    assert not term.assinaturas.exists()


@pytest.mark.django_db
def test_seg_term_001_keeps_valid_signature_workflow(domain):
    process = process_for(domain)
    term = issue(domain.operator, process.termos.get())
    assert term.estado == "AGUARDANDO_ASSINATURAS"
    signer = term.assinaturas.get()
    raw = invitation(domain.operator, signer)
    secret = exchange_token(raw)
    confirm_identity(secret, signer.snapshot["documento"][-4:])
    accept(secret, "127.0.0.1", "SEG-TERM-001 regression")
    term.refresh_from_db()
    assert term.estado == "ASSINADO"
