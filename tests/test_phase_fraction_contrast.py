import pytest

from matintegrity.contracts import RunContext
from matintegrity.models.phase_fraction_contrast import (
    PhaseFractionContrastAssessment,
    phase_fraction_linear_contrast,
    specifications,
)
from matintegrity.registry import ModelRegistry

EVIDENCE = {"source_id": "authored", "origin": "synthetic", "citation": "authored contrast fixture"}


def payload(**updates):
    value = {
        "assessment_id": "phase-contrast-1",
        "asset_id": "asset-1",
        "location_id": "weld-1",
        "material_condition_id": "condition-1",
        "processing_history_id": "history-1",
        "observations": (
            {
                "observation_id": "o-a",
                "sample_id": "sample-1",
                "region_id": "weld-metal",
                "phase_id": "phase-a",
                "measured_fraction": 0.55,
                "expanded_uncertainty_fraction": 0.03,
                "method_id": "method-1",
                "evidence": (EVIDENCE,),
            },
            {
                "observation_id": "o-b",
                "sample_id": "sample-1",
                "region_id": "weld-metal",
                "phase_id": "phase-b",
                "measured_fraction": 0.45,
                "expanded_uncertainty_fraction": 0.03,
                "method_id": "method-1",
                "evidence": (EVIDENCE,),
            },
        ),
        "requirements": (
            {
                "contrast_id": "phase-a-only",
                "terms": ({"phase_id": "phase-a", "coefficient": 1.0},),
                "minimum_value_fraction": 0.50,
                "maximum_value_fraction": 0.60,
                "requirement_basis": "caller-owned envelope",
                "evidence": (EVIDENCE,),
            },
            {
                "contrast_id": "phase-total",
                "terms": (
                    {"phase_id": "phase-a", "coefficient": 1.0},
                    {"phase_id": "phase-b", "coefficient": 1.0},
                ),
                "minimum_value_fraction": 0.95,
                "maximum_value_fraction": 1.05,
                "requirement_basis": "caller-owned sum envelope",
                "evidence": (EVIDENCE,),
            },
        ),
        "covariance": {
            "observation_ids": ("o-a", "o-b"),
            "expanded_covariance_matrix_fraction2": ((0.0009, -0.0003), (-0.0003, 0.0009)),
            "expansion_factor": 2.0,
            "covariance_basis": "authored synthetic covariance",
            "evidence": (EVIDENCE,),
        },
        "sample_region_mapping_reviewed": True,
        "material_processing_identity_reviewed": True,
        "method_applicability_reviewed": True,
        "covariance_basis_reviewed": True,
        "phase_identity_reviewed": True,
        "requirement_authority_reviewed": True,
    }
    value.update(updates)
    return PhaseFractionContrastAssessment(**value)


def test_contrasts_include_covariance_and_user_phase_group_sum():
    result = phase_fraction_linear_contrast(payload())
    rows = {row["contrast_id"]: row for row in result.values["contrast_rows"]}
    assert result.status == "computed"
    assert rows["phase-a-only"]["nominal_value_fraction"] == pytest.approx(0.55)
    assert rows["phase-a-only"]["expanded_uncertainty_fraction"] == pytest.approx(0.03)
    assert rows["phase-total"]["nominal_value_fraction"] == pytest.approx(1.0)
    assert rows["phase-total"]["expanded_uncertainty_fraction"] == pytest.approx((0.0012) ** 0.5)
    assert result.values["all_contrasts_within_declared_ranges"] is True


def test_missing_covariance_returns_needs_data_without_independence_assumption():
    result = phase_fraction_linear_contrast(payload(covariance=None))
    assert result.status == "needs_data"
    assert result.values["all_contrasts_within_declared_ranges"] is None
    assert "expanded_covariance_matrix" in result.values["missing_reviews"]


def test_non_psd_covariance_is_rejected():
    invalid = payload().model_dump()
    invalid["covariance"]["expanded_covariance_matrix_fraction2"] = (
        (0.0009, 0.0012),
        (0.0012, 0.0009),
    )
    with pytest.raises(ValueError, match="positive semidefinite"):
        PhaseFractionContrastAssessment(**invalid)


def test_covariance_diagonal_must_match_observation_uncertainty():
    invalid = payload().model_dump()
    invalid["covariance"]["expanded_covariance_matrix_fraction2"] = (
        (0.0004, 0.0),
        (0.0, 0.0009),
    )
    with pytest.raises(ValueError, match="diagonal"):
        PhaseFractionContrastAssessment(**invalid)


def test_context_identity_is_enforced():
    registry = ModelRegistry()
    registry.register(specifications()[0])
    with pytest.raises(ValueError, match="must match"):
        registry.run(
            "materials.phase_fraction_linear_contrast",
            payload(),
            RunContext(asset_id="other", location_id="weld-1", time_basis="authored"),
        )
