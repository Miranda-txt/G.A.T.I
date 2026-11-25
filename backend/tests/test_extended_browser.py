"""DASH05-06: fluxos adicionais com HTML real, dados sinteticos e CDP offline."""

import json
import os
import shutil

import pytest
from conftest import process_for
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client
from test_dashboard_browser import _inline_assets, browser_session, dashboard_page

from gati.apps.importacoes.services import preview
from gati.apps.pessoas.models import Pessoa
from gati.apps.termos.services import issue

WIDTHS = (320, 768, 900, 901, 1366, 1920)

CHECK_FLOW = """(selector, kind) => {
  const root = document.documentElement;
  const main = document.querySelector('main');
  const errors = [];
  const check = (ok, message) => { if (!ok) errors.push(message); };
  const sample = main.querySelector(selector);
  check(!!sample, 'conteudo esperado ausente: ' + selector);
  if (!sample) return errors;
  function measure(size) {
    root.style.fontSize = size + 'px';
    const prefix = size + 'px: ';
    const font = parseFloat(getComputedStyle(sample).fontSize);
    check(root.scrollWidth <= root.clientWidth + 1,
      prefix + 'overflow documento ' + root.scrollWidth + '/' + root.clientWidth);
    for (const box of main.querySelectorAll('.panel, .public-card, .metric-card, .signature-row, .hash-box')) {
      check(box.scrollWidth <= box.clientWidth + 1,
        prefix + 'overflow ' + box.className + ' ' + box.scrollWidth + '/' + box.clientWidth);
    }
    for (const table of main.querySelectorAll('.table-responsive')) {
      if (table.scrollWidth > table.clientWidth + 1) {
        // Uma regiao de rolagem com controles internos precisa ser alcancavel pelo teclado.
        check(table.tabIndex >= 0, prefix + 'tabela rolavel sem acesso por Tab');
        check(table.getAttribute('role') === 'region' && !!table.getAttribute('aria-label'),
          prefix + 'tabela rolavel sem nome de regiao');
        table.focus({preventScroll: true});
        check(document.activeElement === table, prefix + 'tabela nao recebe foco');
        table.scrollLeft = 40;
        check(table.scrollLeft > 0, prefix + 'rolagem interna indisponivel');
        table.scrollLeft = 0;
      }
    }
    for (const control of main.querySelectorAll('button, input:not([type=hidden]), select, textarea')) {
      if (!control.getClientRects().length || control.disabled || control.closest('.table-responsive')) continue;
      const rect = control.getBoundingClientRect();
      check(rect.width > 0 && rect.left >= -1 && rect.right <= root.clientWidth + 1,
        prefix + 'controle fora do viewport: ' + (control.name || control.tagName));
    }
    return font;
  }
  const normal = measure(16);
  const large = measure(32);
  check(large >= normal * 1.99, 'fonte nao escala ' + selector + ': ' + normal + ' -> ' + large);
  root.style.fontSize = '16px';
  if (kind === 'sign_identity') {
    check(!main.querySelector('.term-text'), 'documento antes da identidade');
    check(!!main.querySelector('input[name=last4][required]'), 'confirmacao de identidade ausente');
  }
  if (kind === 'sign_read') {
    const accept = main.querySelector('input[name=aceito]');
    check(!!accept && accept.required && !accept.checked, 'aceite nao explicito');
    check(!!main.querySelector('.hash-box code'), 'hash ausente');
  }
  if (kind === 'import_preview') {
    const confirm = main.querySelector('input[name=confirm]');
    check(!!confirm && !confirm.checked, 'confirmacao de importacao preselecionada');
  }
  return errors;
}"""


def test_additional_flows_reflow_and_keyboard_regions(domain, client, tmp_path, monkeypatch):
    browser = shutil.which("google-chrome") or shutil.which("chromium") or shutil.which("chromium-browser")
    if browser is None:
        if os.environ.get("GITHUB_ACTIONS") == "true":
            pytest.fail("Chromium/Chrome obrigatorio no CI de acessibilidade.")
        pytest.skip("Chromium/Chrome nao instalado no ambiente local.")

    d = domain
    client.force_login(d.admin)
    pages = [
        ("people", client.get("/cadastros/pessoas/"), ".table td"),
        ("maintenance", client.get("/cadastros/manutencoes/"), ".empty-state"),
        ("process_empty", client.get("/processos/"), ".empty-state"),
        ("term_empty", client.get("/termos/"), ".empty-state"),
        ("catalogs", client.get("/configuracoes/"), ".metric-card h2"),
        ("import_upload", client.get("/importar/pessoas/"), "label[for=import-file]"),
        ("attachments", client.get(f"/cadastros/ativos/{d.asset.pk}/"), "#arquivos h2"),
    ]

    # Apenas o scanner externo e substituido; parser, validacao e previa sao reais.
    monkeypatch.setattr("gati.common.clamav.scan", lambda path: None)
    before = Pessoa.objects.count()
    csv = SimpleUploadedFile(
        "sintetico.csv",
        b"nome;documento;departamento;cargo;email\nPessoa Importada;90000000789;TI;Analista;\n",
    )
    job = preview(d.admin, "pessoas", csv)
    pages.append(("import_preview", client.get(f"/importacoes/{job.pk}/"), ".table td"))
    assert Pessoa.objects.count() == before

    process = process_for(d, witness=True)
    term = issue(d.operator, process.termos.first())
    pages.extend(
        [
            ("process_list", client.get("/processos/"), ".table td"),
            ("process_detail", client.get(f"/processos/{process.pk}/"), ".process-item h3"),
            ("term_list", client.get("/termos/"), ".table td"),
            ("term_detail", client.get(f"/termos/{term.pk}/"), ".hash-box code"),
            ("audit", client.get("/auditoria/"), ".table td"),
        ]
    )

    public = Client()
    pages.extend(
        [
            ("reset_request", public.get("/senha/recuperar/"), ".public-card h1"),
            ("reset_done", public.get("/senha/recuperar/enviado/"), ".public-card p"),
            ("reset_complete", public.get("/senha/redefinida/"), ".public-card h1"),
        ]
    )
    signer = term.assinaturas.get(papel="RESPONSAVEL")
    public.force_login(d.operator)
    assert public.post(f"/assinaturas/{signer.pk}/presencial/").status_code == 302
    assert "_auth_user_id" not in public.session
    pages.append(("sign_identity", public.get("/assinar/"), ".public-card h1"))
    assert public.post("/assinar/confirmar-identidade/", {"last4": "0123"}).status_code == 302
    pages.append(("sign_read", public.get("/assinar/"), ".term-text"))
    assert public.post("/assinar/aceitar/", {"aceito": "yes"}).status_code == 302
    pages.append(("sign_done", public.get("/assinar/"), ".hash-box code"))

    errors = []
    with browser_session(browser, tmp_path / "additional-flows-profile") as cdp:
        for kind, response, selector in pages:
            assert response.status_code == 200, kind
            html = _inline_assets(response.content.decode())
            for width in WIDTHS:
                with dashboard_page(cdp, html, width) as session:
                    expression = f"({CHECK_FLOW})({json.dumps(selector)}, {json.dumps(kind)})"
                    outcome = cdp.evaluate(session, expression)
                    errors.extend(f"{kind}/{width}: {error}" for error in outcome)
    assert not errors, "\n".join(errors)
