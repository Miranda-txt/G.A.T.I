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


def test_shell_controls_and_decorative_icons_render_for_admin(domain, client):
    client.force_login(domain.admin)
    response = client.get("/")
    assert response.status_code == 200
    html = response.content.decode("utf-8")
    nav = _navigation(html)
    assert nav.count('<svg class="ui-icon"') == 10
    assert nav.count('aria-hidden="true" focusable="false"') == 10
    assert '<aside class="sidebar" id="app-sidebar">' in html
    assert 'aria-controls="app-sidebar"' in html
    assert 'aria-expanded="false"' in html
    assert 'aria-label="Fechar navegação"' in html
    assert '<main id="main" class="main-content" tabindex="-1">' in html
    assert '<form method="post" action="/sair/">' in html
    assert 'name="csrfmiddlewaretoken"' in html
    assert 'href="/senha/alterar/"' in html
    assert 'class="shell-backdrop" hidden aria-hidden="true"' in html


def test_shell_is_not_loaded_in_public_or_htmx_partial_views(domain, client):
    public = client.get("/entrar/")
    assert public.status_code == 200
    assert b"gati-shell-v2.css" not in public.content
    assert b'id="app-sidebar"' not in public.content
    client.force_login(domain.operator)
    partial = client.get("/cadastros/ativos/", HTTP_HX_REQUEST="true")
    assert partial.status_code == 200
    assert b'id="app-sidebar"' not in partial.content
