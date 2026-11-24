"""Acessibilidade e autorizacao da navegacao compartilhada (DU-UX-DASH-01)."""

import re

import pytest
from django.test import RequestFactory

from gati.common.context import navigation


def _navigation(html):
    match = re.search(r'<nav aria-label="Navegação principal">(.*?)</nav>', html, flags=re.S)
    assert match is not None, "Navegacao principal ausente"
    return match.group(1)


@pytest.mark.parametrize(
    ("path", "href"),
    [
        ("/", "/"),
        ("/cadastros/ativos/", "/cadastros/ativos/"),
        ("/cadastros/pessoas/", "/cadastros/pessoas/"),
        ("/cadastros/modelos-termo/", "/cadastros/modelos-termo/"),
        ("/processos/", "/processos/"),
        ("/termos/", "/termos/"),
        ("/configuracoes/", "/configuracoes/"),
        ("/usuarios/", "/usuarios/"),
        ("/auditoria/", "/auditoria/"),
    ],
)
def test_admin_navigation_has_one_active_link(domain, client, path, href):
    client.force_login(domain.admin)
    response = client.get(path)
    assert response.status_code == 200, path
    navigation = _navigation(response.content.decode("utf-8"))
    assert navigation.count('class="selected"') == 1
    assert navigation.count('aria-current="page"') == 1
    assert f'href="{href}" class="selected" aria-current="page"' in navigation


def test_deep_asset_route_keeps_inventory_active(domain, client):
    client.force_login(domain.operator)
    response = client.get(f"/cadastros/ativos/{domain.asset.pk}/")
    assert response.status_code == 200
    html = response.content.decode("utf-8")
    navigation = _navigation(html)
    assert 'href="/cadastros/ativos/" class="selected" aria-current="page"' in navigation
    assert '<nav class="breadcrumb-label" aria-label="Trilha de navegação">' in html
    assert 'href="/cadastros/ativos/">Inventário</a>' in html
    assert '<span aria-current="page">Detalhes</span>' in html


def test_operator_does_not_receive_admin_navigation(domain, client):
    client.force_login(domain.operator)
    response = client.get("/")
    assert response.status_code == 200
    navigation = _navigation(response.content.decode("utf-8"))
    assert 'href="/usuarios/"' not in navigation
    assert 'href="/configuracoes/"' not in navigation
    assert 'href="/auditoria/"' not in navigation
    assert client.get("/usuarios/").status_code == 403


def test_breadcrumb_does_not_escape_trusted_route_urls(domain, client):
    client.force_login(domain.admin)
    response = client.get("/cadastros/ativos/")
    assert response.status_code == 200
    html = response.content.decode("utf-8")
    assert '<nav class="breadcrumb-label" aria-label="Trilha de navegação">' in html
    assert '<span aria-current="page">Inventário</span>' in html
    assert 'href="/">GATI</a>' in html


def test_unknown_direct_context_does_not_make_public_nav_links(domain):
    request = RequestFactory().get("/unknown/")
    request.user = domain.operator
    context = navigation(request)
    assert context["navigation_active"] is None
    assert context["navigation_breadcrumbs"] == (("Gestão patrimonial", None),)
