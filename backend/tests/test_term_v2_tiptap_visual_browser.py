"""PoC T01: interação Tiptap real no Chromium e roundtrip server-side isolado.

Não utiliza HTTP, CDNs, assets produtivos nem dados pessoais reais.
"""

import base64
import json
import os
import runpy
import shutil
from pathlib import Path

import pytest
from test_dashboard_browser import browser_session, dashboard_page

POC = Path(__file__).parent / "fixtures" / "term_v2" / "tiptap_poc"
RESOURCE = "a1c92077-aaaa-4f11-8b22-001122334455"


def _browser():
    binary = shutil.which("google-chrome") or shutil.which("chromium") or shutil.which("chromium-browser")
    if binary is None:
        if os.environ.get("GITHUB_ACTIONS") == "true":
            pytest.fail("Chromium obrigatório no CI do editor visual T01")
        pytest.skip("Chromium não encontrado localmente")
    return binary


def _html():
    html = (POC / "visual.html").read_text(encoding="utf-8")
    style = (POC / "visual.css").read_text(encoding="utf-8")
    bundle = (POC / "dist" / "visual.bundle.js").read_text(encoding="utf-8")
    assert '<link rel="stylesheet" href="visual.css">' in html
    assert '<script src="dist/visual.bundle.js" defer></script>' in html
    return html.replace('<link rel="stylesheet" href="visual.css">', f"<style>{style}</style>").replace(
        '<script src="dist/visual.bundle.js" defer></script>',
        "<script>" + bundle.replace("</script", r"<\/script") + "</script>",
    )


def _python_validator():
    # No shared module import: this is not the productive Django term validator.
    return runpy.run_path(str(POC / "rich_schema.py"))["validate_rich_document"]


LAYOUT = r"""(() => {
  const errors = [];
  const add = (ok, msg) => { if (!ok) errors.push(msg); };
  add(window.__gatiVisualReady === true, 'Tiptap não inicializou');
  add(document.querySelector('.ProseMirror[contenteditable=true]') !== null,
      'editor ProseMirror não está editável');
  add(document.querySelectorAll('[data-gati-patrimonial]').length === 1,
      'bloco patrimonial deve ser único');
  const block = document.querySelector('[data-gati-patrimonial]');
  add(block?.getAttribute('contenteditable') === 'false',
      'bloco patrimonial não está protegido no DOM');
  add(document.querySelectorAll('.ProseMirror table').length === 1, 'tabela inicial ausente');
  add(document.querySelector('#editor-toolbar')?.getAttribute('role') === 'toolbar',
      'barra não possui semântica de toolbar');
  add([...document.querySelectorAll('#editor-toolbar button')].every(x => x.textContent.trim()),
      'botões sem nome visível');
  add(document.getElementById('editor-status')?.getAttribute('role') === 'status',
      'mensagem de estado não acessível');
  add(document.documentElement.scrollWidth <= document.documentElement.clientWidth + 1,
      'transbordamento horizontal normal');
  document.documentElement.style.fontSize = '32px';
  const root = document.documentElement;
  const overflow200 = {client: root.clientWidth, scroll: root.scrollWidth,
    scrollables: [...document.querySelectorAll('body, body *')]
      .filter(el => el.scrollWidth > el.clientWidth + 1)
      .slice(0, 22).map(el => ({tag: el.tagName, id: el.id,
        className: typeof el.className === 'string' ? el.className : '',
        scrollWidth: el.scrollWidth, clientWidth: el.clientWidth,
        overflowX: getComputedStyle(el).overflowX})),
    offenders: [...document.querySelectorAll('body *')]
      .filter(el => {
        const rect = el.getBoundingClientRect();
        return rect.width > 0 && rect.right > root.clientWidth + 1 &&
          !el.closest('table, .ProseMirror table');
      }).slice(0, 20).map(el => ({tag: el.tagName, id: el.id,
        className: typeof el.className === 'string' ? el.className : '',
        right: Math.round(el.getBoundingClientRect().right),
        scrollWidth: el.scrollWidth, clientWidth: el.clientWidth}))};
  add(root.scrollWidth <= root.clientWidth + 1,
      'transbordamento horizontal com fonte 200%');
  document.documentElement.style.fontSize = '16px';
  const title = document.querySelector('h1');
  add(title?.textContent.includes('Editor visual'), 'título não apresentado');
  document.querySelector('.ProseMirror').focus();
  add(document.activeElement?.classList.contains('ProseMirror'), 'foco no editor indisponível');
  add(getComputedStyle(document.activeElement).outlineStyle !== 'none', 'foco invisível');
  return {errors, width: innerWidth, overflow200,
    tables: document.querySelectorAll('.ProseMirror table').length};
})()"""


PREPARE_TEXT = r"""(() => {
  const editor = window.__gatiVisual.editor;
  const changed = editor.commands.setTextSelection(2);
  editor.commands.focus();
  document.querySelector('[data-action=bold]').click();
  return {changed, active: editor.isActive('bold')};
})()"""


