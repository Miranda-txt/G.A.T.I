"""Smoke de navegador com viewport real via CDP, sem tempo virtual nem iframe."""

import json
import os
import re
import select
import shutil
import subprocess
import tempfile
import time
from contextlib import contextmanager
from pathlib import Path

import pytest
from django.utils import timezone

STATIC = Path(__file__).resolve().parents[1] / "static"
WIDTHS = (320, 375, 683, 768, 900, 901, 910, 1024, 1093, 1366, 1920)


class CDP:
    """Transporte CDP local por pipes anonimos; sem porta de depuracao."""

    def __init__(self, process):
        self.process = process
        self.sequence = 0
        self.pending = b""

    def call(self, method, params=None, session=None):
        self.sequence += 1
        request = {"id": self.sequence, "method": method, "params": params or {}}
        if session is not None:
            request["sessionId"] = session
        self.process.stdin.write(json.dumps(request).encode() + b"\0")
        self.process.stdin.flush()
        deadline = time.monotonic() + 15
        while time.monotonic() < deadline:
            while b"\0" in self.pending:
                raw, self.pending = self.pending.split(b"\0", 1)
                message = json.loads(raw)
                if message.get("id") == self.sequence:
                    if "error" in message:
                        raise RuntimeError(f"{method}: {message['error']}")
                    return message.get("result", {})
            ready, _, _ = select.select([self.process.stdout], [], [], max(0, deadline - time.monotonic()))
            if not ready:
                break
            chunk = os.read(self.process.stdout.fileno(), 65536)
            if not chunk:
                raise RuntimeError(f"{method}: navegador encerrou o pipe CDP")
            self.pending += chunk
        raise TimeoutError(f"{method}: timeout CDP")

    def evaluate(self, session, expression):
        result = self.call(
            "Runtime.evaluate",
            {"expression": expression, "returnByValue": True, "awaitPromise": True},
            session,
        )
        if "exceptionDetails" in result:
            raise RuntimeError(result["exceptionDetails"])
        return result["result"].get("value")

    def viewport(self, session, width):
        self.call(
            "Emulation.setDeviceMetricsOverride",
            {"width": width, "height": 768, "deviceScaleFactor": 1, "mobile": False},
            session,
        )


@contextmanager
def browser_session(browser, profile):
    # O shell apenas mapeia stdin/stdout para os descritores 3/4 exigidos
    # pelo Chromium. Argumentos sao posicionais, nunca interpolados no comando.
    with (
        tempfile.TemporaryFile() as stderr,
        subprocess.Popen(
            [
                "bash",
                "-c",
                'exec 3<&0 4>&1; exec "$@" 1>&2',
                "gati-cdp",
                browser,
                "--headless",
                "--disable-gpu",
                "--disable-background-networking",
                "--disable-dev-shm-usage",
                "--no-first-run",
                f"--user-data-dir={profile}",
                "--remote-debugging-pipe",
                "about:blank",
            ],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=stderr,
        ) as process,
    ):
        try:
            yield CDP(process)
        except (RuntimeError, TimeoutError, BrokenPipeError) as exc:
            stderr.seek(0)
            raise AssertionError(f"{exc}; navegador: {stderr.read(3000).decode(errors='replace')}") from exc
        finally:
            if process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait(timeout=5)


# Espera apenas o evento de media query do navegador, nunca o estado esperado
# da aplicacao. Um evento ausente continua sendo falha apos 2s reais.
ARM_RESIZE = """void (window.__gatiResize = new Promise(resolve => {
  const media = matchMedia('(max-width: 900px)');
  function changed(event) {
    clearTimeout(timeout);
    setTimeout(() => resolve({matches: event.matches, width: innerWidth}), 0);
  }
  const timeout = setTimeout(() => {
    media.removeEventListener('change', changed);
    resolve({timeout: true, matches: media.matches, width: innerWidth});
  }, 2000);
  media.addEventListener('change', changed, {once: true});
}))"""

READY = """new Promise(resolve => {
  if (document.readyState === 'complete') resolve(true);
  else window.addEventListener('load', () => resolve(true), {once: true});
})"""

