"""Regressao da navegacao contextual do shell administrativo (DU-UX-DASH-01)."""

import pytest
from django.urls import resolve

from gati.common import context


@pytest.mark.parametrize(
    ("path", "active", "labels"),
    [
        ("/", "dashboard", ("Visão geral",)),
        ("/cadastros/ativos/", "ativos", ("Inventário",)),
        ("/cadastros/ativos/17/", "ativos", ("Inventário", "Detalhes")),
        ("/cadastros/ativos/17/editar/", "ativos", ("Inventário", "Editar")),
        ("/cadastros/ativos/novo/", "ativos", ("Inventário", "Novo cadastro")),
        ("/cadastros/pessoas/17/", "pessoas", ("Pessoas", "Detalhes")),
        ("/cadastros/manutencoes/", "manutencoes", ("Manutenções",)),
        ("/cadastros/modelos-termo/", "modelos-termo", ("Modelos de termo",)),
        ("/cadastros/departamentos/", "settings", ("Cadastros auxiliares", "Departamentos")),
        ("/processos/", "processos", ("Entregas e devoluções",)),
        ("/processos/novo/1/", "processos", ("Entregas e devoluções", "Nova movimentação")),
        ("/processos/5/", "processos", ("Entregas e devoluções", "Detalhes")),
        ("/termos/", "termos", ("Termos",)),
        ("/termos/5/", "termos", ("Termos", "Detalhes")),
        ("/usuarios/", "users", ("Usuários de TI",)),
        ("/usuarios/novo/", "users", ("Usuários de TI", "Novo usuário")),
        ("/auditoria/", "audit", ("Auditoria",)),
        ("/configuracoes/", "settings", ("Cadastros auxiliares",)),
        ("/importar/ativos/", "ativos", ("Inventário", "Importação")),
        ("/senha/alterar/", None, ("Alterar senha",)),
    ],
)
def test_named_routes_map_to_single_navigation_group(path, active, labels):
    match = resolve(path)
    selected, breadcrumbs = context.resolve_navigation_state(match.url_name, match.kwargs)
    assert selected == active
    assert tuple(label for label, _url in breadcrumbs) == labels
    assert breadcrumbs[-1][1] is None
    assert all(url.startswith("/") for _label, url in breadcrumbs[:-1])


def test_unknown_resource_falls_back_without_reflecting_user_input():
    selected, breadcrumbs = context.resolve_navigation_state("listing", {"resource": "javascript-bad"})
    assert selected is None
    assert breadcrumbs == (("Gestão patrimonial", None),)


def test_unknown_route_falls_back_to_safe_breadcrumb():
    selected, breadcrumbs = context.resolve_navigation_state("unexpected_route", {})
    assert selected is None
    assert breadcrumbs == (("Gestão patrimonial", None),)


def test_dashboard_has_no_secondary_link():
    selected, breadcrumbs = context.resolve_navigation_state("dashboard", {})
    assert selected == "dashboard"
    assert breadcrumbs == (("Visão geral", None),)
