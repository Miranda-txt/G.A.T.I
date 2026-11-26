"""Smoke real do editor T01 em Chromium, com assets sintéticos e sem rede."""

import json
import os
import runpy
import shutil
from pathlib import Path

import pytest
from test_dashboard_browser import browser_session, dashboard_page

ROOT = Path(__file__).parent / "fixtures" / "term_v2" / "editor_spike"
NORMALIZE = runpy.run_path(str(ROOT / "schema.py"))["normalize"]


def _browser():
    executable = shutil.which("google-chrome") or shutil.which("chromium") or shutil.which("chromium-browser")
    if executable is None:
        if os.environ.get("GITHUB_ACTIONS") == "true":
            pytest.fail("Chromium obrigatório no CI de UX do editor.")
        pytest.skip("Chromium não disponível localmente")
    return executable


def _html():
    html = (ROOT / "index.html").read_text(encoding="utf-8")
    css = (ROOT / "editor.css").read_text(encoding="utf-8")
    model = (ROOT / "model.js").read_text(encoding="utf-8").replace("</script", "<\\/script")
    editor = (ROOT / "editor.js").read_text(encoding="utf-8").replace("</script", "<\\/script")
    html = html.replace('<link rel="stylesheet" href="editor.css">', "<style>" + css + "</style>")
    for script in ("model.js", "editor.js"):
        html = html.replace(f'<script src="{script}" defer></script>', "")
    return html.replace("</body>", "<script>" + model + "</script><script>" + editor + "</script></body>")


SMOKE = r"""(() => {
  const errors = [];
  const assert = (ok, label) => {if (!ok) errors.push(label);};
  const root = document.documentElement;
  assert(!!window.GatiEditorModel, 'modelo JS não inicializado');
  assert(document.querySelectorAll('[data-mark]').length === 4, 'toolbar incompleta');
  assert(document.querySelectorAll('.protected').length === 1, 'bloco protegido ausente');
  assert(document.querySelector('.protected').isContentEditable === false, 'bloco protegido editável');
  assert(document.querySelector('#variable').options.length === 8, 'catálogo entrega incorreto');
  assert(root.scrollWidth <= root.clientWidth + 1, 'overflow horizontal normal');
  root.style.fontSize = '32px';
  const overflow200 = [...document.querySelectorAll('body *')].map((element) => {
    const rect = element.getBoundingClientRect();
    const style = getComputedStyle(element);
    return {selector: element.tagName.toLowerCase() +
        (element.id ? '#' + element.id : '') +
        (typeof element.className === 'string' && element.className ?
          '.' + element.className.trim().replaceAll(' ', '.') : ''),
      right: Math.round(rect.right), left: Math.round(rect.left),
      width: Math.round(rect.width), scrollWidth: element.scrollWidth,
      display: style.display, minWidth: style.minWidth};
  }).filter((element) => element.right > root.clientWidth + 1 || element.left < -1).slice(0, 20);
  const pageWidth200 = {client: root.clientWidth, scroll: root.scrollWidth};
  assert(root.scrollWidth <= root.clientWidth + 1, 'overflow horizontal a 200%');
  root.style.fontSize = '16px';
  const title = document.getElementById('document-title');
  title.focus();
  assert(document.activeElement === title, 'foco no título indisponível');
  const exportButton = document.getElementById('export-document');
  exportButton.click();
  const raw = document.getElementById('json-output').value;
  assert(!!raw, 'exportação de JSON indisponível');
  return {errors, raw, width: innerWidth, overflow200, pageWidth200,
    protectedEditable: document.querySelector('.protected').isContentEditable};
})()"""


