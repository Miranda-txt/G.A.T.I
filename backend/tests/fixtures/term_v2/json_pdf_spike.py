"""T01: conversão offline do schema rico v2. Somente laboratório, não produção."""

import base64
import html
import io
import runpy
from pathlib import Path

import reportlab
from PIL import Image as PillowImage
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    Image,
    KeepTogether,
    LongTable,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    TableStyle,
)
from weasyprint import HTML
from weasyprint.text.fonts import FontConfiguration
from weasyprint.urls import URLFetcherResponse

SCHEMA = Path(__file__).parent / "tiptap_poc" / "rich_schema.py"
FONT_DIR = Path(reportlab.__file__).parent / "fonts"
FONTS = (
    ("GatiVera", "Vera.ttf"),
    ("GatiVeraBold", "VeraBd.ttf"),
    ("GatiVeraItalic", "VeraIt.ttf"),
    ("GatiVeraBoldItalic", "VeraBI.ttf"),
)
LABELS = {
    "responsavel.nome": "Responsável",
    "responsavel.documento_mascarado": "Documento mascarado",
    "responsavel.departamento": "Departamento",
    "processo.tipo": "Classificação",
    "processo.data": "Data do processo",
    "processo.localizacao": "Localização",
    "emissao.numero": "Número da emissão",
    "emissao.data": "Data da emissão",
    "emprestimo.inicio": "Início do empréstimo",
    "emprestimo.prazo_original": "Prazo original",
    "emprestimo.finalidade": "Finalidade",
}


def _fonts():
    for name, filename in FONTS:
        if name not in pdfmetrics.getRegisteredFontNames():
            pdfmetrics.registerFont(TTFont(name, str(FONT_DIR / filename)))
    pdfmetrics.registerFontFamily(
        "GatiVera",
        normal="GatiVera",
        bold="GatiVeraBold",
        italic="GatiVeraItalic",
        boldItalic="GatiVeraBoldItalic",
    )
    return set.intersection(*(set(pdfmetrics.getFont(name).face.charWidths) for name, _ in FONTS))


def _escaped(value, glyphs, limit=4096):
    if not isinstance(value, str) or not 1 <= len(value) <= limit:
        raise ValueError("Texto de renderização inválido")
    if any(ch not in "\t\n" and (ord(ch) < 32 or ord(ch) == 127 or ord(ch) not in glyphs) for ch in value):
        raise ValueError("Caractere não suportado pelas fontes experimentais")
    return html.escape(value).replace("\n", "<br/>").replace("\t", "    ")


def _snapshot(snapshot, classification, schema, glyphs):
    if not isinstance(snapshot, dict) or set(snapshot) != {"fields", "assets", "signers"}:
        raise ValueError("Snapshot inválido")
    fields, assets, signers = snapshot["fields"], snapshot["assets"], snapshot["signers"]
    allowed = schema["COMMON"] | (schema["LOAN"] if classification == "EMPRESTIMO" else set())
    required = {"responsavel.nome", "processo.tipo", "processo.localizacao"}
    if classification == "EMPRESTIMO":
        required |= schema["LOAN"]
    if not isinstance(fields, dict) or not required <= set(fields) <= allowed:
        raise ValueError("Campos do snapshot inválidos")
    if fields["processo.tipo"] != classification:
        raise ValueError("Classificação divergente do snapshot")
    if not isinstance(assets, list) or not 1 <= len(assets) <= 100:
        raise ValueError("Quantidade de ativos inválida")
    if not isinstance(signers, list) or not 1 <= len(signers) <= 10:
        raise ValueError("Quantidade de signatários inválida")
    safe_fields = {key: _escaped(value, glyphs, 400) for key, value in fields.items()}
    rows = [["Patrimônio", "Descrição"]]
    for asset in assets:
        if not isinstance(asset, dict) or set(asset) != {"patrimonio", "descricao"}:
            raise ValueError("Ativo inválido")
        rows.append([_escaped(asset[key], glyphs, 400) for key in ("patrimonio", "descricao")])
    return safe_fields, rows, [_escaped(signer, glyphs, 400) for signer in signers]


def _image(raw):
    if not isinstance(raw, bytes) or not 1 <= len(raw) <= 1024 * 1024:
        raise ValueError("Recurso fora do limite")
    try:
        with PillowImage.open(io.BytesIO(raw), formats=["PNG"]) as image:
            if not all(1 <= dimension <= 512 for dimension in image.size) or image.n_frames != 1:
                raise ValueError("Dimensões ou quadros inválidos")
            image.verify()
        with PillowImage.open(io.BytesIO(raw), formats=["PNG"]) as image:
            image.load()
            output = io.BytesIO()
            image.convert("RGBA").save(output, format="PNG")
            return output.getvalue(), image.size
    except OSError, ValueError, PillowImage.DecompressionBombError:
        raise ValueError("PNG inválido") from None


