import pytest

from matintegrity.contracts import RunContext
from matintegrity.models.solidification_cracking import (
    SolidificationCrackingApplicability,
    solidification_cracking_applicability,
    specifications,
)
from matintegrity.registry import ModelRegistry

EVIDENCE = {"source_id": "authored", "origin": "synthetic", "citation": "authored test"}
DIGEST_A = "a" * 64
DIGEST_B = "b" * 64
DIGEST_C = "c" * 64
DIGEST_D = "d" * 64


def evidence_record(**updates):
    value = {
        "evidence_record_id": "record-1",
        "qualification_test_id": "test-1",
        "physical_specimen_id": "specimen-1",
        "source_group_id": "source-1",
        "weld_metal_condition_id": "condition-1",
        "welding_process_id": "process-1",
        "consumable_classification_id": "consumable-class-1",
        "chemistry_profile_id": "chemistry-1",
        "test_method_id": "method-1",
        "result_definition": "caller crack-length metric",
        "result_value": 0.2,
        "result_unit_token": "custom-length-unit",
        "expanded_uncertainty": 0.02,
        "uncertainty_coverage_factor": 2.0,
        "provider_id": "provider-1",
        "provider_revision": "1",
        "provider_state_digest": DIGEST_A,
        "provider_configuration_digest": DIGEST_B,
        "input_digest": DIGEST_C,
        "result_digest": DIGEST_D,
        "record_valid": True,
        "supports_declared_envelope": True,
        "evidence": (EVIDENCE,),
    }
    value.update(updates)
    return value


def envelope(**updates):
    value = {
        "envelope_id": "envelope-1",
        "weld_metal_condition_id": "condition-1",
        "welding_process_id": "process-1",
        "consumable_classification_id": "consumable-class-1",
        "chemistry_basis_id": "chemistry-basis-1",
        "supported_chemistry_profile_ids": ("chemistry-1",),
        "supported_thermal_history_descriptors": ("thermal-1",),
        "supported_strain_descriptors": ("strain-1",),
        "supported_restraint_descriptors": ("restraint-1",),
        "result_definition": "caller crack-length metric",
        "result_unit_token": "custom-length-unit",
        "minimum_physical_specimen_count": 1,
        "minimum_source_group_count": 1,
        "test_evidence": (evidence_record(),),
        "qualification_basis": "caller qualification plan",
        "evidence": (EVIDENCE,),
    }
    value.update(updates)
    return value


def payload(**updates):
    value = {
        "assessment_id": "assessment-1",
        "asset_id": "asset-1",
        "location_id": "weld-1",
        "production_weld_id": "production-weld-1",
        "weld_metal_condition_id": "condition-1",
        "welding_process_id": "process-1",
        "consumable_classification_id": "consumable-class-1",
        "consumable_lot_id": "lot-1",
        "chemistry_basis_id": "chemistry-basis-1",
        "chemistry_profile_id": "chemistry-1",
        "thermal_history_descriptor": "thermal-1",
        "strain_descriptor": "strain-1",
        "restraint_descriptor": "restraint-1",
        "candidate_envelopes": (envelope(),),
        "weld_metal_process_and_consumable_reviewed": True,
        "chemistry_identity_and_basis_reviewed": True,
        "thermal_history_reviewed": True,
        "strain_and_restraint_reviewed": True,
        "specimen_and_source_group_partitions_reviewed": True,
        "test_method_units_and_uncertainty_reviewed": True,
        "provider_lineage_and_digests_reviewed": True,
        "qualification_envelope_authority_reviewed": True,
        "evidence": (EVIDENCE,),
    }
    value.update(updates)
    return SolidificationCrackingApplicability(**value)


def test_inside_caller_support_is_computed_without_crack_claim():
    result = solidification_cracking_applicability(payload())
    assert result.status == "computed"
    assert result.values["declared_applicability_outcome"] == "within_support"
    assert result.values["physical_specimen_ids"] == ["specimen-1"]


def test_descriptor_or_exact_identity_outside_support_is_out_of_scope():
    result = solidification_cracking_applicability(payload(restraint_descriptor="other"))
    assert result.status == "out_of_scope"
    assert result.values["outside_support_reasons"] == ["restraint_descriptor"]
    assert solidification_cracking_applicability(payload(welding_process_id="other")).status == "out_of_scope"


def test_invalid_evidence_missing_review_and_partition_count_need_data():
    invalid = evidence_record(
        record_valid=False,
        supports_declared_envelope=False,
        invalid_or_limiting_basis="caller marked invalid",
    )
    result = solidification_cracking_applicability(
        payload(candidate_envelopes=(envelope(test_evidence=(invalid,)),))
    )
    assert result.status == "needs_data"
    assert result.values["invalid_test_evidence_ids"] == ["record-1"]
    assert (
        solidification_cracking_applicability(payload(thermal_history_reviewed=False)).status == "needs_data"
    )
    result = solidification_cracking_applicability(
        payload(candidate_envelopes=(envelope(minimum_source_group_count=2),))
    )
    assert result.status == "needs_data"
    assert result.values["evidence_partition_counts_sufficient"] is False


def test_duplicate_support_and_context_identity_are_enforced():
    with pytest.raises(ValueError, match="unique and nonblank"):
        payload(candidate_envelopes=(envelope(supported_strain_descriptors=("strain-1", "strain-1")),))

    registry = ModelRegistry()
    registry.register(specifications()[0])
    with pytest.raises(ValueError, match="must match"):
        registry.run(
            "welding.solidification_cracking_applicability",
            payload(),
            RunContext(asset_id="other", location_id="weld-1", time_basis="authored"),
        )
