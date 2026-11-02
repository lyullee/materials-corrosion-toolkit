import pytest

from matintegrity.contracts import RunContext
from matintegrity.models.temper_bead import (
    TemperBeadQualificationAssessment,
    specifications,
    temper_bead_qualification,
)
from matintegrity.registry import ModelRegistry

EVIDENCE = {"source_id": "authored", "origin": "synthetic", "citation": "authored test"}
DIGEST_A = "a" * 64
DIGEST_B = "b" * 64
DIGEST_C = "c" * 64
DIGEST_D = "d" * 64


def pass_record(identifier="pass-1", position=1, layer="layer-1", **updates):
    value = {
        "pass_record_id": identifier,
        "sequence_position": position,
        "layer_id": layer,
        "start_time_s": float(position - 1) * 10.0,
        "end_time_s": float(position) * 10.0,
        "heat_input_value": 1.0,
        "heat_input_unit_token": "custom-energy-per-length",
        "interpass_temperature_K": 400.0,
        "temper_bead_descriptor": "caller-sequence-a",
        "provider_id": "recorder-1",
        "provider_revision": "1",
        "provider_state_digest": DIGEST_A,
        "provider_configuration_digest": DIGEST_B,
        "input_digest": DIGEST_C,
        "result_digest": DIGEST_D,
        "record_valid": True,
        "evidence": (EVIDENCE,),
    }
    value.update(updates)
    return value


def observation(kind="hardness", identifier="obs-1", **updates):
    value = {
        "observation_id": identifier,
        "observation_kind": kind,
        "physical_specimen_id": "specimen-1",
        "source_group_id": "source-1",
        "physical_region_id": "haz-1",
        "method_id": "hardness-method",
        "result_definition": "caller hardness metric",
        "reported_value": 250.0,
        "result_unit_token": "custom-hardness-unit",
        "expanded_uncertainty": 5.0,
        "uncertainty_coverage_factor": 2.0,
        "provider_id": "laboratory-1",
        "provider_revision": "1",
        "provider_state_digest": DIGEST_A,
        "result_digest": DIGEST_D,
        "record_valid": True,
        "evidence": (EVIDENCE,),
    }
    value.update(updates)
    return value


def envelope(**updates):
    value = {
        "envelope_id": "envelope-1",
        "repair_scope_id": "repair-1",
        "joint_configuration_id": "joint-1",
        "base_material_condition_id": "base-1",
        "deposited_material_condition_id": "deposit-1",
        "welding_process_id": "process-1",
        "required_layer_sequence": ("layer-1", "layer-2"),
        "supported_temper_bead_descriptors": ("caller-sequence-a",),
        "minimum_heat_input_value": 0.5,
        "maximum_heat_input_value": 1.5,
        "heat_input_unit_token": "custom-energy-per-length",
        "minimum_interpass_temperature_K": 350.0,
        "maximum_interpass_temperature_K": 450.0,
        "observation_requirements": (
            {
                "requirement_id": "hardness-1",
                "observation_kind": "hardness",
                "method_id": "hardness-method",
                "result_definition": "caller hardness metric",
                "result_unit_token": "custom-hardness-unit",
                "minimum_value": 200.0,
                "maximum_value": 300.0,
                "requirement_basis": "caller plan",
            },
        ),
        "minimum_physical_specimen_count": 1,
        "minimum_source_group_count": 1,
        "qualification_basis": "caller qualification",
        "evidence": (EVIDENCE,),
    }
    value.update(updates)
    return value


def payload(**updates):
    value = {
        "assessment_id": "assessment-1",
        "asset_id": "asset-1",
        "location_id": "weld-1",
        "repair_scope_id": "repair-1",
        "joint_configuration_id": "joint-1",
        "base_material_condition_id": "base-1",
        "deposited_material_condition_id": "deposit-1",
        "welding_process_id": "process-1",
        "clock_id": "clock-1",
        "pass_records": (
            pass_record(),
            pass_record("pass-2", 2, "layer-2"),
        ),
        "observations": (observation(),),
        "candidate_envelopes": (envelope(),),
        "repair_joint_and_material_identity_reviewed": True,
        "deposition_sequence_and_clock_reviewed": True,
        "heat_input_and_interpass_temperature_reviewed": True,
        "temper_bead_descriptors_reviewed": True,
        "observation_methods_units_and_uncertainty_reviewed": True,
        "specimen_and_source_group_partitions_reviewed": True,
        "provider_lineage_and_digests_reviewed": True,
        "qualification_envelope_authority_reviewed": True,
    }
    value.update(updates)
    return TemperBeadQualificationAssessment(**value)


def test_inside_caller_support_computes_without_acceptance_claim():
    result = temper_bead_qualification(payload())
    assert result.status == "computed"
    assert result.values["declared_qualification_outcome"] == "within_support"
    assert result.values["observed_layer_sequence"] == ["layer-1", "layer-2"]


def test_sequence_or_pass_range_outside_support_is_out_of_scope():
    result = temper_bead_qualification(
        payload(
            pass_records=(
                pass_record(layer="layer-2"),
                pass_record("pass-2", 2, "layer-1", heat_input_value=2.0),
            )
        )
    )
    assert result.status == "out_of_scope"
    assert result.values["layer_sequence_matches"] is False
    assert result.values["outside_support_pass_record_ids"] == ["pass-2"]


def test_missing_observation_unit_or_review_needs_data():
    no_match = observation(method_id="other")
    result = temper_bead_qualification(payload(observations=(no_match,)))
    assert result.status == "needs_data"
    assert result.values["missing_observation_requirement_ids"] == ["hardness-1"]

    wrong_unit = observation(result_unit_token="other")
    assert temper_bead_qualification(payload(observations=(wrong_unit,))).status == "needs_data"
    assert (
        temper_bead_qualification(payload(provider_lineage_and_digests_reviewed=False)).status == "needs_data"
    )


def test_numeric_observation_outside_support_is_out_of_scope():
    result = temper_bead_qualification(payload(observations=(observation(reported_value=350.0),)))
    assert result.status == "out_of_scope"
    assert result.values["outside_support_observation_ids"] == ["obs-1"]


def test_order_contract_and_context_identity_are_enforced():
    with pytest.raises(ValueError, match="consecutive positions"):
        payload(pass_records=(pass_record(position=2),))

    registry = ModelRegistry()
    registry.register(specifications()[0])
    with pytest.raises(ValueError, match="must match"):
        registry.run(
            "welding.temper_bead_qualification",
            payload(),
            RunContext(asset_id="other", location_id="weld-1", time_basis="authored"),
        )
