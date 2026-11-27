"""T01: measure direct JSON v2 rendering in a separate Linux process."""

import argparse
import copy
import io
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
TEST_FILE = ROOT.parent.parent / "test_term_v2_json_pdf_spike.py"


def inspect_pdf(pdf, orientation, assets, signers):
    reader = PdfReader(io.BytesIO(pdf), strict=True)
    width, height = (595.28, 841.89) if orientation == "portrait" else (841.89, 595.28)
    if not pdf.startswith(b"%PDF-") or reader.is_encrypted or not reader.pages:
        raise ValueError("Invalid PDF evidence")
    if any(
        abs(float(page.mediabox.width) - width) >= 1 or abs(float(page.mediabox.height) - height) >= 1
        for page in reader.pages
    ):
        raise ValueError("Incorrect page dimensions")
    text = "\n".join(page.extract_text() or "" for page in reader.pages)
    expected = [f"GATI-{i:04d}" for i in range(1, assets + 1)]
    expected.extend(f"Signatário {i:02d}" for i in range(1, signers + 1))
    if any(text.count(value) != 1 for value in expected):
        raise ValueError("Missing or duplicated snapshot content")
    if "<b>literal</b>" not in text or "Fim do conteúdo." not in text:
        raise ValueError("Missing editor content")
    if not any(page.images for page in reader.pages):
        raise ValueError("Missing approved image")
    return {"pages": len(reader.pages), "size_bytes": len(pdf), "sha256": sha256(pdf).hexdigest()}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--engine", required=True, choices=("reportlab", "weasyprint"))
    parser.add_argument("--orientation", choices=("portrait", "landscape"), default="portrait")
    parser.add_argument("--assets", type=int, choices=(1, 100), default=100)
    parser.add_argument("--signers", type=int, choices=(1, 10), default=10)
    parser.add_argument("--repetitions", type=int, default=10)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if not 2 <= args.repetitions <= 30:
        parser.error("Repetitions must be between 2 and 30")
    if platform.system() != "Linux":
        parser.error("RSS measurement requires Linux")
    document, snapshot, images = runpy.run_path(str(TEST_FILE))["_input"](args.orientation)
    snapshot["assets"] = snapshot["assets"][: args.assets]
    snapshot["signers"] = snapshot["signers"][: args.signers]
    original = copy.deepcopy((document, snapshot, images))
    render = runpy.run_path(str(ROOT / "json_pdf_spike.py"))["render_document"]
    samples = []
    for index in range(args.repetitions + 1):
        start_wall = time.perf_counter_ns()
        start_cpu = time.process_time_ns()
        pdf = render(document, snapshot, images, args.engine)
        cpu_ms = (time.process_time_ns() - start_cpu) / 1_000_000
        wall_ms = (time.perf_counter_ns() - start_wall) / 1_000_000
        evidence = inspect_pdf(pdf, args.orientation, args.assets, args.signers)
        if (document, snapshot, images) != original:
            raise ValueError("Renderer mutated input")
        if index == 0:
            reference = pdf
            reference_metrics = evidence
            first_render_wall_ms = wall_ms
        else:
            if evidence["pages"] != reference_metrics["pages"]:
                raise ValueError("Inconsistent page count")
            samples.append({**evidence, "wall_ms": wall_ms, "cpu_ms": cpu_ms})
    metrics = {
        **reference_metrics,
        "engine": args.engine,
        "orientation": args.orientation,
        "assets": args.assets,
        "signers": args.signers,
        "repetitions": args.repetitions,
        "first_render_wall_ms": first_render_wall_ms,
        "samples": samples,
        "peak_rss_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        "all_same_sha256": all(sample["sha256"] == reference_metrics["sha256"] for sample in samples),
        "python": platform.python_version(),
        "platform": platform.platform(),
        "renderer_version": version(args.engine),
    }
    for key in ("wall_ms", "cpu_ms"):
        values = [sample[key] for sample in samples]
        metrics[f"{key}_median"] = statistics.median(values)
        metrics[f"{key}_max"] = max(values)
    stem = f"json-v2-{args.engine}-{args.orientation}-{args.assets}-{args.signers}"
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / f"{stem}.pdf").write_bytes(reference)
    payload = json.dumps(metrics, ensure_ascii=False, sort_keys=True, allow_nan=False)
    (args.output / f"{stem}.json").write_text(payload + "\n", encoding="utf-8")
    print(payload)


if __name__ == "__main__":
    main()
