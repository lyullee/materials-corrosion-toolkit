import pytest

from matintegrity.contracts import RunContext
from matintegrity.models.cathodic_protection_survey import (
    CathodicProtectionFieldSurvey,
    cathodic_protection_field_survey,
    specifications,
)
from matintegrity.registry import ModelRegistry

EVIDENCE = {"source_id": "authored", "origin": "synthetic", "citation": "authored test"}
DIGEST_A = "a" * 64
DIGEST_B = "b" * 64


def potential(identifier, time_s, convention, value, ir_status, temperature=295.0):
    return {
        "observation_id": identifier,
        "structure_id": "structure-1",
        "zone_id": "zone-1",
        "measurement_location_id": f"location-{identifier}",
        "location_definition": "authored survey location",
        "elapsed_time_s": time_s,
        "potential_convention": convention,
        "reference_electrode_id": "reference-1",
        "calibration_id": "calibration-1",
        "potential_V": value,
        "expanded_uncertainty_V": 0.01,
        "ir_drop_handling_status": ir_status,
        "specimen_temperature_K": temperature,
        "electrolyte_id": "electrolyte-1",
        "environment_id": "environment-1",
        "record_status": "observed",
        "provider_id": "provider-1",
        "provider_revision": "1",
        "result_digest": DIGEST_B,
        "evidence": (EVIDENCE,),
    }


def current(identifier, time_s, kind, value):
    return {
        "observation_id": identifier,
        "structure_id": "structure-1",
        "zone_id": "zone-1",
        "source_kind": kind,
        "source_id": f"source-{kind}-1",
        "measurement_location_id": "current-location-1",
        "elapsed_time_s": time_s,
        "current_A": value,
        "expanded_uncertainty_A": 0.1,
        "current_sign_basis": "positive current delivered to structure",
        "specimen_temperature_K": 295.0,
        "electrolyte_id": "electrolyte-1",
        "environment_id": "environment-1",
        "record_status": "observed",
        "provider_id": "provider-1",
        "provider_revision": "1",
        "result_digest": DIGEST_B,
        "evidence": (EVIDENCE,),
    }


def payload(**updates):
    value = {
        "survey_id": "survey-1",
        "asset_id": "asset-1",
        "location_id": "survey-location-1",
        "physical_scope_id": "structure-zone-scope-1",
        "structure_id": "structure-1",
        "zone_id": "zone-1",
        "clock_id": "clock-1",
        "electrolyte_id": "electrolyte-1",
        "environment_id": "environment-1",
        "reference_calibrations": (
            {
                "calibration_id": "calibration-1",
                "reference_electrode_id": "reference-1",
                "reference_electrode_type_id": "reference-type-1",
                "minimum_supported_temperature_K": 285.0,
                "maximum_supported_temperature_K": 305.0,
                "reported_offset_V": 0.0,
                "expanded_uncertainty_V": 0.005,
                "provider_id": "calibration-provider",
                "provider_revision": "1",
                "configuration_digest": DIGEST_A,
                "result_digest": DIGEST_B,
                "record_valid": True,
                "evidence": (EVIDENCE,),
            },
        ),
        "potential_observations": (
            potential("p-1", 0.0, "native", -0.65, "not_applicable"),
            potential("p-2", 10.0, "on", -0.95, "not_corrected"),
            potential("p-3", 20.0, "instant_off", -0.90, "instant_off_used"),
            potential("p-4", 30.0, "instant_off", -0.88, "instant_off_used"),
        ),
        "current_observations": (
            current("c-1", 0.0, "rectifier", 10.0),
            current("c-2", 10.0, "rectifier", 12.0),
        ),
        "caller_thresholds": (
            {
                "threshold_id": "threshold-1",
                "potential_convention": "instant_off",
                "reference_electrode_id": "reference-1",
                "comparison_direction": "at_or_more_negative",
                "threshold_V": -0.85,
                "threshold_basis": "authored caller threshold",
                "evidence": (EVIDENCE,),
            },
        ),
        "structure_zone_reference_and_location_identity_reviewed": True,
        "reference_electrode_calibrations_reviewed": True,
        "potential_conventions_and_clock_reviewed": True,
        "rectifier_anode_current_and_sign_basis_reviewed": True,
        "ir_drop_handling_status_reviewed": True,
        "temperature_electrolyte_and_environment_reviewed": True,
        "uncertainty_provider_and_result_digests_reviewed": True,
        "missing_and_invalid_records_reviewed": True,
        "caller_threshold_authority_reviewed": True,
        "evidence": (EVIDENCE,),
    }
    value.update(updates)
    return CathodicProtectionFieldSurvey(**value)


def test_native_conventions_currents_and_threshold_margins_are_separate():
    result = cathodic_protection_field_survey(payload())
    assert result.status == "computed"
    summaries = {
        row["potential_convention"]: row for row in result.values["potential_summary_by_native_convention"]
    }
    assert summaries["instant_off"]["arithmetic_mean_potential_V"] == pytest.approx(-0.89)
    assert result.values["current_summary_by_source_kind"][0]["arithmetic_mean_current_A"] == pytest.approx(
        11.0
    )
    margins = result.values["potential_threshold_margins"]
    assert [row["signed_margin_toward_declared_direction_V"] for row in margins] == pytest.approx(
        [0.05, 0.03]
    )


def test_missing_record_or_review_needs_data():
    assert (
        cathodic_protection_field_survey(payload(ir_drop_handling_status_reviewed=False)).status
        == "needs_data"
    )
    rows = list(payload().potential_observations)
    missing = rows[0].model_copy(
        update={
            "potential_V": None,
            "expanded_uncertainty_V": None,
            "result_digest": None,
            "record_status": "missing",
            "missing_or_invalid_basis": "field record unavailable",
        }
    )
    result = cathodic_protection_field_survey(payload(potential_observations=(missing, *rows[1:])))
    assert result.status == "needs_data"
    assert result.values["missing_or_invalid_potential_ids"] == ["p-1"]


def test_reference_calibration_temperature_support_is_not_extrapolated():
    rows = list(payload().potential_observations)
    hot = rows[0].model_copy(update={"specimen_temperature_K": 320.0})
    result = cathodic_protection_field_survey(payload(potential_observations=(hot, *rows[1:])))
    assert result.status == "out_of_scope"
    assert result.values["outside_calibration_temperature_observation_ids"] == ["p-1"]


def test_context_identity_is_enforced():
    registry = ModelRegistry()
    registry.register(specifications()[0])
    with pytest.raises(ValueError, match="must match"):
        registry.run(
            "fabrication.cathodic_protection_field_survey",
            payload(),
            RunContext(asset_id="other", location_id="survey-location-1", time_basis="authored"),
        )
