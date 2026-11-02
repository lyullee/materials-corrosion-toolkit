"""Authored static-pressure demonstration; not actual equipment data."""

from matintegrity.contracts import RunContext
from matintegrity.models.component_pressure_reference import ComponentPressureReference
from matintegrity.registry import default_registry


def request(**updates):
    evidence = (
        dict(source_id="authored", origin="synthetic", citation="Authored static balance", sha256="a" * 64),
    )
    raw = dict(
        asset_id="asset",
        location_id="location",
        physical_scope_id="vessel",
        condition_id="hot-corroded",
        coordinate_frame_id="survey",
        pressure_basis="gauge_common_reference",
        common_pressure_reference_id="ambient",
        reference_elevation_m=10.0,
        uniform_density_kg_m3=1000.0,
        gravity_m_s2=10.0,
        components=(
            dict(
                component_id="upper",
                pressure_limit_Pa=1000000.0,
                elevation_m=10.0,
                condition_id="hot-corroded",
                temperature_K=400.0,
                capacity_input_digest="b" * 64,
                capacity_result_digest="c" * 64,
                evidence=evidence,
            ),
            dict(
                component_id="lower",
                pressure_limit_Pa=1050000.0,
                elevation_m=0.0,
                condition_id="hot-corroded",
                temperature_K=400.0,
                capacity_input_digest="d" * 64,
                capacity_result_digest="e" * 64,
                evidence=evidence,
            ),
        ),
        static_connected_uniform_fluid_reviewed=True,
        component_scope_complete_reviewed=True,
        common_pressure_and_elevation_reference_reviewed=True,
        component_capacity_and_condition_reviewed=True,
    )
    raw.update(updates)
    return ComponentPressureReference(**raw)


if __name__ == "__main__":
    inputs = request()
    result = default_registry().run(
        "structural.component_pressure_reference",
        inputs.model_dump(mode="python"),
        RunContext(asset_id="asset", location_id="location", time_basis="authored static scenario"),
    )
    print(result.model_dump_json(indent=2))
