from datetime import date

from django import forms
from django.core.paginator import Paginator
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render

from gati.apps.ativos.models import Ativo
from gati.apps.cadastros.models import Localizacao
from gati.apps.pessoas.models import Pessoa
from gati.apps.termos.models import ModeloTermo
from gati.apps.termos.services import edit_draft, issue, resolve_values
from gati.common.errors import Conflict
from gati.common.web import internal

from ..models import ProcessoMovimentacao
from ..services import create_process, edit_process

STEPS = ["Contexto", "Responsável", "Ativos e acessórios", "Condições", "Termo", "Signatários", "Revisão"]


@internal
def process_edit(request, pk):
    process = get_object_or_404(ProcessoMovimentacao, pk=pk)
    if process.estado != "EM_EDICAO":
        raise Conflict("Processo congelado.")
    form = forms.Form(
        request.POST or None,
        initial={
            "localizacao": process.localizacao_id,
            "data": process.data,
            "observacoes": process.observacoes,
            "versao": process.versao,
        },
    )
    form.fields["localizacao"] = forms.ModelChoiceField(
        label="Localização de destino", queryset=Localizacao.objects.filter(ativo=True)
    )
    form.fields["data"] = forms.DateField(
        label="Data",
        input_formats=["%Y-%m-%d"],
        widget=forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
    )
    form.fields["observacoes"] = forms.CharField(
        label="Observações", required=False, widget=forms.Textarea, max_length=10000
    )
    form.fields["versao"] = forms.IntegerField(widget=forms.HiddenInput)
    for field in form.fields.values():
        field.widget.attrs["class"] = "form-control"
    if request.method == "POST" and form.is_valid():
        data = dict(form.cleaned_data)
        edit_process(request.user, process, data, data.pop("versao"), request.META.get("REMOTE_ADDR"))
        from django.contrib import messages

        messages.success(request, "Contexto atualizado. Revise o texto do termo antes da emissão.")
        return redirect("process_detail", pk=pk)
    return render(
        request,
        "records/form.html",
        {"form": form, "config": {"title": "Editar contexto do processo"}, "resource": "", "obj": process},
    )


