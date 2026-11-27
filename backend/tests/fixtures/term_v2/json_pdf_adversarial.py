"""T01: bounded, synthetic JSON v2 document corpus; not a production sandbox."""

import argparse
import copy
import io
import json
import re
import resource
import runpy
import sys
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor
from hashlib import sha256
from importlib.metadata import version
from pathlib import Path

from pypdf import PdfReader

ROOT = Path(__file__).resolve().parent
ENGINES = ("reportlab", "weasyprint")
ORIENTATIONS = ("portrait", "landscape")
REJECTIONS = {
    "text-over": "Texto inválido",
    "rows-over": "Limite de linhas",
    "columns-over": "Limite de células",
    "nodes-over": "Limite de nós",
    "bytes-over": "Limite de tamanho",
    "ragged": "Tabela não retangular",
    "missing": "Variável ausente no snapshot",
    "resource": "Imagem não autorizada",
    "tampered": "Campos ou atributos não permitidos",
}
CASES = (
    "text-limit",
    "rows-limit",
    "columns-limit",
    "nodes-limit",
    "bytes-limit",
    "images",
    "variables",
    *REJECTIONS,
)


def _size(document):
    return len(json.dumps(document, ensure_ascii=False, separators=(",", ":")).encode("utf-8"))


def _nodes(node):
    return 1 + sum(_nodes(child) for child in node.get("content", []))


