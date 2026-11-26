"""Testa o contrato experimental do editor T01 sem ativar funcionalidade produtiva."""

import copy
import json
import runpy
from pathlib import Path

import pytest

SPIKE = Path(__file__).parent / "fixtures" / "term_v2" / "editor_spike" / "schema.py"


def _normalize(document):
    assert SPIKE.is_file(), "T01: normalizador do editor ainda não implementado"
    return runpy.run_path(str(SPIKE))["normalize"](document)


def _document(classification="ENTREGA"):
    return {
        "schema_version": 1,
        "classification": classification,
        "layout": {"paper": "A4", "orientation": "portrait", "margin_mm": 20},
        "content": {
            "type": "doc",
            "content": [
                {
                    "type": "heading",
                    "attrs": {"level": 2},
                    "content": [{"type": "text", "text": "Termo de responsabilidade"}],
                },
                {
                    "type": "paragraph",
                    "content": [
                        {
                            "type": "text",
                            "text": "Conferência de patrimônio — condição regular. ",
                            "marks": [{"type": "bold"}],
                        },
                        {"type": "variable", "attrs": {"key": "responsavel.nome"}},
                    ],
                },
                {"type": "patrimonialBlock"},
                {
                    "type": "bulletList",
                    "content": [
                        {
                            "type": "listItem",
                            "content": [
                                {
                                    "type": "paragraph",
                                    "content": [{"type": "text", "text": "Acessórios registrados"}],
                                }
                            ],
                        }
                    ],
                },
            ],
        },
    }


def test_editor_limits_and_roundtrip():
    document = _document()
    normalized = _normalize(document)
    assert normalized["schema_version"] == 1
    assert normalized["classification"] == "ENTREGA"
    assert normalized["layout"] == {"paper": "A4", "orientation": "portrait", "margin_mm": 20}
    assert normalized["content"]["content"][2] == {"type": "patrimonialBlock"}
    assert normalized == _normalize(json.loads(json.dumps(normalized, ensure_ascii=False)))
    assert "patrimônio" in json.dumps(normalized, ensure_ascii=False)
    assert normalized == document


@pytest.mark.parametrize("missing", ["content", "layout", "classification", "schema_version"])
def test_editor_missing_document_field_rejected(missing):
    document = _document()
    del document[missing]
    with pytest.raises(ValueError):
        _normalize(document)


@pytest.mark.parametrize("classification", ["ENTREGA", "DEVOLUCAO", "EMPRESTIMO"])
def test_editor_accepted_classifications(classification):
    document = _document(classification)
    assert _normalize(document)["classification"] == classification


def test_editor_protected_block_is_mandatory_and_unique():
    document = _document()
    document["content"]["content"].pop(2)
    with pytest.raises(ValueError):
        _normalize(document)
    document = _document()
    document["content"]["content"].append({"type": "patrimonialBlock"})
    with pytest.raises(ValueError):
        _normalize(document)


@pytest.mark.parametrize(
    "node",
    [
        {"type": "iframe", "attrs": {"src": "https://example.invalid"}},
        {"type": "image", "attrs": {"src": "file:///etc/passwd"}},
        {
            "type": "text",
            "text": "clique",
            "marks": [{"type": "link", "attrs": {"href": "javascript:alert(1)"}}],
        },
        {"type": "paragraph", "attrs": {"style": "background:url(http://127.0.0.1/a)"}},
        {"type": "text", "text": "a" * 4097},
        {"type": "variable", "attrs": {"key": "nao_existe"}},
        {"type": "patrimonialBlock", "attrs": {"editable": True}},
    ],
)
def test_editor_reject_schema_and_resource_injection(node):
    document = _document()
    document["content"]["content"].insert(1, node)
    with pytest.raises(ValueError):
        _normalize(document)


@pytest.mark.parametrize("bad", [0, 2, "1", None])
def test_editor_schema_version_is_explicit(bad):
    document = _document()
    document["schema_version"] = bad
    with pytest.raises(ValueError):
        _normalize(document)


def test_editor_variable_catalog_is_classification_bound():
    document = _document()
    document["content"]["content"][1]["content"].append(
        {"type": "variable", "attrs": {"key": "emprestimo.prazo_original"}}
    )
    with pytest.raises(ValueError):
        _normalize(document)
    document["classification"] = "EMPRESTIMO"
    assert _normalize(document)["content"]["content"][1]["content"][-1]["attrs"] == {
        "key": "emprestimo.prazo_original"
    }


def test_editor_rejects_unknown_layout_and_field():
    document = _document()
    document["layout"]["orientation"] = "diagonal"
    with pytest.raises(ValueError):
        _normalize(document)
    document = _document()
    document["layout"]["margin_mm"] = 200
    with pytest.raises(ValueError):
        _normalize(document)
    document = _document()
    document["html"] = "<script>alert(1)</script>"
    with pytest.raises(ValueError):
        _normalize(document)


def test_editor_limits_depth_nodes_and_bytes():
    document = _document()
    document["content"]["content"].extend([{"type": "paragraph"}] * 801)
    with pytest.raises(ValueError):
        _normalize(document)
    document = _document()
    document["content"]["content"][0]["content"][0]["text"] = "z" * 100000
    with pytest.raises(ValueError):
        _normalize(document)
    document = _document()
    node = {"type": "text", "text": "profundo"}
    for _ in range(20):
        node = {"type": "paragraph", "content": [node]}
    document["content"]["content"].insert(0, node)
    with pytest.raises(ValueError):
        _normalize(document)


def test_editor_literal_html_remains_text():
    document = _document()
    paragraph = document["content"]["content"][1]
    paragraph["content"][0]["text"] = "<script>não executar</script>"
    assert _normalize(document)["content"]["content"][1]["content"][0]["text"] == (
        "<script>não executar</script>"
    )


def test_editor_input_is_not_mutated():
    document = _document()
    original = copy.deepcopy(document)
    _normalize(document)
    assert document == original
