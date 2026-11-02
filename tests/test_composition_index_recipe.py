import pytest

from matintegrity.contracts import RunContext, canonical_digest
from matintegrity.models.engineering_correlations import (
    CompositionIndexRecipe,
    CompositionIndexTerm,
    composition_index_recipe,
    specifications,
)
from matintegrity.registry import ModelRegistry


def payload(**changes):
    terms = tuple(
        CompositionIndexTerm(
            term_id=f"{a}-{b}", coefficient=1.0, factors=(dict(element_id=a), dict(element_id=b))
        )
        for a in ("A", "B")
        for b in ("I", "J")
    )
    values = (
        dict(
            index_id="authored-interaction",
            chemistry={"A": 2.0, "B": 3.0, "I": 0.01, "J": 0.02},
            input_mass_basis="mass_percent",
            recipe_mass_basis="mass_percent",
            output_unit="authored_index",
            constant_offset=0.0,
            terms=terms,
        )
        | changes
    )
    serialized = CompositionIndexRecipe.model_construct(**values).model_dump(mode="json", exclude={"basis"})
    digest = canonical_digest(serialized)
    return CompositionIndexRecipe(
        **values,
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
                    citation="synthetic composition recipe",
                    license_id="authored-test",
                    sha256=digest,
                ),
            ),
        ),
    )


@pytest.mark.parametrize(
    "basis,multiplier", [("mass_percent", 1.0), ("mass_ppm", 10000.0), ("mass_fraction", 0.01)]
)
def test_mass_basis_conversion_preserves_product_of_sums(basis, multiplier):
    assay = {element: value * multiplier for element, value in payload().chemistry.items()}
    result = composition_index_recipe(payload(chemistry=assay, input_mass_basis=basis))
    assert result.values["index_value"] == pytest.approx(0.15)
    assert sum(result.values["term_contributions"].values()) == pytest.approx(0.15)


def test_signed_offset_and_partial_assay_do_not_infer_balance_metal():
    result = composition_index_recipe(payload(constant_offset=-1.0))
    assert result.values["index_value"] == pytest.approx(-0.85)
    assert set(result.values["converted_assay"]) == {"A", "B", "I", "J"}


def test_small_factor_power_survives_large_coefficient():
    term = CompositionIndexTerm(
        term_id="scaled-square", coefficient=1e308, factors=(dict(element_id="A", power=2),)
    )
    result = composition_index_recipe(payload(chemistry={"A": 1e-200}, terms=(term,)))
    assert result.status == "computed"
    assert result.values["index_value"] == pytest.approx(1e-92, rel=1e-14, abs=0.0)


def test_nonzero_unrepresentable_term_is_not_reported_as_zero():
    term = CompositionIndexTerm(
        term_id="tiny-square", coefficient=1.0, factors=(dict(element_id="A", power=2),)
    )
    result = composition_index_recipe(payload(chemistry={"A": 1e-200}, terms=(term,)))
    assert result.status == "out_of_scope"
    assert "index_value" not in result.values


def test_zero_coefficient_remains_exact_zero():
    term = CompositionIndexTerm(term_id="disabled", coefficient=0.0, factors=(dict(element_id="A", power=4),))
    result = composition_index_recipe(payload(chemistry={"A": 1e-200}, terms=(term,)))
    assert result.status == "computed"
    assert result.values["index_value"] == 0.0


@pytest.mark.parametrize("basis", ["mass_fraction", "mass_percent", "mass_ppm"])
def test_ratio_is_independent_of_common_recipe_mass_basis(basis):
    term = CompositionIndexTerm(
        term_id="ratio",
        coefficient=1,
        factors=(dict(element_id="A", power=1), dict(element_id="B", power=-1)),
    )
    result = composition_index_recipe(
        payload(
            chemistry={"A": 0.003, "B": 0.001},
            input_mass_basis="mass_fraction",
            recipe_mass_basis=basis,
            output_unit="1",
            terms=(term,),
        )
    )
    assert result.values["index_value"] == pytest.approx(3)


def test_zero_denominator_is_undefined_even_with_zero_coefficient():
    term = CompositionIndexTerm(term_id="undefined", coefficient=0, factors=(dict(element_id="B", power=-1),))
    result = composition_index_recipe(payload(chemistry={"B": 0}, terms=(term,)))
    assert result.status == "out_of_scope"
    assert "index_value" not in result.values


def test_reciprocal_intermediate_overflow_can_cancel_in_complete_term():
    term = CompositionIndexTerm(
        term_id="scaled-reciprocal", coefficient=1e-300, factors=(dict(element_id="B", power=-2),)
    )
    result = composition_index_recipe(payload(chemistry={"B": 1e-200}, terms=(term,)))
    assert result.values["index_value"] == pytest.approx(1e100)


def test_zero_power_remains_rejected():
    with pytest.raises(ValueError, match="zero power"):
        CompositionIndexTerm(term_id="constant", coefficient=1, factors=(dict(element_id="B", power=0),))