def _inline(node, fields, glyphs):
    parts = []
    for child in node.get("content", []):
        if child["type"] == "variable":
            key = child["attrs"]["key"]
            if key not in fields:
                raise ValueError("Variável ausente no snapshot")
            parts.append(fields[key])
        else:
            text = _escaped(child["text"], glyphs)
            for mark in child.get("marks", []):
                tag = {"bold": "b", "italic": "i", "underline": "u"}[mark["type"]]
                text = f"<{tag}>{text}</{tag}>"
            parts.append(text)
    return "".join(parts)


def _table(node, fields, glyphs):
    rows = []
    headers = 0
    width = len(node["content"][0]["content"])
    for row in node["content"]:
        cells = row["content"]
        if len(cells) != width:
            raise ValueError("Tabela não retangular")
        kinds = {cell["type"] for cell in cells}
        if kinds == {"tableHeader"} and headers == len(rows):
            headers += 1
        elif kinds != {"tableCell"}:
            raise ValueError("Cabeçalhos mistos ou fora do início não suportados")
        rows.append([_inline(cell["content"][0], fields, glyphs) for cell in cells])
    return ("table", rows, headers)


def _blocks(document, snapshot, approved_images):
    schema = runpy.run_path(str(SCHEMA))
    if not isinstance(approved_images, dict) or len(approved_images) > 8:
        raise ValueError("Catálogo de recursos inválido")
    schema["validate_rich_document"](document, set(approved_images))
    glyphs = _fonts()
    fields, assets, signers = _snapshot(snapshot, document["classification"], schema, glyphs)
    blocks = []
    images = {}
    for node in document["content"]["content"]:
        kind = node["type"]
        if kind == "paragraph":
            blocks.append(("paragraph", _inline(node, fields, glyphs)))
        elif kind == "heading":
            blocks.append(("heading", node["attrs"]["level"], _inline(node, fields, glyphs)))
        elif kind == "table":
            blocks.append(_table(node, fields, glyphs))
        elif kind == "resourceImage":
            attrs = node["attrs"]
            key = attrs["resourceId"]
            if key not in images:
                images[key] = _image(approved_images[key])
            raw, size = images[key]
            blocks.append(
                ("image", raw, size, attrs["width"], attrs["height"], _escaped(attrs["alt"], glyphs, 160))
            )
        elif kind == "patrimonialBlock":
            blocks.append(("heading", 2, "Dados patrimoniais protegidos"))
            blocks.extend(
                ("paragraph", f"<b>{LABELS[key]}:</b> {fields[key]}") for key in LABELS if key in fields
            )
            blocks.append(("table", assets, 1))
            blocks.append(("signers", signers))
    return blocks


def _image_size(block, width, height):
    _, _, (iw, ih), dw, dh, _ = block
    scale = min(dw * 0.75 / iw, dh * 0.75 / ih, width / iw, height / ih)
    return iw * scale, ih * scale


