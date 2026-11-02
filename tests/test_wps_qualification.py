import pytest

from matintegrity.contracts import RunContext
from matintegrity.models.wps_qualification import (
    WPSQualificationAssessment,
    specifications,
    wps_qualification_envelope,
)
from matintegrity.registry import ModelRegistry

EVIDENCE = {"source_id": "authored", "origin": "synthetic", "citation": "authored test"}
DIGEST_A = "a" * 64
DIGEST_B = "b" * 64
DIGEST_C = "c" * 64
DIGEST_D = "d" * 64


def evidence_record(**updates):
    value = {
        "evidence_record_id": "evidence-1",
        "qualification_test_id": "test-1",
        "physical_specimen_id": "specimen-1",
        "source_group_id": "source-group-1",
        "provider_id": "provider-1",
        "provider_revision": "revision-1",
        "provider_state_digest": DIGEST_A,
        "provider_configuration_digest": DIGEST_B,
        "input_digest": DIGEST_C,
        "result_digest": DIGEST_D,
        "supported_variable_ids": ("heat-input", "transfer-mode"),
        "record_valid": True,
        "supports_declared_envelope": True,
        "evidence": (EVIDENCE,),
    }
    value.update(updates)
    return value


def envelope(**updates):
    value = {
        "envelope_id": "envelope-1",
        "qualified_procedure_id": "wps-1",
        "qualified_procedure_revision": "rev-1",
        "base_material_side_a_condition_id": "base-a",
        "base_material_side_b_condition_id": "base-b",
        "joint_configuration_id": "joint-1",
        "welding_process_id": "process-1",
        "essential_variables": (
            {
                "variable_id": "heat-input",
                "variable_kind": "numeric",
                "unit_token": "J/m",
                "minimum_value": 8e5,
                "maximum_value": 1.2e6,
                "applicability_basis": "caller-owned qualification",
            },
            {
                "variable_id": "transfer-mode",
                "variable_kind": "categorical",
                "unit_token": "1",
                "supported_value_tokens": ("spray", "globular"),
                "applicability_basis": "caller-owned qualification",
            },
        ),
        "test_evidence": (evidence_record(),),
        "declaration_basis": "caller-owned procedure qualification",
    }
    value.update(updates)
    return value


def payload(**updates):
    value = {
        "assessment_id": "assessment-1",
        "asset_id": "asset-1",
        "location_id": "joint-1",
        "production_weld_id": "weld-1",
        "production_procedure_id": "wps-1",
        "production_procedure_revision": "rev-1",
        "base_material_side_a_condition_id": "base-a",
        "base_material_side_b_condition_id": "base-b",
        "joint_configuration_id": "joint-1",
        "welding_process_id": "process-1",
        "production_variables": (
            {
                "record_id": "record-1",
                "variable_id": "heat-input",
                "variable_kind": "numeric",
                "unit_token": "J/m",
                "numeric_value": 1e6,
                "record_valid": True,
                "evidence": (EVIDENCE,),
            },
            {
                "record_id": "record-2",
                "variable_id": "transfer-mode",
                "variable_kind": "categorical",
                "unit_token": "1",
                "categorical_value_token": "spray",
                "record_valid": True,
                "evidence": (EVIDENCE,),
            },
        ),
        "candidate_envelopes": (envelope(),),
        "production_procedure_identity_reviewed": True,
        "material_and_joint_identity_reviewed": True,
        "variable_records_reviewed": True,
        "qualification_specimen_identity_reviewed": True,
        "provider_lineage_and_digests_reviewed": True,
        "qualification_envelope_authority_reviewed": True,
    }
    value.update(updates)
    return WPSQualificationAssessment(**value)


def test_exact_identity_units_and_evidence_produce_comparison():
    result = wps_qualification_envelope(payload())
    assert result.status == "computed"
    assert result.values["all_variables_within_declared_envelope"] is True
    assert result.values["physical_specimen_ids"] == ["specimen-1"]


def test_outside_value_is_visible_without_acceptance_claim():
    records = list(payload().production_variables)
    records[0] = records[0].model_copy(update={"numeric_value": 1.3e6})
    result = wps_qualification_envelope(payload(production_variables=tuple(records)))
    assert result.status == "computed"
    assert result.values["outside_declared_envelope_variable_ids"] == ["heat-input"]
    assert result.values["all_variables_within_declared_envelope"] is False


def test_unit_mismatch_or_unqualified_evidence_needs_data():
    records = list(payload().production_variables)
    records[0] = records[0].model_copy(update={"unit_token": "kJ/m"})
    result = wps_qualification_envelope(payload(production_variables=tuple(records)))
    assert result.status == "needs_data"
    assert result.values["unit_mismatch_variable_ids"] == ["heat-input"]

    limited = evidence_record(supports_declared_envelope=False, invalid_or_limiting_basis="not qualified")
    result = wps_qualification_envelope(payload(candidate_envelopes=(envelope(test_evidence=(limited,)),)))
    assert result.status == "needs_data"
    assert result.values["invalid_qualification_evidence_ids"] == ["evidence-1"]


def test_identity_outside_scope_and_context_identity_is_enforced():
    assert wps_qualification_envelope(payload(welding_process_id="other")).status == "out_of_scope"
    registry = ModelRegistry()
    registry.register(specifications()[0])
    with pytest.raises(ValueError, match="must match"):
        registry.run(
            "welding.wps_qualification_envelope",
            payload(),
            RunContext(asset_id="other", location_id="joint-1", time_basis="authored"),
        )


def test_contract_rejects_ambiguous_variable_shapes_and_bad_digests():
    numeric = list(envelope()["essential_variables"])
    numeric[0] = {**numeric[0], "supported_value_tokens": ("wrong",)}
    with pytest.raises(ValueError, match="cannot declare categorical"):
        envelope(essential_variables=tuple(numeric))
        payload(candidate_envelopes=(envelope(essential_variables=tuple(numeric)),))

    with pytest.raises(ValueError, match="provider_state_digest"):
        payload(
            candidate_envelopes=(envelope(test_evidence=(evidence_record(provider_state_digest="bad"),)),)
        )
