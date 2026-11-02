import pytest

from matintegrity.contracts import RunContext, canonical_digest
from matintegrity.models.composition_temperature import (
    CompositionSupportRange,
    CompositionTemperatureCorrelation,
    composition_temperature_correlation,
)
from matintegrity.models.engineering_correlations import CompositionIndexTerm
from matintegrity.registry import default_registry


def request(**updates):
    raw = dict(
        index_id="authored-temperature",
        chemistry={"A": 0.125, "B": 0.015625, "C": 0.015625},
        input_mass_basis="mass_fraction",
        recipe_mass_basis="mass_percent",
        output_unit="degC",
        constant_offset=20.0,
        terms=(CompositionIndexTerm(term_id="a", coefficient=2.0, factors=(dict(element_id="A"),)),),
        material_condition_id="condition",
        temperature_quantity_id="caller_endpoint",
        calibration_population_id="authored-only",
        correlation_revision_id="1",
        composition_support=(
            CompositionSupportRange(support_id="A", element_ids=("A",), minimum_sum=0.0, maximum_sum=20.0),
            CompositionSupportRange(
                support_id="B+C", element_ids=("B", "C"), minimum_sum=0.0, maximum_sum=3.125
            ),
        ),
        correlation_and_composition_support_reviewed=True,
    )
    raw.update(updates)
    digest = canonical_digest(
        CompositionTemperatureCorrelation.model_construct(**raw).model_dump(mode="json", exclude={"basis"})
    )
    return CompositionTemperatureCorrelation(
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
                    citation="Authored thermal recipe",
                    license_id="authored-test",
                    sha256=digest,
                ),
            ),
        ),
    )


def test_composition_units_and_explicit_sum_support_boundary():
    result = composition_temperature_correlation(request())
    assert result.status == "computed"
    assert result.values["predicted_temperature_K"] == pytest.approx(318.15)
    assert result.values["recipe_temperature_value"] == 45.0
    assert composition_temperature_correlation(
        request(input_mass_basis="mass_percent", chemistry={"A": 12.5, "B": 1.5625, "C": 1.5625})
    ).values == result.values | {
        "record_sha256": request(
            input_mass_basis="mass_percent", chemistry={"A": 12.5, "B": 1.5625, "C": 1.5625}
        ).basis.record_sha256
    }


@pytest.mark.parametrize(
    "unit,constant,expected", [("K", 300.0, 300.0), ("degC", 0.0, 273.15), ("degF", 68.0, 293.15)]
)
def test_temperature_origins(unit, constant, expected):
    term = CompositionIndexTerm(term_id="zero", coefficient=0.0, factors=(dict(element_id="A"),))
    result = composition_temperature_correlation(
        request(output_unit=unit, constant_offset=constant, terms=(term,))
    )
    assert result.status == "computed"
    assert result.values["predicted_temperature_K"] == pytest.approx(expected, rel=1e-14)


def test_outside_sum_support_does_not_extrapolate():
    result = composition_temperature_correlation(request(chemistry={"A": 0.125, "B": 0.03125, "C": 0.015625}))
    assert result.status == "out_of_scope"
    assert result.values["outside_support_ids"] == ["B+C"]
    assert "predicted_temperature_K" not in result.values


def test_unreviewed_correlation_and_nonpositive_kelvin_withheld():
    assert (
        composition_temperature_correlation(
            request(correlation_and_composition_support_reviewed=False)
        ).status
        == "needs_data"
    )
    assert composition_temperature_correlation(request(constant_offset=-400.0)).status == "out_of_scope"


def test_required_recipe_elements_need_support_and_assay():
    with pytest.raises(ValueError, match="every recipe element"):
        request(composition_support=(request().composition_support[1],))
    with pytest.raises(ValueError, match="measured chemistry"):
        request(chemistry={"A": 0.125})


def test_registry_exchange_and_digest():
    x = request()
    registry = default_registry()
    model = "materials.composition_temperature_correlation"
    context = RunContext(asset_id="asset", location_id="location", time_basis="synthetic")
    assert (
        registry.run(model, x.model_dump(), context).values
        == registry.run_json(model, x.model_dump_json(), context).values
    )
    raw = x.model_dump()
    raw["output_unit"] = "K"
    with pytest.raises(ValueError, match="pin the complete"):
        CompositionTemperatureCorrelation(**raw)


@pytest.mark.parametrize("denominator,status", [(0.015625, "computed"), (0.0, "out_of_scope")])
def test_reciprocal_temperature_registry_exchange(denominator, status):
    term = CompositionIndexTerm(
        term_id="ratio", coefficient=2, factors=(dict(element_id="A"), dict(element_id="B", power=-1))
    )
    x = request(chemistry={"A": 0.125, "B": denominator, "C": 0.015625}, terms=(term,))
    registry = default_registry()
    context = RunContext(asset_id="asset", location_id="location", time_basis="synthetic")
    model = "materials.composition_temperature_correlation"
    direct = registry.run(model, x, context)
    encoded = registry.run_json(model, x.model_dump_json(), context)
    assert direct.model_dump() == encoded.model_dump()
    assert direct.model_version == "1.0.1"
    assert direct.status == status
    if status == "computed":
        assert direct.values["predicted_temperature_K"] == pytest.approx(309.15)
    else:
        assert "predicted_temperature_K" not in direct.values
