"""Contexto comum: ambiente, acesso administrativo e navegacao por rota resolvida."""

import os

from django.urls import reverse

from gati.apps.usuarios.permissions import is_admin

# Apenas recursos conhecidos aparecem nos breadcrumbs; nunca refletir slugs arbitrarios.
_CATALOGS = {
    "ativos": ("Inventário", "ativos"),
    "pessoas": ("Pessoas", "pessoas"),
    "manutencoes": ("Manutenções", "manutencoes"),
    "modelos-termo": ("Modelos de termo", "modelos-termo"),
    "departamentos": ("Departamentos", "settings"),
    "categorias-ativos": ("Categorias de ativo", "settings"),
    "localizacoes": ("Localizações", "settings"),
    "status-ativos": ("Status dos ativos", "settings"),
}

_CATALOG_ACTIONS = {
    "create": "Novo cadastro",
    "detail": "Detalhes",
    "edit": "Editar",
    "deactivate": "Inativar",
    "upload": "Arquivos",
}

_SECTIONS = {
    "processos": ("Entregas e devoluções", "process_list"),
    "termos": ("Termos", "term_list"),
    "users": ("Usuários de TI", "users"),
}

_SECTION_ROUTES = {
    "process_list": ("processos", None),
    "wizard": ("processos", "Nova movimentação"),
    "process_detail": ("processos", "Detalhes"),
    "process_edit": ("processos", "Editar"),
    "term_list": ("termos", None),
    "term_detail": ("termos", "Detalhes"),
    "term_items": ("termos", "Itens do termo"),
    "term_action": ("termos", "Ação do termo"),
    "signature_action": ("termos", "Assinaturas"),
    "users": ("users", None),
    "user_create": ("users", "Novo usuário"),
    "user_edit": ("users", "Editar usuário"),
}

_SINGLE_ROUTES = {
    "dashboard": ("dashboard", "Visão geral"),
    "settings": ("settings", "Cadastros auxiliares"),
    "audit": ("audit", "Auditoria"),
    "password_change": (None, "Alterar senha"),
}

_FALLBACK = (("Gestão patrimonial", None),)


def resolve_navigation_state(
    url_name: str | None, kwargs: dict[str, object]
) -> tuple[str | None, tuple[tuple[str, str | None], ...]]:
    """Devolve a secao ativa e breadcrumbs de rotas nomeadas, sem usar request.path."""
    if url_name in _SINGLE_ROUTES:
        active, label = _SINGLE_ROUTES[url_name]
        return active, ((label, None),)

    if url_name == "listing" or url_name in _CATALOG_ACTIONS:
        resource = kwargs.get("resource")
        if not isinstance(resource, str) or resource not in _CATALOGS:
            return None, _FALLBACK
        label, section = _CATALOGS[resource]
        root = (label, reverse("listing", kwargs={"resource": resource}))
        parent = (("Cadastros auxiliares", reverse("settings")),) if section == "settings" else ()
        if url_name == "listing":
            return section, (*parent, (label, None))
        return section, (*parent, root, (_CATALOG_ACTIONS[url_name], None))

    if url_name in _SECTION_ROUTES:
        section, page = _SECTION_ROUTES[url_name]
        label, route = _SECTIONS[section]
        if page is None:
            return section, ((label, None),)
        return section, ((label, reverse(route)), (page, None))

    if url_name in {"import", "import_template", "import_preview"}:
        kind = kwargs.get("kind")
        # A previa nao inclui o tipo no resolvedor; nao inferir pela URL nem pelo token UUID.
        if kind not in {"ativos", "pessoas"}:
            return None, _FALLBACK
        label, section = _CATALOGS[kind]
        return section, ((label, reverse("listing", kwargs={"resource": kind})), ("Importação", None))

    if url_name in {"privacy_report", "deidentify"}:
        return "pessoas", (
            ("Pessoas", reverse("listing", kwargs={"resource": "pessoas"})),
            ("Privacidade", None),
        )

    if url_name == "history_correction":
        return "ativos", (
            ("Inventário", reverse("listing", kwargs={"resource": "ativos"})),
            ("Retificação", None),
        )

    return None, _FALLBACK


def navigation(request):
    match = getattr(request, "resolver_match", None)
    active, breadcrumbs = resolve_navigation_state(
        getattr(match, "url_name", None), getattr(match, "kwargs", {}) or {}
    )
    return {
        "admin_funcional": is_admin(request.user),
        "ambiente": os.environ.get("GATI_ENV", "development"),
        "navigation_active": active,
        "navigation_breadcrumbs": breadcrumbs,
    }
