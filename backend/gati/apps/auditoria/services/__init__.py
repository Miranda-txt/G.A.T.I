from ..models import LogAuditoria


def audit(user, action, obj=None, ip=None, details=None):
    return LogAuditoria.objects.create(
        usuario=user if user and user.is_authenticated else None,
        acao=action,
        entidade=obj._meta.label if obj is not None else "sessao",
        objeto_id=str(obj.pk) if obj is not None else "",
        ip=ip,
        detalhes=details or {},
    )
