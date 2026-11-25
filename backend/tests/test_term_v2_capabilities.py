"""Provas de capacidade T01: dados e adapter experimentais, sem ativar o domínio."""

import io
import json
import runpy
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread

import pytest
from pypdf import PdfReader

FIXTURES = Path(__file__).parent / "fixtures" / "term_v2"
DATA = json.loads((FIXTURES / "documents.json").read_text(encoding="utf-8"))


def _document(case):
    """Produz documento sintético; não representa o schema definitivo do editor."""
    return {
        "title": DATA["title"],
        "paragraph": DATA["paragraph"],
        "assets": [
            {
                "patrimonio": f"{DATA['asset_prefix']}-{index:03d}",
                "descricao": DATA["asset_description"],
            }
            for index in range(1, case["assets"] + 1)
        ],
        "signers": [
            {"nome": f"{DATA['signer_prefix']} {index:02d}"} for index in range(1, case["signers"] + 1)
        ],
        "resources": [],
    }


def _renderer():
    # O adapter descartável será implementado após observar a ausência da capacidade.
    # Não importar nem ativar serviços produtivos nesta prova.
    candidate = FIXTURES / "renderer_spike.py"
    assert candidate.is_file(), "T01: candidato de renderização ainda não implementado"
    render = runpy.run_path(str(candidate)).get("render_document")
    assert callable(render), "T01: candidato não oferece render_document"
    return render


def _pdf_text(data):
    reader = PdfReader(io.BytesIO(data), strict=True)
    text = " ".join(" ".join(page.extract_text() for page in reader.pages).split())
    return text, len(reader.pages)


@pytest.mark.parametrize("case", DATA["cases"], ids=[case["id"] for case in DATA["cases"]])
def test_renderer_deterministic_fixture(case):
    document = _document(case)
    render = _renderer()
    rendered_bytes = render(document)
    assert rendered_bytes.startswith(b"%PDF-")
    rendered_text, page_count = _pdf_text(rendered_bytes)
    assert page_count >= 1

    # A referência textual independe do adapter e preserva todos os itens.
    expected_text = " ".join(
        [document["title"], document["paragraph"]]
        + [f"{asset['patrimonio']} {asset['descricao']}" for asset in document["assets"]]
        + [signer["nome"] for signer in document["signers"]]
    )
    assert rendered_text == expected_text
    assert _pdf_text(render(document)) == (expected_text, page_count)


def test_renderer_no_network():
    render = _renderer()
    outbound_requests = []

    class Canary(BaseHTTPRequestHandler):
        def do_GET(self):
            outbound_requests.append(self.path)
            self.send_response(404)
            self.end_headers()

        def do_HEAD(self):
            self.do_GET()

        def log_message(self, *args):
            pass

    # Canary restrito a loopback; nenhum serviço externo ou credencial real.
    with ThreadingHTTPServer(("127.0.0.1", 0), Canary) as server:
        thread = Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            document = _document(DATA["cases"][0])
            document["resources"] = [f"http://127.0.0.1:{server.server_port}/recurso.png"]
            with pytest.raises(ValueError):
                render(document)
        finally:
            server.shutdown()
            thread.join(timeout=5)
    assert outbound_requests == []
