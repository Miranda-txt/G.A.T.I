from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from gati.apps.auditoria.services import audit
from gati.apps.usuarios.permissions import authorize
from gati.common.errors import Conflict

FIELDS = {
    "cadastros.departamento": ["nome"],
    "cadastros.categoriaativo": ["nome", "multiplos_responsaveis"],
    "cadastros.localizacao": ["nome", "descricao"],
    "cadastros.statusativo": ["nome", "codigo"],
    "pessoas.pessoa": ["nome", "documento", "departamento", "cargo", "email"],
    "ativos.ativo": [
        "patrimonio",
        "service_tag",
        "numero_serie",
        "categoria",
        "fabricante",
        "modelo",
        "localizacao",
        "status",
        "data_aquisicao",
        "valor_aquisicao",
        "nota_fiscal",
        "garantia_fim",
        "observacoes",
    ],
    "manutencoes.manutencao": [
        "ativo",
        "data_inicio",
        "data_fim",
        "fornecedor",
        "nota_fiscal",
        "defeito",
        "servico",
        "custo",
        "em_garantia",
    ],
    "termos.modelotermo": ["nome", "texto"],
}


def check_references(obj):
    for field in obj._meta.fields:
        if field.is_relation and getattr(obj, field.attname, None):
            related = getattr(obj, field.name)
            if isinstance(getattr(related, "ativo", None), bool) and not related.ativo:
                raise ValidationError({field.name: "O cadastro selecionado está inativo."})


@transaction.atomic
def save_record(user, model, data, pk=None, version=None, ip=None, *, audit_record=True):
    label = model._meta.label_lower
    if label not in FIELDS:
        raise ValidationError("Entidade não editável diretamente.")
    authorize(user, admin=label.startswith("cadastros.") or (label == "termos.modelotermo" and not pk))
    if set(data) - set(FIELDS[label]):
        raise ValidationError("Há campos não permitidos nesta operação.")
    obj = model.objects.select_for_update().get(pk=pk) if pk else model()
    if pk and (version is None or int(version) != obj.versao):
        raise Conflict("Este registro foi alterado. Recarregue a página antes de salvar.")
    if pk and isinstance(getattr(obj, "ativo", None), bool) and not obj.ativo:
        raise Conflict("O registro está inativo.")
    before = {}
    if label == "ativos.ativo" and pk:
        from gati.apps.movimentacoes.models import ProcessoMovimentacao

        if ProcessoMovimentacao.objects.filter(itens__ativo=obj, estado="AGUARDANDO_ASSINATURAS").exists():
            raise Conflict("O ativo está reservado por um termo aguardando assinatura.")
        before = {"status": obj.status.nome, "localizacao": obj.localizacao.nome}
    for key, value in data.items():
        if isinstance(value, str):
            value = value.strip()
        setattr(obj, key, value)
    if label == "pessoas.pessoa":
        if not obj.documento or not obj.documento.isdigit() or len(obj.documento) < 4:
            raise ValidationError({"documento": "Informe de 4 a 32 dígitos."})
        if not obj.departamento_id:
            raise ValidationError({"departamento": "Departamento obrigatório."})
    if label == "ativos.ativo":
        obj.patrimonio = obj.patrimonio.upper()
        obj.service_tag = obj.service_tag.upper()
        if obj.garantia_fim and obj.data_aquisicao and obj.garantia_fim < obj.data_aquisicao:
            raise ValidationError({"garantia_fim": "A garantia não pode terminar antes da aquisição."})
        if (
            pk
            and obj.responsabilidades.filter(fim__isnull=True).exists()
            and obj.status.codigo == "EM_ESTOQUE"
        ):
            raise Conflict("Conclua a devolução assinada antes de colocar em estoque.")
        if (
            pk
            and obj.categoria_id != model.objects.get(pk=pk).categoria_id
            and obj.responsabilidades.filter(fim__isnull=True).exists()
        ):
            raise Conflict("Encerre as responsabilidades antes de alterar a categoria.")
    if label == "cadastros.categoriaativo" and pk and not obj.multiplos_responsaveis:
        from django.db.models import Count

        from gati.apps.movimentacoes.models import ResponsabilidadeAtivo

        if (
            ResponsabilidadeAtivo.objects.filter(ativo__categoria=obj, fim__isnull=True)
            .values("ativo")
            .annotate(n=Count("id"))
            .filter(n__gt=1)
            .exists()
        ):
            raise Conflict("A categoria possui ativos com múltiplos responsáveis.")
    if label == "cadastros.statusativo" and pk and model.objects.get(pk=pk).codigo != obj.codigo:
        raise Conflict("O código do status é estável; crie outro status.")
    if label == "termos.modelotermo":
        from gati.apps.termos.services import validate_tags

        validate_tags(obj.texto)
    check_references(obj)
    obj.full_clean()
    if pk:
        obj.versao += 1
    obj.save()
    if label == "ativos.ativo":
        from gati.apps.movimentacoes.models import Movimentacao

        after = {"status": obj.status.nome, "localizacao": obj.localizacao.nome}
        if not pk or before != after:
            Movimentacao.objects.create(
                ativo=obj,
                usuario=user,
                tipo="CADASTRO" if not pk else "ALTERACAO",
                descricao="Cadastro do ativo" if not pk else "Atualização de status/localização",
                antes=before,
                depois=after,
            )
    if audit_record:
        audit(user, "CRIAR" if not pk else "EDITAR", obj, ip, {"campos": list(data)})
    return obj


