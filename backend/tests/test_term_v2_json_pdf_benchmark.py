"""T01: evidence contract for the direct JSON PDF benchmark."""

import json
import statistics
import subprocess
import sys
from hashlib import sha256
from pathlib import Path

import pytest
from pypdf import PdfReader

SCRIPT = Path(__file__).parent / "fixtures" / "term_v2" / "json_pdf_benchmark.py"


@pytest.mark.parametrize("engine", ["reportlab", "weasyprint"])
@pytest.mark.parametrize("orientation,assets,signers", [("portrait", 1, 1), ("landscape", 100, 10)])
def test_json_pdf_benchmark_evidence(tmp_path, engine, orientation, assets, signers):
    assert SCRIPT.is_file(), "Direct JSON benchmark not implemented (RED)"
    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--engine",
            engine,
            "--orientation",
            orientation,
            "--assets",
            str(assets),
            "--signers",
            str(signers),
            "--repetitions",
            "2",
            "--output",
            str(tmp_path),
        ],
        check=True,
        capture_output=True,
        text=True,
        timeout=90,
    )
    metrics = json.loads(result.stdout)
    stem = f"json-v2-{engine}-{orientation}-{assets}-{signers}"
    pdf = tmp_path / f"{stem}.pdf"
    assert metrics == json.loads((tmp_path / f"{stem}.json").read_text(encoding="utf-8"))
    assert (metrics["engine"], metrics["orientation"], metrics["assets"], metrics["signers"]) == (
        engine,
        orientation,
        assets,
        signers,
    )
    assert metrics["sha256"] == sha256(pdf.read_bytes()).hexdigest()
    assert metrics["size_bytes"] == pdf.stat().st_size
    reader = PdfReader(pdf, strict=True)
    assert metrics["pages"] == len(reader.pages)
    content = "\n".join(page.extract_text() or "" for page in reader.pages)
    assert content.count("GATI-0001") == 1
    assert content.count(f"GATI-{assets:04d}") == 1
    assert ("GATI-0100" in content) == (assets == 100)
    assert ("Signatário 10" in content) == (signers == 10)
    assert len(metrics["samples"]) == 2
    assert all(sample["pages"] == metrics["pages"] for sample in metrics["samples"])
    for key in ("wall_ms", "cpu_ms"):
        values = [sample[key] for sample in metrics["samples"]]
        assert all(value > 0 for value in values)
        assert metrics[f"{key}_median"] == statistics.median(values)
        assert metrics[f"{key}_max"] == max(values)
    assert metrics["first_render_wall_ms"] > 0
    assert metrics["peak_rss_kib"] > 0


@pytest.mark.parametrize("flag,value", [("--assets", "101"), ("--signers", "11"), ("--repetitions", "1")])
def test_json_pdf_benchmark_rejects_out_of_range(tmp_path, flag, value):
    assert SCRIPT.is_file(), "Direct JSON benchmark not implemented (RED)"
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--engine", "reportlab", "--output", str(tmp_path), flag, value],
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 2
    assert not list(tmp_path.iterdir())
