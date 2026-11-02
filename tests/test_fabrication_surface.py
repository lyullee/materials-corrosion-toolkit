import pytest

from matintegrity.contracts import Evidence
from matintegrity.models.fabrication_surface import (
    CleanlinessObservation,
    DeclaredCleanlinessRequirement,
    PreparedSurfaceArea,
    SurfaceCleanlinessAssessment,
    surface_cleanliness_assessment,
)

EVIDENCE = Evidence(source_id="authored", origin="synthetic", citation="authored unit test")


def request(**updates):
    payload = {
        "assessment_id": "clean-1",
        "procedure_id": "procedure-1",
        "procedure_revision": "A",
        "areas": [
            PreparedSurfaceArea(
                area_id="A",
                physical_location_id="vessel-shell",
                material_condition_id="steel-prepared",
                preparation_process_id="blast-1",
                target_area_m2=10.0,
                inspected_area_m2=10.0,
                evidence=[EVIDENCE],
            )
        ],
        "observations": [
            CleanlinessObservation(
                observation_id="o1",
                area_id="A",
                metric_id="surface-salt",
                method_id="user-method",
                value=18.0,
                expanded_uncertainty=2.0,
                unit_token="mg/m^2",
                sample_location_description="upper shell",
                evidence=[EVIDENCE],
            )
        ],
        "declared_requirements": [
            DeclaredCleanlinessRequirement(
                requirement_id="r1",
                area_id="A",
                metric_id="surface-salt",
                comparator="maximum",
                limit_value=20.0,
                unit_token="mg/m^2",
                requirement_basis="caller-owned coating specification",
                evidence=[EVIDENCE],
            )
        ],
        "areas_mutually_exclusive_reviewed": True,
        "preparation_identity_reviewed": True,
        "method_applicability_reviewed": True,
        "calibration_and_uncertainty_reviewed": True,
        "observation_mapping_reviewed": True,
        "requirement_authority_reviewed": True,
        "evidence": [EVIDENCE],
    }
    payload.update(updates)
    return SurfaceCleanlinessAssessment(**payload)


def test_conservative_declared_limit_comparison():
    result = surface_cleanliness_assessment(request())
    row = result.values["requirement_rows"][0]
    assert result.status == "computed"
    assert row["governing_conservative_value"] == pytest.approx(20.0)
    assert row["declared_requirement_satisfied"] is True
    assert result.values["all_declared_requirements_satisfied"] is True


def test_missing_observation_or_review_needs_data():
    missing = surface_cleanliness_assessment(request(observations=[], negative_result_reviewed=True))
    assert missing.status == "needs_data"
    assert missing.values["all_declared_requirements_satisfied"] is None
    unreviewed = surface_cleanliness_assessment(request(requirement_authority_reviewed=False))
    assert unreviewed.status == "needs_data"


def test_units_and_area_references_are_not_repaired():
    observation = request().observations[0].model_copy(update={"unit_token": "ug/cm^2"})
    with pytest.raises(ValueError, match="units must match"):
        request(observations=[observation])
    observation = request().observations[0].model_copy(update={"area_id": "unknown"})
    with pytest.raises(ValueError, match="declared area"):
        request(observations=[observation])
