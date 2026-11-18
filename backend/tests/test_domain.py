import hashlib
import json
from datetime import date, timedelta

import pytest
from conftest import process_for, sign_all
from django.contrib.auth.models import AnonymousUser, Group
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import IntegrityError, connection, transaction

from gati.apps.ativos.models import Ativo
from gati.apps.auditoria.models import LogAuditoria
from gati.apps.cadastros.models import StatusAtivo
from gati.apps.movimentacoes.models import Movimentacao, ResponsabilidadeAtivo
from gati.apps.movimentacoes.services import complete_process, correct_history
from gati.apps.termos.models import ModeloTermo
from gati.apps.termos.services import cancel, edit_draft, edit_items, issue
from gati.common.catalog import deidentify, inactivate, save_record
from gati.common.errors import Conflict


def test_inventory_uniqueness_and_inactivation(domain):
    d = domain
    with pytest.raises(ValidationError):
        save_record(d.operator, Ativo, {**d.asset_data, "patrimonio": "ti-001", "service_tag": "OTHER"})
    with pytest.raises(ValidationError):
        save_record(d.operator, Ativo, {**d.asset_data, "patrimonio": "OTHER", "service_tag": "demo-001"})
    inactivate(d.operator, d.asset)
    new = save_record(d.operator, Ativo, d.asset_data)
    assert new.pk != d.asset.pk
    assert Movimentacao.objects.filter(ativo=d.asset, tipo="INATIVACAO").exists()


@pytest.mark.parametrize("role", ["outsider", "anonymous", "multiple"])
def test_default_deny_services(domain, role):
    d = domain
    user = d.outsider
    if role == "anonymous":
        user = AnonymousUser()
    if role == "multiple":
        user = d.admin
        user.groups.add(Group.objects.get(name="Operador"))
    with pytest.raises(PermissionDenied):
        save_record(user, Ativo, d.asset_data)


def test_optimistic_lock_and_audit_history(domain):
    d = domain
    obj = save_record(d.operator, Ativo, {"localizacao": d.destination}, d.asset.pk, 1)
    assert obj.versao == 2
    with pytest.raises(Conflict):
        save_record(d.operator, Ativo, {"modelo": "stale"}, obj.pk, 1)
    assert obj.historico.count() == 2
    assert LogAuditoria.objects.filter(acao="EDITAR", objeto_id=str(obj.pk)).exists()
    correct_history(d.operator, obj, "Retificação explicativa do evento original.")
    assert obj.historico.first().tipo == "RETIFICACAO"


