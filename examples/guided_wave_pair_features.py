"""Run a synthetic guided-wave pair through the public registry API."""

from matintegrity.contracts import RunContext
from matintegrity.registry import default_registry

inputs = {
    "specimen_id": "example-tube",
    "baseline_acquisition_id": "baseline-1",
    "observation_acquisition_id": "observation-1",
    "frequency_Hz": 14_000.0,
    "wave_mode": "torsional",
    "baseline_distance_m": [0.0, 0.5, 1.0, 1.5],
    "baseline_voltage_V": [0.01, 0.02, -0.01, -0.02],
    "observation_distance_m": [0.0, 0.5, 1.0, 1.5],
    "observation_voltage_V": [0.012, 0.018, -0.015, -0.018],
    "window_start_m": 0.0,
    "window_end_m": 1.5,
    "distance_match_tolerance_m": 0.0,
    "duplicate_distance_policy": "preserve_samples",
}

result = default_registry().run(
    "inspection.guided_wave_pair_features",
    inputs,
    RunContext(
        asset_id="example-tube",
        location_id="example-window",
        time_basis="synthetic acquisition order",
    ),
)
print(result.model_dump_json(indent=2))
