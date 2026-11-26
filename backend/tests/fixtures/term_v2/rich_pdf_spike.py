"""T01 PDF paginado de laboratório; aceita exclusivamente dados sintéticos validados."""

import base64
import html
import io
import re
from functools import partial

from PIL import Image as PillowImage
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Image, LongTable, Paragraph, SimpleDocTemplate, Spacer, TableStyle
from weasyprint import HTML
from weasyprint.urls import URLFetcherResponse

RESOURCE = re.compile(r"[0-9a-f]{8}-[0-9a-f]{4}-[1-8][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}\Z")
MAX_IMG = 1024 * 1024


def _text(value, size=400):
    if not isinstance(value, str) or not 1 <= len(value) <= size:
        raise ValueError("Texto inválido")
    if any(ord(ch) < 32 for ch in value):
        raise ValueError("Controle no texto")
    return value


def _validate(doc, images):
    if not isinstance(doc, dict) or set(doc) != {"title", "paragraph", "assets", "signers", "resource_id"}:
        raise ValueError("Schema inválido")
    if not isinstance(images, dict):
        raise ValueError("Catálogo de imagens inválido")
    _text(doc["title"])
    _text(doc["paragraph"])
    assets, signers = doc["assets"], doc["signers"]
    if not isinstance(assets, list) or not 1 <= len(assets) <= 100:
        raise ValueError("Quantidade de ativos inválida")
    if not isinstance(signers, list) or not 1 <= len(signers) <= 10:
        raise ValueError("Quantidade de signatários inválida")
    for asset in assets:
        if not isinstance(asset, dict) or set(asset) != {"patrimonio", "descricao"}:
            raise ValueError("Ativo inválido")
        _text(asset["patrimonio"])
        _text(asset["descricao"])
    for signer in signers:
        _text(signer)
    key = doc["resource_id"]
    if not isinstance(key, str) or not RESOURCE.fullmatch(key) or key not in images:
        raise ValueError("Recurso não autorizado")
    raw = images[key]
    if not isinstance(raw, bytes) or not 1 <= len(raw) <= MAX_IMG or not raw.startswith(b"\x89PNG\r\n\x1a\n"):
        raise ValueError("Imagem fora da allowlist")
    try:
        with PillowImage.open(io.BytesIO(raw)) as image:
            image.verify()
        with PillowImage.open(io.BytesIO(raw)) as image:
            width, height = image.size
            if width > 512 or height > 512 or width < 1 or height < 1 or image.format != "PNG":
                raise ValueError("Dimensões não permitidas")
    except Exception:
        raise ValueError("Imagem inválida") from None
    return raw


def restricted_fetcher(url, approved):
    """Não usa default_url_fetcher; somente URI exata de imagem sintética."""
    if url not in approved:
        raise ValueError("Fetch remoto/local proibido")
    return URLFetcherResponse(url=url, body=approved[url], headers={"Content-Type": "image/png"})


def _reportlab(doc, resource):
    buffer = io.BytesIO()
    pdf = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=36,
        leftMargin=36,
        topMargin=48,
        bottomMargin=48,
        title=doc["title"],
        invariant=1,
    )
    style = getSampleStyleSheet()
    rowstyle = style["BodyText"]
    rowstyle.fontSize = 9
    rowstyle.leading = 13
    data = [["Patrimônio", "Descrição"]]
    data.extend(
        [
            Paragraph(html.escape(a["patrimonio"]), rowstyle),
            Paragraph(html.escape(a["descricao"]), rowstyle),
        ]
        for a in doc["assets"]
    )
    table = LongTable(
        data,
        colWidths=[105, A4[0] - 72 - 105],
        repeatRows=1,
        splitByRow=1,
        hAlign="LEFT",
    )
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0F253D")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("LINEBELOW", (0, 0), (-1, -1), 0.25, colors.HexColor("#CBD5E1")),
            ]
        )
    )
    story = [
        Paragraph(html.escape(doc["title"]), style["Heading1"]),
        Paragraph(html.escape(doc["paragraph"]), style["Normal"]),
        Spacer(1, 12),
        Image(io.BytesIO(resource), width=40, height=40),
        Spacer(1, 12),
        table,
        Spacer(1, 16),
        Paragraph("Signatários", style["Heading2"]),
    ]
    story.extend(Paragraph(html.escape(s), style["Normal"]) for s in doc["signers"])

    def footer(canvas, document):
        canvas.saveState()
        canvas.setFont("Helvetica", 8)
        canvas.drawString(36, 28, "GATI — PDF comum experimental")
        canvas.drawRightString(A4[0] - 36, 28, f"Página {document.page}")
        canvas.restoreState()

    pdf.build(story, onFirstPage=footer, onLaterPages=footer)
    return buffer.getvalue()


def _weasyprint(doc, resource):
    uri = "data:image/png;base64," + base64.b64encode(resource).decode("ascii")
    fetcher = partial(restricted_fetcher, approved={uri: resource})
    escape = html.escape
    rows = "".join(
        f"<tr><td>{escape(a['patrimonio'])}</td><td>{escape(a['descricao'])}</td></tr>" for a in doc["assets"]
    )
    signers = "".join(f"<p>{escape(s)}</p>" for s in doc["signers"])
    markup = f"""<!doctype html><html lang="pt-BR"><head><meta charset="utf-8">
    <style>@page {{ size:A4; margin:18mm 13mm;
      @bottom-left {{content:'GATI — PDF comum experimental';font-size:8pt}}
      @bottom-right {{content:'Página ' counter(page);font-size:8pt}}}}
    body {{ font-family:sans-serif;font-size:10pt;line-height:1.5;color:#0F172A }}
    h1 {{ color:#0F253D;font-size:18pt }} table {{border-collapse:collapse;width:100%}}
    th {{background:#0F253D;color:white}}
    td,th {{border-bottom:0.3pt solid #CBD5E1;padding:9pt 5pt;text-align:left}}
    thead {{display:table-header-group}} tr {{break-inside:avoid}}
    img {{width:40px;height:40px}}
    </style></head><body><h1>{escape(doc["title"])}</h1>
    <p>{escape(doc["paragraph"])}</p><img alt="Etiqueta sintética" src="{uri}">
    <table><thead><tr><th>Patrimônio</th><th>Descrição</th></tr></thead>
    <tbody>{rows}</tbody></table><h2>Signatários</h2>{signers}</body></html>"""
    return HTML(string=markup, url_fetcher=fetcher).write_pdf()


def render_rich(doc, engine, approved_images):
    resource = _validate(doc, approved_images)
    if engine == "reportlab":
        return _reportlab(doc, resource)
    if engine == "weasyprint":
        return _weasyprint(doc, resource)
    raise ValueError("Motor desconhecido")
