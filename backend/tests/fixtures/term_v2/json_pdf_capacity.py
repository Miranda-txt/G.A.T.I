"""T01: bounded concurrent JSON PDF laboratory, not a production sandbox."""

import argparse
import io
import json
import os
import signal
import subprocess
import sys
import tempfile
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from hashlib import sha256
from pathlib import Path

from pypdf import PdfReader
from pypdf.errors import PdfReadError

BENCHMARK = Path(__file__).resolve().with_name("json_pdf_benchmark.py")
FILE_BYTES = 5 * 1024 * 1024
PAGE_LIMIT = 50
MEMORY_MIB = 512
CPU_SECONDS = 10
WALL_SECONDS = 30


def run_bounded(
    command,
    directory,
    *,
    memory_mib=MEMORY_MIB,
    cpu_seconds=CPU_SECONDS,
    file_bytes=FILE_BYTES,
    timeout=WALL_SECONDS,
):
    """Limit one trusted laboratory command with Linux rlimits and a wall deadline."""
    start = time.monotonic_ns()
    with subprocess.Popen(
        [
            "prlimit",
            f"--as={memory_mib * 1024 * 1024}",
            f"--cpu={cpu_seconds}",
            f"--fsize={file_bytes}",
            "--core=0",
            "--",
            *command,
        ],
        cwd=directory,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
    ) as process:
        try:
            process.wait(timeout=timeout)
            status = "ok" if process.returncode == 0 else "failed"
        except subprocess.TimeoutExpired:
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            process.wait()
            status = "timeout"
    end = time.monotonic_ns()
    return {
        "status": status,
        "returncode": process.returncode,
        "wall_ms": (end - start) / 1_000_000,
        "start_ns": start,
        "end_ns": end,
    }


def validate_evidence(directory, stem, *, page_limit=PAGE_LIMIT, file_bytes=FILE_BYTES):
    """Accept only complete evidence within the experimental output envelope."""
    pdf = directory / f"{stem}.pdf"
    report = directory / f"{stem}.json"
    try:
        if not 1 <= pdf.stat().st_size <= file_bytes or not 1 <= report.stat().st_size <= FILE_BYTES:
            raise ValueError("Evidence exceeds byte limit")
        raw = pdf.read_bytes()
        metrics = json.loads(report.read_text(encoding="utf-8"))
        reader = PdfReader(io.BytesIO(raw), strict=True)
        if (
            not isinstance(metrics, dict)
            or reader.is_encrypted
            or not 1 <= len(reader.pages) <= page_limit
            or metrics.get("pages") != len(reader.pages)
            or metrics.get("size_bytes") != len(raw)
            or metrics.get("sha256") != sha256(raw).hexdigest()
        ):
            raise ValueError("Invalid PDF evidence")
    except (OSError, PdfReadError) as exc:
        raise ValueError("Missing or invalid PDF evidence") from exc
    return metrics


def run_case(engine, orientation, slot, barrier):
    with tempfile.TemporaryDirectory(prefix="gati-pdf-capacity-") as scratch:
        directory = Path(scratch)
        barrier.wait(timeout=10)
        result = run_bounded(
            [
                sys.executable,
                str(BENCHMARK),
                "--engine",
                engine,
                "--orientation",
                orientation,
                "--assets",
                "100",
                "--signers",
                "10",
                "--repetitions",
                "2",
                "--output",
                str(directory),
            ],
            directory,
        )
        result.update(engine=engine, orientation=orientation, slot=slot)
        if result["status"] != "ok":
            return result
        try:
            metrics = validate_evidence(directory, f"json-v2-{engine}-{orientation}-100-10")
            if (
                metrics.get("engine"),
                metrics.get("orientation"),
                metrics.get("assets"),
                metrics.get("signers"),
            ) != (engine, orientation, 100, 10):
                raise ValueError("Unexpected benchmark scenario")
        except ValueError:
            result["status"] = "invalid_evidence"
            return result
        return {**result, "metrics": metrics}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    cases = []
    for engine in ("reportlab", "weasyprint"):
        for orientation in ("portrait", "landscape"):
            barrier = threading.Barrier(2)
            with ThreadPoolExecutor(max_workers=2) as executor:
                futures = [executor.submit(run_case, engine, orientation, slot, barrier) for slot in (1, 2)]
                pair = [future.result() for future in futures]
            if max(job["start_ns"] for job in pair) >= min(job["end_ns"] for job in pair):
                raise ValueError("Concurrent process intervals did not overlap")
            cases.extend(pair)
    evidence = {
        "limits": {
            "address_space_mib_per_process": MEMORY_MIB,
            "cpu_seconds_per_process": CPU_SECONDS,
            "wall_seconds_per_process": WALL_SECONDS,
            "file_bytes": FILE_BYTES,
            "pdf_pages": PAGE_LIMIT,
            "concurrent_processes": 2,
        },
        "jobs": cases,
    }
    payload = json.dumps(evidence, ensure_ascii=False, sort_keys=True, allow_nan=False)
    args.output.write_text(payload + "\n", encoding="utf-8")
    print(payload)
    if any(job["status"] != "ok" for job in cases):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
