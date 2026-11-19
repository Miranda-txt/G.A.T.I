"""Backend de e-mail que bloqueia envio ate integracao HTTPS homologada."""

from django.core.mail.backends.base import BaseEmailBackend


class FailClosedEmailBackend(BaseEmailBackend):
    """Nao simula sucesso de envio nem registra tokens em logs/arquivos."""

    def send_messages(self, email_messages):
        if email_messages:
            raise RuntimeError("Envio de e-mail indisponivel neste ambiente de homologacao.")
        return 0