AFTER_TYPE = r"""(() => {
  const editor = window.__gatiVisual.editor;
  const typed = '__T01_TIPTAP__';
  const flat = JSON.stringify(editor.getJSON());
  const marked = editor.getJSON().content.some(node =>
    (node.content || []).some(t => t.text?.includes(typed) &&
      t.marks?.some(mark => mark.type === 'bold')));
  document.querySelector('[data-action=undo]').click();
  const undone = !JSON.stringify(editor.getJSON()).includes(typed);
  document.querySelector('[data-action=redo]').click();
  const redone = JSON.stringify(editor.getJSON()).includes(typed);
  document.querySelector('[data-action=table]').click();
  const tables = editor.getJSON().content.filter(n => n.type === 'table').length;
  document.querySelector('[data-action=image]').click();
  const images = editor.getJSON().content.filter(n => n.type === 'resourceImage');
  const imgDom = document.querySelector('[data-gati-resource-id]');
  const noExternalSrc = !imgDom?.querySelector('[src]') &&
    !document.querySelector('.ProseMirror img[src]');
  const beforeProtected = editor.getJSON().content.filter(n => n.type === 'patrimonialBlock');
  let position = -1;
  editor.state.doc.descendants((node, pos) => {
    if (node.type.name === 'patrimonialBlock') position = pos;
  });
  if (position >= 0) editor.commands.deleteRange({from: position, to: position + 1});
  const protectedAfter = editor.getJSON().content.filter(n => n.type === 'patrimonialBlock');
  document.querySelector('[data-action=export]').click();
  return {
    marked, undone, redone, tables, images, noExternalSrc,
    protectedBefore: beforeProtected.length,
    protectedAfter: protectedAfter.length,
    output: document.querySelector('#export-json').value,
    status: document.querySelector('#editor-status').textContent,
    flatContains: flat.includes(typed)
  };
})()"""


@pytest.mark.parametrize("width", [320, 375, 1366])
def test_tiptap_visual_accessibility_and_reflow(tmp_path, width):
    with browser_session(_browser(), tmp_path / f"visual-{width}") as cdp:
        cdp.call("Browser.getVersion")
        with dashboard_page(cdp, _html(), width) as session:
            result = cdp.evaluate(session, LAYOUT)
            if os.environ.get("GITHUB_ACTIONS") == "true" and width in (375, 1366):
                shot = cdp.call("Page.captureScreenshot", {"format": "png"}, session)
                if "data" in shot:
                    artifact = Path(os.environ["RUNNER_TEMP"]) / "term-v2"
                    artifact.mkdir(parents=True, exist_ok=True)
                    (artifact / f"tiptap-visual-{width}.png").write_bytes(base64.b64decode(shot["data"]))
    assert result["width"] == width
    if result["errors"]:
        print("OVERFLOW_WIDTHS", result["overflow200"]["scrollables"])
    assert not result["errors"], {
        "errors": result["errors"],
        "client": result["overflow200"]["client"],
        "scroll": result["overflow200"]["scroll"],
    }


def test_tiptap_visual_toolbar_undo_redo_protection_and_python_roundtrip(tmp_path):
    with browser_session(_browser(), tmp_path / "tiptap-interaction") as cdp:
        with dashboard_page(cdp, _html(), 768) as session:
            prepared = cdp.evaluate(session, PREPARE_TEXT)
            assert prepared["changed"] and prepared["active"], prepared
            cdp.call("Input.insertText", {"text": "__T01_TIPTAP__"}, session)
            result = cdp.evaluate(session, AFTER_TYPE)
    assert result["flatContains"] and result["marked"], result
    assert result["undone"] and result["redone"], result
    assert result["tables"] >= 2, result
    assert len(result["images"]) == 1, result
    assert result["images"][0]["attrs"]["resourceId"] == RESOURCE
    assert result["noExternalSrc"] is True, result
    assert result["protectedBefore"] == result["protectedAfter"] == 1, result
    assert result["output"], result["status"]
    data = json.loads(result["output"])
    verified = _python_validator()(data, allowed_resource_ids={RESOURCE})
    assert verified == data


def test_tiptap_python_validator_rejects_hostile_objects():
    validate = _python_validator()
    document = {
        "schema_version": 2,
        "classification": "EMPRESTIMO",
        "layout": {"paper": "A4", "orientation": "portrait", "margin_mm": 20},
        "content": {
            "type": "doc",
            "content": [
                {"type": "paragraph", "content": [{"type": "text", "text": "Exemplo sintético"}]},
                {"type": "patrimonialBlock"},
            ],
        },
    }
    assert validate(document, allowed_resource_ids=set()) == document
    for change in (
        lambda d: d["content"]["content"].append({"type": "patrimonialBlock"}),
        lambda d: d["content"]["content"][0].update({"attrs": {"onclick": "alert(1)"}}),
        lambda d: d["content"]["content"].append(
            {
                "type": "resourceImage",
                "attrs": {
                    "resourceId": RESOURCE,
                    "alt": "Teste",
                    "width": 48,
                    "height": 48,
                },
            }
        ),
    ):
        payload = json.loads(json.dumps(document))
        change(payload)
        with pytest.raises(ValueError):
            validate(payload, allowed_resource_ids=set())
