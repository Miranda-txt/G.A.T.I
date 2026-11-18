import hashlib
import json
import re
import secrets
from copy import deepcopy
from datetime import timedelta

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.mail import EmailMultiAlternatives
from django.core.validators import validate_email
from django.db import transaction
from django.template.loader import render_to_string
from django.utils import timezone

from gati.apps.auditoria.services import audit
from gati.apps.movimentacoes.models import ProcessoMovimentacao
from gati.apps.usuarios.permissions import authorize
from gati.common.errors import Conflict

from ..models import AssinaturaTermo, SessaoAssinatura, Termo, TermoItem

TAGS = {"responsavel_nome", "responsavel_documento", "departamento", "data", "localizacao", "tipo", "ativos"}


def digest(value):
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def lock_signature(pk):
    """Ordem única para evitar inversão entre aceite, cancelamento e reenvio."""
    reference = AssinaturaTermo.objects.select_related("termo").get(pk=pk)
    process = ProcessoMovimentacao.objects.select_for_update().get(pk=reference.termo.processo_id)
    term = Termo.objects.select_for_update().get(pk=reference.termo_id)
    signature = AssinaturaTermo.objects.select_for_update().get(pk=pk)
    signature.termo = term
    return process, term, signature


@transaction.atomic
def replace_cancelled(user, original, ip=None):
    authorize(user, admin=True)
    process = ProcessoMovimentacao.objects.select_for_update().get(pk=original.processo_id)
    original = Termo.objects.select_for_update().get(pk=original.pk)
    if original.estado != "CANCELADO":
        raise Conflict("Cancele e justifique o termo anterior antes de criar a correção.")
    if Termo.objects.filter(substitui=original).exists():
        raise Conflict("Este termo já possui um substituto; consulte o histórico.")
    if process.estado != "CONCLUIDO":
        from gati.apps.movimentacoes.services import create_process

        fresh = create_process(
            user,
            {
                "tipo": process.tipo,
                "responsavel": process.responsavel,
                "localizacao": process.localizacao,
                "data": process.data,
                "observacoes": process.observacoes,
            },
            [
                {
                    "ativo": item.ativo,
                    "acessorios": item.acessorios,
                    "condicoes": item.condicoes,
                    "avaria": item.avaria,
                    "divergencias": item.divergencias,
                }
                for item in process.itens.all()
            ],
            original.modelo,
            [{"pessoa": s.pessoa, "papel": s.papel, "metodo": s.metodo} for s in original.assinaturas.all()],
        )
        term = fresh.termos.get()
        term.texto = original.texto
        term.substitui = original
        term.save()
    else:
        # Uma correção documental de operação concluída não refaz o movimento patrimonial.
        term = Termo.objects.create(
            processo=process, modelo=original.modelo, texto=original.texto, substitui=original
        )
        for signer in original.assinaturas.all():
            AssinaturaTermo.objects.create(
                termo=term,
                pessoa=signer.pessoa,
                papel=signer.papel,
                metodo=signer.metodo,
                snapshot=deepcopy(signer.snapshot),
            )
        for item in original.itens.all():
            TermoItem.objects.create(termo=term, ativo=item.ativo, snapshot=deepcopy(item.snapshot))
    audit(user, "SUBSTITUIR_TERMO", term, ip, {"termo_anterior": original.pk})
    return term


def validate_tags(text):
    found = set(re.findall(r"{{\s*([\w]+)\s*}}", text))
    if found - TAGS or "{%" in text or "{#" in text:
        raise ValidationError("Modelo contém variável não permitida. Use as tags listadas na tela.")
    remaining = re.sub(r"{{\s*([\w]+)\s*}}", "", text)
    if "{{" in remaining or "}}" in remaining:
        raise ValidationError("Sintaxe de variável inválida.")


def resolve(text, process):
    values = {
        "responsavel_nome": process.responsavel.nome,
        "responsavel_documento": process.responsavel.documento_mascarado,
        "departamento": str(process.responsavel.departamento),
        "data": process.data.strftime("%d/%m/%Y"),
        "localizacao": str(process.localizacao),
        "tipo": process.get_tipo_display(),
        "ativos": ", ".join(str(item.ativo) for item in process.itens.select_related("ativo")),
    }
    return resolve_values(text, values)


def resolve_values(text, values):
    validate_tags(text)
    return re.sub(r"{{\s*([\w]+)\s*}}", lambda m: values[m.group(1)], text)


