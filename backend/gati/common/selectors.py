from django.db.models import Q

from gati.common.errors import Conflict


def records(resource, model, params):
    qs = model.objects.all()
    active_field = next((f for f in model._meta.fields if f.name == "ativo"), None)
    if active_field and active_field.get_internal_type() == "BooleanField":
        state = params.get("situacao", "ativos")
        if state != "todos":
            qs = qs.filter(ativo=state != "inativos")
    q = params.get("q", "").strip()[:200]
    if resource == "ativos":
        qs = qs.select_related("categoria", "status", "localizacao")
        if q:
            qs = qs.filter(
                Q(patrimonio__icontains=q)
                | Q(service_tag__icontains=q)
                | Q(numero_serie__icontains=q)
                | Q(modelo__icontains=q)
                | Q(tecnico__hostname__icontains=q)
                | Q(interfaces__mac__icontains=q)
                | Q(interfaces__ip__icontains=q)
                | Q(responsabilidades__pessoa__nome__icontains=q, responsabilidades__fim__isnull=True)
            )
        mapping = {
            "categoria": "categoria_id",
            "status": "status_id",
            "localizacao": "localizacao_id",
            "responsavel": "responsabilidades__pessoa_id",
            "departamento": "responsabilidades__pessoa__departamento_id",
        }
        for key, field in mapping.items():
            value = params.get(key)
            if value:
                if not value.isdigit():
                    raise Conflict("Filtro inválido.")
                criteria = {field: value}
                if key in {"responsavel", "departamento"}:
                    criteria["responsabilidades__fim__isnull"] = True
                qs = qs.filter(**criteria)
        if params.get("garantia") == "30":
            from datetime import timedelta

            from django.utils import timezone

            qs = qs.filter(
                garantia_fim__range=(timezone.localdate(), timezone.localdate() + timedelta(days=30))
            )
    elif resource == "pessoas":
        qs = qs.select_related("departamento")
        if params.get("departamento"):
            if not params["departamento"].isdigit():
                raise Conflict("Filtro inválido.")
            qs = qs.filter(departamento_id=params["departamento"])
        if q:
            qs = qs.filter(
                Q(nome__icontains=q)
                | Q(documento__icontains=q)
                | Q(email__icontains=q)
                | Q(cargo__icontains=q)
            )
    elif resource == "manutencoes":
        qs = qs.select_related("ativo")
        if q:
            qs = qs.filter(
                Q(ativo__patrimonio__icontains=q) | Q(fornecedor__icontains=q) | Q(defeito__icontains=q)
            )
    elif q:
        qs = qs.filter(nome__icontains=q)
    order = params.get("ordering", "")
    allowed = {
        "ativos": {"patrimonio", "-patrimonio", "garantia_fim", "-criado_em"},
        "pessoas": {"nome", "-nome"},
        "manutencoes": {"data_inicio", "-data_inicio"},
    }
    if order:
        if order not in allowed.get(resource, {"nome", "-nome"}):
            raise Conflict("Ordenação não permitida.")
        qs = qs.order_by(order, "id")
    return qs.distinct()
