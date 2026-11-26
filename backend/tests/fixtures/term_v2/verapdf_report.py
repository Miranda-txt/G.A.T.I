"""Classifica XML de um único PDF validado com veraPDF PDF/A-2b."""

import argparse
from pathlib import Path
from xml.etree.ElementTree import ParseError

from defusedxml.common import DefusedXmlException
from defusedxml.ElementTree import fromstring


def classify(xml, code):
    if code not in (0, 1):
        raise ValueError(f"Falha operacional veraPDF: {code}")
    try:
        root = fromstring(xml, forbid_dtd=True)
    except (ParseError, DefusedXmlException) as exc:
        raise ValueError("Relatório XML inválido") from exc
    reports = root.findall("./jobs/job/validationReport")
    summaries = root.findall("./batchSummary")
    if root.tag != "report" or len(reports) != 1 or len(summaries) != 1:
        raise ValueError("Relatório deve conter exatamente um resultado")
    report, summary = reports[0], summaries[0]
    if report.get("profileName") != "PDF/A-2b validation profile":
        raise ValueError("Perfil inesperado")
    if summary.get("totalJobs") != "1":
        raise ValueError("Quantidade de jobs inesperada")
    for key in ("failedToParse", "encrypted", "outOfMemory", "veraExceptions"):
        if summary.get(key) != "0":
            raise ValueError(f"Falha operacional: {key}")
    counts = summary.findall("validationReports")
    if len(counts) != 1 or counts[0].get("failedJobs") != "0":
        raise ValueError("Falha ou ausência de relatório")
    compliant = report.get("isCompliant")
    if compliant == "true" and code == 0:
        expected = ("1", "0")
        status = "compliant"
    elif compliant == "false" and code == 1:
        expected = ("0", "1")
        status = "noncompliant"
    else:
        raise ValueError("Código e relatório de conformidade inconsistentes")
    if (counts[0].get("compliant"), counts[0].get("nonCompliant")) != expected:
        raise ValueError("Contagens de conformidade inconsistentes")
    return status


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("report", type=Path)
    parser.add_argument("code", type=int)
    args = parser.parse_args()
    print(classify(args.report.read_bytes(), args.code))


if __name__ == "__main__":
    main()
