from django.db import models

from gati.common.models import Cadastro


class Pessoa(Cadastro):
    nome = models.CharField("nome completo", max_length=160)
    documento = models.CharField("documento (somente dígitos)", max_length=32, unique=True, null=True)
    departamento = models.ForeignKey("cadastros.Departamento", on_delete=models.PROTECT, null=True)
    cargo = models.CharField("cargo", max_length=120, blank=True)
    email = models.EmailField("e-mail", blank=True)
    desidentificada_em = models.DateTimeField(null=True, editable=False)

    class Meta:
        ordering = ["nome", "id"]

    def __str__(self):
        return self.nome

    @property
    def documento_mascarado(self):
        return ("••• " + self.documento[-4:]) if self.documento else "Removido"
