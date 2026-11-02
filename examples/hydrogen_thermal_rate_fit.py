"""Fit an authored Arrhenius frequency law with a predeclared holdout."""

import json
import math

from matintegrity.contracts import RunContext
from matintegrity.models.hydrogen import R_J_mol_K
from matintegrity.registry import default_registry

temperatures = [300.0, 350.0, 400.0, 450.0, 500.0, 375.0, 425.0]
prefactor = 2.5e9
activation = 42000.0
request = {
    "fit_id": "synthetic-capture-fit",
    "frequency_id": "synthetic-capture-law",
    "frequency_role": "capture",
    "kind": "arrhenius",
    "trap_id": "synthetic-trap",
    "material_condition_id": "synthetic-state",
    "reference_lattice_id": "synthetic-sites",
    "energy_reference_id": "synthetic-lattice-site-zero",
    "observation_id": [f"synthetic-rate-{index}" for index in range(len(temperatures))],
    "source_group_id": ["synthetic-calibration"] * 5 + ["synthetic-holdout"] * 2,
    "partition": ["calibration"] * 5 + ["holdout"] * 2,
    "temperature_K": temperatures,
    "frequency_per_s": [
        prefactor * math.exp(-activation / (R_J_mol_K * temperature)) for temperature in temperatures
    ],
    "log_frequency_standard_uncertainty": [0.05] * len(temperatures),
    "minimum_calibration_temperature_span_K": 100.0,
    "calibration_observations_independent_reviewed": True,
    "rate_observation_mapping_reviewed": True,
    "common_energy_reference_reviewed": True,
    "holdout_partition_predeclared": True,
    "evidence": [
        {
            "source_id": "authored-synthetic",
            "origin": "synthetic",
            "citation": "Authored thermal-rate fit demonstration",
            "license_id": "MIT",
        }
    ],
}

result = default_registry().run_json(
    "transport.hydrogen_thermal_rate_fit",
    json.dumps(request),
    RunContext(
        asset_id="synthetic-asset",
        location_id="synthetic-trap",
        time_basis="independent rate observations",
    ),
)
print(result.model_dump_json(indent=2))
