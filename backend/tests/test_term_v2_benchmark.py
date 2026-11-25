"""Contratos do coletor de evidências do spike T01."""

import json
import runpy
import subprocess
import sys
from hashlib import sha256
from pathlib import Path

import pytest
from pypdf import PdfReader

FIXTURES = Path(__file__).parent / "fixtures" / "term_v2"


@pytest.mark.skipif(sys.platform != "linux", reason="RSS do benchmark usa unidade Linux")
@pytest.mark.parametrize("case, assets, signers", [("minimo", 1, 1), ("maximo_combinado", 100, 10)])
def test_benchmark_artifacts(tmp_path, case, assets, signers):
    script = FIXTURES / "benchmark_spike.py"
    assert script.is_file(), "Coletor de benchmark ainda não implementado"
    result = subprocess.run(
        [sys.executable, str(script), "--case", case, "--output", str(tmp_path), "--repetitions", "2"],
        check=True,
        capture_output=True,
        text=True,
        timeout=30,
    )
    metrics = json.loads(result.stdout)
    pdf = (tmp_path / f"{case}.pdf").read_bytes()
    assert metrics == json.loads((tmp_path / f"{case}.json").read_text(encoding="utf-8"))
    assert (metrics["assets"], metrics["signers"]) == (assets, signers)
    assert metrics["sha256"] == sha256(pdf).hexdigest()
    assert metrics["size_bytes"] == len(pdf)
    assert metrics["pages"] == len(PdfReader(tmp_path / f"{case}.pdf").pages)
    assert metrics["peak_rss_kib"] > 0
    assert len(metrics["wall_ms"]) == len(metrics["cpu_ms"]) == 2
    assert all(value >= 0 for value in metrics["wall_ms"] + metrics["cpu_ms"])


@pytest.mark.parametrize("compliant, code", [(True, 0), (False, 1)])
def test_verapdf_report_distinguishes_noncompliance(compliant, code):
    script = FIXTURES / "verapdf_report.py"
    assert script.is_file(), "Leitor de relatório ainda não implementado"
    classify = runpy.run_path(str(script))["classify"]
    xml = f"""<report><jobs><job><validationReport profileName="PDF/A-2b validation profile"
        isCompliant="{str(compliant).lower()}"/></job></jobs>
        <batchSummary totalJobs="1" failedToParse="0" encrypted="0" outOfMemory="0" veraExceptions="0">
        <validationReports compliant="{int(compliant)}" nonCompliant="{int(not compliant)}" failedJobs="0"/>
        </batchSummary></report>"""
    assert classify(xml, code) == ("compliant" if compliant else "noncompliant")
    with pytest.raises(ValueError):
        classify(xml, 7)
    with pytest.raises(ValueError):
        classify(xml, 1 - code)
    with pytest.raises(ValueError):
        classify(xml.replace('failedToParse="0"', 'failedToParse="1"'), code)
    with pytest.raises(ValueError):
        classify(xml.replace("PDF/A-2b", "PDF/A-1b"), code)
    with pytest.raises(ValueError):
        classify("<report/>", code)
