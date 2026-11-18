from functools import wraps

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from django.db import IntegrityError
from django.http import FileResponse, Http404, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from gati.apps.arquivos.models import Arquivo
from gati.apps.arquivos.services import download_file, upload_file
from gati.apps.usuarios.permissions import authorize, is_admin
from gati.common.errors import Conflict, ScannerUnavailable

from .catalog import inactivate, save_record
from .forms import record_form
from .registry import RESOURCES
from .selectors import records


def internal(view):
    @login_required
    @wraps(view)
    def wrapped(request, *args, **kwargs):
        authorize(request.user)
        try:
            return view(request, *args, **kwargs)
        except (Conflict, ValidationError, ScannerUnavailable, IntegrityError) as error:
            text = (
                "; ".join(error.messages)
                if isinstance(error, ValidationError)
                else (
                    "Conflito de dados. Recarregue e confira os identificadores."
                    if isinstance(error, IntegrityError)
                    else str(error)
                )
            )
            return render(
                request,
                "errors/action.html",
                {"error": text},
                status=409 if isinstance(error, (Conflict, IntegrityError)) else 400,
            )

    return wrapped


def resource_config(resource):
    if resource not in RESOURCES:
        raise Http404()
    return RESOURCES[resource]


@internal
def listing(request, resource):
    config = resource_config(resource)
    if config.admin:
        authorize(request.user, admin=True)
    queryset = records(resource, config.model, request.GET)
    page = Paginator(queryset, 50).get_page(request.GET.get("page"))
    params = request.GET.copy()
    params.pop("page", None)
    context = {
        "config": config,
        "resource": resource,
        "page": page,
        "query": params.urlencode(),
        "can_create": resource != "modelos-termo" or is_admin(request.user),
    }
    if resource == "ativos":
        from gati.apps.cadastros.models import CategoriaAtivo, Departamento, Localizacao, StatusAtivo

        context.update(
            categorias=CategoriaAtivo.objects.filter(ativo=True),
            statuses=StatusAtivo.objects.filter(ativo=True),
            locais=Localizacao.objects.filter(ativo=True),
            departamentos=Departamento.objects.filter(ativo=True),
        )
    return render(
        request,
        "components/records.html" if request.headers.get("HX-Request") else "records/list.html",
        context,
    )


@internal
def edit(request, resource, pk=None):
    config = resource_config(resource)
    authorize(request.user, admin=config.admin or (resource == "modelos-termo" and pk is None))
    instance = get_object_or_404(config.model, pk=pk) if pk else None
    form = record_form(resource, request.POST if request.method == "POST" else None, instance)
    if request.method == "POST" and form.is_valid():
        data = {k: v for k, v in form.cleaned_data.items() if k != "versao"}
        try:
            obj = save_record(
                request.user,
                config.model,
                data,
                pk,
                form.cleaned_data["versao"],
                request.META.get("REMOTE_ADDR"),
            )
            messages.success(request, "Registro salvo com sucesso.")
            return redirect("detail", resource=resource, pk=obj.pk)
        except (ValidationError, Conflict, IntegrityError) as error:
            form.add_error(
                None,
                "; ".join(error.messages)
                if isinstance(error, ValidationError)
                else ("Identificador já utilizado." if isinstance(error, IntegrityError) else str(error)),
            )
    return render(
        request, "records/form.html", {"config": config, "resource": resource, "form": form, "obj": instance}
    )


@internal
def detail(request, resource, pk):
    config = resource_config(resource)
    if config.admin:
        authorize(request.user, admin=True)
    obj = get_object_or_404(config.model, pk=pk)
    fields = []
    for name in config.fields:
        value = getattr(obj, name)
        if name == "documento" and not is_admin(request.user):
            value = obj.documento_mascarado
        fields.append((config.model._meta.get_field(name).verbose_name, value))
    context = {
        "obj": obj,
        "config": config,
        "resource": resource,
        "fields": fields,
        "can_inactivate": hasattr(obj, "ativo")
        and isinstance(obj.ativo, bool)
        and obj.ativo
        and (resource != "modelos-termo" or is_admin(request.user)),
    }
    if resource == "ativos":
        context.update(
            history=obj.historico.select_related("usuario")[:100],
            responsibilities=obj.responsabilidades.select_related("pessoa").order_by("-inicio"),
            maintenance=obj.manutencoes.all(),
            files=obj.arquivos.filter(ativo=True),
        )
    if resource == "pessoas":
        context["responsibilities"] = obj.responsabilidades.select_related("ativo").order_by("-inicio")
    if resource == "manutencoes":
        context["files"] = obj.arquivos.filter(ativo=True)
    return render(request, "records/detail.html", context)


