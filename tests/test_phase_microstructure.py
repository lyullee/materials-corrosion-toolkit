import pytest

from matintegrity.contracts import RunContext
from matintegrity.models.phase_microstructure import (
    PhaseMicrostructureAssessment,
    phase_microstructure_assessment,
    specifications,
)
from matintegrity.registry import ModelRegistry

EVIDENCE = {"source_id": "authored", "origin": "synthetic", "citation": "authored phase test"}


def payload(**updates):
    value = {
        "assessment_id": "phase-1",
        "asset_id": "asset-1",
        "location_id": "weld-1",
        "material_condition_id": "condition-1",
        "processing_history_id": "history-1",
        "observations": (
            {
                "observation_id": "o1",
                "sample_id": "s1",
                "region_id": "weld-metal",
                "phase_id": "phase-a",
                "measured_fraction": 0.55,
                "expanded_uncertainty_fraction": 0.03,
                "method_id": "method-1",
                "record_valid": True,
                "evidence": (EVIDENCE,),
            },
            {
                "observation_id": "o2",
                "sample_id": "s1",
                "region_id": "weld-metal",
                "phase_id": "phase-b",
                "measured_fraction": 0.45,
                "expanded_uncertainty_fraction": 0.03,
                "method_id": "method-1",
                "record_valid": True,
                "evidence": (EVIDENCE,),
            },
        ),
        "declared_ranges": (
            {
                "requirement_id": "r1",
                "region_id": "weld-metal",
                "phase_id": "phase-a",
                "minimum_fraction": 0.5,
                "maximum_fraction": 0.6,
                "requirement_basis": "caller range",
                "evidence": (EVIDENCE,),
            },
            {
                "requirement_id": "r2",
                "region_id": "weld-metal",
                "phase_id": "phase-b",
                "minimum_fraction": 0.4,
                "maximum_fraction": 0.5,
                "requirement_basis": "caller range",
                "evidence": (EVIDENCE,),
            },
        ),
        "sample_and_region_mapping_reviewed": True,
        "material_and_processing_identity_reviewed": True,
        "method_applicability_reviewed": True,
        "uncertainty_basis_reviewed": True,
        "phase_identity_reviewed": True,
        "requirement_authority_reviewed": True,
    }
    value.update(updates)
    return PhaseMicrostructureAssessment(**value)


def test_uncertainty_intervals_are_compared_with_caller_ranges():
    result = phase_microstructure_assessment(payload())
    assert result.status == "computed"
    assert result.values["all_observations_within_declared_ranges"] is True


def test_missing_review_or_invalid_observation_needs_data():
    assert phase_microstructure_assessment(payload(phase_identity_reviewed=False)).status == "needs_data"
    row = (
        payload()
        .observations[0]
        .model_copy(update={"record_valid": False, "invalid_basis": "image unavailable"})
    )
    result = phase_microstructure_assessment(payload(observations=(row, payload().observations[1])))
    assert result.status == "needs_data"


def test_nominal_fraction_sum_above_one_is_rejected():
    row = payload().observations[1].model_copy(update={"measured_fraction": 0.6})
    with pytest.raises(ValueError, match="cannot exceed one"):
        payload(observations=(payload().observations[0], row))


def test_context_identity_is_enforced():
    registry = ModelRegistry()
    registry.register(specifications()[0])
    with pytest.raises(ValueError, match="must match"):
        registry.run(
            "materials.phase_microstructure_assessment",
            payload(),
            RunContext(asset_id="other", location_id="weld-1", time_basis="authored"),
        )