CHECK_LAYOUT = """(width) => {
  const win = window;
  const doc = document;
  const root = doc.documentElement;
  const errors = [];
  const diagnostics = [];
  const check = (ok, message) => { if (!ok) errors.push(message); };
  function snapshot(stage) {
    const sidebar = doc.getElementById('app-sidebar');
    const menu = doc.querySelector('.menu-button');
    return {stage, requested: width, viewport: win.innerWidth, clientWidth: root.clientWidth,
      mobile: win.matchMedia('(max-width: 900px)').matches, inert: sidebar.inert,
      visibility: win.getComputedStyle(sidebar).visibility,
      menuDisplay: win.getComputedStyle(menu).display,
      navOpen: doc.body.classList.contains('nav-open'), initial: win.__gatiTestInitial || null};
  }
  diagnostics.push(snapshot('load'));
  check(win.__gatiTestInitial?.width === width, width + ': viewport inicial incorreto');
  check(win.__gatiTestInitial?.mobile === (width <= 900), width + ': media query inicial incorreta');
  const label = doc.querySelector('.metric-top > span:first-child');
  const main = doc.querySelector('main');
  root.style.fontSize = '16px';
  const normal = parseFloat(win.getComputedStyle(label).fontSize);
  check(root.scrollWidth <= root.clientWidth + 1, width + ': overflow normal');
  root.style.fontSize = '32px';
  const large = parseFloat(win.getComputedStyle(label).fontSize);
  check(large >= normal * 1.99, width + ': fonte nao dobrou');
  check(root.scrollWidth <= root.clientWidth + 1, width + ': overflow fonte 200%');
  root.style.fontSize = '16px';
  diagnostics.push(snapshot('after-font-scaling'));
  const menu = doc.querySelector('.menu-button');
  const close = doc.querySelector('.shell-close');
  const sidebar = doc.getElementById('app-sidebar');
  const workspace = doc.querySelector('.workspace');
  check(Math.abs(win.innerWidth - width) <= 1, width + ': viewport incorreto');
  check(win.matchMedia('(max-width: 900px)').matches === (width <= 900),
    width + ': media query divergente');
  if (width <= 900) {
    check(sidebar.inert, width + ': sidebar fechada focavel');
    menu.focus();
    menu.click();
    check(menu.getAttribute('aria-expanded') === 'true', width + ': menu nao abriu');
    check(doc.activeElement === close && workspace.inert, width + ': foco modal');
    const links = sidebar.querySelectorAll('nav a');
    const last = links[links.length - 1];
    last.focus();
    last.dispatchEvent(new win.KeyboardEvent('keydown', {key: 'Tab', bubbles: true, cancelable: true}));
    check(doc.activeElement === sidebar.querySelector('.brand'), width + ': ciclo Tab');
    doc.activeElement.dispatchEvent(new win.KeyboardEvent('keydown', {
      key: 'Tab', shiftKey: true, bubbles: true, cancelable: true
    }));
    check(doc.activeElement === last, width + ': ciclo Shift+Tab');
    last.dispatchEvent(new win.KeyboardEvent('keydown', {key: 'Escape', bubbles: true, cancelable: true}));
    check(menu.getAttribute('aria-expanded') === 'false', width + ': Escape nao fechou');
    check(doc.activeElement === menu && !workspace.inert, width + ': retorno de foco');
  } else {
    check(!sidebar.inert, width + ': sidebar desktop inerte');
  }
  main.focus();
  check(doc.activeElement === main, width + ': destino do atalho de conteudo');
  return {errors, diagnostics};
}"""

MENU_STATE = """(() => {
  const sidebar = document.getElementById('app-sidebar');
  const workspace = document.querySelector('.workspace');
  const menu = document.querySelector('.menu-button');
  const close = document.querySelector('.shell-close');
  return {width: innerWidth, mobile: matchMedia('(max-width: 900px)').matches,
    sidebarInert: sidebar.inert, workspaceInert: workspace.inert,
    modal: sidebar.hasAttribute('aria-modal'), expanded: menu.getAttribute('aria-expanded'),
    focusClose: document.activeElement === close, focusMenu: document.activeElement === menu,
    focusDesktopLink: document.activeElement === sidebar.querySelector('a.selected')};
})()"""


