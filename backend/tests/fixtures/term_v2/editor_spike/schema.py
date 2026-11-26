"""Contrato experimental T01: valida JSON estrito, sem persistir nem renderizar HTML."""

import json

SCHEMA_VERSION = 1
MAX_NODES = 800
MAX_DEPTH = 8
MAX_BYTES = 65_536
MAX_TEXT = 4_096
COMMON_VARIABLES = {
    "responsavel.nome",
    "responsavel.documento_mascarado",
    "responsavel.departamento",
    "processo.tipo",
    "processo.data",
    "processo.localizacao",
    "emissao.numero",
    "emissao.data",
}
LOAN_VARIABLES = {"emprestimo.inicio", "emprestimo.prazo_original", "emprestimo.finalidade"}
NODE_TYPES = {
    "doc",
    "heading",
    "paragraph",
    "text",
    "variable",
    "patrimonialBlock",
    "bulletList",
    "orderedList",
    "listItem",
}
MARK_TYPES = {"bold", "italic", "underline", "strike"}


def _keys(value, required):
    if not isinstance(value, dict) or value.keys() != required:
        raise ValueError("Campos desconhecidos ou obrigatórios ausentes")


def _children(node, classification, depth, counts):
    if depth > MAX_DEPTH:
        raise ValueError("Profundidade acima do limite")
    if not isinstance(node, dict):
        raise ValueError("Nó inválido")
    counts["nodes"] += 1
    if counts["nodes"] > MAX_NODES:
        raise ValueError("Quantidade de nós acima do limite")
    typ = node.get("type")
    if typ not in NODE_TYPES:
        raise ValueError("Nó desconhecido")
    if typ == "text":
        if node.keys() not in ({"type", "text"}, {"type", "text", "marks"}):
            raise ValueError("Atributos de texto inválidos")
        value = node["text"]
        if not isinstance(value, str) or not 1 <= len(value) <= MAX_TEXT:
            raise ValueError("Texto fora dos limites")
        if any(ord(char) < 32 and char not in "\t\n" for char in value):
            raise ValueError("Caractere de controle")
        marks = node.get("marks", [])
        if not isinstance(marks, list) or len(marks) > 4:
            raise ValueError("Marcas inválidas")
        kinds = []
        for mark in marks:
            _keys(mark, {"type"})
            if mark["type"] not in MARK_TYPES:
                raise ValueError("Marca desconhecida")
            kinds.append(mark["type"])
        if len(kinds) != len(set(kinds)):
            raise ValueError("Marca duplicada")
        return
    if typ == "variable":
        _keys(node, {"type", "attrs"})
        attrs = node["attrs"]
        _keys(attrs, {"key"})
        allowed = COMMON_VARIABLES | (LOAN_VARIABLES if classification == "EMPRESTIMO" else set())
        if not isinstance(attrs["key"], str) or attrs["key"] not in allowed:
            raise ValueError("Variável ausente ou não autorizada para classificação")
        return
    if typ == "patrimonialBlock":
        _keys(node, {"type"})
        counts["protected"] += 1
        return
    if typ == "heading":
        _keys(node, {"type", "attrs", "content"})
        _keys(node["attrs"], {"level"})
        if type(node["attrs"]["level"]) is not int or node["attrs"]["level"] not in (1, 2, 3):
            raise ValueError("Nível de título inválido")
    elif typ in {"doc", "paragraph", "bulletList", "orderedList", "listItem"}:
        valid = ({"type", "content"}, {"type"} if typ == "paragraph" else set())
        if node.keys() not in valid:
            raise ValueError("Atributos de nó inválidos")
    else:
        raise ValueError("Nó desconhecido")
    contents = node.get("content", [])
    if not isinstance(contents, list):
        raise ValueError("Filhos inválidos")
    if typ == "doc" and not contents:
        raise ValueError("Documento vazio")
    parents = {
        "doc": {"heading", "paragraph", "bulletList", "orderedList", "patrimonialBlock"},
        "paragraph": {"text", "variable"},
        "heading": {"text"},
        "bulletList": {"listItem"},
        "orderedList": {"listItem"},
        "listItem": {"paragraph", "bulletList", "orderedList"},
    }
    for child in contents:
        if not isinstance(child, dict) or child.get("type") not in parents[typ]:
            raise ValueError("Hierarquia de nós inválida")
        _children(child, classification, depth + 1, counts)


def normalize(document):
    """Retorna cópia JSON aceita, preservando texto literal, sem executar markup."""
    _keys(document, {"schema_version", "classification", "layout", "content"})
    if type(document["schema_version"]) is not int or document["schema_version"] != SCHEMA_VERSION:
        raise ValueError("Versão de schema não suportada")
    classification = document["classification"]
    if not isinstance(classification, str) or classification not in {"ENTREGA", "DEVOLUCAO", "EMPRESTIMO"}:
        raise ValueError("Classificação inválida")
    layout = document["layout"]
    _keys(layout, {"paper", "orientation", "margin_mm"})
    if layout["paper"] != "A4" or layout["orientation"] not in ("portrait", "landscape"):
        raise ValueError("Layout inválido")
    if type(layout["margin_mm"]) is not int or not 10 <= layout["margin_mm"] <= 30:
        raise ValueError("Margens inválidas")
    try:
        encoded = json.dumps(document, ensure_ascii=False, allow_nan=False, separators=(",", ":"))
    except (ValueError, TypeError, RecursionError, OverflowError) as exc:
        raise ValueError("JSON inválido") from exc
    if len(encoded.encode("utf-8")) > MAX_BYTES:
        raise ValueError("Documento excede tamanho máximo")
    counts = {"nodes": 0, "protected": 0}
    _children(document["content"], classification, 0, counts)
    if counts["protected"] != 1:
        raise ValueError("Bloco patrimonial obrigatório e único")
    return json.loads(encoded)
