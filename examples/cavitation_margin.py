"""Compose a CoolProp saturated-liquid state with thermodynamic cavitation screening."""

from matintegrity.contracts import RunContext
from matintegrity.registry import default_registry
from matintegrity.thermo import (
    cavitation_history_inputs_from_coolprop,
    cavitation_inputs_from_coolprop,
)


def main():
    inputs = cavitation_inputs_from_coolprop(
        fluid="Water",
        temperature_K=300.0,
        local_static_pressure_Pa=80_000.0,
        characteristic_velocity_m_s=12.0,
        local_pressure_definition="example local absolute static pressure",
        velocity_definition="example section mean velocity",
    )
    result = default_registry().run(
        "degradation.cavitation_margin",
        inputs,
        RunContext(
            asset_id="example-loop",
            location_id="example-throat",
            time_basis="one steady screening state",
        ),
    )
    print(result.model_dump_json(indent=2))
    history_inputs = cavitation_history_inputs_from_coolprop(
        history_id="example-pressure-dip",
        asset_id="example-loop",
        location_id="example-throat",
        clock_id="example-two-second-clock",
        history_origin="synthetic",
        hydraulic_source_digest="e" * 64,
        fluid="Water",
        sample_ids=["t0", "t1", "t2"],
        time_s=[0.0, 1.0, 2.0],
        temperature_K=[300.0, 300.0, 300.0],
        local_static_pressure_Pa=[5_000.0, 3_000.0, 5_000.0],
        characteristic_velocity_m_s=[12.0, 12.0, 12.0],
        sample_valid=[True, True, True],
        local_pressure_definition="example local absolute static pressure",
        velocity_definition="example section mean velocity",
    )
    history_result = default_registry().run(
        "degradation.cavitation_history",
        history_inputs,
        RunContext(
            asset_id="example-loop",
            location_id="example-throat",
            time_basis="two-second example pressure dip",
        ),
    )
    print(history_result.model_dump_json(indent=2))


if __name__ == "__main__":
    main()
