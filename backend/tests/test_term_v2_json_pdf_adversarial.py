"""T01: regression and bounded adversarial document evidence, laboratory only."""

import io
import runpy
from pathlib import Path

import pytest
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parent
FIXTURES = ROOT / "fixtures" / "term_v2"
SCRIPT = FIXTURES / "json_pdf_adversarial.py"
ENGINES = ("reportlab", "weasyprint")


@pytest.mark.parametrize("engine", ENGINES)
@pytest.mark.parametrize("orientation", ("portrait", "landscape"))
def test_headerless_table_keeps_every_cell(engine, orientation):
    fixture = runpy.run_path(str(ROOT / "test_term_v2_json_pdf_spike.py"))
    document, snapshot, images = fixture["_input"](orientation)
    table = document["content"]["content"][2]
    for row in table["content"]:
        for cell in row["content"]:
            cell["type"] = "tableCell"
    pdf = fixture["_renderer"]()(document, snapshot, images, engine)
    content = "\n".join(page.extract_text() or "" for page in PdfReader(io.BytesIO(pdf)).pages)
    expected = ("Campo", "Valor", "Condição", "Aprovada")
    assert all(content.count(value) == 1 for value in expected)
    assert [content.index(value) for value in expected] == sorted(content.index(value) for value in expected)


@pytest.mark.parametrize("engine", ENGINES)
@pytest.mark.parametrize("case", ("text-limit", "text-over", "rows-limit", "rows-over"))
def test_bounded_adversarial_evidence(tmp_path, engine, case):
    assert SCRIPT.is_file(), "adversarial collector not implemented (RED)"
    api = runpy.run_path(str(SCRIPT))
    result = api["run_case"](engine, "portrait", case, tmp_path)
    rejected = case.endswith("-over")
    assert result["status"] == ("rejected" if rejected else "ok")
    assert result["metrics"]["peak_rss_kib"] > 0
    assert result["metrics"]["cpu_ms"] >= 0
    assert result["metrics"]["wall_ms"] >= 0
    assert len(list(tmp_path.glob("*.pdf"))) == (0 if rejected else 1)
    assert result["metrics"]["input_unchanged"] is True
