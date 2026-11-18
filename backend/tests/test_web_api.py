from datetime import date

from django.core import mail
from django.test import Client
from django.utils import timezone

from gati.apps.ativos.models import Ativo
from gati.apps.movimentacoes.models import ProcessoMovimentacao
from gati.apps.usuarios.models import UsuarioTI
from gati.common.registry import RESOURCES


def test_every_catalog_page_and_forms_render(domain, client):
    client.force_login(domain.admin)
    for key in RESOURCES:
        assert client.get(f"/cadastros/{key}/").status_code == 200
        assert client.get(f"/cadastros/{key}/novo/").status_code == 200
    for path in [
        "/",
        "/processos/",
        "/termos/",
        "/usuarios/",
        "/usuarios/novo/",
        "/auditoria/",
        "/configuracoes/",
        "/senha/alterar/",
        "/importar/ativos/",
        "/importar/pessoas/",
        "/internal/metrics/",
    ]:
        assert client.get(path).status_code == 200, path
    for key, obj in [
        ("ativos", domain.asset),
        ("pessoas", domain.person),
        ("modelos-termo", domain.template),
    ]:
        assert client.get(f"/cadastros/{key}/{obj.pk}/").status_code == 200
        assert client.get(f"/cadastros/{key}/{obj.pk}/editar/").status_code == 200


def test_operator_admin_denials_and_masking(domain, client):
    d = domain
    client.force_login(d.operator)
    for path in [
        "/usuarios/",
        "/auditoria/",
        "/configuracoes/",
        "/cadastros/modelos-termo/novo/",
        "/api/v1/logs-auditoria/",
    ]:
        assert client.get(path).status_code == 403, path
    for path in ["/cadastros/pessoas/", f"/cadastros/pessoas/{d.person.pk}/", "/api/v1/pessoas/"]:
        response = client.get(path)
        assert response.status_code == 200
        assert d.person.documento.encode() not in response.content
    client.force_login(d.outsider)
    assert client.get("/api/v1/ativos/").status_code == 403


def test_asset_api_crud_filters_and_conflicts(domain, client):
    d = domain
    client.force_login(d.operator)
    payload = {
        "patrimonio": "API-1",
        "modelo": "API modelo",
        "categoria": d.category.pk,
        "status": d.status.pk,
        "localizacao": d.location.pk,
    }
    response = client.post("/api/v1/ativos/", payload, content_type="application/json")
    assert response.status_code == 201, response.content
    pk = response.json()["id"]
    assert client.get("/api/v1/ativos/?q=API-1").json()["count"] == 1
    assert client.get("/api/v1/ativos/?q=inexistente").json()["count"] == 0
    for query in ["ordering=senha", "inventado=x", "status=bad"]:
        response = client.get("/api/v1/ativos/?" + query)
        assert response.status_code in {400, 409}
        assert response["Content-Type"].startswith("application/problem+json")
    response = client.patch(
        f"/api/v1/ativos/{pk}/", {"modelo": "Editado", "versao": 1}, content_type="application/json"
    )
    assert response.status_code == 200, response.content
    assert (
        client.patch(
            f"/api/v1/ativos/{pk}/", {"modelo": "stale", "versao": 1}, content_type="application/json"
        ).status_code
        == 409
    )
    assert (
        client.patch(
            f"/api/v1/ativos/{pk}/", {"ativo": False, "versao": 2}, content_type="application/json"
        ).status_code
        == 400
    )
    assert client.delete(f"/api/v1/ativos/{pk}/").status_code == 405
    assert client.post(f"/api/v1/ativos/{pk}/inativar/", {"versao": 2}).status_code == 200
    assert client.get("/api/v1/ativos/?situacao=inativos").json()["count"] == 1


def test_security_csrf_logout_password_session_limits(domain):
    d = domain
    client = Client(enforce_csrf_checks=True)
    assert client.post("/entrar/", {"username": "admin", "password": "bad"}).status_code == 403
    client.force_login(d.admin)
    assert client.post("/cadastros/ativos/novo/", {}).status_code == 403
    assert client.get("/sair/").status_code == 405
    session = client.session
    session["auth_started"] = timezone.now().timestamp() - 43201
    session.save()
    assert client.get("/").status_code == 302


def test_login_email_lockout_and_password_reset(domain, client):
    d = domain
    response = client.post("/entrar/", {"username": d.admin.email, "password": "senha sintetica segura 2026"})
    assert response.status_code == 302
    assert client.post("/sair/").status_code == 302
    for _ in range(5):
        assert client.post("/entrar/", {"username": "admin", "password": "invalid"}).status_code == 200
    assert (
        client.post("/entrar/", {"username": "admin", "password": "senha sintetica segura 2026"}).status_code
        == 429
    )
    assert client.post("/senha/recuperar/", {"email": d.admin.email}).status_code == 302
    assert len(mail.outbox) == 1
    assert client.post("/senha/recuperar/", {"email": "unknown@example.invalid"}).status_code == 302
    assert len(mail.outbox) == 1


