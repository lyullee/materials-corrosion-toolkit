import pytest
from pydantic import ValidationError

from matintegrity.high_temperature_history import (
    HighTemperatureCallerProfile,
    HighTemperatureExposureInterval,
    HighTemperatureMeasurementCriterion,
    HighTemperatureMeasurementEvidence,
    assess_high_temperature_history,
    high_temperature_history_assessment,
)

E = {"source_id": "campaign", "origin": "measured", "citation": "caller high-temperature data"}
D = "f" * 64


def interval(activity=True):
    return HighTemperatureExposureInterval(
        interval_id="interval-1",
        start_time_s=0.0,
        end_time_s=100.0,
        record_status="reported",
        temperature_K=800.0,
        temperature_expanded_uncertainty_K=5.0,
        pressure_Pa_abs=100000.0,
        pressure_expanded_uncertainty_Pa=1000.0,
        gas_chemistry_descriptor_id="gas-1",
        gas_chemistry_record_digest=D,
        activity_status="reported" if activity else "not_applicable",
        activity_quantity_id="carbon_activity" if activity else None,
        activity_basis="caller basis" if activity else None,
        activity_value=0.5 if activity else None,
        activity_expanded_uncertainty=0.02 if activity else None,
        activity_unit_token="1" if activity else None,
        activity_record_digest=D if activity else None,
        interval_record_digest=D,
        evidence=(E,),
    )


def measurement(value=1.0, status="reported"):
    return HighTemperatureMeasurementEvidence(
        measurement_id="depth-1",
        measurement_kind="affected_depth",
        quantity_id="affected_depth",
        status=status,
        value=value if status == "reported" else None,
        expanded_uncertainty=0.1 if status == "reported" else None,
        unit_token="mm",
        measurement_time_s=100.0,
        physical_specimen_id="specimen-1",
        source_group_id="campaign-1",
        method_id="sectioning",
        measurement_record_digest=D,
        invalid_or_missing_basis=None if status == "reported" else "not measured",
        evidence=(E,),
    )


def profile(mechanism="carburization", maximum_depth=2.0, activity=True):
    return HighTemperatureCallerProfile(
        profile_id="profile-1",
        profile_revision="1",
        mechanism=mechanism,
        supported_material_ids=("material-1",),
        supported_material_condition_ids=("condition-1",),
        supported_gas_chemistry_descriptor_ids=("gas-1",),
        minimum_temperature_K=700.0,
        maximum_temperature_K=900.0,
        maximum_cumulative_exposure_s=1000.0,
        pressure_required=True,
        minimum_pressure_Pa_abs=90000.0,
        maximum_pressure_Pa_abs=110000.0,
        activity_required=activity,
        activity_quantity_id="carbon_activity" if activity else None,
        activity_basis="caller basis" if activity else None,
        activity_unit_token="1" if activity else None,
        minimum_activity=0.2 if activity else None,
        maximum_activity=0.8 if activity else None,
        measurement_criteria=(
            HighTemperatureMeasurementCriterion(
                criterion_id="depth-rule",
                measurement_kind="affected_depth",
                quantity_id="affected_depth",
                unit_token="mm",
                maximum_acceptable=maximum_depth,
                minimum_reported_measurements=1,
                criterion_basis="caller measured-depth rule",
                criterion_source_digest=D,
                evidence=(E,),
            ),
        ),
        profile_source_digest=D,
        evidence=(E,),
    )


def assessment(mechanism="carburization", **updates):
    uses_activity = mechanism in {"carburization", "nitriding"}
    value = {
        "assessment_id": "assessment-1",
        "mechanism": mechanism,
        "asset_id": "asset-1",
        "location_id": "location-1",
        "physical_scope_id": "scope-1",
        "clock_id": "clock-1",
        "material_id": "material-1",
        "material_condition_id": "condition-1",
        "material_state_digest": D,
        "exposure_intervals": (interval(uses_activity),),
        "measurements": (measurement(),),
        "caller_profile": profile(mechanism, activity=uses_activity),
        "exposure_clock_temperature_gas_and_activity_reviewed": True,
        "material_state_and_measurement_lineage_reviewed": True,
        "caller_profile_and_missing_evidence_policy_reviewed": True,
        "evidence": (E,),
    }
    value.update(updates)
    return high_temperature_history_assessment(**value)


@pytest.mark.parametrize(
    "mechanism",
    ["oxidation", "sulfidation", "carburization", "nitriding", "metallurgical_aging"],
)
def test_all_mechanisms_aggregate_without_rate_or_life_inference(mechanism):
    result = assess_high_temperature_history(assessment(mechanism))
    assert result.decision == "accept"
    assert result.rate_constant_inferred is False
    assert result.remaining_life_inferred is False
    assert result.failure_probability_inferred is False


def test_caller_measurement_rule_drives_reject_and_review():
    rejected = assess_high_temperature_history(assessment(caller_profile=profile(maximum_depth=0.5)))
    reviewed = assess_high_temperature_history(assessment(caller_profile=profile(maximum_depth=1.05)))
    assert (rejected.decision, reviewed.decision) == ("reject", "review")


def test_missing_measurement_is_insufficient_evidence():
    result = assess_high_temperature_history(assessment(measurements=(measurement(status="missing"),)))
    assert result.decision == "insufficient_evidence"
    assert any(row.outcome == "missing" for row in result.findings)


def test_input_and_report_tamper_are_rejected():
    item = assessment()
    changed = item.model_dump(mode="python")
    changed["material_id"] = "other"
    with pytest.raises(ValidationError, match="payload digest mismatch"):
        item.model_validate(changed)
    report = assess_high_temperature_history(item)
    changed_report = report.model_dump(mode="python")
    changed_report["decision"] = "review"
    with pytest.raises(ValidationError, match="report digest mismatch"):
        report.model_validate(changed_report)
