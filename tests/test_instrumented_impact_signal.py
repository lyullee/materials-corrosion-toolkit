import pytest

from matintegrity.contracts import RunContext
from matintegrity.models.instrumented_impact_signal import (
    InstrumentedImpactSignalAssessment,
    instrumented_impact_signal_summary,
    specifications,
)
from matintegrity.registry import ModelRegistry

EVIDENCE = {"source_id": "authored", "origin": "synthetic", "citation": "authored test"}
DIGEST_A = "a" * 64
DIGEST_B = "b" * 64
DIGEST_C = "c" * 64
DIGEST_D = "d" * 64


def signal_point(identifier, time, displacement, force, **updates):
    value = {
        "sample_id": identifier,
        "elapsed_time_s": time,
        "displacement_m": displacement,
        "signed_force_N": force,
        "expanded_force_uncertainty_N": 10.0,
        "expanded_displacement_uncertainty_m": 1e-6,
        "record_valid": True,
        "evidence": (EVIDENCE,),
    }
    value.update(updates)
    return value


def positive_signal():
    return (
        signal_point("p0", 0.0, 0.0, 0.0),
        signal_point("p1", 0.001, 0.001, 1000.0),
        signal_point("p2", 0.002, 0.002, 1000.0),
        signal_point("p3", 0.003, 0.003, 500.0),
        signal_point("p4", 0.004, 0.004, 0.0),
    )


def machine_energy(**updates):
    value = {
        "comparison_record_id": "machine-energy-1",
        "reported_energy_J": 2.6,
        "expanded_uncertainty_J": 0.1,
        "uncertainty_coverage_factor": 2.0,
        "reporting_method_id": "machine-channel-1",
        "independent_data_path_declared": True,
        "provider_id": "machine-provider",
        "provider_revision": "1",
        "configuration_digest": DIGEST_C,
        "result_digest": DIGEST_D,
        "record_valid": True,
        "evidence": (EVIDENCE,),
    }
    value.update(updates)
    return value


def payload(**updates):
    value = {
        "assessment_id": "assessment-1",
        "asset_id": "asset-1",
        "location_id": "impact-machine-1",
        "impact_test_id": "impact-test-1",
        "physical_specimen_id": "specimen-1",
        "source_group_id": "source-1",
        "independence_group_id": "independence-1",
        "material_condition_id": "condition-1",
        "specimen_geometry_id": "geometry-1",
        "notch_geometry_id": "notch-1",
        "notch_orientation_id": "notch-orientation-1",
        "specimen_orientation_id": "specimen-orientation-1",
        "test_temperature_K": 250.0,
        "signal_source_digest": DIGEST_A,
        "force_unit_token": "N",
        "displacement_unit_token": "m",
        "time_unit_token": "s",
        "calibration": {
            "calibration_record_id": "calibration-1",
            "striker_id": "striker-1",
            "striker_configuration_id": "striker-configuration-1",
            "force_instrument_id": "force-instrument-1",
            "displacement_instrument_id": "displacement-instrument-1",
            "timebase_id": "timebase-1",
            "force_calibration_id": "force-calibration-1",
            "displacement_calibration_id": "displacement-calibration-1",
            "force_calibration_digest": DIGEST_A,
            "displacement_calibration_digest": DIGEST_B,
            "timebase_calibration_digest": DIGEST_C,
            "instrument_configuration_digest": DIGEST_D,
            "provider_id": "calibration-provider",
            "provider_revision": "1",
            "calibration_result_digest": DIGEST_A,
            "record_valid": True,
            "evidence": (EVIDENCE,),
        },
        "signal_points": positive_signal(),
        "valid_window_start_sample_id": "p0",
        "valid_window_end_sample_id": "p4",
        "absorbed_energy_force_direction_multiplier": 1,
        "force_sign_convention": "positive force performs positive work along increasing displacement",
        "peak_force_plateau_tolerance_N": 0.0,
        "negative_absorbed_energy_tolerance_J": 1e-12,
        "machine_reported_energy": machine_energy(),
        "specimen_notch_orientation_and_material_reviewed": True,
        "test_temperature_striker_and_instrument_identity_reviewed": True,
        "calibration_and_si_units_reviewed": True,
        "source_digest_and_raw_signal_reviewed": True,
        "monotonic_displacement_and_time_order_reviewed": True,
        "valid_window_and_force_sign_reviewed": True,
        "trapezoidal_integration_and_peak_definition_reviewed": True,
        "machine_energy_comparison_independence_reviewed": True,
    }
    value.update(updates)
    return InstrumentedImpactSignalAssessment(**value)


def test_trapezoidal_energy_peak_plateau_and_machine_comparison():
    result = instrumented_impact_signal_summary(payload())
    assert result.status == "computed"
    assert result.values["absorbed_energy_J"] == pytest.approx(2.5)
    assert result.values["peak_directed_force_N"] == pytest.approx(1000.0)
    assert result.values["peak_plateau_sample_ids"] == ["p1", "p2"]
    assert result.values["peak_first_displacement_m"] == pytest.approx(0.001)
    assert result.values["peak_last_displacement_m"] == pytest.approx(0.002)
    assert result.values["machine_energy_comparison"]["signed_difference_J"] == pytest.approx(-0.1)


def test_signed_force_direction_is_explicit_not_absolute_value():
    negative = tuple(
        signal_point(
            row["sample_id"],
            row["elapsed_time_s"],
            row["displacement_m"],
            -row["signed_force_N"],
        )
        for row in positive_signal()
    )
    result = instrumented_impact_signal_summary(
        payload(signal_points=negative, absorbed_energy_force_direction_multiplier=-1)
    )
    assert result.status == "computed"
    assert result.values["absorbed_energy_J"] == pytest.approx(2.5)

    wrong_sign = instrumented_impact_signal_summary(payload(signal_points=negative))
    assert wrong_sign.status == "needs_data"
    assert wrong_sign.values["absorbed_energy_J"] == pytest.approx(-2.5)


def test_invalid_window_record_review_or_comparison_independence_needs_data():
    signal = list(positive_signal())
    signal[2] = signal_point(
        "p2",
        0.002,
        0.002,
        1000.0,
        record_valid=False,
        invalid_or_missing_basis="signal sample invalid",
    )
    result = instrumented_impact_signal_summary(payload(signal_points=tuple(signal)))
    assert result.status == "needs_data"
    assert result.values["invalid_window_sample_ids"] == ["p2"]

    assert (
        instrumented_impact_signal_summary(payload(valid_window_and_force_sign_reviewed=False)).status
        == "needs_data"
    )
    assert (
        instrumented_impact_signal_summary(
            payload(machine_reported_energy=machine_energy(independent_data_path_declared=False))
        ).status
        == "needs_data"
    )


def test_signal_order_and_window_contracts_are_strict():
    signal = list(positive_signal())
    signal[3] = signal_point("p3", 0.003, 0.0015, 500.0)
    with pytest.raises(ValueError, match="monotonic nondecreasing"):
        payload(signal_points=tuple(signal))

    with pytest.raises(ValueError, match="at least two ordered samples"):
        payload(valid_window_start_sample_id="p3", valid_window_end_sample_id="p2")


def test_context_identity_is_enforced():
    registry = ModelRegistry()
    registry.register(specifications()[0])
    with pytest.raises(ValueError, match="must match"):
        registry.run(
            "inspection.instrumented_impact_signal_summary",
            payload(),
            RunContext(asset_id="other", location_id="impact-machine-1", time_basis="authored"),
        )
