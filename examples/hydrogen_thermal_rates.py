"""Generate synthetic thermal capture/release histories for a kinetic trap."""

import json

from matintegrity.contracts import RunContext
from matintegrity.registry import default_registry

EVIDENCE = {
    "source_id": "authored-synthetic",
    "origin": "synthetic",
    "citation": "Authored parameter demonstration",
}
INPUTS = {
    "trap_id": "synthetic-trap",
    "material_condition_id": "synthetic-state",
    "reference_lattice_id": "synthetic-sites",
    "energy_reference_id": "synthetic-lattice-site-zero",
    "elapsed_time_origin_id": "synthetic-heating-start",
    "elapsed_time_s": [0.0, 5.0, 10.0],
    "temperature_K": [300.0, 400.0, 500.0],
    "supported_temperature_K": [280.0, 520.0],
    "capture": {
        "frequency_id": "synthetic-capture",
        "kind": "arrhenius",
        "pre_exponential_frequency_per_s": 1000000.0,
        "activation_energy_J_mol": 30000.0,
        "evidence": [EVIDENCE],
    },
    "release": {
        "frequency_id": "synthetic-release",
        "kind": "transition_state",
        "activation_enthalpy_J_mol": 65000.0,
        "activation_entropy_J_mol_K": -25.0,
        "transmission_coefficient": 0.8,
        "evidence": [EVIDENCE],
    },
    "temperature_history_reviewed": True,
    "frequency_parameterizations_reviewed": True,
    "common_energy_reference_reviewed": True,
}

if __name__ == "__main__":
    result = default_registry().run_json(
        "transport.hydrogen_trap_thermal_rates",
        json.dumps(INPUTS),
        RunContext(
            asset_id="synthetic-material",
            location_id="trap-population",
            time_basis="elapsed from synthetic heating start",
        ),
    )
    print(
        json.dumps(
            {
                "status": result.status,
                "capture_frequency_per_s": result.values.get("capture_frequency_per_s"),
                "release_frequency_per_s": result.values.get("release_frequency_per_s"),
                "rate_fields_for_HydrogenKineticTrap": result.values.get("independent_rate_contract_fields"),
            },
            indent=2,
        )
    )