@pytest.mark.parametrize("denominator,status", [(0.002, "computed"), (0.0, "out_of_scope")])
def test_reciprocal_registry_exchange(denominator, status):
    term = CompositionIndexTerm(
        term_id="ratio", coefficient=1, factors=(dict(element_id="A"), dict(element_id="B", power=-1))
    )
    x = payload(chemistry={"A": 0.006, "B": denominator}, terms=(term,), output_unit="1")
    registry = ModelRegistry()
    model = "materials.composition_index_recipe"
    registry.register(next(s for s in specifications() if s.model_id == model))
    context = RunContext(asset_id="synthetic", location_id="assay", time_basis="test")
    direct = registry.run(model, x, context)
    encoded = registry.run_json(model, x.model_dump_json(), context)
    assert direct.model_dump() == encoded.model_dump()
    assert direct.model_version == "0.1.2"
    assert direct.status == status


def test_missing_assay_is_rejected_instead_of_assigned_zero():
    with pytest.raises(ValueError, match="explicit assay"):
        payload(chemistry={"A": 2.0, "B": 3.0, "I": 0.01})


def test_invalid_composition_and_duplicate_term_identity():
    with pytest.raises(ValueError, match="exceeds"):
        payload(chemistry={"A": 200.0, "B": 3.0, "I": 0.01, "J": 0.02})
    term = payload().terms[0]
    with pytest.raises(ValueError, match="unique"):
        payload(terms=(term, term))


def test_input_and_recipe_coefficient_tampering_invalidates_identity():
    values = payload().model_dump()
    values["terms"][0]["coefficient"] = 2.0
    with pytest.raises(ValueError, match="pin the complete"):
        CompositionIndexRecipe.model_validate(values)


def test_overflow_is_not_clipped_into_a_finite_descriptor():
    term = CompositionIndexTerm(
        term_id="overflow", coefficient=1e308, factors=(dict(element_id="A", power=4),)
    )
    assert composition_index_recipe(payload(terms=(term,))).status == "out_of_scope"


def test_public_python_json_exchange():
    registry = ModelRegistry()
    registry.register(next(s for s in specifications() if s.model_id == "materials.composition_index_recipe"))
    context = RunContext(asset_id="synthetic", location_id="assay", time_basis="test")
    x = payload()
    direct = registry.run("materials.composition_index_recipe", x, context)
    serialized = registry.run_json("materials.composition_index_recipe", x.model_dump_json(), context)
    assert direct.status == serialized.status == "computed"
    assert direct.model_dump() == serialized.model_dump()


def named_payload(method, **changes):
    from matintegrity.models.engineering_correlations import SteelCompositionIndexRecipe

    coefficients = {
        "J": {"product_scale": 2.0},
        "X": {"P": 2.0, "Sb": 3.0, "Sn": 4.0, "As": 5.0},
        "RCS": {"Cr": 1.0, "Mo": 2.0, "V": 3.0},
        "K": {"Pb": 2.0, "Bi": 3.0, "Sb": 4.0},
    }[method]
    values = (
        dict(
            method=method,
            chemistry={
                "Mn": 2.0,
                "Si": 3.0,
                "P": 0.01,
                "Sn": 0.02,
                "Sb": 0.03,
                "As": 0.04,
                "Cr": 1.0,
                "Mo": 2.0,
                "V": 3.0,
                "Pb": 0.05,
                "Bi": 0.06,
            },
            input_mass_basis="mass_percent",
            recipe_mass_basis="mass_percent",
            coefficients=coefficients,
            normalization=2.0 if method == "RCS" else 1.0,
            constant_offset=-0.25 if method == "RCS" else 0.0,
            output_unit="authored_index",
        )
        | changes
    )
    digest = canonical_digest(values)
    return SteelCompositionIndexRecipe(
        **values,
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
                    citation="synthetic named index coefficients",
                    license_id="authored-test",
                    sha256=digest,
                ),
            ),
        ),
    )


@pytest.mark.parametrize("method,expected", [("J", 0.3), ("X", 0.39), ("RCS", 6.75), ("K", 0.4)])
def test_named_index_structure_arithmetic_and_public_exchange(method, expected):
    from matintegrity.models.engineering_correlations import steel_composition_index

    x = named_payload(method)
    assert steel_composition_index(x).values["index_value"] == pytest.approx(expected)
    registry = ModelRegistry()
    registry.register(next(s for s in specifications() if s.model_id == "materials.steel_composition_index"))
    context = RunContext(asset_id="synthetic", location_id="assay", time_basis="test")
    direct = registry.run("materials.steel_composition_index", x, context)
    serialized = registry.run_json("materials.steel_composition_index", x.model_dump_json(), context)
    assert direct.model_dump() == serialized.model_dump()


@pytest.mark.parametrize("method,element", [("J", "Sn"), ("X", "As"), ("RCS", "V"), ("K", "Pb")])
def test_named_index_requires_its_complete_element_set(method, element):
    assay = dict(named_payload(method).chemistry)
    assay.pop(element)
    with pytest.raises(ValueError, match="explicit assays"):
        named_payload(method, chemistry=assay)


def test_named_index_unit_conversion_and_exact_coefficient_membership():
    from matintegrity.models.engineering_correlations import steel_composition_index

    x = named_payload("J")
    ppm = {element: value * 10000 for element, value in x.chemistry.items()}
    assert steel_composition_index(named_payload("J", chemistry=ppm, input_mass_basis="mass_ppm")).values[
        "index_value"
    ] == pytest.approx(0.3)
    with pytest.raises(ValueError, match="coefficient keys"):
        named_payload("J", coefficients={"product_scale": 2.0, "unused": 1.0})
