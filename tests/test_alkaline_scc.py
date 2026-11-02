import pytest

from matintegrity.contracts import RunContext
from matintegrity.models.alkaline_scc import (
    AlkalineSCCApplicability,
    alkaline_scc_applicability,
    specifications,
)
from matintegrity.registry import ModelRegistry

EVIDENCE = {
    "source_id": "authored-alkaline-scc-record",
    "origin": "synthetic",
    "citation": "authored alkaline-SCC applicability test record",
}


def inputs(**updates):
    payload = {
        "assessment_id": "alkaline-applicability-001",
        "asset_id": "vessel-001",
        "location_id": "weld-a",
        "clock_id": "exposure-clock",
        "material_condition_id": "material-a",
        "heat_treatment_condition_id": "heat-treatment-a",
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
                "material_condition_ids": ["material-a"],
                "heat_treatment_condition_ids": ["heat-treatment-a"],
                "alkaline_species_id": "species-a",
                "concentration_unit": "mol/m^3",
                "minimum_concentration": 10.0,
                "maximum_concentration": 100.0,
                "minimum_temperature_K": 280.0,
                "maximum_temperature_K": 350.0,
                "electrochemical_descriptor_id": "controlled-potential",
                "potential_reference_id": "reference-a",
                "minimum_potential_V": -0.5,
                "maximum_potential_V": -0.2,
                "applied_stress_definition": "caller local tensile stress",
                "minimum_applied_stress_Pa": 0.0,
                "maximum_applied_stress_Pa": 200e6,
                "residual_stress_definition": "caller residual tensile stress",
                "minimum_residual_stress_Pa": -50e6,
                "maximum_residual_stress_Pa": 250e6,
                "maximum_exposure_duration_s": 10000.0,
                "test_evidence_ids": ["test-1"],
                "applicability_basis": "caller-qualified evidence envelope",
                "evidence": [EVIDENCE],
            }
        ],
        "exposure_intervals": [
            {
                "interval_id": "interval-1",
                "envelope_id": "envelope-1",
                "start_time_s": 0.0,
                "end_time_s": 1000.0,
                "alkaline_species_id": "species-a",
                "concentration": 50.0,
                "concentration_unit": "mol/m^3",
                "temperature_K": 320.0,
                "electrochemical_descriptor_id": "controlled-potential",
                "potential_reference_id": "reference-a",
                "potential_V": -0.3,
                "applied_stress_definition": "caller local tensile stress",
                "applied_stress_Pa": 100e6,
                "residual_stress_definition": "caller residual tensile stress",
                "residual_stress_Pa": 50e6,
                "record_valid": True,
                "evidence": [EVIDENCE],
            }
        ],
        "material_and_heat_treatment_reviewed": True,
        "alkaline_chemistry_and_units_reviewed": True,
        "temperature_history_reviewed": True,
        "electrochemical_descriptor_reviewed": True,
        "applied_and_residual_stress_reviewed": True,
        "exposure_clock_reviewed": True,
        "qualification_tests_and_envelopes_reviewed": True,
        "evidence": [EVIDENCE],
    }
    payload.update(updates)
    return payload


def test_inside_caller_qualification_support_is_computed_without_scc_prediction():
    result = alkaline_scc_applicability(AlkalineSCCApplicability.model_validate(inputs()))
    assert result.status == "computed"
    comparison = result.values["qualification_support_comparisons"][0]
    assert comparison["inside_declared_qualification_support"] is True
    assert comparison["outside_support_reasons"] == []
    assert comparison["test_evidence_ids"] == ["test-1"]


def test_complete_record_outside_temperature_support_is_out_of_scope():
    intervals = list(inputs()["exposure_intervals"])
    intervals[0] = {**intervals[0], "temperature_K": 400.0}
    result = alkaline_scc_applicability(
        AlkalineSCCApplicability.model_validate(inputs(exposure_intervals=intervals))
    )
    assert result.status == "out_of_scope"
    assert result.values["outside_qualification_support_interval_ids"] == ["interval-1"]
    assert result.values["qualification_support_comparisons"][0]["outside_support_reasons"] == ["temperature"]


def test_unmatched_envelope_and_exact_concentration_unit_mismatch_need_data():
    intervals = list(inputs()["exposure_intervals"])
    intervals[0] = {**intervals[0], "envelope_id": "not-declared"}
    unmatched = alkaline_scc_applicability(
        AlkalineSCCApplicability.model_validate(inputs(exposure_intervals=intervals))
    )
    assert unmatched.status == "needs_data"
    assert unmatched.values["unmatched_envelope_interval_ids"] == ["interval-1"]

    intervals[0] = {**inputs()["exposure_intervals"][0], "concentration_unit": "mol/L"}
    unit = alkaline_scc_applicability(
        AlkalineSCCApplicability.model_validate(inputs(exposure_intervals=intervals))
    )
    assert unit.status == "needs_data"
    assert unit.values["concentration_unit_mismatch_interval_ids"] == ["interval-1"]


def test_invalid_test_evidence_and_missing_review_take_needs_data_precedence():
    tests = list(inputs()["qualification_tests"])
    tests[0] = {
        **tests[0],
        "record_valid": False,
        "invalid_basis": "specimen identity unresolved",
    }
    intervals = list(inputs()["exposure_intervals"])
    intervals[0] = {**intervals[0], "temperature_K": 400.0}
    result = alkaline_scc_applicability(
        AlkalineSCCApplicability.model_validate(
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
    request = AlkalineSCCApplicability.model_validate(inputs())
    result = registry.run(
        "degradation.alkaline_scc_applicability",
        request,
        RunContext(asset_id="vessel-001", location_id="weld-a", time_basis="exposure clock"),
    )
    assert result.status == "computed"
    with pytest.raises(ValueError, match="must match"):
        registry.run(
            "degradation.alkaline_scc_applicability",
            request,
            RunContext(asset_id="other", location_id="weld-a", time_basis="clock"),
        )
