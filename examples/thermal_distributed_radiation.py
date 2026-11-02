"""Synthetic input wiring for volumetric convection plus gray radiation."""

import json
from pathlib import Path

from matintegrity.contracts import RunContext
from matintegrity.registry import default_registry


def main():
    examples = json.loads(Path(__file__).with_name("model_inputs.json").read_text(encoding="utf-8"))[
        "models"
    ]
    request = examples["thermal.transient_conduction_1d"]
    cell_count = len(request["cell_material_ids"])
    time_count = len(request["time_s"])
    request["distributed_exchange"] = {
        "area_per_volume_m_inv": [12.0] * cell_count,
        "convection_W_m2_K": [8.0] * time_count,
        "ambient_temperature_K": [293.15] * time_count,
        "emissivity_history": [0.78 + 0.08 * index / max(1, time_count - 1) for index in range(time_count)],
        "radiative_environment_temperature_K": [293.15] * time_count,
        "radiation_exchange_basis_reviewed": True,
    }
    result = default_registry().run_json(
        "thermal.transient_conduction_1d",
        json.dumps(request),
        RunContext(
            asset_id="synthetic-radiating-section",
            location_id="synthetic-distributed-surface",
            time_basis="synthetic-elapsed-seconds",
        ),
    )
    print(json.dumps({
        "status": result.status,
        "temperature_history_K": result.values.get("temperature_history_K"),
        "distributed_heat_rate_into_solid_W": result.values.get("distributed_heat_rate_into_solid_W"),
        "maximum_relative_discrete_energy_balance_error": result.values.get(
            "maximum_relative_discrete_energy_balance_error"
        ),
        "notes": result.notes,
    }, indent=2))


if __name__ == "__main__":
    main()
