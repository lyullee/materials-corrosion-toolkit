import pytest
from pydantic import ValidationError

from matintegrity.contracts import Evidence
from matintegrity.models.inspection import (
    PulseEchoCalibrationObservation,
    PulseEchoSoundSpeedFit,
    pulse_echo_sound_speed_fit,
)


def _input(*, holdout_thickness_m=0.009):
    speed = 5900.0
    offset = 40e-9

    def row(index, thickness, partition, group):
        return PulseEchoCalibrationObservation(
            observation_id=f"row-{index}",
            physical_location_id=f"location-{index}",
            source_group_id=group,
            partition=partition,
            reference_thickness_m=thickness,
            round_trip_time_s=2 * thickness / speed + offset,
        )

    return dict(
        calibration_id="reference-block-fit",
        material_id="reviewed-reference-steel",
        probe_id="longitudinal-probe",
        temperature_K=293.15,
        time_zero_offset_s=offset,
        incidence_angle_rad=0.0,
        reference_dimension_method="traceable micrometer readings supplied by caller",
        observations=[
            row(0, 0.004, "calibration", "calibration-a"),
            row(1, 0.006, "calibration", "calibration-a"),
            row(2, 0.008, "calibration", "calibration-b"),
            row(3, holdout_thickness_m, "holdout", "holdout-a"),
        ],
        timing_and_path_reviewed=True,
        reference_dimensions_reviewed=True,
        holdout_partition_predeclared=True,
        evidence=(
            Evidence(
                source_id="caller-reference-block",
                origin="measured",
                citation="caller-owned calibration record",
            ),
        ),
    )


def test_sound_speed_fit_recovers_exact_identity_and_keeps_fragment_unreviewed():
    result = pulse_echo_sound_speed_fit(PulseEchoSoundSpeedFit(**_input()))
    assert result.values["sound_speed_m_s"] == pytest.approx(5900.0)
    assert result.values["holdout_rmse_m"] == pytest.approx(0.0, abs=1e-15)
    fragment = result.values["calibration_fragment"]
    assert fragment["calibration_reviewed"] is False
    assert fragment["applicable_sample_ids"] == []


def test_holdout_value_does_not_change_fitted_speed():
    baseline = pulse_echo_sound_speed_fit(PulseEchoSoundSpeedFit(**_input()))
    changed = _input(holdout_thickness_m=0.010)
    # Retain the same holdout time while changing only its independently measured dimension.
    changed["observations"][-1] = changed["observations"][-1].model_copy(
        update={"round_trip_time_s": _input()["observations"][-1].round_trip_time_s}
    )
    perturbed = pulse_echo_sound_speed_fit(PulseEchoSoundSpeedFit(**changed))
    assert perturbed.values["sound_speed_m_s"] == baseline.values["sound_speed_m_s"]
    assert perturbed.values["holdout_rmse_m"] > baseline.values["holdout_rmse_m"]


@pytest.mark.parametrize("identity", ["physical_location_id", "source_group_id"])
def test_partition_identity_leakage_is_rejected(identity):
    values = _input()
    crossing = getattr(values["observations"][0], identity)
    values["observations"][-1] = values["observations"][-1].model_copy(update={identity: crossing})
    with pytest.raises(ValidationError, match="cannot cross"):
        PulseEchoSoundSpeedFit(**values)


def test_time_zero_must_leave_positive_observation_time():
    values = _input()
    values["observations"][0] = values["observations"][0].model_copy(
        update={"round_trip_time_s": values["time_zero_offset_s"]}
    )
    with pytest.raises(ValidationError, match="positive round-trip"):
        PulseEchoSoundSpeedFit(**values)


def test_effective_variance_fit_uses_declared_point_uncertainties():
    values = _input()
    values["fit_method"] = "iterative_effective_variance"
    values["observations"] = [
        row.model_copy(
            update={
                "reference_thickness_standard_uncertainty_m": 2e-6,
                "round_trip_time_standard_uncertainty_s": 1e-9,
            }
        )
        for row in values["observations"]
    ]
    result = pulse_echo_sound_speed_fit(PulseEchoSoundSpeedFit(**values))
    assert result.values["sound_speed_m_s"] == pytest.approx(5900.0)
    assert result.values["sound_speed_standard_error_m_s"] > 0
    assert result.values["calibration_reduced_chi_square"] == pytest.approx(0.0, abs=1e-20)
    assert result.values["holdout_standardized_residual_rmse"] == pytest.approx(0.0, abs=1e-12)


def test_effective_variance_requires_complete_uncertainty_pairs():
    values = _input()
    values["observations"][0] = values["observations"][0].model_copy(
        update={"reference_thickness_standard_uncertainty_m": 2e-6}
    )
    with pytest.raises(ValidationError, match="uncertainties must be supplied together"):
        PulseEchoSoundSpeedFit(**values)


def test_effective_variance_nonconvergence_is_explicit():
    values = _input()
    values["fit_method"] = "iterative_effective_variance"
    values["maximum_iterations"] = 1
    values["relative_convergence_tolerance"] = 1e-16
    uncertainty = [1e-6, 2e-6, 9e-6, 2e-6]
    values["observations"] = [
        row.model_copy(
            update={
                "reference_thickness_m": row.reference_thickness_m + (index - 1) * 1e-5,
                "reference_thickness_standard_uncertainty_m": uncertainty[index],
                "round_trip_time_standard_uncertainty_s": 2e-9,
            }
        )
        for index, row in enumerate(values["observations"])
    ]
    result = pulse_echo_sound_speed_fit(PulseEchoSoundSpeedFit(**values))
    assert result.status == "needs_data"
    assert result.values["iterations"] == 1
