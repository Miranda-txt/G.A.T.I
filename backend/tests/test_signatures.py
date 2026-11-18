from datetime import timedelta

import pytest
from conftest import process_for
from django.core import mail
from django.db import IntegrityError, connection, transaction
from django.utils import timezone

from gati.apps.movimentacoes.models import ResponsabilidadeAtivo
from gati.apps.termos.models import SessaoAssinatura
from gati.apps.termos.services import (
    accept,
    confirm_identity,
    exchange_token,
    get_session,
    invitation,
    issue,
    send_invitation,
)
from gati.common.errors import Conflict


def invited(d, witness=False, method="PRESENCIAL"):
    p = process_for(d, witness=witness, method=method)
    t = issue(d.operator, p.termos.first())
    s = t.assinaturas.first()
    raw = invitation(d.operator, s)
    secret = exchange_token(raw)
    return t, s, raw, secret


def test_token_one_time_and_identity_gate(domain):
    t, s, raw, secret = invited(domain)
    s.refresh_from_db()
    assert not s.token_hash and raw not in str(s.__dict__)
    with pytest.raises(Conflict):
        exchange_token(raw)
    with pytest.raises(Conflict):
        accept(secret, "127.0.0.1", "test")
    confirm_identity(secret, "0123")
    first = accept(secret, "127.0.0.1", "test")
    again = accept(secret, "127.0.0.1", "test")
    assert first.pk == again.pk and first.assinado_em == again.assinado_em
    assert ResponsabilidadeAtivo.objects.count() == 1


def test_five_attempts_persist_and_reinvite_revokes(domain):
    t, s, raw, secret = invited(domain)
    for _ in range(5):
        with pytest.raises(Conflict):
            confirm_identity(secret, "9999")
    s.refresh_from_db()
    assert s.tentativas == 5
    with pytest.raises(Conflict):
        get_session(secret)
    raw = invitation(domain.operator, s)
    new_secret = exchange_token(raw)
    confirm_identity(new_secret, "0123")
    with pytest.raises(Conflict):
        get_session(secret)


def test_all_signers_required_and_evidence_immutable(domain):
    t, s, raw, secret = invited(domain, witness=True)
    confirm_identity(secret, "0123")
    accept(secret, "127.0.0.1", "agent")
    t.refresh_from_db()
    assert t.estado == "AGUARDANDO_ASSINATURAS"
    assert not ResponsabilidadeAtivo.objects.exists()
    with pytest.raises(IntegrityError), transaction.atomic(), connection.cursor() as cursor:
        cursor.execute("UPDATE termos_assinaturatermo SET user_agent=%s WHERE id=%s", ["alteração", s.pk])


def test_session_expiry(domain):
    _, s, _, secret = invited(domain)
    SessaoAssinatura.objects.filter(assinatura=s).update(vista_em=timezone.now() - timedelta(minutes=31))
    with pytest.raises(Conflict):
        get_session(secret)


def test_email_templates_token_fragment_and_failure(domain, monkeypatch):
    d = domain
    p = process_for(d, method="EMAIL")
    t = issue(d.operator, p.termos.first())
    s = t.assinaturas.first()
    send_invitation(d.operator, s)
    assert len(mail.outbox) == 1 and "/assinar/iniciar/#" in mail.outbox[0].body
    assert d.person.documento not in mail.outbox[0].body
    assert mail.outbox[0].alternatives
    monkeypatch.setattr(
        "django.core.mail.EmailMultiAlternatives.send", lambda *a, **k: (_ for _ in ()).throw(OSError())
    )
    with pytest.raises(Conflict):
        send_invitation(d.operator, s)
    t.refresh_from_db()
    assert t.estado == "AGUARDANDO_ASSINATURAS"


def test_presential_logs_out_and_no_get_accept(domain, client):
    d = domain
    p = process_for(d)
    t = issue(d.operator, p.termos.first())
    s = t.assinaturas.first()
    client.force_login(d.operator)
    response = client.post(f"/assinaturas/{s.pk}/presencial/")
    assert response.status_code == 302
    assert "_auth_user_id" not in client.session
    assert response.cookies["gati_assinatura"]["httponly"]
    assert response.cookies["gati_assinatura"]["path"] == "/assinar/"
    assert client.get("/assinar/aceitar/").status_code == 405
    response = client.get("/assinar/")
    assert t.texto.encode() not in response.content
    assert client.post("/assinar/confirmar-identidade/", {"last4": "0123"}).status_code == 302
    assert client.post("/assinar/aceitar/", {"aceito": "yes"}).status_code == 302
    assert "Aceite registrado" in client.get("/assinar/").content.decode()
