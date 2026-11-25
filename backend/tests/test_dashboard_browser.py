"""Smoke de Chromium sobre HTML real do Django e arquivos estaticos locais."""

import os
import re
import shutil
import subprocess
from html import escape, unescape
from pathlib import Path

import pytest

STATIC = Path(__file__).resolve().parents[1] / "static"

# O documento externo somente hospeda fixtures sinteticas; nenhum servidor e acessado.
HARNESS = """
<!doctype html><meta charset="utf-8">
<textarea id="fixture" hidden>FIXTURE</textarea><pre id="result" data-state="pending"></pre>
<script>
const widths = [320, 375, 683, 768, 910, 1024, 1093, 1366, 1920];
const errors = [];
const diagnostics = [];
const result = document.getElementById('result');
const source = document.getElementById('fixture').value;
let index = 0;
function check(ok, message) { if (!ok) errors.push(message); }
function next() {
  if (index === widths.length) {
    result.dataset.state = errors.length ? 'failed' : 'passed';
    result.textContent = JSON.stringify({errors, diagnostics});
    return;
  }
  const width = widths[index++];
  const frame = document.createElement('iframe');
  frame.width = width;
  frame.height = 768;
  frame.onload = () => {
    const doc = frame.contentDocument;
    if (!doc.querySelector('.dashboard-v2')) return;
    const win = frame.contentWindow;
    const root = doc.documentElement;
    function snapshot(stage) {
      const sidebar = doc.getElementById('app-sidebar');
      const menu = doc.querySelector('.menu-button');
      diagnostics.push({stage, requested: width, frameWidth: frame.clientWidth,
        viewport: win.innerWidth, clientWidth: root.clientWidth,
        mobile: win.matchMedia('(max-width: 900px)').matches,
        inert: sidebar.inert, visibility: win.getComputedStyle(sidebar).visibility,
        menuDisplay: win.getComputedStyle(menu).display,
        navOpen: doc.body.classList.contains('nav-open'),
        initial: win.__gatiTestInitial || null});
    }
    snapshot('load');
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
    snapshot('after-font-scaling');
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
    frame.remove();
    next();
  };
  frame.srcdoc = source;
  document.body.append(frame);
}
next();
</script>
"""


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


def test_dashboard_chromium_reflow_font_scaling_and_keyboard(domain, client, tmp_path):
    # Chrome stable usa o perfil AppArmor do pacote oficial no runner Ubuntu.
    browser = shutil.which("google-chrome") or shutil.which("chromium") or shutil.which("chromium-browser")
    if browser is None:
        if os.environ.get("GITHUB_ACTIONS") == "true":
            pytest.fail("Chromium/Chrome obrigatorio no CI de acessibilidade.")
        pytest.skip("Chromium/Chrome nao instalado no ambiente local.")
    client.force_login(domain.admin)
    response = client.get("/")
    assert response.status_code == 200
    html = _inline_assets(response.content.decode())
    fixture = tmp_path / "dashboard-browser.html"
    fixture.write_text(HARNESS.replace("FIXTURE", escape(html)), encoding="utf-8")
    result = subprocess.run(
        [
            browser,
            "--headless",
            "--disable-gpu",
            "--disable-background-networking",
            "--disable-dev-shm-usage",
            "--no-first-run",
            f"--user-data-dir={tmp_path / 'browser-profile'}",
            "--virtual-time-budget=15000",
            "--dump-dom",
            fixture.as_uri(),
        ],
        capture_output=True,
        text=True,
        timeout=90,
        check=False,
    )
    assert result.returncode == 0, f"{browser}: {result.stderr[:3000]}"
    status = re.search(r'<pre id="result" data-state="([^"]+)">(.*?)</pre>', result.stdout, re.S)
    assert status is not None, "Resultado do navegador ausente."
    assert status[1] == "passed", unescape(status[2]) or "Smoke de navegador nao terminou."
