import pytest

from matintegrity.contracts import RunContext
from matintegrity.models.lamellar_tearing import (
    LamellarTearingApplicability,
    lamellar_tearing_applicability,
    specifications,
)
from matintegrity.registry import ModelRegistry

EVIDENCE = {"source_id": "authored", "origin": "synthetic", "citation": "authored test"}


def evidence_record(record_id="record-1", specimen_id="specimen-1", **updates):
    value = {
        "evidence_record_id": record_id,
        "physical_specimen_id": specimen_id,
        "source_group_id": f"source-{record_id}",
        "independence_group_id": f"independent-{record_id}",
        "parent_material_id": "plate-1",
        "material_condition_id": "condition-1",
        "product_form_id": "rolled-plate",
        "specimen_thickness_m": 0.03,
        "directionality_descriptor": "through-thickness-z",
        "provider_id": "laboratory-1",
        "provider_revision": "1",
        "provider_state_digest": "a" * 64,
        "input_digest": "b" * 64,
        "observations": (
            {
                "observation_id": f"observation-{record_id}",
                "observation_kind": "through-thickness-test",
                "result_name": "reported-reduction",
                "direction_id": "Z",
                "method_id": "caller-method",
                "result_value": 0.25,
                "result_unit_token": "fraction",
                "expanded_uncertainty": 0.02,
                "coverage_factor": 2.0,
                "result_digest": "c" * 64,
                "record_available": True,
                "evidence": (EVIDENCE,),
            },
        ),
        "record_valid": True,
        "supports_declared_envelope": True,
        "evidence": (EVIDENCE,),
    }
    value.update(updates)
    return value


def envelope(**updates):
    value = {
        "envelope_id": "envelope-1",
        "parent_material_id": "plate-1",
        "material_condition_id": "condition-1",
        "product_form_id": "rolled-plate",
        "directionality_descriptor": "through-thickness-z",
        "minimum_thickness_m": 0.01,
        "maximum_thickness_m": 0.05,
        "supported_joint_geometry_descriptors": ("tee-joint",),
        "supported_through_thickness_loading_descriptors": ("weld-shrinkage-normal-to-plate",),
        "supported_restraint_descriptors": ("caller-restraint-a",),
        "supported_weld_process_ids": ("process-1",),
        "supported_consumable_ids": ("consumable-1",),
        "minimum_heat_input_value": 0.5,
        "maximum_heat_input_value": 2.0,
        "heat_input_unit_token": "custom-energy-per-length",
        "evidence_requirements": (
            {
                "requirement_id": "z-test",
                "observation_kind": "through-thickness-test",
                "result_name": "reported-reduction",
                "direction_id": "Z",
                "result_unit_token": "fraction",
                "minimum_record_count": 1,
                "requirement_basis": "caller evidence plan",
            },
        ),
        "test_evidence": (evidence_record(),),
        "qualification_basis": "caller qualification programme",
        "evidence": (EVIDENCE,),
    }
    value.update(updates)
    return value


def joint(**updates):
    value = {
        "joint_id": "joint-1",
        "joint_geometry_descriptor": "tee-joint",
        "governing_thickness_m": 0.03,
        "through_thickness_loading_descriptor": "weld-shrinkage-normal-to-plate",
        "restraint_descriptor": "caller-restraint-a",
        "weld_process_id": "process-1",
        "consumable_id": "consumable-1",
        "minimum_heat_input_value": 0.8,
        "maximum_heat_input_value": 1.5,
        "heat_input_unit_token": "custom-energy-per-length",
        "record_valid": True,
        "evidence": (EVIDENCE,),
    }
    value.update(updates)
    return value


def payload(**updates):
    value = {
        "assessment_id": "lamellar-1",
        "asset_id": "asset-1",
        "location_id": "location-1",
        "physical_scope_id": "scope-1",
        "parent_material_id": "plate-1",
        "material_condition_id": "condition-1",
        "product_form_id": "rolled-plate",
        "directionality_descriptor": "through-thickness-z",
        "joints": (joint(),),
        "qualification_envelope": envelope(),
        "material_product_and_condition_reviewed": True,
        "directionality_and_thickness_reviewed": True,
        "joint_geometry_and_through_thickness_loading_reviewed": True,
        "restraint_descriptor_reviewed": True,
        "welding_process_consumable_and_heat_input_reviewed": True,
        "physical_specimen_and_source_group_partitions_reviewed": True,
        "test_method_units_and_uncertainty_reviewed": True,
        "provider_lineage_and_digests_reviewed": True,
        "qualification_envelope_authority_reviewed": True,
        "evidence": (EVIDENCE,),
    }
    value.update(updates)
    return LamellarTearingApplicability(**value)


def test_supported_joint_computes_without_susceptibility_claim():
    result = lamellar_tearing_applicability(payload())
    assert result.status == "computed"
    assert result.values["declared_applicability_outcome"] == "within_support"
    assert result.values["evidence_requirement_counts"] == {"z-test": 1}


def test_reviewed_joint_outside_caller_support_is_out_of_scope():
    result = lamellar_tearing_applicability(
        payload(joints=(joint(governing_thickness_m=0.06, restraint_descriptor="other"),))
    )
    assert result.status == "out_of_scope"
    assert result.values["joint_comparisons"][0]["outside_support_reasons"] == [
        "governing_thickness",
        "restraint_descriptor",
    ]


def test_missing_review_unit_or_evidence_requirement_needs_data():
    assert lamellar_tearing_applicability(payload(restraint_descriptor_reviewed=False)).status == "needs_data"
    assert (
        lamellar_tearing_applicability(payload(joints=(joint(heat_input_unit_token="other"),))).status
        == "needs_data"
    )
    missing = envelope(
        evidence_requirements=(
            {
                "requirement_id": "other-test",
                "observation_kind": "different",
                "result_name": "reported-reduction",
                "direction_id": "Z",
                "result_unit_token": "fraction",
                "minimum_record_count": 1,
                "requirement_basis": "caller evidence plan",
            },
        )
    )
    result = lamellar_tearing_applicability(payload(qualification_envelope=missing))
    assert result.status == "needs_data"
    assert result.values["missing_evidence_requirement_ids"] == ["other-test"]


def test_specimen_identity_ranges_and_context_are_strict():
    with pytest.raises(ValueError, match="physical specimen"):
        payload(
            qualification_envelope=envelope(
                test_evidence=(
                    evidence_record(),
                    evidence_record("record-2", "specimen-1"),
                )
            )
        )
    with pytest.raises(ValueError, match="heat-input ranges"):
        payload(joints=(joint(minimum_heat_input_value=2.0, maximum_heat_input_value=1.0),))

    registry = ModelRegistry()
    registry.register(specifications()[0])
    with pytest.raises(ValueError, match="must match"):
        registry.run(
            "welding.lamellar_tearing_applicability",
            payload(),
            RunContext(asset_id="other", location_id="location-1", time_basis="authored"),
        )
