import pytest

from matintegrity.contracts import RunContext
from matintegrity.models.nitriding_degradation import (
    NitridingApplicability,
    nitriding_applicability,
    specifications,
)
from matintegrity.registry import ModelRegistry

EVIDENCE = {
    "source_id": "authored-nitriding-record",
    "origin": "synthetic",
    "citation": "authored nitriding applicability test record",
}


def inputs(**updates):
    payload = {
        "assessment_id": "nitriding-001",
        "asset_id": "heater-001",
        "location_id": "tube-a",
        "clock_id": "exposure-clock",
        "material_id": "alloy-a",
        "material_condition_id": "condition-a",
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
                "material_ids": ["alloy-a"],
                "material_condition_ids": ["condition-a"],
                "nitrogen_species_id": "species-a",
                "nitrogen_driving_force_basis": "caller activity definition",
                "nitrogen_driving_force_unit": "1",
                "minimum_nitrogen_driving_force": 0.1,
                "maximum_nitrogen_driving_force": 0.8,
                "minimum_temperature_K": 600.0,
                "maximum_temperature_K": 900.0,
                "minimum_pressure_Pa_abs": 90000.0,
                "maximum_pressure_Pa_abs": 200000.0,
                "gas_environment_descriptor_id": "gas-mixture-a",
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
                "nitrogen_species_id": "species-a",
                "nitrogen_driving_force_basis": "caller activity definition",
                "nitrogen_driving_force_unit": "1",
                "nitrogen_driving_force": 0.5,
                "temperature_K": 750.0,
                "pressure_Pa_abs": 101325.0,
                "gas_environment_descriptor_id": "gas-mixture-a",
                "record_valid": True,
                "evidence": [EVIDENCE],
            }
        ],
        "material_and_condition_reviewed": True,
        "nitrogen_species_basis_and_unit_reviewed": True,
        "temperature_history_reviewed": True,
        "absolute_pressure_reviewed": True,
        "gas_environment_descriptor_reviewed": True,
        "exposure_clock_reviewed": True,
        "qualification_tests_and_envelopes_reviewed": True,
        "evidence": [EVIDENCE],
    }
    payload.update(updates)
    return payload


def test_inside_caller_support_is_computed_without_nitrogen_profile_prediction():
    result = nitriding_applicability(NitridingApplicability.model_validate(inputs()))
    assert result.status == "computed"
    comparison = result.values["qualification_support_comparisons"][0]
    assert comparison["inside_declared_qualification_support"] is True
    assert comparison["outside_support_reasons"] == []
    assert comparison["test_evidence_ids"] == ["test-1"]


def test_valid_pressure_outside_support_is_out_of_scope():
    intervals = list(inputs()["exposure_intervals"])
    intervals[0] = {**intervals[0], "pressure_Pa_abs": 300000.0}
    result = nitriding_applicability(
        NitridingApplicability.model_validate(inputs(exposure_intervals=intervals))
    )
    assert result.status == "out_of_scope"
    assert result.values["outside_qualification_support_interval_ids"] == ["interval-1"]
    assert result.values["qualification_support_comparisons"][0]["outside_support_reasons"] == [
        "absolute_pressure"
    ]


def test_unmatched_envelope_and_exact_basis_or_unit_conflicts_need_data():
    intervals = list(inputs()["exposure_intervals"])
    intervals[0] = {**intervals[0], "envelope_id": "not-declared"}
    unmatched = nitriding_applicability(
        NitridingApplicability.model_validate(inputs(exposure_intervals=intervals))
    )
    assert unmatched.status == "needs_data"
    assert unmatched.values["unmatched_envelope_interval_ids"] == ["interval-1"]

    intervals[0] = {
        **inputs()["exposure_intervals"][0],
        "nitrogen_driving_force_basis": "partial pressure",
    }
    basis = nitriding_applicability(
        NitridingApplicability.model_validate(inputs(exposure_intervals=intervals))
    )
    assert basis.status == "needs_data"
    assert basis.values["nitrogen_driving_force_basis_mismatch_interval_ids"] == ["interval-1"]

    intervals[0] = {**inputs()["exposure_intervals"][0], "nitrogen_driving_force_unit": "Pa"}
    unit = nitriding_applicability(
        NitridingApplicability.model_validate(inputs(exposure_intervals=intervals))
    )
    assert unit.status == "needs_data"
    assert unit.values["nitrogen_driving_force_unit_mismatch_interval_ids"] == ["interval-1"]


def test_invalid_test_and_missing_review_take_needs_data_precedence():
    tests = list(inputs()["qualification_tests"])
    tests[0] = {
        **tests[0],
        "record_valid": False,
        "invalid_basis": "specimen traceability unresolved",
    }
    intervals = list(inputs()["exposure_intervals"])
    intervals[0] = {**intervals[0], "temperature_K": 1000.0}
    result = nitriding_applicability(
        NitridingApplicability.model_validate(
            inputs(
                qualification_tests=tests,
                exposure_intervals=intervals,
                temperature_history_reviewed=False,
            )
        )
    )
    assert result.status == "needs_data"
    assert result.values["invalid_qualification_test_ids"] == ["test-1"]
    assert result.values["missing_reviews"] == ["temperature_history_reviewed"]


def test_model_spec_enforces_context_identity():
    registry = ModelRegistry()
    registry.register(specifications()[0])
    request = NitridingApplicability.model_validate(inputs())
    result = registry.run(
        "degradation.nitriding_applicability",
        request,
        RunContext(asset_id="heater-001", location_id="tube-a", time_basis="exposure clock"),
    )
    assert result.status == "computed"
    with pytest.raises(ValueError, match="must match"):
        registry.run(
            "degradation.nitriding_applicability",
            request,
            RunContext(asset_id="other", location_id="tube-a", time_basis="clock"),
        )
