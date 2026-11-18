from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models.functions import Lower


class UsuarioTI(AbstractUser):
    email = models.EmailField(unique=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(Lower("email"), name="usuario_email_ci"),
            models.UniqueConstraint(Lower("username"), name="usuario_nome_ci"),
        ]


class LoginFailure(models.Model):
    identidade_hash = models.CharField(max_length=64, db_index=True)
    ip = models.GenericIPAddressField()
    criado_em = models.DateTimeField(auto_now_add=True, db_index=True)
