"""Regressoes de acessibilidade da Visao Geral e do shell (DU-UX-DASH-04)."""

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_inventory_distribution_announces_count_and_total(domain, client):
    client.force_login(domain.operator)
    response = client.get("/")
    assert response.status_code == 200
    html = response.content.decode()
    assert re.search(
        r'<progress\b[^>]*value="1"[^>]*max="1"[^>]*aria-label="[^"]+"'
        r'[^>]*aria-valuetext="1 de 1 ativo"[^>]*>',
        html,
    )


def test_dashboard_list_semantics_are_explicit_with_custom_list_styles(domain, client):
    client.force_login(domain.operator)
    response = client.get("/")
    assert response.status_code == 200
    assert '<ul class="status-list" role="list">' in response.content.decode()


def test_dashboard_typography_respects_user_default_font_size():
    css = (ROOT / "static/gati/css/gati-dashboard-v2.css").read_text(encoding="utf-8")
    # Pixels fixos impedem que a fonte padrao escolhida pelo usuario escale o texto.
    assert not re.search(r"font-size:\s*(?:clamp\([^;]*?)?\d+(?:\.\d+)?px\b", css)


def test_shell_typography_respects_user_default_font_size():
    css = (ROOT / "static/gati/css/gati-shell-v2.css").read_text(encoding="utf-8")
    assert not re.search(r"font-size:\s*\d+(?:\.\d+)?px\b", css)
