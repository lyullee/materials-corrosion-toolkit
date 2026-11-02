import pytest

from matintegrity.contracts import RunContext
from matintegrity.models.inspection_replica_metallography import (
    ReplicaMetallographyEvidenceAssessment,
    replica_metallography_evidence,
    specifications,
)
from matintegrity.registry import ModelRegistry

EVIDENCE = {"source_id": "authored", "origin": "synthetic", "citation": "authored replica test"}
DIGEST_A = "a" * 64
DIGEST_B = "b" * 64
DIGEST_C = "c" * 64
DIGEST_D = "d" * 64


def payload(**updates):
    value = {
        "assessment_id": "replica-1",
        "asset_id": "asset-1",
        "location_id": "location-1",
        "component_id": "component-1",
        "material_condition_id": "condition-1",
        "replica_sites": (
            {
                "replica_site_id": "site-1",
                "physical_source_group_id": "surface-1",
                "location_definition": "caller mapped outer surface location",
                "replicated_area_m2": 1e-4,
                "surface_preparation_id": "preparation-1",
                "surface_preparation_description": "caller controlled preparation",
                "surface_preparation_digest": DIGEST_A,
                "preparation_record_valid": True,
                "evidence": (EVIDENCE,),
            },
        ),
        "observations": (
            {
                "observation_id": "observation-1",
                "replica_site_id": "site-1",
                "partition": "application",
                "physical_source_group_id": "surface-1",
                "method_id": "method-1",
                "microscope_id": "microscope-1",
                "microscope_configuration_digest": DIGEST_B,
                "provider_id": "provider-1",
                "provider_version": "1.0",
                "provider_state_digest": DIGEST_C,
                "morphology_descriptor": "caller-descriptor-a",
                "metric_definition": "caller feature area fraction",
                "observed_value": 0.12,
                "expanded_uncertainty": 0.02,
                "coverage_factor": 2.0,
                "unit": "1",
                "uncertainty_basis": "caller image-analysis uncertainty",
                "result_digest": DIGEST_D,
                "record_available": True,
                "evidence": (EVIDENCE,),
            },
        ),
        "candidate_envelopes": (
            {
                "envelope_id": "envelope-1",
                "method_id": "method-1",
                "microscope_id": "microscope-1",
                "microscope_configuration_digest": DIGEST_B,
                "provider_id": "provider-1",
                "provider_version": "1.0",
                "provider_state_digest": DIGEST_C,
                "supported_morphology_descriptors": ("caller-descriptor-a",),
                "metric_definition": "caller feature area fraction",
                "unit": "1",
                "minimum_supported_value": 0.0,
                "maximum_supported_value": 0.5,
                "maximum_supported_expanded_uncertainty": 0.05,
                "minimum_supported_replicated_area_m2": 5e-5,
                "maximum_supported_replicated_area_m2": 2e-4,
                "applicability_basis": "caller morphology evidence programme",
                "provider_qualification": {
                    "qualification_id": "qualification-1",
                    "calibration_dataset_digest": DIGEST_A,
                    "holdout_dataset_digest": DIGEST_D,
                    "calibration_physical_source_group_count": 10,
                    "holdout_physical_source_group_count": 4,
                    "calibration_and_holdout_independent": True,
                    "validation_metric_definition": "caller absolute fraction error",
                    "validation_metric_value": 0.03,
                    "validation_metric_unit": "1",
                    "maximum_supported_validation_metric": 0.05,
                    "qualification_basis": "caller validation plan",
                    "evidence": (EVIDENCE,),
                },
                "evidence": (EVIDENCE,),
            },
        ),
        "component_material_and_locations_reviewed": True,
        "physical_source_groups_reviewed": True,
        "surface_preparation_records_reviewed": True,
        "method_and_microscope_configuration_reviewed": True,
        "provider_identity_and_state_reviewed": True,
        "morphology_and_metric_definitions_reviewed": True,
        "units_and_uncertainty_reviewed": True,
        "result_digests_and_missingness_reviewed": True,
        "calibration_and_holdout_reviewed": True,
        "caller_envelope_authority_reviewed": True,
        "evidence": (EVIDENCE,),
    }
    value.update(updates)
    return ReplicaMetallographyEvidenceAssessment(**value)


def test_reviewed_application_observation_maps_to_declared_envelope():
    result = replica_metallography_evidence(payload())
    assert result.status == "computed"
    assert result.values["all_application_observations_within_declared_envelopes"] is True
    row = result.values["observation_comparisons"][0]
    assert row["uncertainty_interval_minimum"] == pytest.approx(0.10)


def test_outside_morphology_is_visible_without_aging_or_acceptance_inference():
    base = payload()
    observation = base.observations[0].model_copy(update={"morphology_descriptor": "unmapped"})
    result = replica_metallography_evidence(base.model_copy(update={"observations": (observation,)}))
    assert result.status == "computed"
    assert result.values["all_application_observations_within_declared_envelopes"] is False


def test_missing_observation_or_review_needs_data():
    base = payload()
    unavailable = base.observations[0].model_copy(
        update={
            "morphology_descriptor": None,
            "metric_definition": None,
            "observed_value": None,
            "expanded_uncertainty": None,
            "coverage_factor": None,
            "unit": None,
            "uncertainty_basis": None,
            "result_digest": None,
            "record_available": False,
            "missing_basis": "image result unavailable",
        }
    )
    assert replica_metallography_evidence(
        base.model_copy(update={"observations": (unavailable,)})
    ).status == ("needs_data")
    assert replica_metallography_evidence(payload(surface_preparation_records_reviewed=False)).status == (
        "needs_data"
    )


def test_context_identity_is_enforced():
    registry = ModelRegistry()
    registry.register(specifications()[0])
    with pytest.raises(ValueError, match="must match"):
        registry.run(
            "inspection.replica_metallography_evidence",
            payload(),
            RunContext(asset_id="other", location_id="location-1", time_basis="authored"),
        )
