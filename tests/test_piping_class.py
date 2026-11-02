import pytest

from matintegrity.contracts import RunContext, canonical_digest
from matintegrity.models.mechanics import PressureTemperatureEnvelope
from matintegrity.models.piping_class import (
    PipingClassAssessment,
    PipingComponentRecord,
    PipingComponentRule,
    piping_class_assessment,
    specifications,
)
from matintegrity.registry import ModelRegistry


def payload(**changes):
    rule = PipingComponentRule(
        component_kind="pipe",
        allowed_material_condition_ids=("condition-A",),
        minimum_corrosion_allowance_m=0.002,
        required_attributes={"heat_treatment": "state-A"},
    )
    component = PipingComponentRecord(
        component_id="pipe-1",
        physical_scope_id="line-1",
        component_kind="pipe",
        material_condition_id="condition-A",
        corrosion_allowance_m=0.003,
        attributes={"heat_treatment": "state-A"},
    )
    envelope = PressureTemperatureEnvelope(
        envelope_id="curve-1",
        applicability_basis="synthetic example",
        source_sha256="a" * 64,
        knots=[
            dict(temperature_K=300.0, allowable_pressure_Pa=1000.0),
            dict(temperature_K=400.0, allowable_pressure_Pa=800.0),
        ],
        operating_points=[dict(point_id="design-1", temperature_K=350.0, pressure_Pa=850.0)],
        applicability_reviewed=True,
        operating_points_reviewed=True,
    )
    values = (
        dict(
            class_id="caller-class",
            class_revision="1",
            asset_id="asset",
            location_id="location",
            physical_scope_id="line-1",
            service_id="caller-service",
            allowed_service_ids=("caller-service",),
            rating_label="opaque-label-999",
            gauge_reference_id="ambient-1",
            pressure_envelope=envelope,
            component_rules=(rule,),
            required_component_kinds=("pipe",),
            components=(component,),
        )
        | changes
    )
    # Canonical JSON form includes defaults of all nested typed records.
    serialized = PipingClassAssessment.model_construct(**values).model_dump(mode="json", exclude={"basis"})
    digest = canonical_digest(serialized)
    return PipingClassAssessment(
        **values,
        basis=dict(
            source_id="synthetic",
            revision="1",
            license_id="authored-test",
            record_sha256=digest,
            applicability_and_units_reviewed=True,
            computational_use_authorized=True,
            evidence=(
                dict(
                    source_id="synthetic",
                    origin="synthetic",
                    citation="authored piping-class test",
                    license_id="authored-test",
                    sha256=digest,
                ),
            ),
        ),
    )


def test_component_and_pressure_curve_composition():
    result = piping_class_assessment(payload())
    assert result.status == "computed"
    assert result.values["declared_class_outcome"] == "satisfied"
    assert result.values["pressure_envelope"]["values"]["pressure_margins_Pa"] == [50.0]
    assert result.values["rating_label"] == "opaque-label-999"


@pytest.mark.parametrize(
    "changes,field",
    [
        ({"material_condition_id": "unresolved-alias"}, "material_condition_id"),
        ({"corrosion_allowance_m": 0.001}, "corrosion_allowance_m"),
        ({"attributes": {"heat_treatment": "state-B"}}, "attribute:heat_treatment"),
    ],
)
def test_known_component_mismatch_remains_visible(changes, field):
    item = payload().components[0].model_copy(update=changes)
    result = piping_class_assessment(payload(components=(item,)))
    assert result.values["declared_class_outcome"] == "not_satisfied"
    assert field in result.values["component_findings"][0]["mismatched_fields"]


def test_missing_attributes_and_component_kind_are_not_passes():
    item = payload().components[0].model_copy(update={"material_condition_id": None, "attributes": {}})
    result = piping_class_assessment(payload(components=(item,)))
    assert result.status == "needs_data"
    assert result.values["declared_class_outcome"] == "unknown"
    valve = PipingComponentRule(
        component_kind="valve",
        allowed_material_condition_ids=("condition-A",),
        minimum_corrosion_allowance_m=0.0,
        required_attributes={},
    )
    result = piping_class_assessment(
        payload(
            component_rules=(*payload().component_rules, valve), required_component_kinds=("pipe", "valve")
        )
    )
    assert result.values["missing_component_kinds"] == ["valve"]
    assert result.status == "needs_data"


def test_known_failure_is_preserved_alongside_missing_data():
    item = payload().components[0].model_copy(update={"material_condition_id": "other", "attributes": {}})
    result = piping_class_assessment(payload(components=(item,)))
    assert result.status == "needs_data"
    assert result.values["declared_class_outcome"] == "not_satisfied"


def test_unsupported_service_or_temperature_never_extrapolates():
    assert piping_class_assessment(payload(service_id="other-service")).status == "out_of_scope"
    curve = payload().pressure_envelope
    point = curve.operating_points[0].model_copy(update={"temperature_K": 401.0})
    result = piping_class_assessment(
        payload(pressure_envelope=curve.model_copy(update={"operating_points": [point]}))
    )
    assert result.status == "out_of_scope"


def test_cross_scope_and_duplicate_components_are_rejected():
    item = payload().components[0]
    with pytest.raises(ValueError, match="physical scope"):
        payload(components=(item.model_copy(update={"physical_scope_id": "other-line"}),))
    with pytest.raises(ValueError, match="unique nonblank component"):
        payload(components=(item, item))


def test_public_exchange_and_runtime_scope():
    registry = ModelRegistry()
    registry.register(specifications()[0])
    context = RunContext(asset_id="asset", location_id="location", time_basis="test")
    x = payload()
    direct = registry.run("design.piping_class_assessment", x, context)
    serialized = registry.run_json("design.piping_class_assessment", x.model_dump_json(), context)
    assert direct.model_dump() == serialized.model_dump()
    with pytest.raises(ValueError, match="run context"):
        registry.run(
            "design.piping_class_assessment",
            x,
            RunContext(asset_id="other", location_id="location", time_basis="test"),
        )
