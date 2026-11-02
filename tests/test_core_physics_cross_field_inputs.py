"""Cross-field rejection probes for selected audited physics contracts."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from matintegrity.contracts import RunContext
from matintegrity.registry import default_registry

_CASES = json.loads(
    (Path(__file__).parent / "data" / "core_physics_cross_field_rejection_cases.json").read_text(
        encoding="utf-8"
    )
)["cases"]


@pytest.mark.parametrize("case", _CASES, ids=lambda case: f"{case['model_id']}:{case['validator']}")
def test_cross_field_identity_or_history_inconsistency_is_rejected(case: dict) -> None:
    spec = default_registry()._models[case["model_id"]]
    if case.get("validation_stage") == "context":
        request = spec.input_type.model_validate_json(json.dumps(case["input"], allow_nan=False))
        context = RunContext.model_validate_json(json.dumps(case["context"], allow_nan=False))
        with pytest.raises(ValueError, match=case["expected_message"]):
            default_registry().run(case["model_id"], request, context)
        return
    if case.get("validation_stage") == "evaluator_status":
        request = spec.input_type.model_validate_json(json.dumps(case["input"], allow_nan=False))
        result = spec.evaluator(request)
        assert result.status == case["expected_status"]
        return
    if case.get("validation_stage") == "evaluator":
        request = spec.input_type.model_validate_json(json.dumps(case["input"], allow_nan=False))
        with pytest.raises(ValueError, match=case["expected_message"]):
            spec.evaluator(request)
        return
    with pytest.raises(ValidationError, match=case["expected_message"]):
        spec.input_type.model_validate_json(json.dumps(case["input"], allow_nan=False))
