from datetime import timedelta

from django.db.models import Count
from django.shortcuts import render
from django.utils import timezone

from gati.apps.ativos.models import Ativo
from gati.apps.manutencoes.models import Manutencao
from gati.apps.movimentacoes.models import Movimentacao
from gati.apps.pessoas.models import Pessoa
from gati.apps.termos.models import Termo
from gati.common.web import internal


@internal
def dashboard(request):
    assets = Ativo.objects.filter(ativo=True)
    warranty = assets.filter(
        garantia_fim__range=(timezone.localdate(), timezone.localdate() + timedelta(days=30))
    ).order_by("garantia_fim")
    pending = Termo.objects.filter(estado="AGUARDANDO_ASSINATURAS")
    return render(
        request,
        "dashboard.html",
        {
            "total": assets.count(),
            "people": Pessoa.objects.filter(ativo=True).count(),
            "pending_count": pending.count(),
            "warranty_count": warranty.count(),
            "warranty": warranty[:8],
            "pending": pending.select_related("processo__responsavel")[:6],
            "statuses": assets.values("status__nome", "status__codigo")
            .annotate(total=Count("id"))
            .order_by("-total"),
            "history": Movimentacao.objects.select_related("ativo", "usuario")[:6],
            "maintenance_count": Manutencao.objects.filter(data_fim__isnull=True).count(),
        },
    )
