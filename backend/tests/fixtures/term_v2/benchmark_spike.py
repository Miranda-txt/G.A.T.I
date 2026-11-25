"""Medições reproduzíveis do renderer experimental em processo Linux isolado."""

import argparse
import io
import json
import platform
import resource
import runpy
import time
from hashlib import sha256
from importlib.metadata import version
from pathlib import Path

from pypdf import PdfReader

ROOT = Path(__file__).resolve().parent


def main():
    data = json.loads((ROOT / "documents.json").read_text(encoding="utf-8"))
    cases = {case["id"]: case for case in data["cases"]}
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case", choices=cases, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--repetitions", type=int, choices=range(2, 31), default=10)
    args = parser.parse_args()
    case = cases[args.case]
    document = {
        "title": data["title"],
        "paragraph": data["paragraph"],
        "assets": [
            {
                "patrimonio": f"{data['asset_prefix']}-{index:03d}",
                "descricao": data["asset_description"],
            }
            for index in range(1, case["assets"] + 1)
        ],
        "signers": [
            {"nome": f"{data['signer_prefix']} {index:02d}"} for index in range(1, case["signers"] + 1)
        ],
        "resources": [],
    }
    render = runpy.run_path(str(ROOT / "renderer_spike.py"))["render_document"]
    reference = render(document)
    digest = sha256(reference).hexdigest()
    wall_ms = []
    cpu_ms = []
    for _ in range(args.repetitions):
        start_wall = time.perf_counter_ns()
        start_cpu = time.process_time_ns()
        pdf = render(document)
        cpu_ms.append((time.process_time_ns() - start_cpu) / 1_000_000)
        wall_ms.append((time.perf_counter_ns() - start_wall) / 1_000_000)
        if sha256(pdf).hexdigest() != digest:
            raise ValueError("Renderização não determinística")
    rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    metrics = {
        "case": args.case,
        "assets": case["assets"],
        "signers": case["signers"],
        "repetitions": args.repetitions,
        "wall_ms": wall_ms,
        "cpu_ms": cpu_ms,
        "peak_rss_kib": rss,
        "size_bytes": len(reference),
        "pages": len(PdfReader(io.BytesIO(reference), strict=True).pages),
        "sha256": digest,
        "python": platform.python_version(),
        "platform": platform.platform(),
        "reportlab": version("reportlab"),
        "pypdf": version("pypdf"),
    }
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / f"{args.case}.pdf").write_bytes(reference)
    payload = json.dumps(metrics, ensure_ascii=False, sort_keys=True)
    (args.output / f"{args.case}.json").write_text(payload + "\n", encoding="utf-8")
    print(payload)


if __name__ == "__main__":
    main()
