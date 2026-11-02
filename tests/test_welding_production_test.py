import pytest

from matintegrity.contracts import RunContext
from matintegrity.models.welding_production_test import (
    ProductionWeldTestEvidenceAssessment,
    production_weld_test_evidence,
    specifications,
)
from matintegrity.registry import ModelRegistry

EVIDENCE = {"source_id": "authored", "origin": "synthetic", "citation": "authored weld test"}
DIGEST_A = "a" * 64
DIGEST_B = "b" * 64


def payload(**updates):
    value = {
        "assessment_id": "production-test-1",
        "asset_id": "asset-1",
        "location_id": "joint-1",
        "production_weld_id": "weld-1",
        "procedure_id": "procedure-1",
        "procedure_revision": "2",
        "consumable_lot_id": "consumable-lot-1",
        "material_lot_id": "material-lot-1",
        "specimens": (
            {
                "specimen_id": "specimen-1",
                "physical_source_group_id": "coupon-1",
                "extraction_location": "production extension coupon",
                "orientation_definition": "caller longitudinal direction",
                "specimen_preparation_id": "preparation-1",
                "source_mapping_valid": True,
                "evidence": (EVIDENCE,),
            },
        ),
        "observations": (
            {
                "observation_id": "observation-1",
                "requirement_id": "requirement-1",
                "test_kind": "destructive",
                "test_method_id": "test-method-1",
                "physical_source_group_id": "coupon-1",
                "specimen_id": "specimen-1",
                "examination_location": "specimen gauge section",
                "metric_definition": "caller reported proof stress",
                "unit": "Pa",
                "observed_value": 320e6,
                "expanded_uncertainty": 5e6,
                "coverage_factor": 2.0,
                "uncertainty_basis": "laboratory uncertainty record",
                "provider_id": "laboratory-1",
                "provider_version": "method-revision-3",
                "provider_state_digest": DIGEST_A,
                "result_digest": DIGEST_B,
                "record_available": True,
                "evidence": (EVIDENCE,),
            },
        ),
        "requirements": (
            {
                "requirement_id": "requirement-1",
                "test_kind": "destructive",
                "test_method_id": "test-method-1",
                "metric_definition": "caller reported proof stress",
                "unit": "Pa",
                "minimum_value": 300e6,
                "maximum_expanded_uncertainty": 10e6,
                "minimum_available_record_count": 1,
                "minimum_distinct_physical_source_groups": 1,
                "requirement_basis": "caller qualification plan",
                "disposition_id_if_outside": "engineering-review",
                "evidence": (EVIDENCE,),
            },
        ),
        "weld_procedure_and_lot_identity_reviewed": True,
        "specimen_source_mapping_reviewed": True,
        "test_method_and_location_reviewed": True,
        "metric_definitions_and_units_reviewed": True,
        "uncertainty_records_reviewed": True,
        "provider_identity_and_state_reviewed": True,
        "result_digests_reviewed": True,
        "missingness_reviewed": True,
        "caller_requirement_authority_reviewed": True,
        "evidence": (EVIDENCE,),
    }
    value.update(updates)
    return ProductionWeldTestEvidenceAssessment(**value)


def test_reviewed_test_record_is_compared_with_caller_requirement():
    result = production_weld_test_evidence(payload())
    assert result.status == "computed"
    row = result.values["caller_requirement_comparisons"][0]
    assert row["nominal_value_within_caller_requirement"] is True
    assert row["uncertainty_interval_minimum"] == pytest.approx(315e6)


def test_outside_result_is_reported_without_acceptance_inference():
    base = payload()
    observation = base.observations[0].model_copy(update={"observed_value": 290e6})
    result = production_weld_test_evidence(base.model_copy(update={"observations": (observation,)}))
    assert result.status == "computed"
    assert (
        result.values["caller_requirement_comparisons"][0]["nominal_value_within_caller_requirement"] is False
    )


def test_missing_record_or_review_needs_data():
    base = payload()
    unavailable = base.observations[0].model_copy(
        update={
            "observed_value": None,
            "expanded_uncertainty": None,
            "coverage_factor": None,
            "uncertainty_basis": None,
            "result_digest": None,
            "record_available": False,
            "missing_basis": "laboratory result not supplied",
        }
    )
    assert production_weld_test_evidence(base.model_copy(update={"observations": (unavailable,)})).status == (
        "needs_data"
    )
    assert production_weld_test_evidence(payload(missingness_reviewed=False)).status == "needs_data"


def test_context_identity_is_enforced():
    registry = ModelRegistry()
    registry.register(specifications()[0])
    with pytest.raises(ValueError, match="must match"):
        registry.run(
            "welding.production_weld_test_evidence",
            payload(),
            RunContext(asset_id="other", location_id="joint-1", time_basis="authored"),
        )
