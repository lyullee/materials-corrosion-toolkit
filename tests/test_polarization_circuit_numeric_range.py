import math

import pytest

from matintegrity.contracts import RunContext
from matintegrity.models.degradation import GalvanicLinear, SternGeary, galvanic_linear, stern_geary
from matintegrity.registry import default_registry


def galvanic(**updates):
    raw = dict(
        anodic_free_potential_V=-0.4,
        cathodic_free_potential_V=-0.2,
        anodic_area_m2=0.01,
        cathodic_area_m2=0.1,
        anodic_polarization_resistance_ohm_m2=0.02,
        cathodic_polarization_resistance_ohm_m2=0.1,
        electrolyte_resistance_ohm=0.5,
        maximum_linear_overpotential_V=0.2,
    )
    return GalvanicLinear(**(raw | updates))


def test_equal_tafel_slopes_preserve_small_nonzero_coefficient_and_scaled_current():
    slope = 1e-320
    result = stern_geary(
        SternGeary(
            anodic_tafel_slope_V_decade=slope,
            cathodic_tafel_slope_V_decade=slope,
            area_normalized_resistance_ohm_m2=1e-100,
        )
    )
    assert result.status == "computed"
    assert result.values["stern_geary_coefficient_V"] == slope / (2 * math.log(10))
    assert result.values["corrosion_current_density_A_m2"] == pytest.approx(
        slope / (2 * math.log(10) * 1e-100), rel=1e-14, abs=0.0
    )


@pytest.mark.parametrize("slope,resistance", [(5e-324, 1.0), (1.0, 1e-320), (1e-20, 1e308)])
def test_unrepresentable_required_stern_geary_output_is_not_zero(slope, resistance):
    result = stern_geary(
        SternGeary(
            anodic_tafel_slope_V_decade=slope,
            cathodic_tafel_slope_V_decade=slope,
            area_normalized_resistance_ohm_m2=resistance,
        )
    )
    assert result.status == "out_of_scope"
    assert "corrosion_current_density_A_m2" not in result.values


def test_galvanic_series_resistance_sum_can_exceed_float_range():
    x = galvanic(
        anodic_free_potential_V=0.0,
        cathodic_free_potential_V=1.0,
        anodic_area_m2=1e-308,
        cathodic_area_m2=1e-308,
        anodic_polarization_resistance_ohm_m2=1.0,
        cathodic_polarization_resistance_ohm_m2=1.0,
        electrolyte_resistance_ohm=0.0,
        maximum_linear_overpotential_V=1.0,
    )
    result = galvanic_linear(x)
    assert result.status == "computed"
    assert result.values["coupling_current_A"] == pytest.approx(5e-309, rel=1e-14, abs=5e-324)
    assert result.values["anodic_current_density_A_m2"] == pytest.approx(0.5)
    assert result.values["anodic_overpotential_V"] == pytest.approx(0.5)


def test_potential_difference_overflow_does_not_erase_finite_circuit_solution():
    result = galvanic_linear(
        galvanic(
            anodic_free_potential_V=-1e308,
            cathodic_free_potential_V=1e308,
            anodic_area_m2=1.0,
            cathodic_area_m2=1.0,
            anodic_polarization_resistance_ohm_m2=1.0,
            cathodic_polarization_resistance_ohm_m2=1.0,
            electrolyte_resistance_ohm=1e308,
            maximum_linear_overpotential_V=3.0,
        )
    )
    assert result.status == "computed"
    assert result.values["coupling_current_A"] == pytest.approx(2.0)


def test_roles_equal_potential_and_declared_linear_bound():
    assert (
        galvanic_linear(galvanic(anodic_free_potential_V=1.0, cathodic_free_potential_V=0.0)).status
        == "out_of_scope"
    )
    zero = galvanic_linear(galvanic(cathodic_free_potential_V=-0.4))
    assert zero.status == "computed"
    assert all(value == 0.0 for value in zero.values.values())
    assert galvanic_linear(galvanic(maximum_linear_overpotential_V=0.01)).status == "out_of_scope"


@pytest.mark.parametrize(
    "model,x",
    [
        (
            "corrosion.stern_geary",
            SternGeary(
                anodic_tafel_slope_V_decade=0.12,
                cathodic_tafel_slope_V_decade=0.06,
                area_normalized_resistance_ohm_m2=0.2,
            ),
        ),
        ("corrosion.galvanic_linear", galvanic()),
    ],
)
def test_registry_python_json_exchange(model, x):
    registry = default_registry()
    context = RunContext(asset_id="asset", location_id="location", time_basis="synthetic")
    assert (
        registry.run(model, x.model_dump(), context).values
        == registry.run_json(model, x.model_dump_json(), context).values
    )
