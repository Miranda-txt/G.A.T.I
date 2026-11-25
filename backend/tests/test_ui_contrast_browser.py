"""DASH05-08: contraste computado e foco em componentes reais via CDP."""

import json
import os
import shutil

import pytest
from test_dashboard_browser import _inline_assets, browser_session, dashboard_page

# Apenas superficies CSS solidas, sem imagens/gradientes. Nao e um scanner WCAG completo.
# Bordas de controles selecionados sao um requisito conservador do design system,
# nao um requisito universal para toda borda decorativa (WCAG 1.4.11).
MEASURE = """(selector, mode) => {
  const el = document.querySelector(selector);
  if (!el) return {error: 'amostra ausente'};
  const style = getComputedStyle(el);
  function rgba(value) {
    const parts = value.match(/[\\d.]+/g);
    if (!/^rgba?\\(/.test(value) || !parts || ![3, 4].includes(parts.length)) {
      throw new Error('Cor fora do escopo RGB: ' + value);
    }
    return [Number(parts[0]), Number(parts[1]), Number(parts[2]), Number(parts[3] ?? 1)];
  }
  function over(fg, bg) {
    return fg.slice(0, 3).map((v, i) => v * fg[3] + bg[i] * (1 - fg[3])).concat(1);
  }
  function background(node) {
    if (!node) return [255, 255, 255, 1];
    const css = getComputedStyle(node);
    if (css.backgroundImage !== 'none' || Number(css.opacity) !== 1) {
      throw new Error('Superficie requer revisao visual: ' + node.tagName);
    }
    const color = rgba(css.backgroundColor);
    return color[3] === 1 ? color : over(color, background(node.parentElement));
  }
  function luminance(color) {
    const rgb = color.slice(0, 3).map(v => {
      const x = v / 255;
      return x <= .04045 ? x / 12.92 : ((x + .055) / 1.055) ** 2.4;
    });
    return rgb[0] * .2126 + rgb[1] * .7152 + rgb[2] * .0722;
  }
  function contrast(a, b) {
    const values = [luminance(a), luminance(b)].sort((x, y) => y - x);
    return (values[0] + .05) / (values[1] + .05);
  }
  const bg = background(el);
  const adjacent = background(el.parentElement);
  const large = parseFloat(style.fontSize) >= 24 ||
    (parseFloat(style.fontSize) >= 18.6667 && Number(style.fontWeight) >= 700);
  if (mode === 'focus') {
    const rect = el.getBoundingClientRect();
    const x = Math.max(0, Math.min(innerWidth - 1, (rect.left + rect.right) / 2));
    const y = Math.max(0, Math.min(innerHeight - 1, (rect.top + rect.bottom) / 2));
    const hit = document.elementFromPoint(x, y);
    const near = parseFloat(style.outlineOffset) < 0 ? bg : adjacent;
    return {ratio: contrast(over(rgba(style.outlineColor), near), near), minimum: 3,
      focused: document.activeElement === el && el.matches(':focus-visible'),
      visible: el.contains(hit), outline: style.outlineStyle,
      width: parseFloat(style.outlineWidth), foreground: style.outlineColor, background: near};
  }
  if (mode === 'border') {
    const color = over(rgba(style.borderTopColor), bg);
    return {ratio: contrast(color, adjacent), minimum: 3, width: parseFloat(style.borderTopWidth),
      foreground: style.borderTopColor, background: adjacent};
  }
  const fg = mode === 'placeholder' ? getComputedStyle(el, '::placeholder').color : style.color;
  return {ratio: contrast(over(rgba(fg), bg), bg), minimum: large ? 3 : 4.5,
    foreground: fg, background: bg};
}"""


def measure(cdp, session, selector, mode):
    return cdp.evaluate(session, f"({MEASURE})({json.dumps(selector)}, {json.dumps(mode)})")


def verify(cdp, session, selector, mode, errors):
    result = measure(cdp, session, selector, mode)
    valid = "error" not in result and result["ratio"] >= result["minimum"]
    if mode == "focus":
        valid = (
            valid
            and result["focused"]
            and result["visible"]
            and result["outline"] not in ("none", "hidden")
            and result["width"] > 0
        )
    elif mode == "border":
        valid = valid and result["width"] > 0
    if not valid:
        errors.append(f"{selector} [{mode}]: {result}")


def key_tab(cdp, session):
    for event in ("keyDown", "keyUp"):
        cdp.call(
            "Input.dispatchKeyEvent",
            {"type": event, "key": "Tab", "code": "Tab", "windowsVirtualKeyCode": 9},
            session,
        )