def test_web_asset_save_and_xss_escaping(domain, client):
    d = domain
    client.force_login(d.operator)
    data = {
        "patrimonio": "WEB-1",
        "service_tag": "WEB-TAG",
        "modelo": "<script>alert(1)</script>",
        "categoria": d.category.pk,
        "status": d.status.pk,
        "localizacao": d.location.pk,
        "versao": 1,
    }
    response = client.post("/cadastros/ativos/novo/", data)
    assert response.status_code == 302, response.content
    asset = Ativo.objects.get(patrimonio="WEB-1")
    response = client.get(f"/cadastros/ativos/{asset.pk}/")
    assert b"<script>alert(1)</script>" not in response.content
    assert b"&lt;script&gt;" in response.content
    assert "frame-ancestors" in response["Content-Security-Policy"]
    assert client.get("/cadastros/ativos/?q=WEB", HTTP_HX_REQUEST="true").status_code == 200


def test_seven_step_wizard_and_term_views(domain, client):
    d = domain
    client.force_login(d.operator)
    steps = [
        {"tipo": "ENTREGA", "localizacao": d.destination.pk, "data": date.today().isoformat()},
        {"responsavel": d.person.pk},
        {"ativos": [d.asset.pk], "acessorios": "Carregador"},
        {f"condicoes_{d.asset.pk}": "Sem avaria", "observacoes": "Conferido"},
        {"modelo": d.template.pk, "texto": ""},
        {"metodo": "PRESENCIAL", "testemunhas": [], "metodo_testemunhas": "PRESENCIAL"},
        {"confirmar": "on", "action": "draft"},
    ]
    for index, data in enumerate(steps, 1):
        assert client.get(f"/processos/novo/{index}/").status_code == 200
        response = client.post(f"/processos/novo/{index}/", data)
        assert response.status_code == 302, (index, response.content)
    process = ProcessoMovimentacao.objects.get()
    term = process.termos.get()
    for path in [
        f"/processos/{process.pk}/",
        f"/termos/{term.pk}/",
        f"/termos/{term.pk}/editar/",
        f"/termos/{term.pk}/itens/",
        f"/termos/{term.pk}/emitir/",
    ]:
        assert client.get(path).status_code == 200, path
    assert (
        client.post(f"/termos/{term.pk}/editar/", {"texto": "Texto revisado", "versao": 1}).status_code == 302
    )
    assert client.post(f"/termos/{term.pk}/emitir/").status_code == 302
    assert client.get(f"/termos/{term.pk}/").status_code == 200


def test_api_process_term_actions(domain, client):
    d = domain
    client.force_login(d.operator)
    data = {
        "tipo": "ENTREGA",
        "responsavel": d.person.pk,
        "localizacao": d.destination.pk,
        "data": date.today().isoformat(),
        "modelo": d.template.pk,
        "itens": [{"ativo": d.asset.pk, "condicoes": "Conferido"}],
        "signatarios": [{"pessoa": d.person.pk, "papel": "RESPONSAVEL", "metodo": "PRESENCIAL"}],
    }
    response = client.post("/api/v1/processos-movimentacao/", data, content_type="application/json")
    assert response.status_code == 201, response.content
    p = ProcessoMovimentacao.objects.get(pk=response.json()["id"])
    t = p.termos.get()
    assert (
        client.patch(
            f"/api/v1/termos/{t.pk}/", {"texto": "Texto da API", "versao": 1}, content_type="application/json"
        ).status_code
        == 200
    )
    assert client.post(f"/api/v1/termos/{t.pk}/emitir-para-assinatura/").status_code == 200
    assert client.post(f"/api/v1/processos-movimentacao/{p.pk}/concluir/").status_code == 409
    assert (
        client.post(f"/api/v1/termos/{t.pk}/cancelar/", {"motivo": "Teste de cancelamento"}).status_code
        == 403
    )
    client.force_login(d.admin)
    assert (
        client.post(f"/api/v1/termos/{t.pk}/cancelar/", {"motivo": "Teste de cancelamento"}).status_code
        == 200
    )


def test_admin_user_management(domain, client):
    d = domain
    client.force_login(d.admin)
    response = client.post(
        "/usuarios/novo/",
        {
            "username": "novo",
            "email": "novo@example.invalid",
            "first_name": "Novo",
            "last_name": "Usuário",
            "perfil": "Operador",
            "senha": "senha sintetica longa 12345",
            "is_active": "on",
        },
    )
    assert response.status_code == 302, response.content
    user = UsuarioTI.objects.get(username="novo")
    assert not user.is_superuser and user.groups.get().name == "Operador"
    response = client.post(
        f"/usuarios/{d.admin.pk}/",
        {
            "username": "admin",
            "email": d.admin.email,
            "first_name": "Admin",
            "perfil": "Operador",
            "is_active": "on",
        },
    )
    assert response.status_code == 200 and "próprio acesso" in response.content.decode()


def test_health_and_schema_access(domain, client):
    assert client.get("/health/live/").status_code == 200
    assert client.get("/health/ready/").status_code == 200
    assert client.get("/api/v1/schema/").status_code == 403
    client.force_login(domain.admin)
    assert client.get("/api/v1/schema/").status_code == 200
