import hashlib
import json

import pytest

from matintegrity.api581_pinned_adapter import (
    PINNED_SCHEMA_SHA256,
    PinnedPofMethodSelectionRequest,
)
from matintegrity.api581_pinned_validation import (
    _independent_minimal_validate,
    _select_and_check_contract,
    validate_pinned_method_selection_request,
)
from matintegrity.contracts import canonical_digest


def input_schema():
    return {
        "additionalProperties": False,
        "properties": {
            "method": {
                "enum": [
                    "structural_reliability",
                    "statistical_generic_data",
                    "expert_judgment",
                    "combined",
                ],
                "type": "string",
            },
            "qualification_basis": {"maxLength": 1000, "minLength": 1, "type": "string"},
            "uncertainty_quantified": {"type": "boolean"},
        },
        "required": ["method", "qualification_basis", "uncertainty_quantified"],
        "type": "object",
    }


def document():
    return {"frequency/pof-method-selection": {"input_schema": input_schema()}}


def request():
    return PinnedPofMethodSelectionRequest(
        method="structural_reliability",
        qualification_basis="Caller-reviewed qualification QB-1.",
        uncertainty_quantified=True,
    )


def test_provenance_bound_report_with_pinned_bytes(monkeypatch):
    raw = json.dumps(document(), separators=(",", ":")).encode()
    digest = hashlib.sha256(raw).hexdigest()
    monkeypatch.setattr("matintegrity.api581_pinned_validation.PINNED_SCHEMA_SHA256", digest)

    report = validate_pinned_method_selection_request(raw, request())

    assert report.schema_sha256 == PINNED_SCHEMA_SHA256
    assert report.calculation_id == "frequency/pof-method-selection"
    assert report.required_fields == ("method", "qualification_basis", "uncertainty_quantified")
    assert report.additional_properties is False
    assert report.request_digest == canonical_digest(request().model_dump(mode="json"))
    assert report.validation_engine in {"jsonschema", "independent_minimal"}


def test_raw_schema_digest_mismatch_is_rejected():
    with pytest.raises(ValueError, match="SHA256"):
        validate_pinned_method_selection_request(b"{}", request())


@pytest.mark.parametrize(
    ("mutation", "message"),
    [
        (lambda schema: schema.update(additionalProperties=True), "additionalProperties"),
        (lambda schema: schema.update(required=["method"]), "required fields"),
        (lambda schema: schema["properties"].pop("uncertainty_quantified"), "property fields"),
        (lambda schema: schema["properties"]["method"].update(enum=["combined"]), "method enum"),
    ],
)
def test_selected_contract_shape_mismatch_is_rejected(mutation, message):
    value = document()
    mutation(value["frequency/pof-method-selection"]["input_schema"])
    with pytest.raises(ValueError, match=message):
        _select_and_check_contract(value)


def test_independent_validator_rejects_additional_or_wrongly_typed_fields():
    schema = input_schema()
    extra = {**request().model_dump(), "probability_of_failure": 0.2}
    with pytest.raises(ValueError, match="additional properties"):
        _independent_minimal_validate(extra, schema)
    wrong_type = {**request().model_dump(), "uncertainty_quantified": 1}
    with pytest.raises(ValueError, match="must be boolean"):
        _independent_minimal_validate(wrong_type, schema)
