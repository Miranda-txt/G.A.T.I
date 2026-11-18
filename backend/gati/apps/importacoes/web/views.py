import csv

from django.core.exceptions import ValidationError
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render

from gati.common.web import internal

from ..models import ImportacaoExecucao
from ..services import HEADERS, cancel_import, confirm, preview, read_preview


@internal
def import_view(request, kind):
    if kind not in HEADERS:
        raise ValidationError("Entidade inválida.")
    if request.method == "POST":
        if len(request.FILES) != 1 or "arquivo" not in request.FILES:
            raise ValidationError("Envie um arquivo CSV ou XLSX.")
        job = preview(request.user, kind, request.FILES["arquivo"], request.META.get("REMOTE_ADDR"))
        return redirect("import_preview", pk=job.pk)
    return render(request, "imports/upload.html", {"kind": kind, "headers": HEADERS[kind]})


@internal
def template(request, kind):
    if kind not in HEADERS:
        raise ValidationError("Entidade inválida.")
    response = HttpResponse(content_type="text/csv; charset=utf-8")
    response["Content-Disposition"] = f'attachment; filename="modelo-{kind}.csv"'
    response.write("\ufeff")
    csv.writer(response, delimiter=";").writerow(HEADERS[kind])
    return response


@internal
def preview_view(request, pk):
    job = get_object_or_404(ImportacaoExecucao, pk=pk, usuario=request.user)
    if request.method == "POST":
        if request.POST.get("action") == "cancel":
            cancel_import(request.user, job, request.META.get("REMOTE_ADDR"))
        elif request.POST.get("confirm") == "yes":
            confirm(request.user, job, request.META.get("REMOTE_ADDR"))
        else:
            raise ValidationError("Confirme explicitamente a importação.")
        return redirect("listing", resource=job.entidade)
    rows = read_preview(request.user, job)
    # Exibe só amostra; a validação e confirmação abrangem todas as linhas.
    for row in rows:
        if "documento" in row:
            row["documento"] = "••• " + row["documento"][-4:]
    return render(
        request,
        "imports/preview.html",
        {"job": job, "headers": HEADERS[job.entidade], "rows": [list(r.values()) for r in rows[:50]]},
    )