def test_template_rbac_tags_and_snapshot(domain):
    d = domain
    with pytest.raises(PermissionDenied):
        save_record(d.operator, ModeloTermo, {"nome": "Novo", "texto": "texto"})
    with pytest.raises(PermissionDenied):
        inactivate(d.operator, d.template)
    with pytest.raises(ValidationError):
        save_record(d.admin, ModeloTermo, {"nome": "Inválido", "texto": "{{ request.secret }}"})
    process = process_for(d)
    term = issue(d.operator, process.termos.first())
    save_record(d.operator, ModeloTermo, {"texto": "Novo texto"}, d.template.pk, d.template.versao)
    term.refresh_from_db()
    assert "Novo texto" not in term.texto
    canonical = json.dumps(term.payload, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    assert term.sha256 == hashlib.sha256(canonical.encode()).hexdigest()


@pytest.mark.parametrize("avaria,expected", [(False, "EM_ESTOQUE"), (True, "EM_MANUTENCAO")])
def test_delivery_return_signed(domain, avaria, expected):
    d = domain
    delivery = process_for(d, witness=True)
    issue(d.operator, delivery.termos.first())
    assert not ResponsabilidadeAtivo.objects.exists()
    with pytest.raises(Conflict):
        complete_process(d.operator, delivery)
    sign_all(d, delivery)
    d.asset.refresh_from_db()
    delivery.refresh_from_db()
    assert delivery.estado == "CONCLUIDO" and d.asset.status.codigo == "EM_USO"
    assert ResponsabilidadeAtivo.objects.filter(ativo=d.asset, fim__isnull=True).count() == 1
    with pytest.raises(Conflict):
        inactivate(d.operator, d.asset)
    with pytest.raises(Conflict):
        inactivate(d.operator, d.person)
    returned = process_for(d, "DEVOLUCAO", avaria=avaria)
    sign_all(d, returned)
    d.asset.refresh_from_db()
    assert d.asset.status.codigo == expected
    assert not ResponsabilidadeAtivo.objects.filter(fim__isnull=True).exists()
    complete_process(d.operator, returned)
    assert d.asset.historico.filter(tipo="DEVOLUCAO").count() == 1


def test_pending_reservation_and_cancel(domain):
    d = domain
    p1 = process_for(d)
    p2 = process_for(d)
    t1 = issue(d.operator, p1.termos.first())
    with pytest.raises(Conflict):
        issue(d.operator, p2.termos.first())
    with pytest.raises(PermissionDenied):
        cancel(d.operator, t1, "Cancelamento autorizado para revisão")
    cancel(d.admin, t1, "Cancelamento autorizado para revisão")
    issue(d.operator, p2.termos.first())
    p1.refresh_from_db()
    assert p1.estado == "CANCELADO"


def test_edit_draft_and_items(domain):
    d = domain
    p = process_for(d)
    t = p.termos.first()
    edit_draft(d.operator, t, "Termo personalizado para {{ responsavel_nome }}.", 1)
    t.refresh_from_db()
    edit_items(
        d.operator,
        t,
        [{"ativo": d.asset, "condicoes": "Revisado"}],
        [{"pessoa": d.person, "papel": "RESPONSAVEL", "metodo": "PRESENCIAL"}],
        t.versao,
    )
    t.refresh_from_db()
    assert p.itens.get().condicoes == "Revisado"
    issue(d.operator, t)
    with pytest.raises(Conflict):
        edit_draft(d.operator, t, "alteração proibida", t.versao)


@pytest.mark.parametrize(
    "table,field,value",
    [
        ("termos_termo", "texto", "alterado"),
        ("termos_termoitem", "snapshot", "{}"),
        ("termos_assinaturatermo", "papel", "TESTEMUNHA"),
        ("movimentacoes_processoitem", "condicoes", "alterada"),
        ("movimentacoes_processomovimentacao", "observacoes", "alterada"),
    ],
)
def test_frozen_database_guards(domain, table, field, value):
    d = domain
    p = process_for(d)
    issue(d.operator, p.termos.first())
    with pytest.raises(IntegrityError), transaction.atomic(), connection.cursor() as cursor:
        cursor.execute(f"UPDATE {table} SET {field}=%s", [value])


@pytest.mark.parametrize("model", [LogAuditoria, Movimentacao])
def test_append_only_orm_sql(domain, model):
    obj = model.objects.first()
    with pytest.raises(ValidationError):
        obj.delete()
    with pytest.raises(ValidationError):
        obj.save()
    with pytest.raises(ValidationError):
        model.objects.all().delete()
    with pytest.raises(IntegrityError), transaction.atomic(), connection.cursor() as cursor:
        cursor.execute(f"DELETE FROM {model._meta.db_table} WHERE id=%s", [obj.pk])


def test_privacy_guards(domain):
    d = domain
    p = process_for(d)
    with pytest.raises(Conflict):
        deidentify(d.admin, d.person, "Análise formal de finalidade encerrada.")
    cancel(d.admin, p.termos.first(), "Processo criado apenas para teste")
    result = deidentify(d.admin, d.person, "Análise formal de finalidade encerrada.")
    assert result.documento is None and not result.ativo and not result.email
    assert result.desidentificada_em


def test_maintenance_dates_and_catalog_references(domain):
    from gati.apps.manutencoes.models import Manutencao

    d = domain
    with pytest.raises(ValidationError):
        save_record(
            d.operator,
            Manutencao,
            {
                "ativo": d.asset,
                "fornecedor": "Oficina sintética",
                "defeito": "Teste",
                "data_inicio": date.today(),
                "data_fim": date.today() - timedelta(days=1),
            },
        )
    with pytest.raises(PermissionDenied):
        save_record(d.operator, StatusAtivo, {"nome": "Outro", "codigo": "OUTRO"})
    with pytest.raises(Conflict):
        inactivate(d.admin, d.status)
    with pytest.raises(Conflict):
        inactivate(d.admin, d.category)
