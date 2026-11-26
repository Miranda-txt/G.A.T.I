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
  assert(root.scrollWidth <= root.clientWidth + 1, 'overflow horizontal a 200%');
  root.style.fontSize = '16px';
  const title = document.getElementById('document-title');
  title.focus();
  assert(document.activeElement === title, 'foco no título indisponível');
  const exportButton = document.getElementById('export-document');
  exportButton.click();
  const raw = document.getElementById('json-output').value;
  assert(!!raw, 'exportação de JSON indisponível');
  return {errors, raw, width: innerWidth, protectedEditable: document.querySelector('.protected').isContentEditable};
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
    assert not state["errors"], state
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
