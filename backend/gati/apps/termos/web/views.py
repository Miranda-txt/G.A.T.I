from django import forms
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import logout
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_GET, require_POST

from gati.apps.usuarios.permissions import authorize
from gati.common.errors import Conflict
from gati.common.web import internal

from ..models import AssinaturaTermo, Termo
from ..services import (
    accept,
    cancel,
    confirm_identity,
    edit_draft,
    exchange_token,
    get_session,
    invitation,
    issue,
    replace_cancelled,
    send_invitation,
)


@internal
def term_list(request):
    qs = Termo.objects.select_related("processo__responsavel", "modelo")
    if request.GET.get("estado") in {"EM_EDICAO", "AGUARDANDO_ASSINATURAS", "ASSINADO", "CANCELADO"}:
        qs = qs.filter(estado=request.GET["estado"])
    return render(request, "terms/list.html", {"page": Paginator(qs, 50).get_page(request.GET.get("page"))})


@internal
def term_detail(request, pk):
    term = get_object_or_404(Termo.objects.select_related("processo__responsavel", "modelo"), pk=pk)
    return render(
        request,
        "terms/detail.html",
        {
            "term": term,
            "signatures": term.assinaturas.select_related("pessoa"),
            "items": term.itens.all()
            if term.estado != "EM_EDICAO" or term.processo.estado == "CONCLUIDO"
            else term.processo.itens.select_related("ativo"),
        },
    )


@internal
def term_items(request, pk):
    from gati.apps.ativos.models import Ativo
    from gati.apps.pessoas.models import Pessoa

    from ..services import edit_items

    term = get_object_or_404(Termo, pk=pk)
    if term.estado != "EM_EDICAO" or term.processo.estado != "EM_EDICAO":
        raise Conflict("Termo congelado.")
    form = forms.Form(
        request.POST or None,
        initial={
            "ativos": list(term.processo.itens.values_list("ativo_id", flat=True)),
            "versao": term.versao,
            "testemunhas": list(
                term.assinaturas.exclude(papel="RESPONSAVEL").values_list("pessoa_id", flat=True)
            ),
        },
    )
    form.fields["ativos"] = forms.ModelMultipleChoiceField(
        label="Ativos do termo", queryset=Ativo.objects.filter(ativo=True)
    )
    form.fields["condicoes"] = forms.CharField(
        label="Condições / conferência (aplicadas aos ativos selecionados)",
        widget=forms.Textarea,
        max_length=4000,
    )
    form.fields["acessorios"] = forms.CharField(
        label="Acessórios (aplicados aos ativos selecionados)",
        required=False,
        widget=forms.Textarea,
        max_length=2000,
    )
    form.fields["avaria"] = forms.BooleanField(
        label="Avaria nos ativos selecionados (devolução)", required=False
    )
    form.fields["divergencias"] = forms.CharField(
        label="Divergências", required=False, widget=forms.Textarea, max_length=4000
    )
    form.fields["metodo"] = forms.ChoiceField(
        label="Método do responsável", choices=[("PRESENCIAL", "Presencial"), ("EMAIL", "E-mail")]
    )
    form.fields["testemunhas"] = forms.ModelMultipleChoiceField(
        label="Testemunhas / acompanhantes",
        queryset=Pessoa.objects.filter(ativo=True).exclude(pk=term.processo.responsavel_id),
        required=False,
    )
    form.fields["metodo_testemunhas"] = forms.ChoiceField(
        label="Método das testemunhas", choices=[("PRESENCIAL", "Presencial"), ("EMAIL", "E-mail")]
    )
    form.fields["versao"] = forms.IntegerField(widget=forms.HiddenInput)
    for field in form.fields.values():
        field.widget.attrs["class"] = (
            "form-check-input" if isinstance(field.widget, forms.CheckboxInput) else "form-control"
        )
    if request.method == "POST" and form.is_valid():
        data = form.cleaned_data
        items = [
            {"ativo": a, **{k: data[k] for k in ["condicoes", "acessorios", "avaria", "divergencias"]}}
            for a in data["ativos"]
        ]
        signers = [{"pessoa": term.processo.responsavel, "papel": "RESPONSAVEL", "metodo": data["metodo"]}]
        signers += [
            {"pessoa": p, "papel": "TESTEMUNHA", "metodo": data["metodo_testemunhas"]}
            for p in data["testemunhas"]
        ]
        edit_items(request.user, term, items, signers, data["versao"], request.META.get("REMOTE_ADDR"))
        messages.success(request, "Itens atualizados. Revise também o texto antes de emitir o termo.")
        return redirect("term_detail", pk=pk)
    return render(
        request,
        "records/form.html",
        {"form": form, "config": {"title": "Itens e signatários do termo"}, "resource": "", "obj": term},
    )


