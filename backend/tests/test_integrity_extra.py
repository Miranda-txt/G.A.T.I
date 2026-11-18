from concurrent.futures import ThreadPoolExecutor
from datetime import date
from threading import Barrier
from unittest.mock import MagicMock, patch

import pytest
from conftest import process_for, sign_all
from django.core.exceptions import ValidationError
from django.db import connection, connections

from gati.apps.ativos.models import Ativo
from gati.apps.movimentacoes.models import ResponsabilidadeAtivo
from gati.apps.movimentacoes.services import edit_process
from gati.apps.termos.services import (
    accept,
    cancel,
    confirm_identity,
    edit_draft,
    exchange_token,
    invitation,
    issue,
    replace_cancelled,
)
from gati.common.catalog import save_record
from gati.common.clamav import scan
from gati.common.errors import Conflict, ScannerUnavailable


def test_correction_preserves_completed_movement(domain, client):
    d = domain
    process = process_for(d)
    sign_all(d, process)
    term = process.termos.get()
    old_hash = term.sha256
    events = d.asset.historico.count()
    cancel(d.admin, term, "Correção documental solicitada pelo responsável")
    replacement = replace_cancelled(d.admin, term)
    with pytest.raises(Conflict):
        replace_cancelled(d.admin, term)
    replacement = edit_draft(d.operator, replacement, "Texto corrigido e conferido", replacement.versao)
    issue(d.operator, replacement)
    signer = replacement.assinaturas.get()
    secret = exchange_token(invitation(d.operator, signer))
    confirm_identity(secret, "0123")
    accept(secret, "127.0.0.1", "Teste sintético")
    term.refresh_from_db()
    replacement.refresh_from_db()
    assert term.estado == "CANCELADO" and term.sha256 == old_hash
    assert replacement.estado == "ASSINADO" and replacement.sha256 != old_hash
    assert d.asset.historico.count() == events
    assert ResponsabilidadeAtivo.objects.count() == 1
    client.force_login(d.admin)
    assert client.get(f"/termos/{term.pk}/").status_code == 200
    assert client.get(f"/termos/{replacement.pk}/").status_code == 200


def test_cancelled_draft_replacement_and_context_edit(domain, client):
    d = domain
    process = process_for(d)
    term = process.termos.get()
    with pytest.raises(Conflict):
        replace_cancelled(d.admin, term)
    with pytest.raises(Conflict):
        edit_process(d.operator, process, {"observacoes": "Novas"}, 0)
    with pytest.raises(ValidationError):
        edit_process(d.operator, process, {"tipo": "DEVOLUCAO"}, 1)
    client.force_login(d.operator)
    assert client.get(f"/processos/{process.pk}/editar/").status_code == 200
    response = client.patch(
        f"/api/v1/processos-movimentacao/{process.pk}/",
        {"observacoes": "Novo contexto", "versao": 1},
        content_type="application/json",
    )
    assert response.status_code == 200, response.content
    response = client.post(
        f"/processos/{process.pk}/editar/",
        {"data": date.today().isoformat(), "localizacao": d.location.pk, "versao": 2},
    )
    assert response.status_code == 302, response.content
    term.refresh_from_db()
    issue(d.operator, term)
    with pytest.raises(Conflict):
        save_record(d.operator, Ativo, {"modelo": "Outro"}, d.asset.pk, d.asset.versao)
    cancel(d.admin, term, "Dados precisam de nova conferência")
    client.force_login(d.admin)
    response = client.post("/api/v1/termos/", {"substitui": term.pk}, content_type="application/json")
    assert response.status_code == 201, response.content
    assert response.json()["processo"] != process.pk
    assert response.json()["substitui"] == term.pk


def test_issued_process_completes_when_creator_deactivated(domain):
    d = domain
    process = process_for(d)
    term = issue(d.admin, process.termos.get())
    signature = term.assinaturas.get()
    secret = exchange_token(invitation(d.admin, signature))
    confirm_identity(secret, "0123")
    d.operator.is_active = False
    d.operator.save()
    accept(secret, "127.0.0.1", "Teste")
    process.refresh_from_db()
    assert process.estado == "CONCLUIDO"


