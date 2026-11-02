"""Apply a caller-owned pulse-echo calibration to an already qualified SI observation series."""

from datetime import datetime

from matintegrity.contracts import Evidence
from matintegrity.ultrasound_data import (
    PulseEchoThicknessCalibration,
    pulse_echo_thickness_observations,
)

series = {
    "source_id": "user-qualified-device-export",
    "series_id": "coupon-location-a",
    "reported_tof_unit": "s",
    "observations": [
        {
            "source_order": 0,
            "timestamp": datetime(2026, 1, 1),
            "observational_unit_id": "coupon-location-a",
            "sample_id": "coupon-01",
            "piezo_id": "probe-01",
            "tof_s": 1.68e-6,
            "tof_compensated_s": None,
        }
    ],
}
calibration = PulseEchoThicknessCalibration(
    calibration_id="user-calibration-revision-3",
    material_id="user-material-heat-01",
    applicable_sample_ids=("coupon-01",),
    applicable_probe_ids=("probe-01",),
    wave_mode="longitudinal",
    sound_speed_m_s=5950.0,
    sound_speed_temperature_K=293.15,
    time_zero_offset_s=0.0,
    tof_field="tof_s",
    calibration_basis="user-owned reference-block calibration; illustrative values only",
    evidence=Evidence(
        source_id="user-calibration-record",
        origin="user_declared",
        citation="replace with the controlled calibration record",
    ),
    calibration_reviewed=True,
)

print(pulse_echo_thickness_observations(series, calibration=calibration))
