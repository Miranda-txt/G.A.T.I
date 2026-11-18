from django.db import models

from gati.common.models import Cadastro


class Referencia(Cadastro):
    nome = models.CharField("nome", max_length=120, unique=True)

    class Meta:
        abstract = True
        ordering = ["nome"]

    def __str__(self):
        return self.nome


class Departamento(Referencia):
    pass


class CategoriaAtivo(Referencia):
    multiplos_responsaveis = models.BooleanField("permite múltiplos responsáveis", default=False)


class Localizacao(Referencia):
    descricao = models.CharField("descrição", max_length=240, blank=True)


class StatusAtivo(Referencia):
    codigo = models.SlugField("código", unique=True, max_length=40)
