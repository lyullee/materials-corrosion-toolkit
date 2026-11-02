import math

import pytest

from matintegrity.models.inspection import (
    GasInventoryEnergy,
    PipeMembraneTestPressure,
    PressureTest,
    gas_expansion_energy,
    pipe_membrane_test_pressure,
    pressure_test,
)


def gas(p1, p2, volume, gamma=2.0):
    return gas_expansion_energy(
        GasInventoryEnergy(
            initial_absolute_pressure_Pa=p1,
            final_absolute_pressure_Pa=p2,
            initial_volume_m3=volume,
            heat_capacity_ratio=gamma,
        )
    )


def test_isentropic_integral_known_gamma_two():
    result = gas(4.0, 1.0, 1.0)
    assert result.values["final_volume_m3"] == pytest.approx(2.0)
    assert result.values["ideal_expansion_work_J"] == pytest.approx(2.0)


def test_pressure_ratio_overflow_does_not_destroy_finite_work_and_volume():
    result = gas(1e300, 1e-300, 1e-300)
    assert result.status == "computed"
    assert result.values["final_volume_m3"] == pytest.approx(1.0, rel=1e-12)
    assert result.values["ideal_expansion_work_J"] == pytest.approx(1.0)


def test_equal_pressure_retains_zero_work_even_if_pressure_volume_overflows():
    assert gas(1e300, 1e300, 1e300).values["ideal_expansion_work_J"] == 0


def test_nearly_equal_pressures_do_not_round_release_to_zero():
    result = gas(math.nextafter(1.0, math.inf), 1.0, 1.0)
    assert result.status == "computed"
    assert result.values["ideal_expansion_work_J"] == pytest.approx(2**-53, rel=1e-14, abs=0)


@pytest.mark.parametrize("args", [(1e300, 1.0, 1e300), (1e-300, 1e-301, 1e-300)])
def test_unrepresentable_gas_outputs_return_status(args):
    assert gas(*args).status == "out_of_scope"


def test_pressure_test_ratio_cancels_intermediate_overflow():
    result = pressure_test(
        PressureTest(
            design_pressure_Pa=1e200,
            declared_test_factor=1e200,
            allowable_at_test_Pa=1e-200,
            allowable_at_design_Pa=1e200,
            fluid_density_kg_m3=0,
            elevation_below_gauge_m=0,
        )
    )
    assert result.status == "computed"
    assert result.values["reference_test_pressure_Pa"] == pytest.approx(1.0)


def test_pressure_test_local_head_is_preserved():
    result = pressure_test(
        PressureTest(
            design_pressure_Pa=100.0,
            declared_test_factor=2.0,
            allowable_at_test_Pa=2.0,
            allowable_at_design_Pa=4.0,
            fluid_density_kg_m3=1000.0,
            elevation_below_gauge_m=2.0,
        )
    )
    assert result.values["local_test_pressure_Pa"] == pytest.approx(100 + 19613.3)


def test_unrepresentable_local_head_returns_status():
    result = pressure_test(
        PressureTest(
            design_pressure_Pa=1.0,
            declared_test_factor=1.0,
            allowable_at_test_Pa=1.0,
            allowable_at_design_Pa=1.0,
            fluid_density_kg_m3=1e308,
            elevation_below_gauge_m=1e308,
        )
    )
    assert result.status == "out_of_scope"


def test_membrane_pressure_avoids_intermediate_product_overflow():
    result = pipe_membrane_test_pressure(
        PipeMembraneTestPressure(
            outside_diameter_m=1e200,
            wall_thickness_m=1e199,
            yield_strength_Pa=1e200,
            declared_yield_fraction=0.5,
            factor_basis="authored",
            geometry_material_and_factor_applicability_reviewed=True,
        )
    )
    assert result.status == "computed"
    assert result.values["membrane_test_pressure_difference_Pa"] == pytest.approx(1e199)
