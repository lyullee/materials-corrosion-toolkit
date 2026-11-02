import numpy as np
import pytest
from pint.errors import DimensionalityError
from pydantic import ValidationError
from scipy.integrate import quad

from matintegrity.contracts import RunContext
from matintegrity.registry import default_registry
from matintegrity.units import absolute_pressure, convert


@pytest.fixture
def registry():
    return default_registry()


@pytest.fixture
def context():
    return RunContext(asset_id="test-asset", location_id="test-location", time_basis="synthetic verification")


def calculate(registry, context, name, payload):
    result = registry.run(name, payload, context)
    assert result.status == "computed"
    return result.values


def test_lame_boundary_tractions_and_hydrostatic_limit(registry, context):
    base = dict(
        inner_radius_m=0.05,
        outer_radius_m=0.1,
        internal_pressure_Pa=2e7,
        external_pressure_Pa=3e6,
        closed_ends=True,
    )
    inner = calculate(registry, context, "mechanics.lame_cylinder", dict(base, evaluation_radius_m=0.05))
    outer = calculate(registry, context, "mechanics.lame_cylinder", dict(base, evaluation_radius_m=0.1))
    assert inner["radial_stress_Pa"] == pytest.approx(-2e7)
    assert outer["radial_stress_Pa"] == pytest.approx(-3e6)
    hydro = calculate(
        registry,
        context,
        "mechanics.lame_cylinder",
        dict(base, internal_pressure_Pa=3e6, evaluation_radius_m=0.075),
    )
    assert hydro["von_mises_Pa"] == pytest.approx(0, abs=1e-8)


def test_coupon_loss_matches_removed_volume_and_annual_exposure(registry, context):
    # 7.85 g removed from 100 cm² of 7850 kg/m³ steel is 0.1 mm mean penetration.
    values = calculate(registry, context, "corrosion.coupon_loss", {
        "mass_loss_kg": 0.00785, "exposed_area_m2": 0.01,
        "density_kg_m3": 7850.0, "duration_s": 365.25 * 86400.0,
    })
    assert values["mean_penetration_m"] == pytest.approx(0.0001)
    assert values["rate_mm_year"] == pytest.approx(0.1)
    assert values["mean_penetration_m"] * 0.01 == pytest.approx(0.00785 / 7850.0)


def test_membrane_converges_to_thick_wall_solution(registry, context):
    errors = []
    for thickness in (0.01, 0.001, 0.0001):
        thin = calculate(
            registry,
            context,
            "mechanics.thin_cylinder",
            dict(
                pressure_difference_Pa=1e6,
                mean_radius_m=1 + thickness / 2,
                wall_thickness_m=thickness,
                allowable_hoop_stress_Pa=2e10,
            ),
        )
        exact = calculate(
            registry,
            context,
            "mechanics.lame_cylinder",
            dict(
                inner_radius_m=1.0,
                outer_radius_m=1 + thickness,
                internal_pressure_Pa=1e6,
                external_pressure_Pa=0.0,
                evaluation_radius_m=1 + thickness / 2,
                closed_ends=True,
            ),
        )
        errors.append(abs(thin["hoop_stress_Pa"] / exact["hoop_stress_Pa"] - 1))
    assert errors[2] < errors[1] / 9 < errors[0] / 81
    assert errors[2] < 1e-4


@pytest.mark.parametrize("exponent", [2.0, 2.000000000001, 3.0, 4.0])
def test_paris_integral_against_independent_quadrature(registry, context, exponent):
    x = dict(
        initial_depth_m=0.001,
        terminal_depth_m=0.008,
        stress_range_Pa=1e8,
        geometry_factor=1.12,
        coefficient_m_cycle_per_Pa_sqrt_m_power=1e-28,
        exponent=exponent,
    )
    result = calculate(registry, context, "fracture.paris_constant_amplitude", x)

    def rate(a):
        return (
            x["coefficient_m_cycle_per_Pa_sqrt_m_power"]
            * (x["geometry_factor"] * x["stress_range_Pa"] * np.sqrt(np.pi * a)) ** exponent
        )

    numeric = quad(lambda a: 1 / rate(a), 0.001, 0.008, epsabs=1e-5)[0]
    assert result["cycles_to_terminal_depth"] == pytest.approx(numeric, rel=1e-10)


