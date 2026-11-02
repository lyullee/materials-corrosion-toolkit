import pytest

from matintegrity.contracts import RunContext, canonical_digest
from matintegrity.models.engineering_correlations import (
    ConductivityPreheatCorrelation,
    conductivity_preheat_correlation,
)
from matintegrity.registry import default_registry


def request(**updates):
    raw = dict(
        material_condition_id="authored-condition",
        correlation_id="authored-preheat",
        solidus_temperature_K=900,
        thermal_conductivity_W_mK=200,
        conductivity_reference_temperature_K=300,
        reciprocal_conductivity_coefficient_W_m=20000,
        minimum_supported_conductivity_W_mK=100,
        maximum_supported_conductivity_W_mK=400,
        minimum_supported_solidus_temperature_K=500,
        maximum_supported_solidus_temperature_K=1000,
    )
    raw.update(updates)
    digest = canonical_digest(
        ConductivityPreheatCorrelation.model_construct(**raw).model_dump(mode="json", exclude={"basis"})
    )
    return ConductivityPreheatCorrelation(
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
                    citation="Authored conductivity correlation",
                    license_id="authored-test",
                    sha256=digest,
                ),
            ),
        ),
    )


def test_declared_si_coefficient_and_conductivity():
    result = conductivity_preheat_correlation(request())
    assert result.values["temperature_offset_K"] == 100
    assert result.values["correlation_preheat_temperature_K"] == 800


def test_below_ambient_result_is_retained_without_clamping_or_recommendation():
    result = conductivity_preheat_correlation(request(reciprocal_conductivity_coefficient_W_m=160000))
    assert result.values["correlation_preheat_temperature_K"] == 100


@pytest.mark.parametrize("changes", [dict(thermal_conductivity_W_mK=99), dict(solidus_temperature_K=1001)])
def test_no_property_extrapolation(changes):
    result = conductivity_preheat_correlation(request(**changes))
    assert result.status == "out_of_scope"
    assert "correlation_preheat_temperature_K" not in result.values


def test_nonpositive_absolute_temperature_is_withheld():
    result = conductivity_preheat_correlation(request(reciprocal_conductivity_coefficient_W_m=180000))
    assert result.status == "out_of_scope"


def test_nonzero_offset_underflow_is_not_reported_as_zero():
    result = conductivity_preheat_correlation(
        request(
            thermal_conductivity_W_mK=1e308,
            maximum_supported_conductivity_W_mK=1e308,
            reciprocal_conductivity_coefficient_W_m=5e-324,
        )
    )
    assert result.status == "out_of_scope"
    assert "temperature_offset_K" not in result.values


def test_property_support_must_be_ordered():
    with pytest.raises(ValueError, match="supports must be ordered"):
        request(minimum_supported_conductivity_W_mK=401)


def test_registered_python_json_exchange():
    registry = default_registry()
    x = request()
    model = "welding.conductivity_preheat_correlation"
    context = RunContext(asset_id="authored", location_id="location", time_basis="synthetic")
    assert (
        registry.run(model, x, context).model_dump()
        == registry.run_json(model, x.model_dump_json(), context).model_dump()
    )