def wizard_form(step, state, data=None):
    form = forms.Form(data=data, initial=state.get(str(step), {}))
    if step == 1:
        form.fields["tipo"] = forms.ChoiceField(label="Operação", choices=ProcessoMovimentacao.TIPOS)
        form.fields["localizacao"] = forms.ModelChoiceField(
            label="Localização de destino", queryset=Localizacao.objects.filter(ativo=True)
        )
        form.fields["data"] = forms.DateField(
            label="Data da movimentação",
            initial=date.today,
            widget=forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
            input_formats=["%Y-%m-%d"],
        )
    elif step == 2:
        form.fields["responsavel"] = forms.ModelChoiceField(
            label="Responsável pelo equipamento", queryset=Pessoa.objects.filter(ativo=True)
        )
    elif step == 3:
        qs = Ativo.objects.filter(ativo=True).select_related("status")
        if state["1"]["tipo"] == "DEVOLUCAO":
            qs = qs.filter(
                responsabilidades__pessoa_id=state["2"]["responsavel"], responsabilidades__fim__isnull=True
            )
        form.fields["ativos"] = forms.ModelMultipleChoiceField(
            label="Ativos",
            queryset=qs,
            widget=forms.SelectMultiple(attrs={"size": 10}),
            help_text="Use Ctrl para selecionar mais de um ativo.",
        )
        form.fields["acessorios"] = forms.CharField(
            label="Acessórios entregues / devolvidos", required=False, widget=forms.Textarea, max_length=2000
        )
    elif step == 4:
        for asset in Ativo.objects.filter(id__in=state["3"]["ativos"]).order_by("id"):
            form.fields[f"condicoes_{asset.pk}"] = forms.CharField(
                label=f"{asset.patrimonio} — condições e conferência", widget=forms.Textarea, max_length=4000
            )
            if state["1"]["tipo"] == "DEVOLUCAO":
                form.fields[f"avaria_{asset.pk}"] = forms.BooleanField(
                    label=f"{asset.patrimonio} — possui avaria", required=False
                )
                form.fields[f"divergencias_{asset.pk}"] = forms.CharField(
                    label=f"{asset.patrimonio} — divergências",
                    required=False,
                    widget=forms.Textarea,
                    max_length=4000,
                )
        form.fields["observacoes"] = forms.CharField(
            label="Observações do processo", required=False, widget=forms.Textarea, max_length=10000
        )
    elif step == 5:
        form.fields["modelo"] = forms.ModelChoiceField(
            label="Modelo de termo", queryset=ModeloTermo.objects.filter(ativo=True)
        )
        form.fields["texto"] = forms.CharField(
            label="Texto específico (opcional)",
            required=False,
            widget=forms.Textarea,
            max_length=30000,
            help_text="Deixe vazio para usar o texto do modelo. As variáveis serão resolvidas antes da emissão.",
        )
    elif step == 6:
        form.fields["metodo"] = forms.ChoiceField(
            label="Assinatura do responsável", choices=[("PRESENCIAL", "Presencial"), ("EMAIL", "E-mail")]
        )
        form.fields["testemunhas"] = forms.ModelMultipleChoiceField(
            label="Testemunhas / acompanhantes (opcional)",
            queryset=Pessoa.objects.filter(ativo=True).exclude(pk=state["2"]["responsavel"]),
            required=False,
        )
        form.fields["metodo_testemunhas"] = forms.ChoiceField(
            label="Assinatura das testemunhas", choices=[("PRESENCIAL", "Presencial"), ("EMAIL", "E-mail")]
        )
    else:
        form.fields["confirmar"] = forms.BooleanField(
            label="Conferi os dados, os ativos e os signatários desta movimentação."
        )
    for field in form.fields.values():
        field.widget.attrs["class"] = (
            "form-check-input"
            if isinstance(field.widget, forms.CheckboxInput)
            else ("form-select" if isinstance(field.widget, forms.Select) else "form-control")
        )
        if isinstance(field.widget, forms.Textarea):
            field.widget.attrs["rows"] = 3
    return form


def serialize(values):
    result = {}
    for key, value in values.items():
        if hasattr(value, "pk"):
            value = value.pk
        elif hasattr(value, "values_list"):
            value = list(value.values_list("pk", flat=True))
        elif isinstance(value, date):
            value = value.isoformat()
        result[key] = value
    return result


