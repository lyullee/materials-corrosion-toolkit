import pytest

from matintegrity.contracts import RunContext
from matintegrity.models.peening_treatment import (
    PeeningTreatmentAssessment,
    peening_treatment_evidence,
    specifications,
)
from matintegrity.registry import ModelRegistry

EVIDENCE = {"source_id": "authored", "origin": "synthetic", "citation": "authored test"}
DIGEST_A = "a" * 64
DIGEST_B = "b" * 64


def payload(**updates):
    value = {
        "assessment_id": "peening-1",
        "asset_id": "asset-1",
        "location_id": "location-1",
        "physical_scope_id": "scope-1",
        "component_id": "component-1",
        "material_condition_id": "condition-1",
        "clock_id": "clock-1",
        "treatment_records": (
            {
                "treatment_record_id": "treatment-1",
                "zone_id": "zone-1",
                "method_id": "method-1",
                "media_condition_id": "media-1",
                "media_lot_id": "lot-1",
                "equipment_id": "equipment-1",
                "direction_descriptor": "direction-a",
                "start_time_s": 0.0,
                "end_time_s": 100.0,
                "intensity_metric_definition": "caller intensity",
                "intensity_value": 0.4,
                "intensity_unit_token": "custom-intensity",
                "intensity_expanded_uncertainty": 0.02,
                "coverage_metric_definition": "caller coverage",
                "coverage_value": 1.0,
                "coverage_unit_token": "custom-coverage",
                "coverage_expanded_uncertainty": 0.05,
                "provider_id": "provider-1",
                "provider_version": "1",
                "provider_state_digest": DIGEST_A,
                "result_digest": DIGEST_B,
                "record_valid": True,
                "evidence": (EVIDENCE,),
            },
        ),
        "residual_stress_observations": (
            {
                "observation_id": "stress-1",
                "zone_id": "zone-1",
                "physical_specimen_id": "specimen-1",
                "source_group_id": "source-1",
                "independence_group_id": "independent-1",
                "partition": "qualification",
                "coordinate_frame_id": "surface-frame",
                "stress_component_id": "tangential",
                "depth_m": 0.0001,
                "method_id": "stress-method-1",
                "reported_value": -200.0,
                "unit_token": "custom-stress",
                "expanded_uncertainty": 20.0,
                "provider_id": "laboratory-1",
                "provider_version": "1",
                "provider_state_digest": DIGEST_A,
                "result_digest": DIGEST_B,
                "record_valid": True,
                "evidence": (EVIDENCE,),
            },
        ),
        "candidate_envelopes": (
            {
                "envelope_id": "envelope-1",
                "material_condition_id": "condition-1",
                "supported_method_ids": ("method-1",),
                "supported_media_condition_ids": ("media-1",),
                "supported_direction_descriptors": ("direction-a",),
                "intensity_metric_definition": "caller intensity",
                "intensity_unit_token": "custom-intensity",
                "minimum_intensity_value": 0.2,
                "maximum_intensity_value": 0.6,
                "coverage_metric_definition": "caller coverage",
                "coverage_unit_token": "custom-coverage",
                "minimum_coverage_value": 0.9,
                "maximum_coverage_value": 1.1,
                "stress_requirements": (
                    {
                        "requirement_id": "stress-requirement-1",
                        "stress_component_id": "tangential",
                        "method_id": "stress-method-1",
                        "unit_token": "custom-stress",
                        "minimum_depth_m": 0.0,
                        "maximum_depth_m": 0.001,
                        "minimum_value": -400.0,
                        "maximum_value": -50.0,
                        "minimum_record_count": 1,
                        "requirement_basis": "authored plan",
                    },
                ),
                "minimum_physical_specimen_count": 1,
                "minimum_source_group_count": 1,
                "qualification_basis": "authored qualification",
                "evidence": (EVIDENCE,),
            },
        ),
        "component_material_and_zone_identity_reviewed": True,
        "treatment_clock_and_sequence_reviewed": True,
        "method_media_equipment_and_direction_reviewed": True,
        "intensity_coverage_units_and_uncertainty_reviewed": True,
        "stress_coordinate_method_units_and_uncertainty_reviewed": True,
        "specimen_source_group_and_partition_reviewed": True,
        "provider_lineage_and_digests_reviewed": True,
        "qualification_envelope_authority_reviewed": True,
        "evidence": (EVIDENCE,),
    }
    value.update(updates)
    return PeeningTreatmentAssessment(**value)


def test_reviewed_evidence_is_within_caller_support():
    result = peening_treatment_evidence(payload())
    assert result.status == "computed"
    assert result.values["declared_qualification_outcome"] == "within_support"


def test_treatment_or_stress_outside_support_is_visible():
    base = payload()
    treatment = base.treatment_records[0].model_copy(update={"intensity_value": 0.8})
    stress = base.residual_stress_observations[0].model_copy(update={"reported_value": 10.0})
    result = peening_treatment_evidence(
        base.model_copy(update={"treatment_records": (treatment,), "residual_stress_observations": (stress,)})
    )
    assert result.status == "out_of_scope"
    assert result.values["outside_support_treatment_ids"] == ["treatment-1"]
    assert result.values["outside_support_stress_observation_ids"] == ["stress-1"]


def test_unit_mismatch_or_missing_review_needs_data():
    base = payload()
    treatment = base.treatment_records[0].model_copy(update={"coverage_unit_token": "other"})
    assert (
        peening_treatment_evidence(base.model_copy(update={"treatment_records": (treatment,)})).status
        == "needs_data"
    )
    assert (
        peening_treatment_evidence(payload(provider_lineage_and_digests_reviewed=False)).status
        == "needs_data"
    )


def test_zone_linkage_and_context_identity_are_strict():
    base = payload()
    stress = base.residual_stress_observations[0].model_copy(update={"zone_id": "other"})
    with pytest.raises(ValueError, match="treated zone"):
        PeeningTreatmentAssessment(
            **base.model_dump(exclude={"residual_stress_observations"}),
            residual_stress_observations=(stress,),
        )
    registry = ModelRegistry()
    registry.register(specifications()[0])
    with pytest.raises(ValueError, match="must match"):
        registry.run(
            "welding.peening_treatment_evidence",
            base,
            RunContext(asset_id="other", location_id="location-1", time_basis="authored"),
        )
