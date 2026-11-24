"""Contrato estatico do shell: sem banco, dependencias ou recursos remotos."""

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_shell_uses_shared_decorative_svg_icons():
    html = (ROOT / "templates/base.html").read_text(encoding="utf-8")
    icon = ROOT / "templates/components/ui_icon.html"
    assert icon.is_file(), "Componente SVG compartilhado ausente"
    svg = icon.read_text(encoding="utf-8")
    assert re.findall(r"<svg\b[^>]*>", svg) == [
        '<svg class="ui-icon" width="20" height="20" viewBox="0 0 24 24" fill="none" '
        'stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round" '
        'aria-hidden="true" focusable="false">'
    ]
    names = re.findall(r"name == '([a-z-]+)'", svg)
    includes = re.findall(r"include 'components/ui_icon.html' with name='([a-z-]+)' only", html)
    assert len(includes) == 13
    assert set(includes) <= set(names)
    assert len(set(names)) == len(names)
    assert "<script" not in svg and "<use" not in svg and "|safe" not in svg
    assert re.search(r'<span class="nav-icon">[^<{]*[\u0080-\uffff]', html) is None


def test_shell_styles_preserve_semantic_tokens_and_progressive_enhancement():
    css = (ROOT / "static/gati/css/gati-shell-v2.css").read_text(encoding="utf-8")
    assert not re.search(r"#[0-9a-fA-F]{3,8}\b", css)
    assert "@import" not in css and "url(" not in css
    assert "var(--sidebar)" in css and "var(--surface)" in css
    assert "@media (max-width: 900px)" in css
    assert ".nav-enhanced .app-shell .sidebar" in css
    assert "@media (prefers-reduced-motion: reduce)" in css
    assert "@media print" in css