@internal
def wizard(request, step=1):
    if step < 1 or step > 7:
        return redirect("wizard", step=1)
    state = request.session.get("movement_wizard", {})
    if step > 1 and any(str(s) not in state for s in range(1, step)):
        return redirect("wizard", step=1)
    form = wizard_form(step, state, request.POST if request.method == "POST" else None)
    if request.method == "POST" and form.is_valid():
        if step < 7:
            state[str(step)] = serialize(form.cleaned_data)
            # Mudanças anteriores invalidam passos dependentes já preenchidos.
            state = {k: v for k, v in state.items() if int(k) <= step}
            request.session["movement_wizard"] = state
            return redirect("wizard", step=step + 1)
        cleaned = {}
        for index in range(1, 7):
            check = wizard_form(index, state, state[str(index)])
            if not check.is_valid():
                raise Conflict("Um cadastro mudou durante o preenchimento. Revise os passos anteriores.")
            cleaned[index] = check.cleaned_data
        person = cleaned[2]["responsavel"]
        signers = [{"pessoa": person, "papel": "RESPONSAVEL", "metodo": cleaned[6]["metodo"]}]
        signers += [
            {"pessoa": p, "papel": "TESTEMUNHA", "metodo": cleaned[6]["metodo_testemunhas"]}
            for p in cleaned[6]["testemunhas"]
        ]
        items = []
        for asset in cleaned[3]["ativos"]:
            items.append(
                {
                    "ativo": asset,
                    "acessorios": cleaned[3]["acessorios"],
                    "condicoes": cleaned[4][f"condicoes_{asset.pk}"],
                    "avaria": cleaned[4].get(f"avaria_{asset.pk}", False),
                    "divergencias": cleaned[4].get(f"divergencias_{asset.pk}", ""),
                }
            )
        with transaction.atomic():
            process = create_process(
                request.user,
                {**cleaned[1], "responsavel": person, "observacoes": cleaned[4]["observacoes"]},
                items,
                cleaned[5]["modelo"],
                signers,
                request.META.get("REMOTE_ADDR"),
            )
            term = process.termos.first()
            if cleaned[5]["texto"]:
                term = edit_draft(request.user, term, cleaned[5]["texto"], term.versao)
            if request.POST.get("action") == "emitir":
                issue(request.user, term, request.META.get("REMOTE_ADDR"))
        request.session.pop("movement_wizard", None)
        return redirect("process_detail", pk=process.pk)
    review = None
    if step == 7:
        person = Pessoa.objects.get(pk=state["2"]["responsavel"])
        review = {
            "tipo": state["1"]["tipo"],
            "data": state["1"]["data"],
            "local": Localizacao.objects.get(pk=state["1"]["localizacao"]),
            "pessoa": person,
            "ativos": Ativo.objects.filter(pk__in=state["3"]["ativos"]),
            "acessorios": state["3"]["acessorios"],
            "condicoes": [(k, v) for k, v in state["4"].items()],
            "modelo": ModeloTermo.objects.get(pk=state["5"]["modelo"]),
            "texto": state["5"].get("texto") or ModeloTermo.objects.get(pk=state["5"]["modelo"]).texto,
            "metodo": state["6"]["metodo"],
            "testemunhas": Pessoa.objects.filter(pk__in=state["6"]["testemunhas"]),
        }
        review["texto"] = resolve_values(
            review["texto"],
            {
                "responsavel_nome": person.nome,
                "responsavel_documento": person.documento_mascarado,
                "departamento": str(person.departamento),
                "data": date.fromisoformat(review["data"]).strftime("%d/%m/%Y"),
                "localizacao": str(review["local"]),
                "tipo": dict(ProcessoMovimentacao.TIPOS)[review["tipo"]],
                "ativos": ", ".join(str(a) for a in review["ativos"]),
            },
        )
        review["conferencia"] = [
            {
                "ativo": a,
                "condicoes": state["4"].get(f"condicoes_{a.pk}", ""),
                "avaria": state["4"].get(f"avaria_{a.pk}", False),
                "divergencias": state["4"].get(f"divergencias_{a.pk}", ""),
            }
            for a in review["ativos"]
        ]
    return render(
        request,
        "processes/wizard.html",
        {"form": form, "step": step, "steps": STEPS, "step_name": STEPS[step - 1], "review": review},
    )


@internal
def process_list(request):
    qs = ProcessoMovimentacao.objects.select_related("responsavel", "localizacao")
    if request.GET.get("estado") in {"EM_EDICAO", "AGUARDANDO_ASSINATURAS", "CONCLUIDO", "CANCELADO"}:
        qs = qs.filter(estado=request.GET["estado"])
    return render(
        request, "processes/list.html", {"page": Paginator(qs, 50).get_page(request.GET.get("page"))}
    )


@internal
def process_detail(request, pk):
    process = get_object_or_404(
        ProcessoMovimentacao.objects.select_related("responsavel", "localizacao", "criado_por"), pk=pk
    )
    return render(
        request,
        "processes/detail.html",
        {
            "process": process,
            "items": process.itens.select_related("ativo"),
            "terms": process.termos.all(),
            "files": process.arquivos.filter(ativo=True),
        },
    )
