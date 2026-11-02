import pytest

from matintegrity.contracts import RunContext, canonical_digest
from matintegrity.models.engineering_correlations import (
    DeclaredTemperatureRateFactor,
    declared_temperature_rate_factor,
)
from matintegrity.registry import default_registry


def request(**updates):
    raw = dict(
        material_condition_id="authored-condition",
        mechanism_id="authored-rate",
        temperature_K=310,
        reference_temperature_K=300,
        temperature_increment_K=10,
        rate_factor_per_increment=2,
        minimum_supported_temperature_K=200,
        maximum_supported_temperature_K=400,
    )
    raw.update(updates)
    digest = canonical_digest(
        DeclaredTemperatureRateFactor.model_construct(**raw).model_dump(mode="json", exclude={"basis"})
    )
    return DeclaredTemperatureRateFactor(
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
                    citation="Authored rate multiplier",
                    license_id="authored-test",
                    sha256=digest,
                ),
            ),
        ),
    )


@pytest.mark.parametrize("temperature,expected", [(300, 1), (310, 2), (290, 0.5), (305, 2**0.5)])
def test_declared_temperature_steps(temperature, expected):
    result = declared_temperature_rate_factor(request(temperature_K=temperature))
    assert result.values["equivalent_time_rate_multiplier"] == pytest.approx(expected)


def test_rate_may_decrease_with_increasing_temperature_when_explicitly_declared():
    assert declared_temperature_rate_factor(request(rate_factor_per_increment=0.5)).values[
        "equivalent_time_rate_multiplier"
    ] == pytest.approx(0.5)


def test_unsupported_temperature_is_not_extrapolated():
    result = declared_temperature_rate_factor(request(temperature_K=401))
    assert result.status == "out_of_scope"
    assert "equivalent_time_rate_multiplier" not in result.values


@pytest.mark.parametrize("temperature", [200, 400])
def test_unrepresentable_factor_withheld(temperature):
    result = declared_temperature_rate_factor(
        request(temperature_K=temperature, temperature_increment_K=1e-308)
    )
    assert result.status == "out_of_scope"
    assert "equivalent_time_rate_multiplier" not in result.values


def test_unity_rate_is_constant_even_for_tiny_temperature_increment():
    result = declared_temperature_rate_factor(
        request(temperature_increment_K=5e-324, rate_factor_per_increment=1)
    )
    assert result.values["equivalent_time_rate_multiplier"] == 1


def test_reference_must_be_inside_support():
    with pytest.raises(ValueError, match="reference temperature"):
        request(reference_temperature_K=500)


def test_registered_python_json_exchange():
    registry = default_registry()
    x = request()
    context = RunContext(asset_id="authored", location_id="location", time_basis="synthetic")
    model = "degradation.declared_temperature_rate_factor"
    assert (
        registry.run(model, x, context).model_dump()
        == registry.run_json(model, x.model_dump_json(), context).model_dump()
    )
