from django.core.exceptions import ValidationError
from django.db import models


class Registro(models.Model):
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)
    versao = models.PositiveIntegerField(default=1)

    class Meta:
        abstract = True


class Cadastro(Registro):
    ativo = models.BooleanField(default=True, db_index=True)

    class Meta:
        abstract = True

    def delete(self, *args, **kwargs):
        raise ValidationError("Use inativação; exclusão física não é permitida.")


class AppendOnlyQuerySet(models.QuerySet):
    def update(self, **kwargs):
        raise ValidationError("Registro histórico imutável.")

    def delete(self):
        raise ValidationError("Registro histórico imutável.")


class AppendOnly(models.Model):
    objects = AppendOnlyQuerySet.as_manager()

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        if self.pk:
            raise ValidationError("Registro histórico imutável.")
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError("Registro histórico imutável.")
