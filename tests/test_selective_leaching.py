import pytest

from matintegrity.contracts import RunContext
from matintegrity.models.selective_leaching import (
    SelectiveLeachingApplicability,
    selective_leaching_applicability,
    specifications,
)
from matintegrity.registry import ModelRegistry

EVIDENCE = {
    "source_id": "authored-selective-leaching-record",
    "origin": "synthetic",
    "citation": "authored selective-leaching applicability test record",
}


def inputs(**updates):
    payload = {
        "assessment_id": "selective-leaching-001",
        "asset_id": "valve-001",
        "location_id": "body-a",
        "clock_id": "exposure-clock",
        "alloy_id": "alloy-a",
        "composition_condition_id": "composition-a",
        "phase_condition_id": "phase-a",
        "qualification_tests": [
            {
                "test_id": "test-1",
                "physical_specimen_id": "specimen-1",
                "test_method_id": "caller-test-method",
                "reported_endpoint": "caller-reported completed exposure",
                "record_valid": True,
                "evidence": [EVIDENCE],
            }
        ],
        "qualification_envelopes": [
            {
                "envelope_id": "envelope-1",
                "alloy_ids": ["alloy-a"],
                "composition_condition_ids": ["composition-a"],
                "phase_condition_ids": ["phase-a"],
                "environment_id": "water-a",
                "minimum_temperature_K": 280.0,
                "maximum_temperature_K": 350.0,
                "minimum_pH": 5.0,
                "maximum_pH": 9.0,
                "redox_or_potential_descriptor_id": "controlled-potential",
                "potential_basis": "reference-a",
                "potential_unit": "V",
                "minimum_potential": -0.5,
                "maximum_potential": 0.1,
                "maximum_exposure_duration_s": 10000.0,
                "test_evidence_ids": ["test-1"],
                "applicability_basis": "caller qualification envelope",
                "evidence": [EVIDENCE],
            }
        ],
        "exposure_intervals": [
            {
                "interval_id": "interval-1",
                "envelope_id": "envelope-1",
                "start_time_s": 0.0,
                "end_time_s": 1000.0,
                "environment_id": "water-a",
                "temperature_K": 320.0,
                "pH": 7.0,
                "redox_or_potential_descriptor_id": "controlled-potential",
                "potential_basis": "reference-a",
                "potential_unit": "V",
                "potential_value": -0.2,
                "record_valid": True,
                "evidence": [EVIDENCE],
            }
        ],
        "observations": [
            {
                "observation_id": "obs-1",
                "physical_region_id": "surface-a",
                "observation_kind": "microscopy",
                "method_id": "method-a",
                "metric_definition": "caller-defined affected dimension",
                "reported_value": 0.009,
                "expanded_uncertainty": 0.002,
                "unit": "m",
                "caller_range_id": "range-1",
                "reported_description": "caller-reported contrast region",
                "record_valid": True,
                "evidence": [EVIDENCE],
            }
        ],
        "caller_observation_ranges": [
            {
                "range_id": "range-1",
                "observation_kind": "microscopy",
                "method_id": "method-a",
                "metric_definition": "caller-defined affected dimension",
                "unit": "m",
                "maximum_value": 0.01,
                "range_basis": "caller observation review plan",
                "caller_disposition_id_if_outside": "engineering-review",
            }
        ],
        "alloy_composition_and_phase_reviewed": True,
        "environment_temperature_and_pH_reviewed": True,
        "redox_or_potential_basis_reviewed": True,
        "exposure_clock_reviewed": True,
        "microscopy_and_composition_observations_reviewed": True,
        "measurement_units_and_uncertainty_reviewed": True,
        "qualification_tests_envelopes_and_ranges_reviewed": True,
        "evidence": [EVIDENCE],
    }
    payload.update(updates)
    return payload


def test_inside_support_preserves_observation_uncertainty_without_strength_inference():
    result = selective_leaching_applicability(SelectiveLeachingApplicability.model_validate(inputs()))
    assert result.status == "computed"
    assert (
        result.values["qualification_support_comparisons"][0]["inside_declared_qualification_support"] is True
    )
    comparison = result.values["caller_observation_range_comparisons"][0]
    assert comparison["nominal_above_declared_maximum"] is False
    assert comparison["uncertainty_interval_extends_above_declared_maximum"] is True
    assert comparison["caller_disposition_id_if_outside"] == "engineering-review"


def test_valid_environment_outside_support_is_out_of_scope():
    intervals = list(inputs()["exposure_intervals"])
    intervals[0] = {**intervals[0], "environment_id": "different-water"}
    result = selective_leaching_applicability(
        SelectiveLeachingApplicability.model_validate(inputs(exposure_intervals=intervals))
    )
    assert result.status == "out_of_scope"
    assert result.values["outside_qualification_support_interval_ids"] == ["interval-1"]
    assert result.values["qualification_support_comparisons"][0]["outside_support_reasons"] == ["environment"]


def test_potential_basis_and_observation_unit_mismatch_need_data():
    intervals = list(inputs()["exposure_intervals"])
    intervals[0] = {**intervals[0], "potential_basis": "reference-b"}
    basis = selective_leaching_applicability(
        SelectiveLeachingApplicability.model_validate(inputs(exposure_intervals=intervals))
    )
    assert basis.status == "needs_data"
    assert basis.values["potential_basis_mismatch_interval_ids"] == ["interval-1"]

    observations = list(inputs()["observations"])
    observations[0] = {**observations[0], "unit": "mm"}
    unit = selective_leaching_applicability(
        SelectiveLeachingApplicability.model_validate(inputs(observations=observations))
    )
    assert unit.status == "needs_data"
    assert unit.values["observation_unit_mismatch_ids"] == ["obs-1"]


def test_invalid_observation_and_missing_review_take_needs_data_precedence():
    observations = list(inputs()["observations"])
    observations[0] = {
        **observations[0],
        "record_valid": False,
        "invalid_basis": "image calibration unavailable",
    }
    intervals = list(inputs()["exposure_intervals"])
    intervals[0] = {**intervals[0], "temperature_K": 400.0}
    result = selective_leaching_applicability(
        SelectiveLeachingApplicability.model_validate(
            inputs(
                observations=observations,
                exposure_intervals=intervals,
                measurement_units_and_uncertainty_reviewed=False,
            )
        )
    )
    assert result.status == "needs_data"
    assert result.values["invalid_observation_ids"] == ["obs-1"]
    assert result.values["missing_reviews"] == ["measurement_units_and_uncertainty_reviewed"]


def test_model_spec_enforces_context_identity():
    registry = ModelRegistry()
    registry.register(specifications()[0])
    request = SelectiveLeachingApplicability.model_validate(inputs())
    result = registry.run(
        "degradation.selective_leaching_applicability",
        request,
        RunContext(asset_id="valve-001", location_id="body-a", time_basis="exposure clock"),
    )
    assert result.status == "computed"
    with pytest.raises(ValueError, match="must match"):
        registry.run(
            "degradation.selective_leaching_applicability",
            request,
            RunContext(asset_id="other", location_id="body-a", time_basis="clock"),
        )
