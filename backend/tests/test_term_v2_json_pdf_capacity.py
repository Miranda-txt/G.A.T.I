"""T01: bounded subprocess and evidence checks, using synthetic files only."""

import json
import runpy
import shutil
import subprocess
import sys
from hashlib import sha256
from pathlib import Path
from textwrap import dedent

import pytest
from pypdf import PdfWriter

SCRIPT = Path(__file__).parent / "fixtures" / "term_v2" / "json_pdf_capacity.py"


def _capacity():
    assert SCRIPT.is_file(), "Bounded capacity runner not implemented (RED)"
    return runpy.run_path(str(SCRIPT))


def test_bounded_process_success(tmp_path):
    result = _capacity()["run_bounded"]([sys.executable, "-c", "pass"], tmp_path)
    assert result["status"] == "ok"
    assert result["returncode"] == 0
    assert result["wall_ms"] > 0


def test_bounded_process_wall_timeout(tmp_path):
    result = _capacity()["run_bounded"](
        [sys.executable, "-c", "import time; time.sleep(60)"], tmp_path, timeout=0.2
    )
    assert result["status"] == "timeout"
    assert result["returncode"] < 0
    assert result["wall_ms"] < 5000


@pytest.mark.parametrize(
    "source,limits",
    [
        ("bytearray(256 * 1024 * 1024)", {"memory_mib": 64}),
        ("while True: pass", {"cpu_seconds": 1}),
        ("open('excess.bin', 'wb').write(b'x' * 8192)", {"file_bytes": 1024}),
    ],
)
def test_bounded_process_rejects_resource_exhaustion(tmp_path, source, limits):
    result = _capacity()["run_bounded"]([sys.executable, "-c", source], tmp_path, **limits)
    assert result["status"] == "failed"
    assert result["returncode"] != 0
    if (tmp_path / "excess.bin").exists():
        assert (tmp_path / "excess.bin").stat().st_size <= 1024


def _evidence(directory, pages=1):
    pdf = directory / "sample.pdf"
    writer = PdfWriter()
    for _ in range(pages):
        writer.add_blank_page(width=595, height=842)
    writer.write(pdf)
    raw = pdf.read_bytes()
    metrics = {"pages": pages, "size_bytes": len(raw), "sha256": sha256(raw).hexdigest()}
    (directory / "sample.json").write_text(json.dumps(metrics), encoding="utf-8")
    return metrics


def test_capacity_accepts_verified_evidence(tmp_path):
    expected = _evidence(tmp_path)
    assert _capacity()["validate_evidence"](tmp_path, "sample") == expected


@pytest.mark.parametrize("case", ["pages", "bytes", "hash", "page_count", "missing"])
def test_capacity_rejects_invalid_evidence(tmp_path, case):
    metrics = _evidence(tmp_path, pages=2)
    limits = {}
    if case == "pages":
        limits["page_limit"] = 1
    elif case == "bytes":
        limits["file_bytes"] = 1
    elif case == "hash":
        metrics["sha256"] = "0" * 64
    elif case == "page_count":
        metrics["pages"] = 1
    else:
        (tmp_path / "sample.pdf").unlink()
    (tmp_path / "sample.json").write_text(json.dumps(metrics), encoding="utf-8")
    with pytest.raises(ValueError):
        _capacity()["validate_evidence"](tmp_path, "sample", **limits)


@pytest.mark.parametrize("fail", [False, True])
def test_capacity_matrix_records_every_job(tmp_path, fail):
    # Exercise the real launcher with a small synthetic benchmark, not renderer timings.
    script = tmp_path / SCRIPT.name
    shutil.copyfile(SCRIPT, script)
    (tmp_path / "json_pdf_benchmark.py").write_text(
        dedent(
            f"""
            import argparse
            import json
            from hashlib import sha256
            from pathlib import Path
            from pypdf import PdfWriter

            parser = argparse.ArgumentParser()
            for key in ("engine", "orientation", "assets", "signers", "repetitions", "output"):
                parser.add_argument("--" + key, required=True)
            args = parser.parse_args()
            if {fail!r} and args.engine == "reportlab":
                raise SystemExit(3)
            stem = f"json-v2-{{args.engine}}-{{args.orientation}}-100-10"
            directory = Path(args.output)
            pdf = directory / (stem + ".pdf")
            writer = PdfWriter()
            writer.add_blank_page(width=595, height=842)
            writer.write(pdf)
            raw = pdf.read_bytes()
            metrics = {{"pages": 1, "size_bytes": len(raw), "sha256": sha256(raw).hexdigest(),
                       "engine": args.engine, "orientation": args.orientation, "assets": 100, "signers": 10}}
            (directory / (stem + ".json")).write_text(json.dumps(metrics), encoding="utf-8")
            """
        ),
        encoding="utf-8",
    )
    output = tmp_path / "capacity.json"
    result = subprocess.run(
        [sys.executable, str(script), "--output", str(output)], capture_output=True, text=True, timeout=30
    )
    assert result.returncode == (1 if fail else 0)
    assert output.is_file()
    jobs = json.loads(output.read_text(encoding="utf-8"))["jobs"]
    assert len(jobs) == 8
    assert sum(job["status"] == "ok" for job in jobs) == (4 if fail else 8)
    assert all("metrics" not in job for job in jobs if job["status"] != "ok")
    for first, second in zip(jobs[::2], jobs[1::2], strict=True):
        assert max(first["start_ns"], second["start_ns"]) < min(first["end_ns"], second["end_ns"])
