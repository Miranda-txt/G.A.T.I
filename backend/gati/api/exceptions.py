from django.core.exceptions import ValidationError
from django.db import IntegrityError
from rest_framework.response import Response
from rest_framework.views import exception_handler

from gati.common.errors import Conflict, ScannerUnavailable


def problem_handler(exc, context):
    response = exception_handler(exc, context)
    errors = {}
    if isinstance(exc, ValidationError):
        status = 400
        detail = "Dados inválidos."
        errors = getattr(exc, "message_dict", {"non_field_errors": exc.messages})
        code = "validation_error"
    elif isinstance(exc, (Conflict, IntegrityError)):
        status = 409
        detail = (
            str(exc)
            if isinstance(exc, Conflict)
            else "Conflito de integridade. Confira os dados e tente novamente."
        )
        code = "conflict"
    elif isinstance(exc, ScannerUnavailable):
        status = 503
        detail = str(exc)
        code = "scanner_unavailable"
    elif response is not None:
        status = response.status_code
        code = {
            400: "validation_error",
            401: "unauthorized",
            403: "forbidden",
            404: "not_found",
            405: "method_not_allowed",
            429: "rate_limit",
        }.get(status, "request_error")
        detail = "Não foi possível concluir a solicitação."
        if isinstance(response.data, dict) and "detail" in response.data:
            detail = str(response.data["detail"])
        elif status == 400:
            errors = response.data
    else:
        status = 500
        detail = "Erro interno. Tente novamente ou informe o administrador."
        code = "internal_error"
    return Response(
        {
            "type": "about:blank",
            "title": {
                400: "Dados inválidos",
                403: "Acesso negado",
                404: "Não encontrado",
                409: "Conflito",
                503: "Serviço indisponível",
            }.get(status, "Falha na solicitação"),
            "status": status,
            "detail": detail,
            "instance": context["request"].path,
            "code": code,
            "errors": errors,
        },
        status=status,
        content_type="application/problem+json",
    )