def build_case(case, orientation):
    fixture = runpy.run_path(str(ROOT.parent.parent / "test_term_v2_json_pdf_spike.py"))
    schema = runpy.run_path(str(ROOT / "tiptap_poc" / "rich_schema.py"))
    document, snapshot, images = fixture["_input"](orientation)
    nodes = document["content"]["content"]
    text, cell = fixture["_text"], fixture["_cell"]
    expected = []
    extra = []

    def paragraph(value):
        expected.append(value)
        extra.append({"type": "paragraph", "content": [text(value)]})

    if case.startswith("text-"):
        limit = schema["TEXT_LIMIT"]
        value = ("Revisão çãé " * limit)[:limit].rstrip().ljust(limit, "x")
        paragraph(value + ("x" if case == "text-over" else ""))
        extra[0]["content"][0]["marks"] = [{"type": "bold"}, {"type": "italic"}]
        paragraph("Q" + "x" * (limit - 2) + "Z")
    elif case.startswith(("rows-", "columns-")):
        count = (101 if case == "rows-over" else 100) if case.startswith("rows-") else 10
        width = (13 if case == "columns-over" else 12) if case.startswith("columns-") else 2
        rows = []
        for i in range(count):
            values = [f"R{i:03d}C{j:02d}" for j in range(width)]
            expected.extend(values)
            rows.append({"type": "tableRow", "content": [cell(value) for value in values]})
        extra.append({"type": "table", "content": rows})
    elif case.startswith("nodes-"):
        remaining = schema["NODE_LIMIT"] - _nodes(document["content"])
        for i in range(remaining // 2):
            paragraph(f"NODO-{i:04d}-FIM")
        if remaining % 2:
            extra.append({"type": "paragraph"})
        if case == "nodes-over":
            extra.append({"type": "paragraph"})
    elif case.startswith("bytes-"):
        for i in range(33):
            paragraph(f"B{i:03d}-FIM:")
        nodes[2:2] = extra
        remaining = schema["BYTE_LIMIT"] - _size(document) + (case == "bytes-over")
        expected.clear()
        for block in extra:
            leaf = block["content"][0]
            capacity = schema["TEXT_LIMIT"] - len(leaf["text"])
            take = min(remaining, capacity * 2)
            leaf["text"] += "ç" * (take // 2) + "x" * (take % 2)
            expected.append(leaf["text"])
            remaining -= take
        if remaining != 0:
            raise ValueError("Byte corpus construction failed")
        return document, snapshot, images, expected
    elif case == "images":
        for i in range(8):
            image = copy.deepcopy(nodes[3])
            image["attrs"]["alt"] = f"IMAGEM-{i:02d}-FIM"
            expected.append(image["attrs"]["alt"])
            extra.append(image)
    elif case == "variables":
        value = "VAR-" + "x" * 392 + "-FIM"
        snapshot["fields"]["emissao.numero"] = value
        for i in range(20):
            marker = f"CAMPO-{i:02d}:"
            expected.append(marker + value)
            extra.append(
                {
                    "type": "paragraph",
                    "content": [text(marker), {"type": "variable", "attrs": {"key": "emissao.numero"}}],
                }
            )
    elif case == "ragged":
        nodes[2]["content"][1]["content"].pop()
    elif case == "missing":
        nodes[1]["content"][1]["attrs"]["key"] = "emissao.numero"
    elif case == "resource":
        nodes[3]["attrs"]["resourceId"] = "bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb"
    elif case == "tampered":
        nodes[4]["attrs"] = {"patrimonio": "FALSO"}
    else:
        raise ValueError("Unknown corpus case")
    nodes[2:2] = extra
    return document, snapshot, images, expected


def _normalized(value):
    return re.sub(r"\s+", "", value)


def inspect_pdf(pdf, orientation, expected, capacity, image_count):
    if not pdf.startswith(b"%PDF-") or not 1 <= len(pdf) <= capacity["FILE_BYTES"]:
        raise ValueError("Invalid PDF size or signature")
    reader = PdfReader(io.BytesIO(pdf), strict=True)
    if reader.is_encrypted or not 1 <= len(reader.pages) <= capacity["PAGE_LIMIT"]:
        raise ValueError("Invalid PDF page envelope")
    width, height = (595.28, 841.89) if orientation == "portrait" else (841.89, 595.28)
    if any(
        abs(float(p.mediabox.width) - width) >= 1 or abs(float(p.mediabox.height) - height) >= 1
        for p in reader.pages
    ):
        raise ValueError("Invalid PDF dimensions")
    content = "\n".join(p.extract_text() or "" for p in reader.pages)
    content = re.sub(r"GATI - PDF comum experimental|Página\s+\d+", "", content)
    content = _normalized(content)
    values = ["<b>literal</b>", *expected, "Campo", "Valor", "Condição", "Aprovada", "Etiqueta sintética"]
    values += [f"GATI-{i:04d}" for i in range(1, 101)]
    values += [f"Signatário {i:02d}" for i in range(1, 11)] + ["Fim do conteúdo."]
    cursor = 0
    for value in values:
        needle = _normalized(value)
        if content.count(needle) != 1:
            raise ValueError("Missing or duplicated expected content")
        cursor = content.index(needle, cursor) + len(needle)
    if content.count(_normalized("Equipamento sintético")) != 100:
        raise ValueError("Missing snapshot descriptions")
    # These two candidates use direct image XObjects; count drawing operations, not resources.
    draws = 0
    for page in reader.pages:
        objects = page["/Resources"].get("/XObject", {})
        for operands, operator in page.get_contents().operations:
            if operator == b"Do" and objects[operands[0]].get_object().get("/Subtype") == "/Image":
                draws += 1
    if draws != image_count:
        raise ValueError("Missing or duplicated image draws")
    return {
        "pages": len(reader.pages),
        "size_bytes": len(pdf),
        "sha256": sha256(pdf).hexdigest(),
        "image_draws": draws,
    }


def _stem(engine, orientation, case):
    return f"adversarial-{engine}-{orientation}-{case}"


def child(engine, orientation, case, directory):
    capacity = runpy.run_path(str(ROOT / "json_pdf_capacity.py"))
    renderer = runpy.run_path(str(ROOT / "json_pdf_spike.py"))["render_document"]
    document, snapshot, images, expected = build_case(case, orientation)
    original = copy.deepcopy((document, snapshot, images))
    start_wall, start_cpu = time.monotonic_ns(), time.process_time_ns()
    rejection = REJECTIONS.get(case)
    pdf = None
    try:
        pdf = renderer(document, snapshot, images, engine)
    except ValueError as exc:
        if rejection is None or str(exc) != rejection:
            raise
    if (pdf is None) != (rejection is not None):
        raise ValueError("Unexpected accept/reject result")
    metrics = {
        "engine": engine,
        "orientation": orientation,
        "case": case,
        "engine_version": version(engine),
        "python_version": sys.version.split()[0],
        "status": "rejected" if rejection else "ok",
        "input_bytes": _size(document),
        "input_nodes": _nodes(document["content"]),
        "wall_ms": (time.monotonic_ns() - start_wall) / 1_000_000,
        "cpu_ms": (time.process_time_ns() - start_cpu) / 1_000_000,
        "input_unchanged": (document, snapshot, images) == original,
    }
    if not metrics["input_unchanged"]:
        raise ValueError("Input mutation")
    stem = _stem(engine, orientation, case)
    if pdf is not None:
        image_count = sum(node["type"] == "resourceImage" for node in document["content"]["content"])
        metrics.update(inspect_pdf(pdf, orientation, expected, capacity, image_count))
        (directory / f"{stem}.pdf").write_bytes(pdf)
    else:
        metrics["rejection"] = case
    metrics["peak_rss_kib"] = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    (directory / f"{stem}.json").write_text(json.dumps(metrics, allow_nan=False) + "\n", encoding="utf-8")


def run_case(engine, orientation, case, output):
    if engine not in ENGINES or orientation not in ORIENTATIONS or case not in CASES:
        raise ValueError("Invalid corpus scenario")
    capacity = runpy.run_path(str(ROOT / "json_pdf_capacity.py"))
    stem = _stem(engine, orientation, case)
    if any((output / f"{stem}.{suffix}").exists() for suffix in ("pdf", "json")):
        raise ValueError("Output already exists; use an empty evidence directory")
    with tempfile.TemporaryDirectory(prefix="gati-pdf-adversarial-") as scratch:
        directory = Path(scratch)
        result = capacity["run_bounded"](
            [
                sys.executable,
                str(Path(__file__).resolve()),
                "--child",
                engine,
                orientation,
                case,
                "--output",
                str(directory),
            ],
            directory,
        )
        result.update(engine=engine, orientation=orientation, case=case)
        if result["status"] != "ok":
            return result
        report = directory / f"{stem}.json"
        pdf = directory / f"{stem}.pdf"
        expected_status = "rejected" if case in REJECTIONS else "ok"
        try:
            if not 1 <= report.stat().st_size <= capacity["FILE_BYTES"]:
                raise ValueError("Invalid report size")
            metrics = json.loads(report.read_text(encoding="utf-8"))
            if not isinstance(metrics, dict) or (
                metrics.get("engine"),
                metrics.get("orientation"),
                metrics.get("case"),
                metrics.get("status"),
                metrics.get("input_unchanged"),
            ) != (engine, orientation, case, expected_status, True):
                raise ValueError("Invalid report metadata")
            if expected_status == "ok":
                capacity["validate_evidence"](directory, stem)
            elif pdf.exists() or metrics.get("rejection") != case:
                raise ValueError("Rejected document produced PDF or incorrect result")
        except (OSError, ValueError):
            result["status"] = "invalid_evidence"
            return result
        output.mkdir(parents=True, exist_ok=True)
        # Publish only validated bytes; a failed copy must not leave a partial PDF.
        with tempfile.TemporaryDirectory(prefix=".publish-", dir=output) as staging:
            stage = Path(staging)
            (stage / report.name).write_bytes(report.read_bytes())
            if expected_status == "ok":
                (stage / pdf.name).write_bytes(pdf.read_bytes())
            (stage / report.name).replace(output / report.name)
            if expected_status == "ok":
                (stage / pdf.name).replace(output / pdf.name)
        return {**result, "status": expected_status, "metrics": metrics}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--child", nargs=3, metavar=("ENGINE", "ORIENTATION", "CASE"))
    args = parser.parse_args()
    if args.child:
        engine, orientation, case = args.child
        if engine not in ENGINES or orientation not in ORIENTATIONS or case not in CASES:
            parser.error("Invalid corpus scenario")
        child(engine, orientation, case, args.output)
        return
    args.output.mkdir(parents=True, exist_ok=True)
    if any(args.output.iterdir()):
        parser.error("Use an empty evidence directory")
    jobs = []
    with ThreadPoolExecutor(max_workers=2) as executor:
        for orientation in ORIENTATIONS:
            for case in CASES:
                futures = [executor.submit(run_case, e, orientation, case, args.output) for e in ENGINES]
                jobs.extend(f.result() for f in futures)
    payload = json.dumps({"jobs": jobs}, ensure_ascii=False, sort_keys=True, allow_nan=False)
    (args.output / "adversarial-summary.json").write_text(payload + "\n", encoding="utf-8")
    print(payload)
    if any(job["status"] != ("rejected" if job["case"] in REJECTIONS else "ok") for job in jobs):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