def _reportlab(blocks, page, margin):
    buffer = io.BytesIO()
    pdf = SimpleDocTemplate(
        buffer,
        pagesize=page,
        leftMargin=margin,
        rightMargin=margin,
        topMargin=margin,
        bottomMargin=margin,
        invariant=1,
    )
    width = page[0] - 2 * margin - 12
    height = page[1] - 2 * margin - 70
    body = ParagraphStyle("body", fontName="GatiVera", fontSize=10, leading=14, spaceAfter=5)
    cell = ParagraphStyle("cell", parent=body, fontSize=9, leading=12, spaceAfter=0)
    story = []
    for block in blocks:
        kind = block[0]
        if kind == "paragraph":
            story.append(Paragraph(block[1] or "&nbsp;", body))
        elif kind == "heading":
            size = {1: 18, 2: 14, 3: 12}[block[1]]
            style = ParagraphStyle(
                "heading",
                parent=body,
                fontName="GatiVeraBold",
                fontSize=size,
                leading=size + 4,
                keepWithNext=True,
                textColor=colors.HexColor("#0F253D"),
            )
            story.append(Paragraph(block[2], style))
        elif kind == "table":
            rows, headers = block[1:]
            data = [
                [Paragraph(f"<b>{value}</b>" if i < headers else value or "&nbsp;", cell) for value in row]
                for i, row in enumerate(rows)
            ]
            table = LongTable(
                data,
                colWidths=[width / len(rows[0])] * len(rows[0]),
                repeatRows=headers,
                splitByRow=1,
                splitInRow=1,
                hAlign="LEFT",
            )
            commands = [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#CBD5E1")),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]
            if headers:
                commands.append(("BACKGROUND", (0, 0), (-1, headers - 1), colors.HexColor("#E8EFF6")))
            table.setStyle(TableStyle(commands))
            story.extend((table, Spacer(1, 8)))
        elif kind == "signers":
            style = ParagraphStyle("signers", parent=body, fontName="GatiVeraBold", fontSize=14, leading=18)
            story.append(
                KeepTogether([Paragraph("Signatários", style), *[Paragraph(s, body) for s in block[1]]])
            )
        else:
            iw, ih = _image_size(block, width, height)
            image = Image(io.BytesIO(block[1]), width=iw, height=ih, hAlign="LEFT")
            story.extend((image, Paragraph(block[5], body)))

    def footer(canvas, document):
        canvas.setFont("GatiVera", 8)
        canvas.drawString(margin, margin / 2, "GATI - PDF comum experimental")
        canvas.drawRightString(page[0] - margin, margin / 2, f"Página {document.page}")

    pdf.build(story, onFirstPage=footer, onLaterPages=footer)
    return buffer.getvalue()


def _weasyprint(blocks, page, margin, orientation):
    approved = {}
    denied = []

    def uri(raw, mime):
        url = f"data:{mime};base64," + base64.b64encode(raw).decode("ascii")
        approved[url] = (raw, mime)
        return url

    def fetch(url):
        if url not in approved:
            denied.append(True)
            raise ValueError("Fetch remoto/local proibido")
        raw, mime = approved[url]
        return URLFetcherResponse(url=url, body=raw, headers={"Content-Type": mime})

    fonts = []
    variants = ((400, "normal"), (700, "normal"), (400, "italic"), (700, "italic"))
    for (_, filename), (weight, style) in zip(FONTS, variants, strict=True):
        source = uri((FONT_DIR / filename).read_bytes(), "font/ttf")
        fonts.append(
            f"@font-face{{font-family:GatiVera;src:url('{source}');font-weight:{weight};font-style:{style}}}"
        )
    width = page[0] - 2 * margin - 12
    height = page[1] - 2 * margin - 70
    parts = []
    for block in blocks:
        kind = block[0]
        if kind == "paragraph":
            parts.append(f"<p>{block[1] or '&nbsp;'}</p>")
        elif kind == "heading":
            parts.append(f"<h{block[1]}>{block[2]}</h{block[1]}>")
        elif kind == "table":
            rows, headers = block[1:]
            head = "".join("<tr>" + "".join(f"<th>{v}</th>" for v in row) + "</tr>" for row in rows[:headers])
            body = "".join("<tr>" + "".join(f"<td>{v}</td>" for v in row) + "</tr>" for row in rows[headers:])
            parts.append(f"<table><thead>{head}</thead><tbody>{body}</tbody></table>")
        elif kind == "signers":
            signers = "".join(f"<p>{signer}</p>" for signer in block[1])
            parts.append(f'<section class="signers"><h2>Signatários</h2>{signers}</section>')
        else:
            iw, ih = _image_size(block, width, height)
            source = uri(block[1], "image/png")
            parts.append(f'<img src="{source}" alt="" style="width:{iw}pt;height:{ih}pt"><p>{block[5]}</p>')
    markup = f"""<!doctype html><html lang="pt-BR"><head><meta charset="utf-8"><style>
    {"".join(fonts)}
    @page {{size:A4 {orientation};margin:{margin}pt;
      @bottom-left {{content:'GATI - PDF comum experimental';font:8pt GatiVera}}
      @bottom-right {{content:'Página ' counter(page);font:8pt GatiVera}}}}
    body {{font:10pt GatiVera;line-height:1.4;color:#0F172A;overflow-wrap:anywhere}}
    p {{margin:0 0 5pt}} h1,h2,h3 {{color:#0F253D;break-after:avoid}}
    h1 {{font-size:18pt}} h2 {{font-size:14pt}} h3 {{font-size:12pt}}
    .signers {{break-inside:avoid}}
    table {{width:100%;table-layout:fixed;border-collapse:collapse;margin-bottom:8pt;font-size:9pt}}
    th,td {{border:0.3pt solid #CBD5E1;padding:5pt;text-align:left;vertical-align:top}}
    th {{background:#E8EFF6}} thead {{display:table-header-group}} tr {{break-inside:avoid}}
    </style></head><body>{"".join(parts)}</body></html>"""
    pdf = HTML(string=markup, url_fetcher=fetch).write_pdf(font_config=FontConfiguration())
    if denied:
        raise ValueError("Tentativa de fetch não autorizado")
    return pdf


def render_document(document, snapshot, approved_images, engine):
    """Recebe JSON validado novamente, snapshot e bytes aprovados pelo chamador."""
    if engine not in ("reportlab", "weasyprint"):
        raise ValueError("Motor desconhecido")
    blocks = _blocks(document, snapshot, approved_images)
    orientation = document["layout"]["orientation"]
    page = A4 if orientation == "portrait" else landscape(A4)
    margin = document["layout"]["margin_mm"] * mm
    if engine == "reportlab":
        return _reportlab(blocks, page, margin)
    return _weasyprint(blocks, page, margin, orientation)