def _inline_assets(html):
    def stylesheet(match):
        path = STATIC / match[1]
        return f"<style>{path.read_text(encoding='utf-8')}</style>"

    def script(match):
        path = STATIC / match[1]
        source = path.read_text(encoding="utf-8").replace("</script", r"<\/script")
        return f"<script>{source}</script>"

    html = re.sub(r'<link rel="stylesheet" href="/static/([^"]+)">', stylesheet, html)
    html = re.sub(r'<script src="/static/([^"]+)" defer></script>', script, html)
    # Captura a largura antes da inicializacao do shell, sem modificar o codigo real.
    probe = """<script>document.addEventListener('DOMContentLoaded', () => {
      window.__gatiTestInitial = {width: innerWidth,
        mobile: matchMedia('(max-width: 900px)').matches};
    });</script>"""
    return html.replace("</title>", "</title>" + probe, 1)


@contextmanager
def dashboard_page(cdp, html, width):
    target = cdp.call("Target.createTarget", {"url": "about:blank"})["targetId"]
    try:
        session = cdp.call("Target.attachToTarget", {"targetId": target, "flatten": True})["sessionId"]
        cdp.call("Target.activateTarget", {"targetId": target})
        cdp.viewport(session, width)
        assert cdp.evaluate(session, "innerWidth") == width, "Viewport antes da carga incorreto."
        # HTML sintetico e assets locais, sem acesso aos servicos reais.
        cdp.call("Network.enable", session=session)
        cdp.call("Network.setBlockedURLs", {"urls": ["http://*", "https://*"]}, session)
        frame_id = cdp.call("Page.getFrameTree", session=session)["frameTree"]["frame"]["id"]
        cdp.call("Page.setDocumentContent", {"frameId": frame_id, "html": html}, session)
        assert cdp.evaluate(session, READY) is True
        yield session
    finally:
        cdp.call("Target.closeTarget", {"targetId": target})


def resize(cdp, session, width, mobile):
    cdp.evaluate(session, ARM_RESIZE)
    cdp.viewport(session, width)
    event = cdp.evaluate(session, "window.__gatiResize")
    state = cdp.evaluate(session, MENU_STATE)
    assert event == {"matches": mobile, "width": width}, {"event": event, "state": state}
    assert state["width"] == width and state["mobile"] is mobile, state
    return state


def check_bidirectional_resize(cdp, session):
    cdp.evaluate(session, "document.querySelector('.menu-button').click()")
    state = cdp.evaluate(session, MENU_STATE)
    assert state["workspaceInert"] and not state["sidebarInert"], state
    assert state["focusClose"], state

    # Mobile aberto -> desktop: o modal precisa terminar e a sidebar voltar a funcionar.
    state = resize(cdp, session, 910, False)
    assert not state["sidebarInert"] and not state["workspaceInert"], state
    assert not state["modal"] and state["expanded"] == "false", state
    cdp.evaluate(session, "document.querySelector('#app-sidebar a.selected').focus()")
    state = cdp.evaluate(session, MENU_STATE)
    assert state["focusDesktopLink"], state

    # Desktop -> mobile: o menu precisa fechar, reabrir e restaurar o foco.
    state = resize(cdp, session, 768, True)
    assert state["sidebarInert"] and not state["workspaceInert"], state
    assert not state["modal"] and state["expanded"] == "false", state
    cdp.evaluate(session, "document.querySelector('.menu-button').focus()")
    cdp.evaluate(session, "document.querySelector('.menu-button').click()")
    state = cdp.evaluate(session, MENU_STATE)
    assert state["focusClose"] and state["workspaceInert"], state
    cdp.evaluate(session, "document.querySelector('.shell-close').click()")
    state = cdp.evaluate(session, MENU_STATE)
    assert state["focusMenu"] and not state["workspaceInert"], state


def test_dashboard_chromium_reflow_font_scaling_and_keyboard(domain, client, tmp_path):
    browser = shutil.which("google-chrome") or shutil.which("chromium") or shutil.which("chromium-browser")
    if browser is None:
        if os.environ.get("GITHUB_ACTIONS") == "true":
            pytest.fail("Chromium/Chrome obrigatorio no CI de acessibilidade.")
        pytest.skip("Chromium/Chrome nao instalado no ambiente local.")
    client.force_login(domain.admin)
    response = client.get("/")
    assert response.status_code == 200
    html = _inline_assets(response.content.decode())

    with browser_session(browser, tmp_path / "browser-profile") as cdp:
        version = cdp.call("Browser.getVersion")["product"]
        errors = []
        diagnostics = []
        for width in WIDTHS:
            with dashboard_page(cdp, html, width) as session:
                outcome = cdp.evaluate(session, f"({CHECK_LAYOUT})({width})")
                errors.extend(outcome["errors"])
                diagnostics.extend(outcome["diagnostics"])
        assert not errors, {"browser": version, "errors": errors, "diagnostics": diagnostics}

        with dashboard_page(cdp, html, 768) as session:
            check_bidirectional_resize(cdp, session)


