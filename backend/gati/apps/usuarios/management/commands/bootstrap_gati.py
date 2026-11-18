import getpass

from django.contrib.auth.models import Group, Permission
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from gati.apps.cadastros.models import StatusAtivo
from gati.apps.usuarios.models import UsuarioTI


class Command(BaseCommand):
    help = "Cria perfis, status obrigatórios e, opcionalmente, o primeiro administrador funcional."

    def add_arguments(self, parser):
        parser.add_argument("--admin", action="store_true")
        parser.add_argument("--username")
        parser.add_argument("--email")

    @transaction.atomic
    def handle(self, *args, **options):
        admin, _ = Group.objects.get_or_create(name="Administrador")
        operator, _ = Group.objects.get_or_create(name="Operador")
        permissions = Permission.objects.filter(
            content_type__app_label__in=[
                "usuarios",
                "auditoria",
                "cadastros",
                "pessoas",
                "ativos",
                "manutencoes",
                "arquivos",
                "importacoes",
                "termos",
                "movimentacoes",
            ]
        )
        # Não concede exclusão física nem edição de eventos/evidências.
        allowed = [
            p
            for p in permissions
            if not p.codename.startswith("delete_")
            and not (
                p.content_type.model
                in {"logauditoria", "movimentacao", "assinaturatermo", "responsabilidadeativo"}
                and not p.codename.startswith("view_")
            )
        ]
        admin.permissions.set(allowed)
        operator.permissions.set(
            [
                p
                for p in allowed
                if p.content_type.app_label not in {"usuarios", "auditoria"}
                and not (p.content_type.app_label == "cadastros" and not p.codename.startswith("view_"))
                and p.codename != "add_modelotermo"
            ]
        )
        for code, name in [
            ("EM_ESTOQUE", "Em Estoque"),
            ("EM_USO", "Em Uso"),
            ("EM_MANUTENCAO", "Em Manutenção"),
            ("BAIXADO", "Baixado"),
        ]:
            StatusAtivo.objects.get_or_create(codigo=code, defaults={"nome": name})
        if options["admin"]:
            username = options["username"] or input("Nome do administrador: ").strip()
            email = options["email"] or input("E-mail do administrador: ").strip()
            if "@" in username:
                raise CommandError("Use nome de usuário sem @ para evitar ambiguidade com e-mail.")
            if UsuarioTI.objects.filter(username__iexact=username).exists():
                raise CommandError("Usuário já existe; nenhuma senha foi sobrescrita.")
            password = getpass.getpass("Senha (mínimo 15 caracteres): ")
            if password != getpass.getpass("Confirme a senha: "):
                raise CommandError("Senhas diferentes.")
            user = UsuarioTI(username=username, email=email)
            try:
                validate_password(password, user)
                user.set_password(password)
                user.full_clean()
                user.save()
                user.groups.set([admin])
            except ValidationError as error:
                raise CommandError("; ".join(error.messages)) from error
        self.stdout.write(self.style.SUCCESS("Perfis e status estruturais preparados."))
