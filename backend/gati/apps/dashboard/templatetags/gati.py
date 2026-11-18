from datetime import date, datetime
from decimal import Decimal

from django import template
from django.utils import formats, timezone

register = template.Library()


@register.filter
def attr(obj, name):
    value = getattr(obj, name, "")
    return display(value)


@register.filter
def display(value):
    if value is None or value == "":
        return "—"
    if isinstance(value, bool):
        return "Sim" if value else "Não"
    if isinstance(value, datetime):
        return timezone.localtime(value).strftime("%d/%m/%Y %H:%M")
    if isinstance(value, date):
        return value.strftime("%d/%m/%Y")
    if isinstance(value, Decimal):
        return formats.number_format(value, decimal_pos=2, use_l10n=True, force_grouping=True)
    return value


@register.filter
def state(value):
    return {
        "EM_EDICAO": "Em edição",
        "AGUARDANDO_ASSINATURAS": "Aguardando assinaturas",
        "ASSINADO": "Assinado",
        "CANCELADO": "Cancelado",
        "CONCLUIDO": "Concluído",
        "ENTREGA": "Entrega",
        "DEVOLUCAO": "Devolução",
    }.get(value, value)
