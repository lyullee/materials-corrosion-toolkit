import pytest

from matintegrity.contracts import RunContext, canonical_digest
from matintegrity.models.engineering_correlations import (
    FlooredCompositionIndexRecipe,
    floored_composition_index_recipe,
)
from matintegrity.registry import default_registry


def test_explicit_positive_floor_can_supply_reciprocal_effective_assay():
    x = request(
        chemistry={"A": 0.0},
        constituent_floors={"A": 0.25},
        constant_offset=0,
        terms=(dict(term_id="reciprocal", coefficient=1, factors=(dict(element_id="A", power=-1),)),),
    )
    result = floored_composition_index_recipe(x)
    assert result.values["index_value"] == 4
    assert result.values["converted_assay"]["A"] == 0
    assert result.values["floor_applied_elements"] == ["A"]


@pytest.mark.parametrize(
    "coefficient,status,expected",
    [(1e308, "computed", 1e-92), (1.0, "out_of_scope", None), (0.0, "computed", 0.0)],
)
def test_floored_recipe_preserves_nonzero_scaled_powers(coefficient, status, expected):
    x = request(
        chemistry={"A": 1e-200},
        constituent_floors={"A": 0.0},
        constant_offset=0.0,
        terms=(dict(term_id="square", coefficient=coefficient, factors=(dict(element_id="A", power=2),)),),
    )
    result = floored_composition_index_recipe(x)
    assert result.status == status
    if expected is None:
        assert "index_value" not in result.values
    else:
        assert result.values["index_value"] == pytest.approx(expected, rel=1e-14, abs=0.0)


def request(**updates):
    raw = dict(
        index_id="authored-floor",
        chemistry={"A": 0.02, "B": 0.3},
        input_mass_basis="mass_percent",
        recipe_mass_basis="mass_percent",
        output_unit="authored",
        constant_offset=-1.0,
        constituent_floors={"A": 0.1},
        terms=(
            dict(
                term_id="interaction",
                coefficient=2.0,
                factors=(dict(element_id="A", power=2), dict(element_id="B")),
            ),
        ),
    )
    raw.update(updates)
    # Build nested defaults through their contracts before pinning the request.
    from matintegrity.models.engineering_correlations import CompositionIndexTerm

    raw["terms"] = tuple(CompositionIndexTerm(**term) for term in raw["terms"])
    normalized = FlooredCompositionIndexRecipe.model_construct(**raw)
    digest = canonical_digest(normalized.model_dump(mode="json", exclude={"basis"}))
    raw["basis"] = dict(
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
                citation="authored floor arithmetic",
                license_id="authored-test",
                sha256=digest,
            ),
        ),
    )
    return FlooredCompositionIndexRecipe(**raw)


@pytest.mark.parametrize(
    "basis,scale", [("mass_percent", 1.0), ("mass_fraction", 0.01), ("mass_ppm", 10000.0)]
)
def test_floor_uses_recipe_basis_and_retains_measured_assay(basis, scale):
    x = request(input_mass_basis=basis, chemistry={"A": 0.02 * scale, "B": 0.3 * scale})
    r = floored_composition_index_recipe(x)
    assert r.status == "computed"
    assert r.values["index_value"] == pytest.approx(-0.994)
    assert r.values["converted_assay"]["A"] == pytest.approx(0.02)
    assert r.values["effective_constituents"]["A"] == 0.1
    assert r.values["floor_applied_elements"] == ["A"]


@pytest.mark.parametrize("value", [0.1, 0.2])
def test_at_or_above_floor_does_not_modify_measurement(value):
    r = floored_composition_index_recipe(request(chemistry={"A": value, "B": 0.3}))
    assert r.values["index_value"] == pytest.approx(2 * value**2 * 0.3 - 1)
    assert r.values["floor_applied_elements"] == []


def test_unmeasured_floor_does_not_fill_missing_assay():
    with pytest.raises(ValueError, match="measured constituents"):
        request(constituent_floors={"missing": 0.1})


def test_floor_tampering_breaks_identity():
    raw = request().model_dump()
    raw["constituent_floors"]["A"] = 0.2
    with pytest.raises(ValueError, match="pin the complete"):
        FlooredCompositionIndexRecipe.model_validate(raw)


def test_public_python_json_exchange():
    x = request()
    registry = default_registry()
    context = RunContext(asset_id="synthetic", location_id="assay", time_basis="authored")
    a = registry.run("materials.floored_composition_index_recipe", x, context)
    b = registry.run_json("materials.floored_composition_index_recipe", x.model_dump_json(), context)
    assert a.status == b.status == "computed"
    assert a.model_dump() == b.model_dump()
