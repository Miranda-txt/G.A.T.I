from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from gati.apps.ativos.models import Ativo
from gati.apps.auditoria.services import audit
from gati.apps.cadastros.models import Localizacao, StatusAtivo
from gati.apps.pessoas.models import Pessoa
from gati.apps.usuarios.permissions import authorize
from gati.common.errors import Conflict

from ..models import Movimentacao, ProcessoItem, ProcessoMovimentacao, ResponsabilidadeAtivo


def locked_assets(process):
    ids = list(process.itens.values_list("ativo_id", flat=True))
    return list(Ativo.objects.select_for_update().filter(id__in=ids).order_by("id"))


def validate_process(process, assets):
    if not process.responsavel.ativo or not process.localizacao.ativo:
        raise Conflict("Responsável ou localização inativo.")
    if not assets:
        raise Conflict("Selecione pelo menos um ativo.")
    for asset in assets:
        if not asset.ativo:
            raise Conflict(f"O ativo {asset.patrimonio} está inativo.")
        active = ResponsabilidadeAtivo.objects.filter(ativo=asset, fim__isnull=True)
        if process.tipo == "ENTREGA":
            if active.filter(pessoa=process.responsavel).exists() or (
                not asset.categoria.multiplos_responsaveis and active.exists()
            ):
                raise Conflict(f"O ativo {asset.patrimonio} já tem responsabilidade incompatível.")
            if asset.status.codigo not in {"EM_ESTOQUE", "EM_USO"}:
                raise Conflict(f"O ativo {asset.patrimonio} não está disponível para entrega.")
            if active.exists() and asset.localizacao_id != process.localizacao_id:
                raise Conflict("Ativo compartilhado deve permanecer na localização atual.")
        elif not active.filter(pessoa=process.responsavel).exists():
            raise Conflict(f"O responsável não possui o ativo {asset.patrimonio}.")


@transaction.atomic
def create_process(user, data, items, model, signers, ip=None):
    authorize(user)
    if set(data) - {"tipo", "responsavel", "localizacao", "data", "observacoes"} or data.get("tipo") not in {
        "ENTREGA",
        "DEVOLUCAO",
    }:
        raise ValidationError("Contexto do processo inválido.")
    person = Pessoa.objects.select_for_update().get(pk=data["responsavel"].pk)
    location = Localizacao.objects.select_for_update().get(pk=data["localizacao"].pk)
    if not person.ativo or not location.ativo or not model.ativo:
        raise Conflict("Selecione cadastros ativos.")
    process = ProcessoMovimentacao.objects.create(**data, criado_por=user)
    ids = [int(item["ativo"].pk) for item in items]
    if len(set(ids)) != len(ids) or not ids or len(ids) > 100:
        raise ValidationError("Selecione de 1 a 100 ativos distintos.")
    for item in items:
        if set(item) - {"ativo", "acessorios", "condicoes", "avaria", "divergencias"}:
            raise ValidationError("Item contém campos não permitidos.")
        obj = ProcessoItem(processo=process, **item)
        obj.full_clean()
        obj.save()
    validate_process(process, locked_assets(process))
    from gati.apps.termos.services import create_draft

    create_draft(user, process, model, signers)
    audit(user, "CRIAR_PROCESSO", process, ip)
    return process


@transaction.atomic
def complete_process(user, process, ip=None):
    authorize(user)
    return _complete_signed_process(user, process, ip)


@transaction.atomic
def _complete_signed_process(user, process, ip=None):
    """Conclusão interna após aceite: não depende da conta do criador continuar ativa."""
    process = ProcessoMovimentacao.objects.select_for_update().get(pk=process.pk)
    if process.estado == "CONCLUIDO":
        return process
    term = process.termos.exclude(estado="CANCELADO").first()
    if not term or term.estado != "ASSINADO":
        raise Conflict("Todas as assinaturas obrigatórias devem ser concluídas.")
    assets = locked_assets(process)
    validate_process(process, assets)
    now = timezone.now()
    for asset in assets:
        item = process.itens.get(ativo=asset)
        before = {"status": asset.status.nome, "localizacao": asset.localizacao.nome}
        if process.tipo == "ENTREGA":
            ResponsabilidadeAtivo.objects.create(
                ativo=asset, pessoa=process.responsavel, inicio=now, processo_inicio=process
            )
            code = "EM_USO"
        else:
            responsibility = ResponsabilidadeAtivo.objects.select_for_update().get(
                ativo=asset, pessoa=process.responsavel, fim__isnull=True
            )
            responsibility.fim = now
            responsibility.processo_fim = process
            responsibility.save(update_fields=["fim", "processo_fim"])
            others = ResponsabilidadeAtivo.objects.filter(ativo=asset, fim__isnull=True).exists()
            if others and item.avaria:
                raise Conflict("Devolva todas as responsabilidades do ativo compartilhado com avaria.")
            code = "EM_USO" if others else ("EM_MANUTENCAO" if item.avaria else "EM_ESTOQUE")
        asset.status = StatusAtivo.objects.get(codigo=code, ativo=True)
        if not (process.tipo == "DEVOLUCAO" and code == "EM_USO"):
            asset.localizacao = process.localizacao
        asset.versao += 1
        asset.save(update_fields=["status", "localizacao", "versao", "atualizado_em"])
        Movimentacao.objects.create(
            ativo=asset,
            usuario=user,
            processo=process,
            tipo=process.tipo,
            descricao=f"{process.get_tipo_display()} concluída pelo termo #{term.pk}",
            antes=before,
            depois={
                "status": asset.status.nome,
                "localizacao": asset.localizacao.nome,
                "responsavel_id": process.responsavel_id,
            },
        )
    process.estado = "CONCLUIDO"
    process.concluido_em = now
    process.versao += 1
    process.save()
    audit(user, "CONCLUIR_PROCESSO", process, ip)
    return process


@transaction.atomic
def edit_process(user, process, data, version, ip=None):
    authorize(user)
    process = ProcessoMovimentacao.objects.select_for_update().get(pk=process.pk)
    if process.estado != "EM_EDICAO" or version != process.versao:
        raise Conflict("Processo congelado ou versão desatualizada.")
    if set(data) - {"localizacao", "data", "observacoes"}:
        raise ValidationError(
            "Edite somente data, localização e observações. Para outro responsável ou operação, crie novo processo."
        )
    for key, value in data.items():
        setattr(process, key, value)
    process.full_clean(exclude=["concluido_em"])
    validate_process(process, locked_assets(process))
    term = process.termos.select_for_update().get(estado="EM_EDICAO")
    # O texto já resolvido é preservado; a interface orienta a revisão antes da emissão.
    process.versao += 1
    process.save()
    term.versao += 1
    term.save()
    audit(user, "EDITAR_PROCESSO", process, ip, {"campos": list(data)})
    return process


@transaction.atomic
def correct_history(user, asset, description, ip=None):
    authorize(user)
    if len(description.strip()) < 10:
        raise ValidationError("Descreva a correção em pelo menos 10 caracteres.")
    event = Movimentacao.objects.create(
        ativo=asset, usuario=user, tipo="RETIFICACAO", descricao=description[:4000]
    )
    audit(user, "RETIFICAR_HISTORICO", event, ip)
    return event