# Testa o HTML real dos componentes sem enviar requisicoes ao ambiente publicado.
CHECK_SHARED = """(kind) => {
  const errors = [];
  const check = (ok, message) => { if (!ok) errors.push(message); };
  if (kind === 'users') {
    const table = document.querySelector('main table');
    const wrapper = table.closest('.table-responsive');
    check(!!wrapper, 'tabela sem regiao responsiva');
    if (wrapper) {
      check(wrapper.getAttribute('role') === 'region' && !!wrapper.getAttribute('aria-label'),
        'regiao de tabela sem nome acessivel');
      wrapper.focus();
      check(document.activeElement === wrapper, 'regiao de tabela nao focavel');
      if (wrapper.scrollWidth > wrapper.clientWidth) {
        wrapper.scrollLeft = 40;
        check(wrapper.scrollLeft > 0, 'rolagem horizontal interna indisponivel');
      }
    }
    check(document.documentElement.scrollWidth <= innerWidth + 1, 'overflow do documento');
  } else if (kind === 'empty') {
    const table = document.querySelector('#records table');
    check(table.tBodies[0].rows[0].cells[0].colSpan === table.tHead.rows[0].cells.length,
      'colspan da linha vazia diverge do cabecalho');
  } else if (kind === 'wizard') {
    const current = document.querySelectorAll('.wizard-steps [aria-current="step"]');
    check(current.length === 1 && current[0].classList.contains('current'),
      'etapa atual sem semantica');
    const field = document.querySelector('[name="ativos"]');
    const ids = (field.getAttribute('aria-describedby') || '').split(/\\s+/).filter(Boolean);
    check(field.getAttribute('aria-invalid') === 'true', 'campo invalido sem estado');
    check(ids.length === 2 && ids.every(id => !!document.getElementById(id)),
      'ajuda ou erro sem destino');
  }
  return errors;
}"""


def test_shared_components_chromium(domain, client, tmp_path):
    browser = shutil.which("google-chrome") or shutil.which("chromium") or shutil.which("chromium-browser")
    if browser is None:
        if os.environ.get("GITHUB_ACTIONS") == "true":
            pytest.fail("Chromium/Chrome obrigatorio no CI de acessibilidade.")
        pytest.skip("Chromium/Chrome nao instalado no ambiente local.")
    client.force_login(domain.admin)
    domain.outsider.username = "u" * 150
    domain.outsider.first_name = "N" * 150
    domain.outsider.save(update_fields=["username", "first_name"])
    users = client.get("/usuarios/")
    empty = client.get("/cadastros/ativos/?q=SEM-REGISTROS-TESTE-05")
    assert (
        client.post(
            "/processos/novo/1/",
            {
                "tipo": "ENTREGA",
                "localizacao": domain.destination.pk,
                "data": timezone.localdate().isoformat(),
            },
        ).status_code
        == 302
    )
    assert client.post("/processos/novo/2/", {"responsavel": domain.person.pk}).status_code == 302
    wizard = client.post("/processos/novo/3/", {})
    pages = [("users", users), ("empty", empty), ("wizard", wizard)]
    errors = []
    with browser_session(browser, tmp_path / "shared-browser-profile") as cdp:
        for kind, response in pages:
            assert response.status_code == 200, kind
            html = _inline_assets(response.content.decode())
            for width in (320, 768, 1366):
                with dashboard_page(cdp, html, width) as session:
                    outcome = cdp.evaluate(session, f"({CHECK_SHARED})({json.dumps(kind)})")
                    errors.extend(f"{kind}/{width}: {error}" for error in outcome)
    assert not errors, errors