@internal
def term_action(request, pk, action):
    term = get_object_or_404(Termo, pk=pk)
    if action not in {"emitir", "cancelar", "editar", "substituir"}:
        raise ValidationError("Ação inválida.")
    if action in {"cancelar", "substituir"}:
        authorize(request.user, admin=True)
    if request.method == "POST":
        if action == "substituir":
            fresh = replace_cancelled(request.user, term, request.META.get("REMOTE_ADDR"))
            return redirect("term_detail", pk=fresh.pk)
        elif action == "emitir":
            issue(request.user, term, request.META.get("REMOTE_ADDR"))
        elif action == "cancelar":
            cancel(request.user, term, request.POST.get("reason", ""), request.META.get("REMOTE_ADDR"))
        else:
            edit_draft(
                request.user,
                term,
                request.POST.get("texto", ""),
                request.POST.get("versao", 0),
                request.META.get("REMOTE_ADDR"),
            )
        return redirect("term_detail", pk=pk)
    if action == "editar":
        if term.estado != "EM_EDICAO":
            raise Conflict("Termo congelado.")
        return render(request, "terms/edit.html", {"term": term})
    return render(
        request,
        "records/confirm.html",
        {
            "obj": term,
            "action": {
                "emitir": "Emitir para assinatura",
                "cancelar": "Cancelar termo",
                "substituir": "Criar termo substituto",
            }[action],
            "reason": action == "cancelar",
            "explanation": "O conteúdo, os ativos e os signatários serão congelados."
            if action == "emitir"
            else "As evidências anteriores serão preservadas. A correção documental não reverte nem repete movimentações concluídas.",
        },
    )


@require_POST
@internal
def signature_action(request, pk, action):
    signer = get_object_or_404(AssinaturaTermo, pk=pk)
    if action == "email":
        send_invitation(request.user, signer, request.META.get("REMOTE_ADDR"))
        messages.success(request, "Convite submetido ao serviço de e-mail.")
        return redirect("term_detail", pk=signer.termo_id)
    if action != "presencial" or signer.metodo != "PRESENCIAL":
        raise Conflict("Método de assinatura incompatível.")
    raw = invitation(request.user, signer, request.META.get("REMOTE_ADDR"))
    secret = exchange_token(raw)
    logout(request)
    response = redirect("sign_view")
    set_signature_cookie(response, secret)
    return response


def set_signature_cookie(response, secret):
    response.set_cookie(
        "gati_assinatura",
        secret,
        max_age=7200,
        secure=settings.SESSION_COOKIE_SECURE,
        httponly=True,
        samesite="Lax",
        path="/assinar/",
    )


def public_error(request, error):
    return render(request, "signature/error.html", {"error": str(error)}, status=400)


def sign_start(request):
    if request.method == "POST":
        try:
            secret = exchange_token(request.POST.get("token", "")[:200])
            response = JsonResponse({"url": "/assinar/"})
            set_signature_cookie(response, secret)
            return response
        except Conflict as error:
            return JsonResponse({"error": str(error)}, status=400)
    return render(request, "signature/start.html")


@require_GET
def sign_view(request):
    try:
        session = get_session(request.COOKIES.get("gati_assinatura"))
    except Conflict as error:
        return public_error(request, error)
    return render(
        request,
        "signature/sign.html",
        {
            "signature": session.assinatura,
            "confirmed": session.identidade_confirmada,
            "term": session.assinatura.termo if session.identidade_confirmada else None,
        },
    )


@require_POST
def sign_identity(request):
    try:
        confirm_identity(request.COOKIES.get("gati_assinatura"), request.POST.get("last4", ""))
        return redirect("sign_view")
    except Conflict as error:
        return public_error(request, error)


@require_POST
def sign_accept(request):
    try:
        if request.POST.get("aceito") != "yes":
            raise Conflict("O aceite precisa ser explícito.")
        accept(
            request.COOKIES.get("gati_assinatura"),
            request.META.get("REMOTE_ADDR"),
            request.META.get("HTTP_USER_AGENT", ""),
        )
        return redirect("sign_view")
    except (Conflict, ValidationError) as error:
        return public_error(request, error)
