import math

import pytest

from matintegrity.contracts import RunContext
from matintegrity.models.reference_leak_calibration import (
    ReferenceLeakResponseCalibration,
    reference_leak_response_calibration,
    specifications,
)
from matintegrity.registry import ModelRegistry

EVIDENCE = {"source_id": "authored", "origin": "synthetic", "citation": "authored test"}
DIGEST_A = "a" * 64
DIGEST_B = "b" * 64
DIGEST_C = "c" * 64
DIGEST_D = "d" * 64


def detected(identifier, partition, leak_rate, response, **updates):
    value = {
        "observation_id": identifier,
        "partition": partition,
        "physical_specimen_id": f"specimen-{identifier}",
        "reference_leak_id": f"reference-{identifier}",
        "source_group_id": f"source-{identifier}",
        "independence_group_id": f"independence-{identifier}",
        "instrument_id": "instrument-1",
        "instrument_configuration_id": "configuration-1",
        "test_gas_id": "gas-1",
        "boundary_condition_id": "boundary-1",
        "observation_clock_id": "clock-1",
        "reference_time_s": 10.0,
        "response_time_s": 10.0,
        "reporting_status": "detected",
        "reference_leak_rate_mol_s": leak_rate,
        "expanded_reference_leak_uncertainty_mol_s": leak_rate * 0.01,
        "response_value": response,
        "response_unit_token": "custom-response-unit",
        "expanded_response_uncertainty": response * 0.02,
        "sample_weight": 1.0,
        "reference_provider_id": "reference-provider",
        "reference_provider_revision": "1",
        "reference_provider_state_digest": DIGEST_A,
        "instrument_provider_id": "instrument-provider",
        "instrument_provider_revision": "1",
        "instrument_configuration_digest": DIGEST_B,
        "result_digest": DIGEST_C,
        "record_digest": DIGEST_D,
        "record_valid": True,
        "evidence": (EVIDENCE,),
    }
    value.update(updates)
    return value


def default_observations():
    return (
        detected("calibration-a", "calibration", 1.0, 2.0),
        detected("calibration-b", "calibration", 4.0, 4.0),
        detected("calibration-c", "calibration", 16.0, 8.0),
        detected("holdout-d", "holdout", 9.0, 6.0),
    )


def payload(observations=None, **updates):
    value = {
        "calibration_id": "leak-calibration-1",
        "asset_id": "asset-1",
        "location_id": "instrument-location-1",
        "physical_scope_id": "scope-1",
        "observation_clock_id": "clock-1",
        "time_basis": "reference-clock",
        "instrument_id": "instrument-1",
        "instrument_configuration_id": "configuration-1",
        "test_gas_id": "gas-1",
        "boundary_condition_id": "boundary-1",
        "leak_quantity_definition": "molar_flow_rate",
        "leak_rate_unit_token": "mol/s",
        "pressure_basis": "caller absolute upstream and downstream pressure basis",
        "reference_temperature_basis": "caller traceable reference temperature basis",
        "response_definition": "caller instrument response amplitude",
        "response_unit_token": "custom-response-unit",
        "log_reference_leak_rate_mol_s": 1.0,
        "log_reference_response_value": 1.0,
        "maximum_clock_alignment_error_s": 0.1,
        "observations": observations or default_observations(),
        "minimum_calibration_detected_count": 3,
        "minimum_holdout_detected_count": 1,
        "minimum_calibration_source_group_count": 3,
        "minimum_holdout_source_group_count": 1,
        "minimum_holdout_independence_group_count": 1,
        "instrument_configuration_gas_and_boundary_reviewed": True,
        "clock_alignment_and_physical_scope_reviewed": True,
        "si_leak_quantity_pressure_and_temperature_basis_reviewed": True,
        "reference_traceability_and_uncertainty_reviewed": True,
        "response_definition_units_and_uncertainty_reviewed": True,
        "partition_and_group_independence_reviewed": True,
        "censored_missing_and_invalid_status_reviewed": True,
        "provider_and_result_digests_reviewed": True,
    }
    value.update(updates)
    return ReferenceLeakResponseCalibration(**value)


def test_log_response_fit_and_holdout_metrics_are_computed():
    result = reference_leak_response_calibration(payload())
    assert result.status == "computed"
    assert result.values["log_response_log_leak_slope"] == pytest.approx(0.5)
    assert result.values["log_response_intercept"] == pytest.approx(math.log(2.0))
    assert result.values["holdout_log_response_bias"] == pytest.approx(0.0, abs=1e-12)
    assert result.values["holdout_log_response_rmse"] == pytest.approx(0.0, abs=1e-12)


def test_censored_and_missing_records_are_preserved_not_substituted():
    censored = detected("censored-e", "calibration", 2.0, 3.0)
    censored.update(
        {
            "reporting_status": "censored",
            "response_value": None,
            "expanded_response_uncertainty": None,
            "response_detection_limit": 1.5,
            "exclusion_or_status_basis": "caller reported censored response",
        }
    )
    result = reference_leak_response_calibration(payload(observations=(*default_observations(), censored)))
    assert result.status == "computed"
    assert result.values["excluded_observations"] == [
        {
            "observation_id": "censored-e",
            "partition": "calibration",
            "reporting_status": "censored",
            "exclusion_basis": "caller reported censored response",
            "reference_leak_rate_mol_s": 2.0,
            "response_detection_limit": 1.5,
        }
    ]


def test_holdout_outside_calibration_support_is_not_extrapolated():
    observations = (*default_observations()[:3], detected("holdout-d", "holdout", 25.0, 10.0))
    result = reference_leak_response_calibration(payload(observations=observations))
    assert result.status == "out_of_scope"
    assert result.values["outside_calibration_support_holdout_ids"] == ["holdout-d"]
    assert "holdout_log_response_rmse" not in result.values


def test_identifiability_clock_alignment_and_review_gates_need_data():
    same_rate = (
        detected("calibration-a", "calibration", 1.0, 2.0),
        detected("calibration-b", "calibration", 1.0, 2.1),
        detected("calibration-c", "calibration", 1.0, 1.9),
        detected("holdout-d", "holdout", 1.0, 2.0),
    )
    result = reference_leak_response_calibration(payload(observations=same_rate))
    assert result.status == "needs_data"
    assert result.values["identifiable_log_leak_span"] is False

    misaligned = list(default_observations())
    misaligned[0] = detected("calibration-a", "calibration", 1.0, 2.0, response_time_s=11.0)
    assert reference_leak_response_calibration(payload(observations=tuple(misaligned))).status == "needs_data"
    assert (
        reference_leak_response_calibration(
            payload(reference_traceability_and_uncertainty_reviewed=False)
        ).status
        == "needs_data"
    )


def test_partition_leakage_and_context_identity_are_enforced():
    observations = list(default_observations())
    observations[-1] = detected(
        "holdout-d",
        "holdout",
        9.0,
        6.0,
        reference_leak_id="reference-calibration-a",
    )
    with pytest.raises(ValueError, match="cannot cross"):
        payload(observations=tuple(observations))

    registry = ModelRegistry()
    registry.register(specifications()[0])
    with pytest.raises(ValueError, match="must match"):
        registry.run(
            "inspection.reference_leak_response_calibration",
            payload(),
            RunContext(
                asset_id="other",
                location_id="instrument-location-1",
                time_basis="reference-clock",
            ),
        )
    with pytest.raises(ValueError, match="time basis"):
        registry.run(
            "inspection.reference_leak_response_calibration",
            payload(),
            RunContext(
                asset_id="asset-1",
                location_id="instrument-location-1",
                time_basis="other",
            ),
        )