@pytest.mark.django_db(transaction=True)
def test_concurrent_accept_is_idempotent(domain):
    d = domain
    process = process_for(d)
    term = issue(d.operator, process.termos.get())
    secret = exchange_token(invitation(d.operator, term.assinaturas.get()))
    confirm_identity(secret, "0123")
    barrier = Barrier(2)

    def submit():
        try:
            with connection.cursor() as cursor:
                cursor.execute("SET lock_timeout = '5s'")
            barrier.wait(timeout=10)
            return accept(secret, "127.0.0.1", "Teste concorrente").pk
        finally:
            connections.close_all()

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda _: submit(), range(2)))
    assert len(set(results)) == 1
    assert ResponsabilidadeAtivo.objects.count() == 1
    assert d.asset.historico.filter(tipo="ENTREGA").count() == 1


@pytest.mark.parametrize(
    "reply,error",
    [
        (b"stream: OK\0", None),
        (b"stream: Eicar-Signature FOUND\0", ValidationError),
        (b"stream: UNKNOWN\0", ScannerUnavailable),
        (b"", ScannerUnavailable),
    ],
)
def test_clamav_stream_protocol(tmp_path, reply, error):
    path = tmp_path / "sample.bin"
    path.write_bytes(b"synthetic sample")
    conn = MagicMock()
    conn.recv.side_effect = [reply, b""]
    with patch("gati.common.clamav.socket.create_connection") as create:
        create.return_value.__enter__.return_value = conn
        if error:
            with pytest.raises(error):
                scan(path)
        else:
            scan(path)
        assert conn.sendall.call_args_list[0].args[0] == b"zINSTREAM\0"
        assert conn.sendall.call_args_list[-1].args[0] == b"\0\0\0\0"


def test_clamav_connection_error(tmp_path):
    with patch("gati.common.clamav.socket.create_connection", side_effect=OSError("offline")):
        with pytest.raises(ScannerUnavailable):
            scan(tmp_path / "sample")


def test_password_reset_rate_limit_and_referrer(domain, client, mailoutbox):
    assert client.get("/entrar/")["Referrer-Policy"] == "same-origin"
    for _ in range(4):
        assert client.post("/senha/recuperar/", {"email": domain.admin.email}).status_code == 302
    assert len(mailoutbox) == 3


def test_api_items_edit_frozen_and_unknown_fields(domain, client):
    d = domain
    term = process_for(d).termos.get()
    client.force_login(d.operator)
    path = f"/api/v1/termos/{term.pk}/itens/"
    data = {
        "itens": [{"ativo": d.asset.pk, "condicoes": "Conferência revista"}],
        "signatarios": [{"pessoa": d.person.pk, "metodo": "PRESENCIAL", "papel": "RESPONSAVEL"}],
        "versao": 1,
    }
    assert client.patch(path, data, content_type="application/json").status_code == 200
    issue(d.operator, term)
    data["versao"] = 2
    assert client.patch(path, data, content_type="application/json").status_code == 409
    assert (
        client.post("/api/v1/termos/", {"texto": "Inválido"}, content_type="application/json").status_code
        == 400
    )


def test_invalid_versions_are_controlled_errors(domain, client):
    d = domain
    term = process_for(d).termos.get()
    client.force_login(d.operator)
    for path, data, method in [
        (f"/api/v1/termos/{term.pk}/", {"texto": "Novo texto", "versao": "invalida"}, "patch"),
        (f"/api/v1/ativos/{d.asset.pk}/inativar/", {"versao": "invalida"}, "post"),
        (f"/api/v1/termos/{term.pk}/cancelar/", {"motivo": {"sql": "qualquer"}}, "post"),
    ]:
        response = getattr(client, method)(path, data, content_type="application/json")
        assert response.status_code == 400
        assert response["Content-Type"].startswith("application/problem+json")
    with pytest.raises(ValidationError):
        edit_draft(d.operator, term, "Texto", "invalida")
