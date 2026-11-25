"""Provas de capacidade T01: dados e adapter experimentais, sem ativar o domínio."""

import io
import json
import runpy
from hashlib import sha256
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


@pytest.mark.parametrize("case", DATA["cases"], ids=[case["id"] for case in DATA["cases"]])
def test_renderer_binary_determinism(case):
    document = _document(case)
    render = _renderer()
    first = render(document)
    assert sha256(first).digest() == sha256(render(document)).digest()
    document["title"] += " revisado"
    assert sha256(first).digest() != sha256(render(document)).digest()


def test_renderer_maximum_pagination():
    document = _document(DATA["cases"][-1])
    reader = PdfReader(io.BytesIO(_renderer()(document)), strict=True)
    assert 2 <= len(reader.pages) <= 20
    for page in reader.pages:
        assert float(page.mediabox.width) == pytest.approx(595.28, abs=0.1)
        assert float(page.mediabox.height) == pytest.approx(841.89, abs=0.1)
    text = " ".join(page.extract_text() for page in reader.pages)
    assert text.count("GATI-SINT-") == 100
    assert text.count("Signatário sintético") == 10


def test_renderer_embeds_fonts():
    reader = PdfReader(io.BytesIO(_renderer()(_document(DATA["cases"][-1]))), strict=True)
    for page in reader.pages:
        fonts = page["/Resources"]["/Font"]
        assert fonts
        for ref in fonts.values():
            font = ref.get_object()
            descriptor = font.get("/FontDescriptor")
            assert descriptor is not None, "Fonte sem descritor incorporado"
            descriptor = descriptor.get_object()
            assert any(key in descriptor for key in ("/FontFile", "/FontFile2", "/FontFile3"))
            assert "/ToUnicode" in font


@pytest.mark.parametrize(
    "patch",
    [
        {"resources": ["file:///tmp/gati-synthetic-canary.txt"]},
        {"resources": ["data:text/plain,synthetic"]},
        {"resources": ["../gati-synthetic-canary.txt"]},
        {"resources": None},
        {"assets": []},
        {"assets": [{"patrimonio": "SINT", "descricao": "Teste"}] * 101},
        {"signers": []},
        {"signers": [{"nome": "Sintético"}] * 11},
        {"title": "a" * 513},
        {"paragraph": "texto\x00inválido"},
        {"title": "😀"},
        {"unexpected": "campo não autorizado"},
        {"assets": [{"patrimonio": "SINT"}]},
        {"signers": [{"nome": "Sintético", "extra": "não permitido"}]},
    ],
)
def test_renderer_rejects_invalid_document(patch):
    document = _document(DATA["cases"][0])
    document.update(patch)
    with pytest.raises(ValueError):
        _renderer()(document)


def test_renderer_rejects_missing_field():
    document = _document(DATA["cases"][0])
    del document["resources"]
    with pytest.raises(ValueError):
        _renderer()(document)


def test_renderer_rejects_page_limit():
    document = _document(DATA["cases"][-1])
    for asset in document["assets"]:
        asset["patrimonio"] = ("WW " * 170).strip()
        asset["descricao"] = ("WW " * 170).strip()
    with pytest.raises(ValueError, match="páginas"):
        _renderer()(document)
