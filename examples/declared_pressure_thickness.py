"""Authored algebra demonstration; coefficients are not equipment or code data."""

from matintegrity.contracts import RunContext, canonical_digest
from matintegrity.models.declared_pressure_relation import DeclaredPressureThicknessRelation
from matintegrity.registry import default_registry


def request(**changes):
    raw = dict(
        asset_id="asset",
        location_id="location",
        component_id="component",
        geometry_definition_id="authored-geometry",
        material_condition_id="hot-corroded",
        temperature_K=400.0,
        coefficient_definition_id="authored-relation",
        dimension_convention_id="authored-length",
        direction="pressure_from_thickness",
        allowable_stress_Pa=100.0,
        joint_efficiency=0.8,
        numerator_factor=2.0,
        geometry_length_m=4.0,
        thickness_coefficient=0.5,
        effective_thickness_m=2.0,
        pressure_difference_Pa=None,
        minimum_supported_thickness_m=0.1,
        maximum_supported_thickness_m=5.0,
        minimum_supported_pressure_Pa=0.0,
        maximum_supported_pressure_Pa=1000.0,
        geometry_material_temperature_and_coefficient_scope_reviewed=True,
        effective_thickness_and_allowances_reviewed=True,
        pressure_difference_and_load_scope_reviewed=True,
    )
    raw.update(changes)
    digest = canonical_digest(raw)
    return DeclaredPressureThicknessRelation(
        **raw,
        basis=dict(
            source_id="authored",
            revision="1",
            license_id="authored-test",
            record_sha256=digest,
            applicability_and_units_reviewed=True,
            computational_use_authorized=True,
            evidence=(
                dict(
                    source_id="authored",
                    origin="synthetic",
                    citation="Authored algebra",
                    license_id="authored-test",
                    sha256=digest,
                ),
            ),
        ),
    )


if __name__ == "__main__":
    inputs = request()
    result = default_registry().run(
        "structural.declared_pressure_thickness_relation",
        inputs.model_dump(mode="python"),
        RunContext(asset_id="asset", location_id="location", time_basis="authored static scenario"),
    )
    print(result.model_dump_json(indent=2))