@transaction.atomic
def inactivate(user, obj, version=None, ip=None):
    label = obj._meta.label_lower
    authorize(user, admin=label.startswith("cadastros.") or label == "termos.modelotermo")
    obj = type(obj).objects.select_for_update().get(pk=obj.pk)
    try:
        version = int(version) if version is not None else None
    except ValueError, TypeError:
        raise ValidationError("Versão inválida; recarregue o formulário.") from None
    if version is not None and version != obj.versao:
        raise Conflict("Registro alterado; recarregue a página.")
    if not obj.ativo:
        return obj
    if label in {"ativos.ativo", "pessoas.pessoa"}:
        if obj.responsabilidades.filter(fim__isnull=True).exists():
            raise Conflict("Existe responsabilidade em aberto.")
        from gati.apps.movimentacoes.models import ProcessoMovimentacao

        query = {"itens__ativo": obj} if label == "ativos.ativo" else {"responsavel": obj}
        if ProcessoMovimentacao.objects.filter(
            **query, estado__in=["EM_EDICAO", "AGUARDANDO_ASSINATURAS"]
        ).exists():
            raise Conflict("Existe processo em andamento.")
        from gati.apps.termos.models import AssinaturaTermo

        if (
            label == "pessoas.pessoa"
            and AssinaturaTermo.objects.filter(
                pessoa=obj, termo__estado__in=["EM_EDICAO", "AGUARDANDO_ASSINATURAS"]
            ).exists()
        ):
            raise Conflict("Existe assinatura pendente.")
    if label.startswith("cadastros."):
        if label == "cadastros.statusativo" and obj.codigo in {"EM_ESTOQUE", "EM_USO", "EM_MANUTENCAO"}:
            raise Conflict("Status obrigatório para o fluxo patrimonial.")
        for relation in obj._meta.related_objects:
            related_model = relation.related_model
            if (
                related_model._meta.label_lower in {"ativos.ativo", "pessoas.pessoa"}
                and related_model.objects.filter(**{relation.field.name: obj, "ativo": True}).exists()
            ):
                raise Conflict("O catálogo ainda possui cadastros ativos vinculados.")
    obj.ativo = False
    obj.versao += 1
    obj.save(update_fields=["ativo", "versao", "atualizado_em"])
    if label == "ativos.ativo":
        from gati.apps.movimentacoes.models import Movimentacao

        Movimentacao.objects.create(ativo=obj, usuario=user, tipo="INATIVACAO", descricao="Ativo inativado")
    audit(user, "INATIVAR", obj, ip)
    return obj


@transaction.atomic
def deidentify(user, person, reason, ip=None):
    authorize(user, admin=True)
    if len(reason.strip()) < 10:
        raise ValidationError("Registre a justificativa e a análise de finalidade (mínimo 10 caracteres).")
    person = type(person).objects.select_for_update().get(pk=person.pk)
    if person.desidentificada_em:
        return person
    inactivate(user, person, ip=ip)
    # A inativação anterior não substitui a checagem de finalidades operacionais.
    from gati.apps.termos.models import AssinaturaTermo

    if (
        person.responsabilidades.filter(fim__isnull=True).exists()
        or AssinaturaTermo.objects.filter(
            pessoa=person, termo__estado__in=["EM_EDICAO", "AGUARDANDO_ASSINATURAS"]
        ).exists()
    ):
        raise Conflict("Há finalidade operacional ativa.")
    person.refresh_from_db()
    person.nome = f"Pessoa desidentificada #{person.pk}"
    person.documento = None
    person.email = ""
    person.cargo = ""
    person.departamento = None
    person.desidentificada_em = timezone.now()
    person.versao += 1
    person.save()
    audit(user, "DESIDENTIFICAR", person, ip, {"justificativa": reason[:2000]})
    return person