@internal
def deactivate(request, resource, pk):
    config = resource_config(resource)
    obj = get_object_or_404(config.model, pk=pk)
    if request.method == "POST":
        inactivate(request.user, obj, request.POST.get("versao"), request.META.get("REMOTE_ADDR"))
        messages.success(request, "Registro inativado. O histórico foi preservado.")
        return redirect("listing", resource=resource)
    return render(
        request,
        "records/confirm.html",
        {
            "obj": obj,
            "action": "Inativar registro",
            "explanation": "O registro deixará de estar disponível em novas operações. O histórico será mantido.",
            "version": obj.versao,
        },
    )


@require_POST
@internal
def upload(request, resource, pk):
    if resource == "processos":
        from gati.apps.movimentacoes.models import ProcessoMovimentacao

        target = get_object_or_404(ProcessoMovimentacao, pk=pk)
    else:
        target = get_object_or_404(resource_config(resource).model, pk=pk)
    if len(request.FILES) != 1 or "arquivo" not in request.FILES:
        raise ValidationError("Selecione um único arquivo.")
    upload_file(request.user, request.FILES["arquivo"], target, request.META.get("REMOTE_ADDR"))
    messages.success(request, "Arquivo verificado e anexado.")
    return (
        redirect("process_detail", pk=pk)
        if resource == "processos"
        else redirect("detail", resource=resource, pk=pk)
    )


@internal
def download(request, pk):
    obj = get_object_or_404(Arquivo, pk=pk)
    stream = download_file(request.user, obj, request.META.get("REMOTE_ADDR"))
    return FileResponse(stream, as_attachment=True, filename=obj.nome_original, content_type=obj.mime)


@require_POST
@internal
def file_deactivate(request, pk):
    obj = get_object_or_404(Arquivo, pk=pk)
    inactivate(request.user, obj, ip=request.META.get("REMOTE_ADDR"))
    return redirect("dashboard")


@internal
def deidentify_view(request, pk):
    from gati.apps.pessoas.models import Pessoa

    from .catalog import deidentify

    authorize(request.user, admin=True)
    obj = get_object_or_404(Pessoa, pk=pk)
    if request.method == "POST":
        deidentify(request.user, obj, request.POST.get("reason", ""), request.META.get("REMOTE_ADDR"))
        return redirect("detail", resource="pessoas", pk=pk)
    return render(
        request,
        "records/confirm.html",
        {
            "obj": obj,
            "action": "Desidentificar cadastro",
            "reason": True,
            "explanation": "Remover nome, documento, e-mail, cargo e departamento do cadastro mestre após análise de finalidade. Evidências históricas serão preservadas.",
        },
    )


@internal
def privacy_report(request, pk):
    from gati.apps.auditoria.services import audit
    from gati.apps.pessoas.models import Pessoa

    authorize(request.user, admin=True)
    obj = get_object_or_404(Pessoa, pk=pk)
    audit(request.user, "RELATORIO_TITULAR", obj, request.META.get("REMOTE_ADDR"))
    response = JsonResponse(
        {
            "pessoa": {
                f: getattr(obj, f)
                for f in ["id", "nome", "documento", "email", "cargo", "departamento_id", "ativo"]
            },
            "responsabilidades": list(obj.responsabilidades.values("ativo_id", "inicio", "fim")),
            "termos": list(
                obj.assinaturatermo_set.values("termo_id", "papel", "metodo", "assinado_em", "hash_assinado")
            ),
        },
        json_dumps_params={"ensure_ascii": False},
    )
    response["Content-Disposition"] = f'attachment; filename="relatorio-titular-{pk}.json"'
    return response


@require_POST
@internal
def history_correction(request, pk):
    from gati.apps.ativos.models import Ativo
    from gati.apps.movimentacoes.services import correct_history

    correct_history(
        request.user,
        get_object_or_404(Ativo, pk=pk),
        request.POST.get("descricao", ""),
        request.META.get("REMOTE_ADDR"),
    )
    return redirect("detail", resource="ativos", pk=pk)