INTERACTION = r"""(() => {
  const errors = [];
  const assert = (ok, label) => {if (!ok) errors.push(label);};
  const edit = document.querySelector('#editable-blocks .editable');
  const selection = window.getSelection();
  const range = document.createRange();
  range.setStart(edit.firstChild, 0);
  range.setEnd(edit.firstChild, 8);
  selection.removeAllRanges();
  selection.addRange(range);
  document.dispatchEvent(new Event('selectionchange'));
  document.querySelector('[data-mark=bold]').click();
  assert(!!edit.querySelector('strong'), 'negrito não aplicou à seleção');
  const category = document.querySelector('#classification');
  category.value = 'EMPRESTIMO';
  category.dispatchEvent(new Event('change', {bubbles: true}));
  const variableSelect = document.querySelector('#variable');
  assert(variableSelect.options.length === 11, 'catálogo empréstimo incorreto');
  variableSelect.value = 'emprestimo.prazo_original';
  const plain = edit.firstChild;
  const insertion = document.createRange();
  insertion.selectNodeContents(edit);
  insertion.collapse(false);
  selection.removeAllRanges();
  selection.addRange(insertion);
  document.dispatchEvent(new Event('selectionchange'));
  document.querySelector('#insert-variable').click();
  assert(!!edit.querySelector('span.variable'), 'variável não inserida');
  const immutable = document.querySelector('.protected');
  assert(immutable.isContentEditable === false, 'bloco patrimonial editável');
  document.querySelector('#export-document').click();
  const raw = document.querySelector('#json-output').value;
  assert(!!raw, 'exportação após edições falhou');
  return {errors, raw};
})()"""


@pytest.mark.parametrize("width", [320, 375, 768, 1366])
def test_editor_browser_layout_and_backend_roundtrip(tmp_path, width):
    with browser_session(_browser(), tmp_path / f"editor-browser-{width}") as cdp:
        cdp.call("Browser.getVersion")
        with dashboard_page(cdp, _html(), width) as session:
            state = cdp.evaluate(session, SMOKE)
    if state["errors"]:
        print("OVERFLOW:", state["pageWidth200"], state["overflow200"])
    assert not state["errors"], {"errors": state["errors"], "pageWidth200": state["pageWidth200"]}
    assert state["width"] == width
    document = NORMALIZE(json.loads(state["raw"]))
    assert sum(n["type"] == "patrimonialBlock" for n in document["content"]["content"]) == 1
    assert document["layout"]["paper"] == "A4"


def test_editor_browser_marks_variables_and_backend_roundtrip(tmp_path):
    with browser_session(_browser(), tmp_path / "editor-interactions") as cdp:
        cdp.call("Browser.getVersion")
        with dashboard_page(cdp, _html(), 768) as session:
            state = cdp.evaluate(session, INTERACTION)
    assert not state["errors"], state
    document = NORMALIZE(json.loads(state["raw"]))
    assert document["classification"] == "EMPRESTIMO"
    assert any(
        node.get("type") == "variable" and node["attrs"]["key"] == "emprestimo.prazo_original"
        for block in document["content"]["content"]
        for node in block.get("content", [])
        if isinstance(node, dict)
    )


TITLE_PASTE = r"""(() => {
  const title = document.querySelector('#document-title');
  const selection = window.getSelection();
  const range = document.createRange();
  title.focus();
  range.selectNodeContents(title);
  selection.removeAllRanges();
  selection.addRange(range);
  const data = new DataTransfer();
  data.setData('text/plain', 'Termo <img src=x onerror=alert(1)>\nResponsável');
  data.setData('text/html', '<img src=x onerror=window.__gatiInjected=true>');
  const pasted = new ClipboardEvent('paste',
    {bubbles: true, cancelable: true, clipboardData: data});
  title.dispatchEvent(pasted);
  const enter = new KeyboardEvent('keydown',
    {key: 'Enter', bubbles: true, cancelable: true});
  title.dispatchEvent(enter);
  const drop = new DragEvent('drop',
    {dataTransfer: data, bubbles: true, cancelable: true});
  title.dispatchEvent(drop);
  document.querySelector('#export-document').click();
  return {
    pasteBlocked: pasted.defaultPrevented,
    enterBlocked: enter.defaultPrevented,
    dropBlocked: drop.defaultPrevented,
    text: title.textContent,
    elementCount: title.childElementCount,
    injected: window.__gatiInjected === true,
    json: document.querySelector('#json-output').value
  };
})()"""


