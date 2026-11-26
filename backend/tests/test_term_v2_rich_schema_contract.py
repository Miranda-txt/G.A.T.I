"""T01: mesmo corpus adversarial para o contrato Python e Tiptap."""

import json
import runpy
from copy import deepcopy
from pathlib import Path

import pytest

POC = Path(__file__).parent / "fixtures" / "term_v2" / "tiptap_poc"
CASES = json.loads((POC / "schema_contract_cases.json").read_text(encoding="utf-8"))
VALIDATE = runpy.run_path(str(POC / "rich_schema.py"))["validate_rich_document"]


@pytest.mark.parametrize("case", CASES, ids=[case["id"] for case in CASES])
def test_shared_rich_schema_contract(case):
    source = deepcopy(case["document"])
    allowed = set(case["allowed_resource_ids"])
    if case["accept"]:
        assert VALIDATE(case["document"], allowed) == source
    else:
        with pytest.raises(ValueError):
            VALIDATE(case["document"], allowed)
    assert case["document"] == source