def test_waveform_retains_voltage_current_covariance(registry, context):
    varying = calculate(
        registry,
        context,
        "welding.waveform_energy",
        dict(
            time_s=[0.0, 1.0, 2.0],
            voltage_V=[10.0, 30.0, 10.0],
            current_A=[100.0, 300.0, 100.0],
            travel_distance_m=0.02,
            efficiency=1.0,
        ),
    )
    assert varying["arc_energy_J"] == pytest.approx(10000)
    assert varying["arc_energy_J"] != pytest.approx((50 / 3) * (500 / 3) * 2)


def test_units_pressure_basis_and_temperature():
    assert convert(1.0, "mm/year", "m/s") == pytest.approx(0.001 / (365.25 * 86400))
    assert convert(0.0, "degC", "K") == pytest.approx(273.15)
    assert absolute_pressure(1.0, "bar", basis="gauge", ambient_pa=101325) == 201325
    with pytest.raises(ValueError):
        absolute_pressure(1.0, "bar", basis="gauge")
    with pytest.raises(DimensionalityError):
        convert(1.0, "mm", "Pa")


def test_thickness_growth_does_not_silently_become_life(registry, context):
    from matintegrity.units import SECONDS_PER_YEAR

    trend = calculate(
        registry,
        context,
        "corrosion.thickness_trend",
        dict(
            time_s=[0.0, SECONDS_PER_YEAR, 2 * SECONDS_PER_YEAR],
            thickness_m=[0.01, 0.0101, 0.0102],
            method="ols",
        ),
    )
    assert trend["rate_m_s"] < 0
    with pytest.raises(ValidationError):
        registry.run(
            "corrosion.uniform_forecast",
            dict(
                current_thickness_m=0.01,
                required_thickness_m=0.006,
                rate_m_s=trend["rate_m_s"],
                horizon_s=SECONDS_PER_YEAR,
            ),
            context,
        )


def test_no_indication_is_bayesian_information_not_physical_repair(registry, context):
    result = calculate(
        registry,
        context,
        "inspection.no_indication_update",
        dict(prior_weights=[0.5, 0.5], probabilities_of_detection=[0.1, 0.9], coverage_fraction=1.0),
    )
    assert result["posterior_weights"] == pytest.approx([0.9, 0.1])
    assert result["probability_of_no_indication"] == pytest.approx(0.5)


def test_weibull_conditioning_and_exclusive_frequency_conservation(registry, context):
    early = calculate(
        registry,
        context,
        "reliability.weibull_interval",
        dict(shape=2.0, scale_s=100.0, current_age_s=0.0, horizon_s=10.0),
    )
    late = calculate(
        registry,
        context,
        "reliability.weibull_interval",
        dict(shape=2.0, scale_s=100.0, current_age_s=100.0, horizon_s=10.0),
    )
    assert late["probability_given_survival"] > early["probability_given_survival"]
    paths = calculate(
        registry,
        context,
        "reliability.exclusive_paths",
        dict(initiating_frequency_per_s=1e-8, conditional_probabilities=[0.2, 0.3, 0.5]),
    )
    assert sum(paths["path_frequencies_per_s"]) == pytest.approx(1e-8)


def test_invalid_and_out_of_scope_are_explicit(registry, context):
    with pytest.raises(ValidationError):
        registry.run(
            "mechanics.plane_stress",
            dict(stress_x_Pa=float("nan"), stress_y_Pa=0.0, shear_xy_Pa=0.0),
            context,
        )
    with pytest.raises(ValidationError):
        registry.run(
            "corrosion.coupon_loss",
            dict(mass_loss_kg=True, exposed_area_m2=1.0, density_kg_m3=7800.0, duration_s=10.0),
            context,
        )
    result = registry.run(
        "mechanics.thin_cylinder",
        dict(
            pressure_difference_Pa=1e6, mean_radius_m=0.1, wall_thickness_m=0.03, allowable_hoop_stress_Pa=2e8
        ),
        context,
    )
    assert result.status == "out_of_scope" and result.values == {}
    gate = registry.run(
        "reliability.independent_gate",
        dict(probabilities=[0.1, 0.2], gate="OR", independence_declared=False),
        context,
    )
    assert gate.status == "needs_data"
