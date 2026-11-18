import os
from datetime import timedelta

from django.contrib.auth.models import Group
from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from gati.apps.ativos.models import Ativo
from gati.apps.cadastros.models import CategoriaAtivo, Departamento, Localizacao, StatusAtivo
from gati.apps.pessoas.models import Pessoa
from gati.apps.termos.models import ModeloTermo
from gati.apps.usuarios.models import UsuarioTI
from gati.common.catalog import save_record


class Command(BaseCommand):
    help = "Cria dados sintéticos locais. Exige GATI_DEMO_PASSWORD e não sobrescreve usuários existentes."

    @transaction.atomic
    def handle(self, *args, **options):
        if os.environ.get("GATI_ENV", "development") not in {"development", "test"}:
            raise CommandError("Demonstração proibida fora de development/test.")
        password = os.environ.get("GATI_DEMO_PASSWORD", "")
        if len(password) < 15:
            raise CommandError("Defina GATI_DEMO_PASSWORD com pelo menos 15 caracteres.")
        call_command("bootstrap_gati")
        user, created = UsuarioTI.objects.get_or_create(
            username="demo.admin",
            defaults={"email": "demo.admin@example.invalid", "first_name": "Equipe", "last_name": "de TI"},
        )
        if created:
            user.set_password(password)
            user.save()
            user.groups.set([Group.objects.get(name="Administrador")])
        elif not user.groups.filter(name="Administrador").exists():
            raise CommandError("Conta existente sem perfil esperado; não foi alterada.")
        department, _ = Departamento.objects.get_or_create(nome="Tecnologia da Informação")
        people = []
        for i, name in enumerate(
            ["Ana Souza (demonstração)", "Bruno Lima (demonstração)", "Carla Alves (demonstração)"]
        ):
            person, _ = Pessoa.objects.get_or_create(
                documento=f"90000000{i + 1:03}",
                defaults={
                    "nome": name,
                    "departamento": department,
                    "cargo": "Colaborador de demonstração",
                    "email": f"pessoa{i + 1}@example.invalid",
                },
            )
            people.append(person)
        office, _ = Localizacao.objects.get_or_create(nome="Sede · Escritório")
        stock, _ = Localizacao.objects.get_or_create(nome="Almoxarifado de TI")
        notebook, _ = CategoriaAtivo.objects.get_or_create(nome="Notebook")
        monitor, _ = CategoriaAtivo.objects.get_or_create(nome="Monitor")
        status = StatusAtivo.objects.get(codigo="EM_ESTOQUE")
        models = [
            "Latitude 5450",
            "ThinkPad E14",
            "ProBook 440",
            "Monitor P2425H",
            "ThinkCentre M70q",
            "Latitude 3550",
            "Monitor ThinkVision T24i",
            "EliteBook 640",
        ]
        for i, model in enumerate(models, 1):
            tag = f"GATI-{i:04}"
            if not Ativo.objects.filter(patrimonio=tag).exists():
                save_record(
                    user,
                    Ativo,
                    {
                        "patrimonio": tag,
                        "service_tag": f"DEMO{i:05}",
                        "numero_serie": f"SINTETICO{i:05}",
                        "modelo": model,
                        "categoria": monitor if "Monitor" in model else notebook,
                        "status": status,
                        "localizacao": stock,
                        "fabricante": "Demonstração",
                        "data_aquisicao": timezone.localdate() - timedelta(days=320),
                        "garantia_fim": timezone.localdate() + timedelta(days=12 * i),
                        "valor_aquisicao": 3200 + i * 100,
                    },
                )
        ModeloTermo.objects.get_or_create(
            nome="Termo padrão de responsabilidade",
            defaults={
                "texto": "TERMO DE {{ tipo }} DE EQUIPAMENTOS\n\nEu, {{ responsavel_nome }}, documento {{ responsavel_documento }}, do departamento {{ departamento }}, declaro estar ciente da movimentação dos equipamentos abaixo relacionados em {{ data }}.\n\nAtivos: {{ ativos }}.\nLocalização: {{ localizacao }}.\n\nComprometo-me a zelar pelos equipamentos, comunicar ocorrências à equipe de TI e observar as condições e os acessórios registrados neste documento.\n\nEste texto é um modelo demonstrativo e deve ser revisado pela organização antes do uso real."
            },
        )
        self.stdout.write(
            self.style.SUCCESS(
                "Dados sintéticos disponíveis. Login: demo.admin. Senha: a informada em GATI_DEMO_PASSWORD."
            )
        )