def create_draft(user, process, model, signers):
    authorize(user)
    if process.estado != "EM_EDICAO":
        raise Conflict("Processo não editável.")
    term = Termo.objects.create(processo=process, modelo=model, texto=resolve(model.texto, process))
    if not signers or not any(
        s["pessoa"].pk == process.responsavel_id and s["papel"] == "RESPONSAVEL" for s in signers
    ):
        raise ValidationError("O responsável precisa ser signatário.")
    if len(signers) > 10:
        raise ValidationError("Máximo de dez signatários.")
    for signer in signers:
        if signer["metodo"] not in {"EMAIL", "PRESENCIAL"} or signer["papel"] not in {
            "RESPONSAVEL",
            "TESTEMUNHA",
            "ACOMPANHANTE",
        }:
            raise ValidationError("Método ou papel inválido.")
        if not signer["pessoa"].ativo:
            raise ValidationError("Signatário inativo.")
        if signer["metodo"] == "EMAIL":
            validate_email(signer["pessoa"].email)
        AssinaturaTermo.objects.create(termo=term, **signer)
    return term


@transaction.atomic
def edit_draft(user, term, text, version, ip=None):
    authorize(user)
    try:
        version = int(version)
    except ValueError, TypeError:
        raise ValidationError("Versão inválida; recarregue o formulário.") from None
    term = Termo.objects.select_for_update().get(pk=term.pk)
    if term.estado != "EM_EDICAO" or term.versao != version:
        raise Conflict("Termo congelado ou versão desatualizada.")
    if not text.strip() or len(text) > 30000:
        raise ValidationError("Texto obrigatório, com até 30.000 caracteres.")
    term.texto = resolve(text, term.processo)
    term.versao += 1
    term.save()
    audit(user, "EDITAR_TERMO", term, ip)
    return term


@transaction.atomic
def edit_items(user, term, items, signers, version, ip=None):
    authorize(user)
    process = ProcessoMovimentacao.objects.select_for_update().get(pk=term.processo_id)
    term = Termo.objects.select_for_update().get(pk=term.pk)
    if term.estado != "EM_EDICAO" or process.estado != "EM_EDICAO" or term.versao != int(version):
        raise Conflict("Termo congelado ou versão desatualizada.")
    from gati.apps.movimentacoes.models import ProcessoItem
    from gati.apps.movimentacoes.services import locked_assets, validate_process

    ids = [item["ativo"].pk for item in items]
    if not ids or len(ids) != len(set(ids)) or len(ids) > 100:
        raise ValidationError("Selecione de 1 a 100 ativos distintos.")
    if len(signers) > 10 or not any(
        s["pessoa"].pk == process.responsavel_id and s["papel"] == "RESPONSAVEL" for s in signers
    ):
        raise ValidationError("O responsável precisa assinar.")
    process.itens.all().delete()
    for data in items:
        item = ProcessoItem(processo=process, **data)
        item.full_clean()
        item.save()
    validate_process(process, locked_assets(process))
    term.assinaturas.all().delete()
    for data in signers:
        if data["metodo"] not in {"PRESENCIAL", "EMAIL"} or data["papel"] not in {
            "RESPONSAVEL",
            "TESTEMUNHA",
            "ACOMPANHANTE",
        }:
            raise ValidationError("Signatário inválido.")
        if not data["pessoa"].ativo:
            raise ValidationError("Signatário inativo.")
        if data["metodo"] == "EMAIL":
            validate_email(data["pessoa"].email)
        signer = AssinaturaTermo(termo=term, **data)
        signer.full_clean(exclude=["snapshot", "expira_em", "assinado_em", "ip"])
        signer.save()
    term.versao += 1
    term.save()
    process.versao += 1
    process.save()
    audit(user, "EDITAR_ITENS_TERMO", term, ip)
    return term


