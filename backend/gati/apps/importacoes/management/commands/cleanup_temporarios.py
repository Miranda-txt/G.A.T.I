from datetime import timedelta

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from gati.apps.importacoes.models import ImportacaoExecucao
from gati.apps.importacoes.services import temp_path
from gati.apps.termos.models import SessaoAssinatura
from gati.apps.usuarios.models import LoginFailure


class Command(BaseCommand):
    help = "Expira prévias após 1h e limpa resíduos privados após 24h."

    def handle(self, *args, **options):
        now = timezone.now()
        count = 0
        for pk in ImportacaoExecucao.objects.filter(
            estado="PREVIEW", criado_em__lt=now - timedelta(hours=1)
        ).values_list("pk", flat=True):
            with transaction.atomic():
                job = ImportacaoExecucao.objects.select_for_update().get(pk=pk)
                if job.estado == "PREVIEW":
                    job.estado = "EXPIRADA"
                    job.concluido_em = now
                    job.save()
                    transaction.on_commit(lambda path=temp_path(job): path.unlink(missing_ok=True))
                    count += 1
        for area in ["quarantine", "imports"]:
            directory = settings.RUNTIME / area
            if directory.exists():
                for path in directory.iterdir():
                    if path.is_file() and now.timestamp() - path.stat().st_mtime > 86400:
                        path.unlink()
                        count += 1
        LoginFailure.objects.filter(criado_em__lt=now - timedelta(days=1)).delete()
        SessaoAssinatura.objects.filter(criada_em__lt=now - timedelta(hours=2)).update(encerrada=True)
        self.stdout.write(f"{count} temporários expirados ou removidos.")
