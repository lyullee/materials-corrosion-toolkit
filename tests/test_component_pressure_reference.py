import pytest
from pydantic import ValidationError

from matintegrity.contracts import RunContext
from matintegrity.models.component_pressure_reference import (
    ComponentPressureReference,
    component_pressure_reference,
)
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


def test_lower_component_can_govern_after_datum_translation():
    result = component_pressure_reference(request())
    assert result.values["reference_pressure_limits_Pa"] == [1000000.0, 950000.0]
    assert result.values["governing_component_ids"] == ["lower"]
    assert result.values["governing_reference_pressure_limit_Pa"] == 950000.0


def test_datum_translation_preserves_governing_identity():
    a = component_pressure_reference(request())
    b = component_pressure_reference(request(reference_elevation_m=0.0))
    assert a.values["governing_component_ids"] == b.values["governing_component_ids"]
    assert b.values["governing_reference_pressure_limit_Pa"] == 1050000.0


def test_zero_density_retains_input_limits():
    result = component_pressure_reference(request(uniform_density_kg_m3=0.0))
    assert result.values["governing_component_ids"] == ["upper"]


@pytest.mark.parametrize(
    "gate",
    [
        "static_connected_uniform_fluid_reviewed",
        "component_scope_complete_reviewed",
        "common_pressure_and_elevation_reference_reviewed",
        "component_capacity_and_condition_reviewed",
    ],
)
def test_unreviewed_scope_withholds_values(gate):
    assert component_pressure_reference(request(**{gate: False})).status == "needs_data"


def test_duplicate_and_mixed_condition_rejected():
    raw = request().model_dump(mode="python")
    raw["components"][1]["component_id"] = "upper"
    with pytest.raises(ValidationError):
        ComponentPressureReference(**raw)
    raw["components"][1]["component_id"] = "lower"
    raw["components"][1]["condition_id"] = "cold-new"
    with pytest.raises(ValidationError):
        ComponentPressureReference(**raw)


def test_python_json_registry_equal_and_context_bound():
    x = request()
    registry = default_registry()
    context = RunContext(asset_id="asset", location_id="location", time_basis="static")
    a = registry.run("structural.component_pressure_reference", x.model_dump(mode="python"), context)
    b = registry.run_json("structural.component_pressure_reference", x.model_dump_json(), context)
    assert a.model_dump(mode="json") == b.model_dump(mode="json")
    with pytest.raises(ValueError):
        registry.run(
            "structural.component_pressure_reference",
            x.model_dump(mode="python"),
            RunContext(asset_id="other", location_id="location", time_basis="static"),
        )


def test_exact_governing_ties_preserved():
    raw = request().model_dump(mode="python")
    raw["components"][1]["pressure_limit_Pa"] = 1100000.0
    result = component_pressure_reference(ComponentPressureReference(**raw))
    assert result.values["governing_component_ids"] == ["upper", "lower"]


def test_impossible_absolute_reference_withheld():
    result = component_pressure_reference(request(pressure_basis="absolute", reference_elevation_m=1000.0))
    assert result.status == "out_of_scope"
    assert result.values == {}


def test_extreme_intermediate_cancellation_retains_zero_offset():
    result = component_pressure_reference(
        request(uniform_density_kg_m3=1e300, gravity_m_s2=1e300, components=(request().components[0],))
    )
    assert result.values["hydrostatic_reference_offsets_Pa"] == [0.0]


def test_unrepresentable_offsets_withheld():
    result = component_pressure_reference(request(uniform_density_kg_m3=1e300, gravity_m_s2=1e300))
    assert result.status == "out_of_scope"