@transaction.atomic
def issue(user, term, ip=None):
    authorize(user)
    process = ProcessoMovimentacao.objects.select_for_update().get(pk=term.processo_id)
    term = Termo.objects.select_for_update().get(pk=term.pk)
    if term.estado == "AGUARDANDO_ASSINATURAS":
        return term
    if term.estado == "EM_EDICAO" and term.substitui_id and process.estado == "CONCLUIDO":
        term.payload = deepcopy(term.substitui.payload)
        term.payload.update({"termo_id": term.pk, "texto": term.texto, "substitui": term.substitui_id})
        term.sha256 = digest(
            json.dumps(term.payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        )
        term.estado = "AGUARDANDO_ASSINATURAS"
        term.emitido_em = timezone.now()
        term.versao += 1
        term.save()
        audit(user, "EMITIR_CORRECAO_TERMO", term, ip, {"sha256": term.sha256})
        return term
    if term.estado != "EM_EDICAO" or process.estado != "EM_EDICAO":
        raise Conflict("Termo não pode ser emitido neste estado.")
    from gati.apps.movimentacoes.services import locked_assets, validate_process

    assets = locked_assets(process)
    validate_process(process, assets)
    if (
        ProcessoMovimentacao.objects.filter(itens__ativo__in=assets, estado="AGUARDANDO_ASSINATURAS")
        .exclude(pk=process.pk)
        .exists()
    ):
        raise Conflict("Um dos ativos já está reservado por outro processo aguardando assinatura.")
    items = []
    for item in process.itens.select_related("ativo", "ativo__categoria").order_by("ativo_id"):
        snap = {
            "patrimonio": item.ativo.patrimonio,
            "service_tag": item.ativo.service_tag,
            "numero_serie": item.ativo.numero_serie,
            "modelo": item.ativo.modelo,
            "categoria": item.ativo.categoria.nome,
            "acessorios": item.acessorios,
            "condicoes": item.condicoes,
            "avaria": item.avaria,
            "divergencias": item.divergencias,
        }
        TermoItem.objects.create(termo=term, ativo=item.ativo, snapshot=snap)
        items.append({"ativo_id": item.ativo_id, **snap})
    signers = []
    for signer in term.assinaturas.select_for_update().select_related("pessoa").order_by("id"):
        if not signer.pessoa.ativo:
            raise Conflict("Signatário inativo.")
        if signer.metodo == "EMAIL":
            validate_email(signer.pessoa.email)
        signer.snapshot = {
            "nome": signer.pessoa.nome,
            "documento": signer.pessoa.documento,
            "email": signer.pessoa.email,
        }
        signer.save(update_fields=["snapshot"])
        signers.append(
            {"pessoa_id": signer.pessoa_id, "papel": signer.papel, "metodo": signer.metodo, **signer.snapshot}
        )
    term.payload = {
        "versao": 1,
        "termo_id": term.pk,
        "texto": term.texto,
        "processo": {
            "id": process.pk,
            "tipo": process.tipo,
            "data": process.data.isoformat(),
            "localizacao": process.localizacao.nome,
            "observacoes": process.observacoes,
        },
        "itens": items,
        "signatarios": signers,
    }
    term.sha256 = digest(json.dumps(term.payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
    term.estado = "AGUARDANDO_ASSINATURAS"
    term.emitido_em = timezone.now()
    term.versao += 1
    term.save()
    process.estado = "AGUARDANDO_ASSINATURAS"
    process.versao += 1
    process.save()
    audit(user, "EMITIR_TERMO", term, ip, {"sha256": term.sha256})
    return term


@transaction.atomic
def cancel(user, term, reason, ip=None):
    authorize(user, admin=True)
    process = ProcessoMovimentacao.objects.select_for_update().get(pk=term.processo_id)
    term = Termo.objects.select_for_update().get(pk=term.pk)
    if len(reason.strip()) < 10:
        raise ValidationError("Justifique o cancelamento em pelo menos 10 caracteres.")
    if term.estado == "CANCELADO":
        return term
    term.estado = "CANCELADO"
    term.cancelado_em = timezone.now()
    term.motivo_cancelamento = reason
    term.versao += 1
    term.save()
    SessaoAssinatura.objects.filter(assinatura__termo=term).update(encerrada=True)
    if process.estado != "CONCLUIDO":
        process.estado = "CANCELADO"
        process.versao += 1
        process.save()
    audit(user, "CANCELAR_TERMO", term, ip, {"motivo": reason})
    return term


@transaction.atomic
def invitation(user, signature, ip=None):
    authorize(user)
    _, _, signature = lock_signature(signature.pk)
    if signature.termo.estado != "AGUARDANDO_ASSINATURAS" or signature.assinado_em:
        raise Conflict("Assinatura não está pendente.")
    raw = secrets.token_urlsafe(32)
    signature.token_hash = digest(raw)
    signature.expira_em = timezone.now() + timedelta(hours=48)
    signature.tentativas = 0
    signature.save(update_fields=["token_hash", "expira_em", "tentativas"])
    SessaoAssinatura.objects.filter(assinatura=signature).update(encerrada=True)
    audit(user, "GERAR_CONVITE", signature, ip)
    return raw


def send_invitation(user, signature, ip=None):
    if signature.metodo != "EMAIL":
        raise Conflict("Esta assinatura utiliza o modo presencial.")
    raw = invitation(user, signature, ip)
    signature.refresh_from_db()
    validate_email(signature.snapshot["email"])
    context = {"url": settings.PUBLIC_BASE_URL + "/assinar/iniciar/#" + raw}
    message = EmailMultiAlternatives(
        "Documento disponível para aceite",
        render_to_string("emails/term_signature.txt", context),
        settings.DEFAULT_FROM_EMAIL,
        [signature.snapshot["email"]],
    )
    message.attach_alternative(render_to_string("emails/term_signature.html", context), "text/html")
    try:
        message.send(fail_silently=False)
    except Exception:
        audit(user, "ENVIO_CONVITE_FALHOU", signature, ip)
        raise Conflict(
            "Não foi possível enviar o convite. O termo continua congelado; tente reenviar."
        ) from None
    audit(user, "CONVITE_SUBMETIDO_SMTP", signature, ip)


@transaction.atomic
def exchange_token(raw):
    if not raw:
        raise Conflict("Convite inválido ou expirado.")
    reference = AssinaturaTermo.objects.filter(token_hash=digest(raw)).first()
    signature = lock_signature(reference.pk)[2] if reference else None
    if (
        not signature
        or signature.token_hash != digest(raw)
        or not signature.expira_em
        or signature.expira_em <= timezone.now()
        or signature.assinado_em
        or signature.tentativas >= 5
        or signature.termo.estado != "AGUARDANDO_ASSINATURAS"
    ):
        raise Conflict("Convite inválido ou expirado.")
    signature.token_hash = ""
    signature.save(update_fields=["token_hash"])
    secret = secrets.token_urlsafe(32)
    SessaoAssinatura.objects.create(segredo_hash=digest(secret), assinatura=signature)
    return secret


def get_session(secret, lock=False, touch=True):
    query = SessaoAssinatura.objects.select_related("assinatura__termo")
    if lock:
        query = query.select_for_update(of=("self",))
    session = query.filter(segredo_hash=digest(secret or ""), encerrada=False).first()
    now = timezone.now()
    if (
        not session
        or now - session.criada_em >= timedelta(hours=2)
        or now - session.vista_em >= timedelta(minutes=30)
        or session.assinatura.termo.estado not in {"AGUARDANDO_ASSINATURAS", "ASSINADO"}
    ):
        raise Conflict("Sessão de assinatura encerrada ou expirada.")
    if touch:
        session.vista_em = now
        session.save(update_fields=["vista_em"])
    return session


def confirm_identity(secret, last4):
    valid = False
    with transaction.atomic():
        reference = get_session(secret, touch=False)
        _, _, signer = lock_signature(reference.assinatura_id)
        session = get_session(secret, lock=True)
        if signer.tentativas >= 5:
            session.encerrada = True
            session.save(update_fields=["encerrada"])
        elif len(last4) == 4 and secrets.compare_digest(last4, signer.snapshot["documento"][-4:]):
            session.identidade_confirmada = True
            session.save(update_fields=["identidade_confirmada"])
            valid = True
        else:
            signer.tentativas += 1
            signer.save(update_fields=["tentativas"])
            if signer.tentativas >= 5:
                SessaoAssinatura.objects.filter(assinatura=signer).update(encerrada=True)
    # Falhas precisam ser persistidas mesmo quando a interface exibe erro.
    if not valid:
        raise Conflict(
            "Não foi possível confirmar a identidade. Após cinco tentativas, solicite novo convite."
        )


@transaction.atomic
def accept(secret, ip, user_agent):
    session = get_session(secret, touch=False)
    if not session.identidade_confirmada:
        raise Conflict("Confirme a identidade antes de aceitar.")
    process, term, signer = lock_signature(session.assinatura_id)
    session = get_session(secret, lock=True)
    if signer.assinado_em:
        return signer
    if term.estado != "AGUARDANDO_ASSINATURAS":
        raise Conflict("Termo indisponível para assinatura.")
    signer.assinado_em = timezone.now()
    signer.hash_assinado = term.sha256
    signer.ip = ip
    signer.user_agent = user_agent[:512]
    signer.token_hash = ""
    signer.save()
    audit(None, "ACEITAR_TERMO", signer, ip, {"sha256": term.sha256, "metodo": signer.metodo})
    if not term.assinaturas.filter(assinado_em__isnull=True).exists():
        term.estado = "ASSINADO"
        term.versao += 1
        term.save()
        from gati.apps.movimentacoes.services import _complete_signed_process

        _complete_signed_process(process.criado_por, process, ip)
    return signer
