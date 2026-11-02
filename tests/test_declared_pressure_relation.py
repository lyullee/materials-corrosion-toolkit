import pytest
from pydantic import ValidationError

from matintegrity.contracts import RunContext, canonical_digest
from matintegrity.models.declared_pressure_relation import (
    DeclaredPressureThicknessRelation,
    declared_pressure_thickness_relation,
)
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


def test_forward_and_inverse_authored_relation():
    result = declared_pressure_thickness_relation(request())
    assert result.values["pressure_difference_Pa"] == 64.0
    inverse = declared_pressure_thickness_relation(
        request(direction="thickness_from_pressure", effective_thickness_m=None, pressure_difference_Pa=64.0)
    )
    assert inverse.values["effective_thickness_m"] == pytest.approx(2.0, rel=1e-15)


@pytest.mark.parametrize("coefficient", [-0.5, 0.0, 0.5])
def test_signed_coefficient_roundtrip(coefficient):
    forward = declared_pressure_thickness_relation(request(thickness_coefficient=coefficient))
    inverse = declared_pressure_thickness_relation(
        request(
            thickness_coefficient=coefficient,
            direction="thickness_from_pressure",
            effective_thickness_m=None,
            pressure_difference_Pa=forward.values["pressure_difference_Pa"],
        )
    )
    assert inverse.values["effective_thickness_m"] == pytest.approx(2.0)


@pytest.mark.parametrize(
    "changes",
    [
        dict(thickness_coefficient=-2.0),
        dict(direction="thickness_from_pressure", effective_thickness_m=None, pressure_difference_Pa=320.0),
        dict(maximum_supported_pressure_Pa=63.0),
        dict(maximum_supported_thickness_m=1.0),
    ],
)
def test_singular_or_unsupported_values_withheld(changes):
    result = declared_pressure_thickness_relation(request(**changes))
    assert result.status == "out_of_scope"
    assert result.values == {}


@pytest.mark.parametrize(
    "gate",
    [
        "geometry_material_temperature_and_coefficient_scope_reviewed",
        "effective_thickness_and_allowances_reviewed",
        "pressure_difference_and_load_scope_reviewed",
    ],
)
def test_missing_review_withholds_result(gate):
    assert declared_pressure_thickness_relation(request(**{gate: False})).status == "needs_data"


def test_conflicting_direction_inputs_rejected():
    with pytest.raises(ValidationError):
        request(pressure_difference_Pa=64.0)


def test_evidence_digest_rejects_coefficient_mutation():
    raw = request().model_dump(mode="python")
    raw["numerator_factor"] = 3.0
    with pytest.raises(ValidationError, match="pin"):
        DeclaredPressureThicknessRelation(**raw)


def test_intermediate_overflow_cancelled_before_conversion():
    result = declared_pressure_thickness_relation(
        request(
            numerator_factor=1e300,
            allowable_stress_Pa=1e300,
            joint_efficiency=1.0,
            geometry_length_m=1e300,
            thickness_coefficient=0.0,
            effective_thickness_m=1e-300,
            minimum_supported_thickness_m=1e-300,
        )
    )
    assert result.values["pressure_difference_Pa"] == pytest.approx(1.0)


def test_default_registry_python_json_execution_equal():
    x = request()
    registry = default_registry()
    context = RunContext(asset_id="asset", location_id="location", time_basis="authored")
    a = registry.run("structural.declared_pressure_thickness_relation", x.model_dump(mode="python"), context)
    b = registry.run_json("structural.declared_pressure_thickness_relation", x.model_dump_json(), context)
    assert a.model_dump(mode="json") == b.model_dump(mode="json")
