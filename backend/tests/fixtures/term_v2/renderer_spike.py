"""Spike descartável de PDF T01; não importar no código produtivo."""

from io import BytesIO
from pathlib import Path

import reportlab
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase.pdfmetrics import registerFont, stringWidth
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen.canvas import Canvas

FONT = "GATISpikeVera"
FONT_SIZE = 11
MARGIN = 42
LEADING = 16
MAX_PAGES = 20
MAX_TEXT = 512

# Fonte local do pacote fixado, nunca selecionada por entrada do usuário.
registerFont(TTFont(FONT, str(Path(reportlab.__file__).resolve().parent / "fonts" / "Vera.ttf")))


def _require_keys(value, expected):
    if not isinstance(value, dict) or value.keys() != expected:
        raise ValueError("Campos inválidos no documento experimental")


def _plain_text(value):
    if not isinstance(value, str) or not value.strip() or len(value) > MAX_TEXT:
        raise ValueError("Texto inválido no spike")
    if any(ord(char) < 32 or 127 <= ord(char) < 160 for char in value):
        raise ValueError("Caractere de controle não permitido")
    # O protótipo limita o conjunto de caracteres ao WinAnsi; não substitui glifos.
    try:
        value.encode("cp1252")
    except UnicodeEncodeError as exc:
        raise ValueError("Caractere fora da fonte experimental") from exc
    return value


def _lines(value, width):
    line = ""
    for word in value.split():
        if stringWidth(word, FONT, FONT_SIZE) > width:
            raise ValueError("Palavra excede a largura disponível")
        candidate = f"{line} {word}" if line else word
        if stringWidth(candidate, FONT, FONT_SIZE) > width:
            yield line
            line = word
        else:
            line = candidate
    if line:
        yield line


def render_document(document):
    """Gera PDF comum de texto literal, sem interpretar HTML ou carregar recursos."""
    _require_keys(document, {"title", "paragraph", "assets", "signers", "resources"})
    if document["resources"] != []:
        raise ValueError("Recursos externos ou não aprovados são proibidos")
    assets = document["assets"]
    signers = document["signers"]
    if not isinstance(assets, list) or not 1 <= len(assets) <= 100:
        raise ValueError("Limite de ativos do spike")
    if not isinstance(signers, list) or not 1 <= len(signers) <= 10:
        raise ValueError("Limite de signatários do spike")

    for asset in assets:
        _require_keys(asset, {"patrimonio", "descricao"})
    for signer in signers:
        _require_keys(signer, {"nome"})

    blocks = [_plain_text(document["title"]), _plain_text(document["paragraph"])]
    blocks.extend(f"{_plain_text(asset['patrimonio'])} {_plain_text(asset['descricao'])}" for asset in assets)
    blocks.extend(_plain_text(signer["nome"]) for signer in signers)

    width, height = A4
    text_width = width - 2 * MARGIN
    stream = BytesIO()
    pdf = Canvas(stream, pagesize=A4, invariant=1, pageCompression=1, initialFontName=FONT)
    pdf.setFont(FONT, FONT_SIZE)
    y = height - MARGIN
    pages = 1
    for block in blocks:
        for line in _lines(block, text_width):
            if y < MARGIN:
                if pages >= MAX_PAGES:
                    raise ValueError("Limite de páginas do spike")
                pdf.showPage()
                pdf.setFont(FONT, FONT_SIZE)
                y = height - MARGIN
                pages += 1
            pdf.drawString(MARGIN, y, line)
            y -= LEADING
    pdf.save()
    return stream.getvalue()