PARAGRAPH_PASTE = r"""(() => {
  const paragraph = document.querySelector('#editable-blocks .editable');
  const range = document.createRange();
  const selection = window.getSelection();
  paragraph.focus();
  range.selectNodeContents(paragraph);
  selection.removeAllRanges();
  selection.addRange(range);
  const data = new DataTransfer();
  data.setData('text/plain', '<script>alert(1)</script> patrimônio sintético');
  data.setData('text/html', '<img src=x onerror=window.__gatiInjected=true>');
  const pasted = new ClipboardEvent('paste',
    {bubbles: true, cancelable: true, clipboardData: data});
  paragraph.dispatchEvent(pasted);
  document.querySelector('#export-document').click();
  return {
    pasteBlocked: pasted.defaultPrevented,
    text: paragraph.textContent,
    elementCount: paragraph.childElementCount,
    injected: window.__gatiInjected === true,
    json: document.querySelector('#json-output').value
  };
})()"""


def test_editor_title_paste_is_plain_text_single_line_and_drop_blocked(tmp_path):
    with browser_session(_browser(), tmp_path / "editor-title-paste") as cdp:
        with dashboard_page(cdp, _html(), 375) as session:
            state = cdp.evaluate(session, TITLE_PASTE)
    assert state["pasteBlocked"] is True, state
    assert state["enterBlocked"] is True, state
    assert state["dropBlocked"] is True, state
    assert state["elementCount"] == 0 and state["injected"] is False, state
    assert state["text"] == "Termo <img src=x onerror=alert(1)> Responsável", state
    document = NORMALIZE(json.loads(state["json"]))
    assert document["content"]["content"][0]["content"][0]["text"] == state["text"]


def test_editor_paragraph_paste_rejects_html_but_preserves_literal_text(tmp_path):
    with browser_session(_browser(), tmp_path / "editor-paragraph-paste") as cdp:
        with dashboard_page(cdp, _html(), 375) as session:
            state = cdp.evaluate(session, PARAGRAPH_PASTE)
    assert state["pasteBlocked"] is True, state
    assert state["elementCount"] == 0 and state["injected"] is False, state
    assert state["text"] == "<script>alert(1)</script> patrimônio sintético", state
    document = NORMALIZE(json.loads(state["json"]))
    assert document["content"]["content"][2]["content"][0]["text"] == state["text"]


def _tab(cdp, session, reverse=False):
    params = {
        "key": "Tab",
        "code": "Tab",
        "windowsVirtualKeyCode": 9,
        "nativeVirtualKeyCode": 9,
        "modifiers": 8 if reverse else 0,
    }
    cdp.call("Input.dispatchKeyEvent", {"type": "keyDown", **params}, session)
    cdp.call("Input.dispatchKeyEvent", {"type": "keyUp", **params}, session)


def test_editor_keyboard_tab_order_and_visible_focus(tmp_path):
    with browser_session(_browser(), tmp_path / "editor-keyboard") as cdp:
        with dashboard_page(cdp, _html(), 375) as session:
            cdp.evaluate(session, "document.querySelector('#document-title').focus()")
            _tab(cdp, session)
            first = cdp.evaluate(
                session,
                "({label: document.activeElement.getAttribute('aria-label'),"
                " outline: getComputedStyle(document.activeElement).outlineStyle})",
            )
            _tab(cdp, session)
            second = cdp.evaluate(session, "document.activeElement.id")
            _tab(cdp, session, reverse=True)
            back = cdp.evaluate(session, "document.activeElement.getAttribute('aria-label')")
    assert first["label"] == "Parágrafo inicial"
    assert first["outline"] != "none", first
    assert second == "variable"
    assert back == "Parágrafo inicial"
