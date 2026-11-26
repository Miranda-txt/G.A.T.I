"""Contratos para benchmark isolado de renderização rica T01."""

import json
import subprocess
import sys
from hashlib import sha256
from pathlib import Path

import pytest
from pypdf import PdfReader

SCRIPT = Path(__file__).parent / "fixtures" / "term_v2" / "rich_pdf_benchmark.py"


@pytest.mark.parametrize("engine", ["reportlab", "weasyprint"])
def test_rich_pdf_benchmark_evidence(tmp_path, engine):
    assert SCRIPT.is_file(), "Coletor de PDF rico ainda não implementado (RED)"
    proc = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--engine",
            engine,
            "--output",
            str(tmp_path),
            "--repetitions",
            "2",
        ],
        check=True,
        text=True,
        capture_output=True,
        timeout=90,
    )
    metrics = json.loads(proc.stdout)
    pdf = tmp_path / f"rico-{engine}.pdf"
    data = pdf.read_bytes()
    assert metrics == json.loads((tmp_path / f"rico-{engine}.json").read_text(encoding="utf-8"))
    assert metrics["engine"] == engine
    assert metrics["assets"] == 100
    assert metrics["signers"] == 10
    assert metrics["sha256"] == sha256(data).hexdigest()
    assert metrics["size_bytes"] == len(data)
    assert metrics["pages"] == len(PdfReader(pdf, strict=True).pages)
    assert metrics["pages"] >= 3
    assert metrics["peak_rss_kib"] > 0
    assert len(metrics["wall_ms"]) == len(metrics["cpu_ms"]) == 2
    assert all(value >= 0 for value in metrics["wall_ms"] + metrics["cpu_ms"])
