"""Authored relation-to-common-pressure aggregation demonstration."""

from declared_pressure_thickness import request

from matintegrity.models.component_pressure_reference import (
    ComponentPressureReference,
    component_pressure_reference,
)
from matintegrity.models.pressure_limit_binding import (
    PressureLimitReferenceContext,
    bind_pressure_relation_component_limit,
    verify_pressure_reference_bindings,
)


def reference(**updates):
    raw = dict(
        asset_id="asset",
        location_id="location",
        physical_scope_id="vessel",
        condition_id="hot-corroded",
        coordinate_frame_id="survey",
        component_elevation_m=0.0,
        pressure_basis="gauge_common_reference",
        common_pressure_reference_id="ambient",
        external_absolute_pressure_Pa=100000.0,
        common_reference_absolute_pressure_Pa=100000.0,
        external_pressure_and_common_reference_reviewed=True,
        component_scenario_and_coordinate_mapping_reviewed=True,
        evidence=(
            dict(source_id="authored", origin="synthetic", citation="Authored reference", sha256="a" * 64),
        ),
    )
    raw.update(updates)
    return PressureLimitReferenceContext(**raw)


def aggregation(binding, **updates):
    raw = dict(
        asset_id="asset",
        location_id="location",
        physical_scope_id="vessel",
        condition_id="hot-corroded",
        coordinate_frame_id="survey",
        pressure_basis="gauge_common_reference",
        common_pressure_reference_id="ambient",
        reference_elevation_m=0.0,
        uniform_density_kg_m3=1000.0,
        gravity_m_s2=10.0,
        components=(binding.component_limit,),
        static_connected_uniform_fluid_reviewed=True,
        component_scope_complete_reviewed=True,
        common_pressure_and_elevation_reference_reviewed=True,
        component_capacity_and_condition_reviewed=True,
    )
    raw.update(updates)
    return ComponentPressureReference(**raw)


if __name__ == "__main__":
    binding = bind_pressure_relation_component_limit(request(), reference())
    combined = aggregation(binding)
    verify_pressure_reference_bindings(combined, (binding,))
    print(binding.model_dump_json(indent=2))
    print(component_pressure_reference(combined).model_dump_json(indent=2))
