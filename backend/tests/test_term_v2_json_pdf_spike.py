"""T01: PDF comum diretamente do JSON v2 e snapshot sintético autorizado."""

import copy
import io
import runpy
import socket
from pathlib import Path

import pytest
from PIL import Image
from pypdf import PdfReader

SCRIPT = Path(__file__).parent / "fixtures" / "term_v2" / "json_pdf_spike.py"
RID = "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"
ENGINES = ["reportlab", "weasyprint"]


def _text(value, *marks):
    return {"type": "text", "text": value, **({"marks": [{"type": m} for m in marks]} if marks else {})}


def _cell(value, header=False):
    return {
        "type": "tableHeader" if header else "tableCell",
        "content": [{"type": "paragraph", "content": [_text(value)]}],
    }


def _input(orientation="portrait"):
    buf = io.BytesIO()
    Image.new("RGB", (24, 12), "#183A59").save(buf, format="PNG")
    document = {
        "schema_version": 2,
        "classification": "EMPRESTIMO",
        "layout": {"paper": "A4", "orientation": orientation, "margin_mm": 18},
        "content": {
            "type": "doc",
            "content": [
                {"type": "heading", "attrs": {"level": 1}, "content": [_text("Termo de empréstimo")]},
                {
                    "type": "paragraph",
                    "content": [
                        _text("Responsável: ", "bold"),
                        {"type": "variable", "attrs": {"key": "responsavel.nome"}},
                        _text(" — revisão ", "italic"),
                        _text("<b>literal</b>", "underline"),
                    ],
                },
                {
                    "type": "table",
                    "content": [
                        {"type": "tableRow", "content": [_cell("Campo", True), _cell("Valor", True)]},
                        {"type": "tableRow", "content": [_cell("Condição"), _cell("Aprovada")]},
                    ],
                },
                {
                    "type": "resourceImage",
                    "attrs": {"resourceId": RID, "alt": "Etiqueta sintética", "width": 120, "height": 60},
                },
                {"type": "patrimonialBlock"},
                {"type": "paragraph", "content": [_text("Fim do conteúdo.")]},
            ],
        },
    }
    snapshot = {
        "fields": {
            "responsavel.nome": "Pessoa Sintética",
            "processo.tipo": "EMPRESTIMO",
            "processo.localizacao": "Laboratório",
            "emprestimo.inicio": "27/11/2026",
            "emprestimo.prazo_original": "05/12/2026",
            "emprestimo.finalidade": "Teste controlado",
        },
        "assets": [
            {"patrimonio": f"GATI-{i:04d}", "descricao": "Equipamento sintético"} for i in range(1, 101)
        ],
        "signers": [f"Signatário {i:02d}" for i in range(1, 11)],
    }
    return document, snapshot, {RID: buf.getvalue()}


def _renderer():
    assert SCRIPT.is_file(), "conversor direto JSON v2 ainda não implementado (RED)"
    return runpy.run_path(str(SCRIPT))["render_document"]


@pytest.mark.parametrize("engine", ENGINES)
@pytest.mark.parametrize("orientation", ["portrait", "landscape"])
def test_json_pdf_preserves_content_and_regenerates_snapshot(engine, orientation):
    render = _renderer()
    document, snapshot, images = _input(orientation)
    original = copy.deepcopy((document, snapshot, images))
    pdf = render(document, snapshot, images, engine)
    reader = PdfReader(io.BytesIO(pdf), strict=True)
    assert pdf.startswith(b"%PDF-") and not reader.is_encrypted
    assert len(reader.pages) >= 3
    width, height = (595.28, 841.89) if orientation == "portrait" else (841.89, 595.28)
    assert all(abs(float(p.mediabox.width) - width) < 1 for p in reader.pages)
    assert all(abs(float(p.mediabox.height) - height) < 1 for p in reader.pages)
    assert sum(len(p.images) for p in reader.pages) >= 1
    content = "\n".join(p.extract_text() or "" for p in reader.pages)
    for value in (
        "Termo de empréstimo",
        "Pessoa Sintética",
        "<b>literal</b>",
        "Condição",
        "Aprovada",
        "Laboratório",
        "05/12/2026",
        "Signatário 10",
        "Fim do conteúdo.",
    ):
        assert value in content
    assert all(content.count(f"GATI-{i:04d}") == 1 for i in range(1, 101))
    assert content.index("GATI-0100") < content.index("Fim do conteúdo.")
    assert (document, snapshot, images) == original


@pytest.mark.parametrize("engine", ENGINES)
@pytest.mark.parametrize(
    "case",
    [
        "missing_variable",
        "tampered_block",
        "remote_image",
        "bad_png",
        "wrong_classification",
        "ragged_table",
        "unknown_snapshot_field",
        "too_many_assets",
        "unsupported_glyph",
        "oversized_image",
    ],
)
def test_json_pdf_rejects_invalid_inputs(engine, case):
    render = _renderer()
    document, snapshot, images = _input()
    nodes = document["content"]["content"]
    if case == "missing_variable":
        nodes[1]["content"][1]["attrs"]["key"] = "emissao.numero"
    elif case == "tampered_block":
        nodes[4]["attrs"] = {"patrimonio": "FALSO"}
    elif case == "remote_image":
        nodes[3]["attrs"]["resourceId"] = "http://127.0.0.1/private"
    elif case == "bad_png":
        images[RID] = b"not a PNG"
    elif case == "wrong_classification":
        snapshot["fields"]["processo.tipo"] = "ENTREGA"
    elif case == "ragged_table":
        nodes[2]["content"][1]["content"].pop()
    elif case == "unknown_snapshot_field":
        snapshot["fields"]["secret"] = "não permitido"
    elif case == "too_many_assets":
        snapshot["assets"].append({"patrimonio": "EXTRA", "descricao": "Excedente"})
    elif case == "unsupported_glyph":
        nodes[1]["content"] = [_text("𐐀")]
    else:
        buf = io.BytesIO()
        Image.new("RGB", (513, 12)).save(buf, format="PNG")
        images[RID] = buf.getvalue()
    with pytest.raises(ValueError):
        render(document, snapshot, images, engine)


@pytest.mark.parametrize("engine", ENGINES)
def test_json_pdf_literal_markup_never_connects(engine, monkeypatch):
    render = _renderer()
    document, snapshot, images = _input()
    document["content"]["content"][1]["content"] = [_text('<img src="http://127.0.0.1/x">')]
    attempts = []

    def deny(*args, **kwargs):
        attempts.append("socket.connect")
        raise AssertionError("Rede proibida")

    monkeypatch.setattr(socket.socket, "connect", deny)
    pdf = render(document, snapshot, images, engine)
    content = "\n".join(p.extract_text() or "" for p in PdfReader(io.BytesIO(pdf)).pages)
    assert '<img src="http://127.0.0.1/x">' in content
    assert attempts == []


@pytest.mark.parametrize("engine", ENGINES)
@pytest.mark.parametrize("orientation", ["portrait", "landscape"])
def test_short_signer_block_stays_together(engine, orientation):
    document, snapshot, images = _input(orientation)
    pdf = _renderer()(document, snapshot, images, engine)
    pages = [p.extract_text() or "" for p in PdfReader(io.BytesIO(pdf)).pages]
    assert any(
        "Signatários" in page and all(f"Signatário {i:02d}" in page for i in range(1, 11)) for page in pages
    )
