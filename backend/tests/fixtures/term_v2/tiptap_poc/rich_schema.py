"""Servidor experimental: valida JSON rico sem confiar em Tiptap, DOM ou URLs.

Não integrar ao Django produtivo. Não consulta banco e não usa dados pessoais.
"""

import json
import re
import uuid

NODE_TYPES = {
    "doc",
    "heading",
    "paragraph",
    "text",
    "variable",
    "patrimonialBlock",
    "table",
    "tableRow",
    "tableCell",
    "tableHeader",
    "resourceImage",
}
MARKS = {"bold", "italic", "underline"}
COMMON = {
    "responsavel.nome",
    "responsavel.documento_mascarado",
    "responsavel.departamento",
    "processo.tipo",
    "processo.data",
    "processo.localizacao",
    "emissao.numero",
    "emissao.data",
}
LOAN = {"emprestimo.inicio", "emprestimo.prazo_original", "emprestimo.finalidade"}
CHILDREN = {
    "doc": {"heading", "paragraph", "patrimonialBlock", "table", "resourceImage"},
    "heading": {"text", "variable"},
    "paragraph": {"text", "variable"},
    "table": {"tableRow"},
    "tableRow": {"tableCell", "tableHeader"},
    "tableCell": {"paragraph"},
    "tableHeader": {"paragraph"},
}
NO_CONTENT = {"text", "variable", "patrimonialBlock", "resourceImage"}
TEXT_LIMIT = 4096
BYTE_LIMIT = 131072
NODE_LIMIT = 1000
DEPTH_LIMIT = 8


def _obj(obj, required, optional=()):
    if (
        not isinstance(obj, dict)
        or not set(required).issubset(obj)
        or not set(obj).issubset(set(required) | set(optional))
    ):
        raise ValueError("Campos ou atributos não permitidos")


def _node(node, parent, depth, ctx):
    if depth > DEPTH_LIMIT:
        raise ValueError("Profundidade acima do limite")
    _obj(node, ("type",), ("content", "attrs", "text", "marks"))
    kind = node["type"]
    if kind not in NODE_TYPES:
        raise ValueError("Nó não permitido")
    if parent is not None and kind not in CHILDREN.get(parent, set()):
        raise ValueError("Hierarquia inválida")
    ctx["count"] += 1
    if ctx["count"] > NODE_LIMIT:
        raise ValueError("Limite de nós")
    if kind == "text":
        _obj(node, ("type", "text"), ("marks",))
        value = node["text"]
        if (
            not isinstance(value, str)
            or not 1 <= len(value) <= TEXT_LIMIT
            or any(ord(ch) < 32 and ch not in "\t\n" for ch in value)
        ):
            raise ValueError("Texto inválido")
        marks = node.get("marks", [])
        if not isinstance(marks, list) or len(marks) > 3:
            raise ValueError("Marcas inválidas")
        seen = set()
        for mark in marks:
            _obj(mark, ("type",))
            if mark["type"] not in MARKS or mark["type"] in seen:
                raise ValueError("Marca não permitida")
            seen.add(mark["type"])
        return
    if kind == "patrimonialBlock":
        _obj(node, ("type",))
        ctx["protected"] += 1
        return
    if kind == "variable":
        _obj(node, ("type", "attrs"))
        _obj(node["attrs"], ("key",))
        key = node["attrs"]["key"]
        if not isinstance(key, str) or key not in (
            COMMON | (LOAN if ctx["classification"] == "EMPRESTIMO" else set())
        ):
            raise ValueError("Variável fora da classificação")
        return
    if kind == "resourceImage":
        _obj(node, ("type", "attrs"))
        attrs = node["attrs"]
        _obj(attrs, ("resourceId", "alt", "width", "height"))
        try:
            rid = uuid.UUID(attrs["resourceId"])
        except TypeError, ValueError, AttributeError:
            raise ValueError("Recurso inválido") from None
        if (
            str(rid) != attrs["resourceId"]
            or rid.version != 4
            or attrs["resourceId"] not in ctx["allowed"]
            or not isinstance(attrs["alt"], str)
            or not attrs["alt"].strip()
            or len(attrs["alt"]) > 160
            or type(attrs["width"]) is not int
            or type(attrs["height"]) is not int
            or not 16 <= attrs["width"] <= 2000
            or not 16 <= attrs["height"] <= 2000
        ):
            raise ValueError("Imagem não autorizada")
        return
    if kind == "heading":
        _obj(node, ("type", "attrs", "content"))
        _obj(node["attrs"], ("level",))
        if type(node["attrs"]["level"]) is not int or node["attrs"]["level"] not in {1, 2, 3}:
            raise ValueError("Nível de título inválido")
    elif kind == "paragraph":
        _obj(node, ("type",), ("content",))
    else:
        _obj(node, ("type", "content"))
    children = node.get("content", [])
    if not isinstance(children, list) or (kind != "paragraph" and not children):
        raise ValueError("Conteúdo obrigatório")
    if kind == "table" and not 1 <= len(children) <= 100:
        raise ValueError("Limite de linhas")
    if kind == "tableRow" and not 1 <= len(children) <= 12:
        raise ValueError("Limite de células")
    if kind in ("tableCell", "tableHeader") and len(children) != 1:
        raise ValueError("Célula exige um parágrafo")
    for child in children:
        _node(child, kind, depth + 1, ctx)


def validate_rich_document(document, allowed_resource_ids):
    """Validates without modifying source, allowing opaque IDs only from server."""
    _obj(document, ("schema_version", "classification", "layout", "content"))
    if type(document["schema_version"]) is not int or document["schema_version"] != 2:
        raise ValueError("Versão do documento inválida")
    if document["classification"] not in {"ENTREGA", "DEVOLUCAO", "EMPRESTIMO"}:
        raise ValueError("Classificação inválida")
    _obj(document["layout"], ("paper", "orientation", "margin_mm"))
    lay = document["layout"]
    if (
        lay["paper"] != "A4"
        or lay["orientation"] not in {"portrait", "landscape"}
        or type(lay["margin_mm"]) is not int
        or not 10 <= lay["margin_mm"] <= 30
    ):
        raise ValueError("Layout inválido")
    if not isinstance(allowed_resource_ids, (set, frozenset)):
        raise ValueError("Allowlist controlada pelo servidor obrigatória")
    if any(
        not isinstance(key, str) or re.fullmatch(r"[0-9a-f-]{36}", key) is None
        for key in allowed_resource_ids
    ):
        raise ValueError("Identificadores inválidos")
    serialized = json.dumps(document, ensure_ascii=False, separators=(",", ":"))
    if len(serialized.encode("utf-8")) > BYTE_LIMIT:
        raise ValueError("Limite de tamanho")
    ctx = {
        "classification": document["classification"],
        "allowed": allowed_resource_ids,
        "count": 0,
        "protected": 0,
    }
    _node(document["content"], None, 0, ctx)
    if ctx["protected"] != 1:
        raise ValueError("Bloco patrimonial obrigatório e único")
    return document