def check_states(cdp, session, selector, errors):
    # Forca somente pseudoestados CSS, sem clicar/enviar formularios.
    cdp.call("DOM.enable", session=session)
    cdp.call("CSS.enable", session=session)
    root = cdp.call("DOM.getDocument", session=session)["root"]["nodeId"]
    node = cdp.call("DOM.querySelector", {"nodeId": root, "selector": selector}, session)["nodeId"]
    assert node, selector
    try:
        for state in ("hover", "active"):
            cdp.call("CSS.forcePseudoState", {"nodeId": node, "forcedPseudoClasses": [state]}, session)
            verify(cdp, session, selector, "text", errors)
    finally:
        cdp.call("CSS.forcePseudoState", {"nodeId": node, "forcedPseudoClasses": []}, session)


def test_rendered_contrast_and_focus(domain, client, tmp_path):
    browser = shutil.which("google-chrome") or shutil.which("chromium") or shutil.which("chromium-browser")
    if browser is None:
        if os.environ.get("GITHUB_ACTIONS") == "true":
            pytest.fail("Chromium/Chrome obrigatorio no CI de acessibilidade.")
        pytest.skip("Chromium/Chrome nao instalado no ambiente local.")

    login = client.get("/entrar/")
    invalid_login = client.post("/entrar/", {})
    warning = client.get("/assinar/")
    assert warning.status_code == 400
    client.force_login(domain.admin)
    pages = [
        (
            "login",
            login,
            [".public-card h1", ".form-label", ".public-foot", ".subtle-link", ".btn-primary"],
            [".form-control"],
            [".public-brand", ".form-control", ".btn-primary"],
            [".btn-primary", ".subtle-link"],
        ),
        ("login_invalid", invalid_login, [".field-error"], [], [], []),
        ("signature_error", warning, [".alert-warning"], [], [], []),
        (
            "dashboard",
            client.get("/"),
            [".sidebar nav a.selected", ".metric-card small", ".metric-link", ".btn-primary", ".status-line"],
            [".user-menu .btn-light"],
            [".sidebar nav a.selected", ".dashboard-create", ".metric-card", ".user-menu .btn-light"],
            [".sidebar nav a.selected", ".dashboard-create"],
        ),
        (
            "inventory",
            client.get("/cadastros/ativos/"),
            [".table thead th", ".record-primary", ".clear-filters", ".btn-outline-secondary", ".btn-dark"],
            [".filter-bar .form-control", ".filter-bar .form-select", ".btn-outline-secondary"],
            [".filter-bar .form-control", ".table-responsive", ".btn-outline-secondary"],
            [".btn-outline-secondary", ".btn-dark", ".record-primary"],
        ),
        (
            "wizard",
            client.get("/processos/novo/1/"),
            [".wizard-steps .current span", ".wizard-steps li:not(.current)", ".form-label"],
            [".form-select", ".btn-light"],
            [".form-select", ".btn-light"],
            [".btn-light"],
        ),
        (
            "user_form",
            client.get("/usuarios/novo/"),
            [".form-label", ".required"],
            [".form-check-input"],
            [".form-check-input"],
            [],
        ),
        (
            "asset_invalid",
            client.post("/cadastros/ativos/novo/", {"versao": 1}),
            [".field-error", ".required"],
            [],
            [],
            [],
        ),
    ]
    errors = []
    with browser_session(browser, tmp_path / "contrast-profile") as cdp:
        for kind, response, texts, borders, focuses, states in pages:
            assert response.status_code == (400 if kind == "signature_error" else 200), kind
            for width in (320, 1366):
                with dashboard_page(cdp, _inline_assets(response.content.decode()), width) as session:
                    failures = []
                    for selector in texts:
                        if width == 320 and selector.startswith(".sidebar"):
                            continue
                        verify(cdp, session, selector, "text", failures)
                    for selector in borders:
                        verify(cdp, session, selector, "border", failures)
                    if kind == "inventory":
                        verify(cdp, session, "#search", "placeholder", failures)
                    # Tab real estabelece modalidade teclado; focus() seleciona a amostra,
                    # sem afirmar que foi auditada toda a ordem de tabulacao.
                    key_tab(cdp, session)
                    for selector in focuses:
                        if width == 320 and selector.startswith(".sidebar"):
                            continue
                        cdp.evaluate(session, f"document.querySelector({json.dumps(selector)}).focus()")
                        verify(cdp, session, selector, "focus", failures)
                    for selector in states:
                        if width == 320 and selector.startswith(".sidebar"):
                            continue
                        check_states(cdp, session, selector, failures)
                    errors.extend(f"{kind}/{width}: {failure}" for failure in failures)
    assert not errors, "\n".join(errors)
