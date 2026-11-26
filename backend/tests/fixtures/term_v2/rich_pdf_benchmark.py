"""T01: collect rich PDF experiment metrics in an isolated Linux process."""

import argparse
import json
import platform
import resource
import runpy
import statistics
import time
from hashlib import sha256
from importlib.metadata import version
from pathlib import Path

from pypdf import PdfReader

ROOT = Path(__file__).resolve().parent
TEST_FILE = ROOT.parent.parent / "test_term_v2_rich_pdf_spike.py"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--engine", required=True, choices=("reportlab", "weasyprint"))
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--repetitions", type=int, default=5)
    args = parser.parse_args()
    if not 2 <= args.repetitions <= 30:
        parser.error("Repetições devem estar entre 2 e 30")
    doc, images = runpy.run_path(str(TEST_FILE))["_input"]()
    render = runpy.run_path(str(ROOT / "rich_pdf_spike.py"))["render_rich"]
    reference = render(doc, engine=args.engine, approved_images=images)
    wall_ms = []
    cpu_ms = []
    for _ in range(args.repetitions):
        start_wall = time.perf_counter_ns()
        start_cpu = time.process_time_ns()
        render(doc, engine=args.engine, approved_images=images)
        cpu_ms.append((time.process_time_ns() - start_cpu) / 1_000_000)
        wall_ms.append((time.perf_counter_ns() - start_wall) / 1_000_000)
    result = {
        "engine": args.engine,
        "assets": len(doc["assets"]),
        "signers": len(doc["signers"]),
        "repetitions": args.repetitions,
        "wall_ms": wall_ms,
        "cpu_ms": cpu_ms,
        "wall_median_ms": statistics.median(wall_ms),
        "cpu_median_ms": statistics.median(cpu_ms),
        "peak_rss_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        "pages": len(PdfReader(__import__("io").BytesIO(reference), strict=True).pages),
        "size_bytes": len(reference),
        "sha256": sha256(reference).hexdigest(),
        "python": platform.python_version(),
        "renderer_version": version("reportlab" if args.engine == "reportlab" else "weasyprint"),
    }
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / f"rico-{args.engine}.pdf").write_bytes(reference)
    payload = json.dumps(result, ensure_ascii=False, sort_keys=True)
    (args.output / f"rico-{args.engine}.json").write_text(payload + "\n", encoding="utf-8")
    print(payload)


if __name__ == "__main__":
    main()
