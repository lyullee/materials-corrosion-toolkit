"""Fit pulse-echo sound speed directly with Python objects; JSON is not required."""

from matintegrity.contracts import Evidence
from matintegrity.models.inspection import (
    PulseEchoCalibrationObservation,
    PulseEchoSoundSpeedFit,
    pulse_echo_sound_speed_fit,
)

known_speed_m_s = 5900.0
time_zero_offset_s = 40e-9


def observation(index, thickness_m, partition, group):
    return PulseEchoCalibrationObservation(
        observation_id=f"reference-{index}",
        physical_location_id=f"location-{index}",
        source_group_id=group,
        partition=partition,
        reference_thickness_m=thickness_m,
        round_trip_time_s=2 * thickness_m / known_speed_m_s + time_zero_offset_s,
        reference_thickness_standard_uncertainty_m=2e-6,
        round_trip_time_standard_uncertainty_s=1e-9,
    )


request = PulseEchoSoundSpeedFit(
    calibration_id="user-reference-block-revision-1",
    material_id="user-reference-material",
    probe_id="user-longitudinal-probe",
    temperature_K=293.15,
    time_zero_offset_s=time_zero_offset_s,
    incidence_angle_rad=0.0,
    reference_dimension_method="replace with controlled dimensional-metrology method",
    fit_method="iterative_effective_variance",
    observations=[
        observation(0, 0.004, "calibration", "calibration-a"),
        observation(1, 0.006, "calibration", "calibration-a"),
        observation(2, 0.008, "calibration", "calibration-b"),
        observation(3, 0.009, "holdout", "holdout-a"),
    ],
    timing_and_path_reviewed=True,
    reference_dimensions_reviewed=True,
    holdout_partition_predeclared=True,
    evidence=(
        Evidence(
            source_id="user-reference-block-record",
            origin="user_declared",
            citation="replace with the controlled user calibration record",
        ),
    ),
)

result = pulse_echo_sound_speed_fit(request)
print(result.model_dump_json(indent=2))
