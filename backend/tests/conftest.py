from datetime import date
from types import SimpleNamespace

import pytest
from django.contrib.auth.models import Group
from django.core.management import call_command

from gati.apps.ativos.models import Ativo
from gati.apps.cadastros.models import CategoriaAtivo, Departamento, Localizacao, StatusAtivo
from gati.apps.movimentacoes.services import create_process
from gati.apps.pessoas.models import Pessoa
from gati.apps.termos.models import ModeloTermo
from gati.apps.termos.services import accept, confirm_identity, exchange_token, invitation, issue
from gati.apps.usuarios.models import UsuarioTI
from gati.common.catalog import save_record


@pytest.fixture
def domain(db, settings, tmp_path):
    settings.RUNTIME = tmp_path
    call_command("bootstrap_gati", verbosity=0)
    users = {}
    for name, role in [("admin", "Administrador"), ("operator", "Operador"), ("outsider", None)]:
        user = UsuarioTI.objects.create_user(
            username=name, email=f"{name}@example.invalid", password="senha sintetica segura 2026"
        )
        if role:
            user.groups.set([Group.objects.get(name=role)])
        users[name] = user
    category = CategoriaAtivo.objects.create(nome="Notebook")
    location = Localizacao.objects.create(nome="Estoque TI")
    destination = Localizacao.objects.create(nome="Escritório")
    department = Departamento.objects.create(nome="TI")
    person = save_record(
        users["operator"],
        Pessoa,
        {
            "nome": "Pessoa Sintética",
            "documento": "90000000123",
            "departamento": department,
            "cargo": "Analista",
            "email": "pessoa@example.invalid",
        },
    )
    witness = save_record(
        users["operator"],
        Pessoa,
        {
            "nome": "Testemunha Sintética",
            "documento": "90000000456",
            "departamento": department,
            "cargo": "Analista",
            "email": "testemunha@example.invalid",
        },
    )
    status = StatusAtivo.objects.get(codigo="EM_ESTOQUE")
    data = {
        "patrimonio": "TI-001",
        "service_tag": "DEMO-001",
        "modelo": "Modelo de teste",
        "categoria": category,
        "status": status,
        "localizacao": location,
    }
    asset = save_record(users["operator"], Ativo, data)
    template = save_record(
        users["admin"],
        ModeloTermo,
        {
            "nome": "Padrão",
            "texto": "{{ tipo }} para {{ responsavel_nome }}, {{ responsavel_documento }}: {{ ativos }} em {{ data }}.",
        },
    )
    return SimpleNamespace(
        **users,
        category=category,
        location=location,
        destination=destination,
        department=department,
        person=person,
        witness=witness,
        status=status,
        asset=asset,
        template=template,
        asset_data=data,
    )


def process_for(d, kind="ENTREGA", avaria=False, witness=False, method="PRESENCIAL", asset=None):
    signers = [{"pessoa": d.person, "papel": "RESPONSAVEL", "metodo": method}]
    if witness:
        signers.append({"pessoa": d.witness, "papel": "TESTEMUNHA", "metodo": method})
    return create_process(
        d.operator,
        {
            "tipo": kind,
            "responsavel": d.person,
            "localizacao": d.destination if kind == "ENTREGA" else d.location,
            "data": date.today(),
        },
        [
            {
                "ativo": asset or d.asset,
                "condicoes": "Conferido presencialmente",
                "avaria": avaria,
                "divergencias": "Tela danificada" if avaria else "",
            }
        ],
        d.template,
        signers,
    )


def sign_all(d, process):
    term = issue(d.operator, process.termos.first())
    for signature in term.assinaturas.all():
        raw = invitation(d.operator, signature)
        secret = exchange_token(raw)
        confirm_identity(secret, signature.snapshot["documento"][-4:])
        accept(secret, "127.0.0.1", "Synthetic test agent")
    return term