# DASH05-05: mede a cascata real em telas publicas e administrativas.
# A escala da fonte raiz simula a preferencia de tamanho de texto, nao zoom nativo.
CHECK_LEGACY_SCALING = """(selectors) => {
  const root = document.documentElement;
  const errors = [];
  const samples = selectors.map(selector => ({selector, element: document.querySelector(selector)}));
  const missing = samples.filter(sample => !sample.element).map(sample => sample.selector);
  if (missing.length) return ['seletores ausentes: ' + missing.join(', ')];
  function measure(size) {
    root.style.fontSize = size + 'px';
    const label = 'fonte raiz ' + size;
    const fonts = samples.map(sample => parseFloat(getComputedStyle(sample.element).fontSize));
    if (root.scrollWidth > root.clientWidth + 1) {
      const offenders = [...document.querySelectorAll('body *')].filter(element => {
        const container = element.closest('.table-responsive, .detail-tabs');
        if (container && container !== element) return false;
        const rect = element.getBoundingClientRect();
        return rect.width > 0 && rect.right > root.clientWidth + 1
          && getComputedStyle(element).visibility === 'visible';
      }).slice(0, 10).map(element => element.tagName + '.' + element.className);
      errors.push(label + ': overflow documento ' + root.scrollWidth + '/' + root.clientWidth
        + ' [' + offenders.join(', ') + ']');
    }
    for (const element of document.querySelectorAll(
      'main .panel, .public-card, .public-brand, .filter-bar, .wizard-steps, .form-actions, .button-group'
    )) {
      if (element.clientWidth && element.scrollWidth > element.clientWidth + 1) {
        errors.push(label + ': overflow ' + element.className + ' '
          + element.scrollWidth + '/' + element.clientWidth);
      }
    }
    return fonts;
  }
  const normal = measure(16);
  const large = measure(32);
  for (const [index, sample] of samples.entries()) {
    if (large[index] < normal[index] * 1.99) {
      errors.push(sample.selector + ': fonte nao escala ' + normal[index] + ' -> ' + large[index]);
    }
  }
  root.style.fontSize = '16px';
  return errors;
}"""


def test_legacy_typography_reflows_at_double_root_font_size(domain, client, tmp_path):
    browser = shutil.which("google-chrome") or shutil.which("chromium") or shutil.which("chromium-browser")
    if browser is None:
        if os.environ.get("GITHUB_ACTIONS") == "true":
            pytest.fail("Chromium/Chrome obrigatorio no CI de acessibilidade.")
        pytest.skip("Chromium/Chrome nao instalado no ambiente local.")

    login = client.get("/entrar/")
    client.force_login(domain.admin)
    pages = [
        (
            "login",
            login,
            [
                ".public-brand small",
                ".public-card h1",
                ".form-label",
                ".form-control",
                ".btn",
                ".public-foot",
            ],
        ),
        (
            "inventory",
            client.get("/cadastros/ativos/"),
            [
                "main h1",
                ".filter-bar .form-control",
                ".filter-bar .btn",
                ".table th",
                ".table td",
                ".table-footer",
            ],
        ),
        (
            "form",
            client.post("/cadastros/ativos/novo/", {"versao": 1}),
            ["main h1", ".form-label", ".form-control", ".field-error", ".form-actions .btn"],
        ),
        (
            "detail",
            client.get(f"/cadastros/ativos/{domain.asset.pk}/"),
            ["main h1", ".detail-tabs a", ".details-grid dt", ".details-grid dd", ".detail-section h2"],
        ),
        (
            "wizard",
            client.get("/processos/novo/1/"),
            [
                "main h1",
                ".wizard-steps li",
                ".form-panel h2",
                ".form-label",
                ".form-select",
                ".form-actions .btn",
            ],
        ),
    ]
    errors = []
    with browser_session(browser, tmp_path / "typography-browser-profile") as cdp:
        for kind, response, selectors in pages:
            assert response.status_code == 200, kind
            html = _inline_assets(response.content.decode())
            for width in (320, 768, 900, 901, 1366, 1920):
                with dashboard_page(cdp, html, width) as session:
                    outcome = cdp.evaluate(session, f"({CHECK_LEGACY_SCALING})({json.dumps(selectors)})")
                    errors.extend(f"{kind}/{width}: {error}" for error in outcome)
    assert not errors, "\n".join(errors)
