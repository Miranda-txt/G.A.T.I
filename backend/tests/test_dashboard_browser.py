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
const widths = [320, 375, 683, 768, 900, 901, 910, 1024, 1093, 1366, 1920];
const errors = [];
const diagnostics = [];
const result = document.getElementById('result');
const source = document.getElementById('fixture').value;
let index = 0;
function check(ok, message) { if (!ok) errors.push(message); }
// O evento e emitido pelo navegador, nao pelo codigo testado. O timeout
// impede que uma media query que nao muda produza um falso positivo.
function resize(frame, width) {
  const win = frame.contentWindow;
  const media = win.matchMedia('(max-width: 900px)');
  return new Promise((resolve, reject) => {
    const timeout = setTimeout(() => {
      media.removeEventListener('change', changed);
      reject(new Error('media query nao mudou para ' + width));
    }, 2000);
    function changed(event) {
      clearTimeout(timeout);
      // A proxima tarefa ocorre apos a entrega dos listeners do evento.
      setTimeout(() => resolve(event.matches), 0);
    }
    media.addEventListener('change', changed, {once: true});
    frame.width = width;
    // Materializa a nova geometria do frame sem alterar o estado da aplicacao.
    void frame.clientWidth;
    void win.innerWidth;
  });
}
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
  frame.onload = async () => {
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
    // Testa mudanca real de viewport com a aplicacao ja carregada.
    if (width === 768) {
      try {
        menu.click();
        check(workspace.inert && !sidebar.inert, 'resize: modal aberto antes de ampliar');
        check(await resize(frame, 910) === false, 'resize: media desktop');
        snapshot('resized-desktop');
        check(win.innerWidth === 910, 'resize: viewport desktop');
        check(!sidebar.inert && !workspace.inert, 'resize: desktop deve ser interativo');
        check(!sidebar.hasAttribute('aria-modal') && menu.getAttribute('aria-expanded') === 'false',
          'resize: modal deve ser encerrado ao ampliar');
        const desktopLink = sidebar.querySelector('a.selected');
        desktopLink.focus();
        check(doc.activeElement === desktopLink, 'resize: link desktop focavel');
        check(await resize(frame, 768) === true, 'resize: media mobile');
        snapshot('resized-mobile');
        check(win.innerWidth === 768, 'resize: viewport mobile');
        check(sidebar.inert && !workspace.inert, 'resize: sidebar mobile deve fechar');
        menu.focus();
        menu.click();
        check(doc.activeElement === close && workspace.inert, 'resize: reabertura mobile');
        close.click();
        check(doc.activeElement === menu && !workspace.inert, 'resize: fechamento e foco');
      } catch (error) {
        errors.push('resize: ' + error.message);
      }
    }
    frame.remove();
    next();
  };
  // Inicializa o browsing context e confirma a geometria ANTES de carregar
  // o HTML da aplicacao. Assim DOMContentLoaded nao observa um viewport provisorio.
  document.body.append(frame);
  check(frame.clientWidth === width, width + ': geometria do iframe incorreta');
  check(frame.contentWindow.innerWidth === width, width + ': viewport antes da carga incorreto');
  frame.srcdoc = source;
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
