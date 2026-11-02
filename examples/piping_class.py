"""Synthetic caller-owned class definition; no nominal rating table bundled."""

from matintegrity.contracts import RunContext, canonical_digest
from matintegrity.models.mechanics import PressureTemperatureEnvelope
from matintegrity.models.piping_class import PipingClassAssessment, PipingComponentRecord, PipingComponentRule
from matintegrity.registry import default_registry


def sample_requests():
    curve = PressureTemperatureEnvelope(
        envelope_id="synthetic-curve",
        applicability_basis="authored synthetic curve",
        source_sha256="a" * 64,
        knots=[
            dict(temperature_K=300.0, allowable_pressure_Pa=1000.0),
            dict(temperature_K=400.0, allowable_pressure_Pa=800.0),
        ],
        operating_points=[dict(point_id="design", temperature_K=350.0, pressure_Pa=850.0)],
        applicability_reviewed=True,
        operating_points_reviewed=True,
    )
    rule = PipingComponentRule(
        component_kind="pipe",
        allowed_material_condition_ids=("condition-A",),
        minimum_corrosion_allowance_m=0.002,
        required_attributes={"heat_treatment": "state-A"},
    )
    part = PipingComponentRecord(
        component_id="pipe-1",
        physical_scope_id="line-1",
        component_kind="pipe",
        material_condition_id="condition-A",
        corrosion_allowance_m=0.003,
        attributes={"heat_treatment": "state-A"},
    )
    values = dict(
        class_id="synthetic-class",
        class_revision="1",
        asset_id="synthetic",
        location_id="line",
        physical_scope_id="line-1",
        service_id="synthetic-service",
        allowed_service_ids=("synthetic-service",),
        rating_label="opaque-caller-label",
        gauge_reference_id="synthetic-ambient",
        pressure_envelope=curve,
        component_rules=(rule,),
        required_component_kinds=("pipe",),
        components=(part,),
    )
    # Only assemble a JSON hash here; the returned constructor validates every field.
    serialized = PipingClassAssessment.model_construct(**values).model_dump(mode="json", exclude={"basis"})
    digest = canonical_digest(serialized)
    inputs = PipingClassAssessment(
        **values,
        basis=dict(
            source_id="synthetic",
            revision="1",
            license_id="authored-example",
            record_sha256=digest,
            applicability_and_units_reviewed=True,
            computational_use_authorized=True,
            evidence=(
                dict(
                    source_id="synthetic",
                    origin="synthetic",
                    citation="authored class example",
                    license_id="authored-example",
                    sha256=digest,
                ),
            ),
        ),
    )
    return (("design.piping_class_assessment", inputs),)


if __name__ == "__main__":
    registry = default_registry()
    for model_id, inputs in sample_requests():
        print(
            registry.run(
                model_id, inputs, RunContext(asset_id="synthetic", location_id="line", time_basis="example")
            ).model_dump_json(indent=2)
        )
