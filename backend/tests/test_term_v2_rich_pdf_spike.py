"""T01: compara PDFs paginados com recurso sintético aprovado."""

import io
import runpy
from pathlib import Path

import pytest
from PIL import Image
from pypdf import PdfReader

SCRIPT = Path(__file__).parent / "fixtures" / "term_v2" / "rich_pdf_spike.py"


def _input():
    buf = io.BytesIO()
    Image.new("RGB", (12, 12), "#183A59").save(buf, format="PNG")
    doc = {
        "title": "Termo de responsabilidade — patrimônio",
        "paragraph": "Empréstimo de equipamentos com verificação individual, válido somente após aceite.",
        "assets": [
            {
                "patrimonio": f"GATI-{i:04d}",
                "descricao": "Equipamento com acessórios e informações individuais.",
            }
            for i in range(1, 101)
        ],
        "signers": [f"Signatário {i:02d}" for i in range(1, 11)],
        "resource_id": "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa",
    }
    return doc, {doc["resource_id"]: buf.getvalue()}


@pytest.mark.parametrize("engine", ["reportlab", "weasyprint"])
def test_rich_paginated_pdf_with_long_table(engine):
    assert SCRIPT.is_file(), "renderer rico ainda não implementado (RED)"
    render = runpy.run_path(str(SCRIPT))["render_rich"]
    doc, images = _input()
    pdf = render(doc, engine=engine, approved_images=images)
    reader = PdfReader(io.BytesIO(pdf), strict=True)
    assert not reader.is_encrypted
    assert len(reader.pages) >= 3
    assert all(abs(float(p.mediabox.width) - 595.28) < 1 for p in reader.pages)
    assert all(abs(float(p.mediabox.height) - 841.89) < 1 for p in reader.pages)
    content = "\n".join(p.extract_text() or "" for p in reader.pages)
    assert "GATI-0001" in content and "GATI-0100" in content
    assert "Signatário 10" in content
    assert pdf.startswith(b"%PDF-")


@pytest.mark.parametrize("engine", ["reportlab", "weasyprint"])
def test_rich_rejects_unknown_resources_and_markup(engine):
    assert SCRIPT.is_file(), "renderer rico ainda não implementado (RED)"
    render = runpy.run_path(str(SCRIPT))["render_rich"]
    doc, images = _input()
    doc["resource_id"] = "https://127.0.0.1/private"
    with pytest.raises(ValueError):
        render(doc, engine=engine, approved_images=images)
    doc, images = _input()
    doc["html"] = '<iframe src="file:///etc/passwd">'
    with pytest.raises(ValueError):
        render(doc, engine=engine, approved_images=images)
    doc, _ = _input()
    with pytest.raises(ValueError):
        render(doc, engine=engine, approved_images={})


def test_rich_weasyprint_never_uses_network_or_file_fetcher():
    assert SCRIPT.is_file(), "renderer rico ainda não implementado (RED)"
    module = runpy.run_path(str(SCRIPT))
    with pytest.raises(ValueError):
        module["restricted_fetcher"]("http://127.0.0.1/private", {})
    with pytest.raises(ValueError):
        module["restricted_fetcher"]("file:///etc/passwd", {})
