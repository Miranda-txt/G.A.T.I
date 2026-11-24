"""Contratos da Visao Geral: valores reais, acessibilidade e estados vazios."""

import re
from datetime import timedelta

from django.utils import timezone

from gati.apps.movimentacoes.models import Movimentacao


def _metrics(html):
    return {
        href: (classes, body)
        for classes, href, body in re.findall(
            r'<a class="(metric-card[^"]*)" href="([^"]+)">(.*?)</a>', html, flags=re.S
        )
    }


def test_dashboard_empty_inventory_does_not_claim_warranties_are_current(domain, client):
    domain.asset.ativo = False
    domain.asset.save(update_fields=["ativo"])
    client.force_login(domain.operator)
    response = client.get("/")
    assert response.status_code == 200
    html = response.content.decode()
    assert response.context["total"] == 0
    assert response.context["warranty_count"] == 0
    assert "Nenhum ativo cadastrado" in html
    assert "Cadastre ativos e informe as datas de garantia." in html
    assert "Você está em dia por aqui" not in html
    metrics = _metrics(html)
    for href in (
        "/cadastros/ativos/",
        "/termos/?estado=AGUARDANDO_ASSINATURAS",
        "/cadastros/ativos/?garantia=30",
    ):
        classes, body = metrics[href]
        assert "amber" not in classes.split()
        assert re.search(r"<strong(?: [^>]*)?>\s*0\s*</strong>", body)


def test_dashboard_metrics_keep_real_values_and_filtered_links(domain, client):
    domain.asset.garantia_fim = timezone.localdate() + timedelta(days=30)
    domain.asset.save(update_fields=["garantia_fim"])
    client.force_login(domain.admin)
    response = client.get("/")
    assert response.status_code == 200
    metrics = _metrics(response.content.decode())
    expected = {
        "/cadastros/ativos/": 1,
        "/cadastros/pessoas/": 2,
        "/termos/?estado=AGUARDANDO_ASSINATURAS": 0,
        "/cadastros/ativos/?garantia=30": 1,
    }
    assert set(metrics) == set(expected)
    for href, count in expected.items():
        classes, body = metrics[href]
        assert re.search(rf"<strong(?: [^>]*)?>\s*{count}\s*</strong>", body)
        assert ("amber" in classes.split()) == (href == "/cadastros/ativos/?garantia=30")
    assert response.context["warranty_count"] == 1


def test_dashboard_sections_have_names_and_decorative_svg_icons(domain, client):
    client.force_login(domain.operator)
    response = client.get("/")
    assert response.status_code == 200
    html = response.content.decode()
    for heading in ("inventory-heading", "actions-heading", "activity-heading", "warranty-heading"):
        assert re.search(rf'<section\b[^>]*aria-labelledby="{heading}"', html)
        assert re.search(rf'<h2\b[^>]*id="{heading}"', html)
    for classes, body in _metrics(html).values():
        assert re.search(r'<svg\b[^>]*aria-hidden="true"[^>]*>', body)
    assert re.search(r'<progress\b[^>]*value="1"[^>]*max="1"[^>]*aria-label="[^"]+"', html)


def test_dashboard_renders_recent_activity_and_escapes_database_text(domain, client):
    description = "<script>alert(1)</script>"
    Movimentacao.objects.create(
        ativo=domain.asset, usuario=domain.operator, tipo="ENTREGA", descricao=description
    )
    client.force_login(domain.operator)
    response = client.get("/")
    assert response.status_code == 200
    html = response.content.decode()
    assert "&lt;script&gt;alert(1)&lt;/script&gt;" in html
    assert description not in html
    assert f'href="/cadastros/ativos/{domain.asset.pk}/"' in html
    assert 'class="timeline-item"' in html


def test_dashboard_css_is_loaded_only_on_dashboard(domain, client):
    public = client.get("/entrar/")
    assert public.status_code == 200
    assert b"gati-dashboard-v2.css" not in public.content
    client.force_login(domain.operator)
    dashboard = client.get("/")
    assert dashboard.status_code == 200
    assert b"gati-dashboard-v2.css" in dashboard.content
    listing = client.get("/cadastros/ativos/")
    assert listing.status_code == 200
    assert b"gati-dashboard-v2.css" not in listing.content
