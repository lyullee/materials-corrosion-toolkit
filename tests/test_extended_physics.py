"""Independent balances, identities and missing-observation boundaries."""

import math

import numpy as np
import pytest
from pydantic import ValidationError
from scipy.integrate import quad

from matintegrity.contracts import RunContext
from matintegrity.registry import default_registry


def run(name, **inputs):
    return default_registry().run(
        name,
        inputs,
        RunContext(asset_id="test", location_id="test", time_basis="synthetic mathematical verification"),
    )


def test_diffusion_integral_and_surface_flux_obey_mass_balance():
    d, t, cs = 2e-10, 400.0, 3.0
    scale = math.sqrt(d * t)
    result = run(
        "transport.semi_infinite_diffusion",
        diffusivity_m2_s=d,
        exposure_s=t,
        depth_m=[0.0, 2 * scale, 100 * scale],
        initial_concentration_mol_m3=0.0,
        surface_concentration_mol_m3=cs,
    )
    concentration = result.values["concentration_mol_m3"]
    assert concentration[0] == cs and concentration[-1] == 0
    independent = quad(lambda z: cs * math.erfc(z / (2 * scale)), 0, 20 * scale, epsabs=1e-13)[0]
    assert result.values["integrated_excess_mol_m2"] == pytest.approx(independent)
    assert 2 * t * result.values["surface_flux_mol_m2_s"] == pytest.approx(independent)


def test_diffusion_desorption_is_signed_and_nonnegative_in_concentration():
    result = run(
        "transport.semi_infinite_diffusion",
        diffusivity_m2_s=1e-10,
        exposure_s=100.0,
        depth_m=[0.0, 0.1],
        initial_concentration_mol_m3=3.0,
        surface_concentration_mol_m3=1.0,
    )
    assert result.values["concentration_mol_m3"] == [1.0, 3.0]
    assert result.values["integrated_excess_mol_m2"] < 0


def test_thickness_map_preserves_missing_coverage_and_diagonal_separation():
    result = run(
        "geometry.thickness_grid",
        cell_thickness_m=[[0.005, 0.01], [None, 0.005]],
        cell_size_x_m=0.1,
        cell_size_y_m=0.2,
        reference_thickness_m=0.01,
        reporting_threshold_m=0.006,
    )
    assert result.values["connected_below_threshold_areas_m2"] == pytest.approx([0.02, 0.02])
    assert result.values["observed_fraction"] == 0.75
    assert result.values["missing_area_m2"] == pytest.approx(0.02)
    with pytest.raises(ValidationError):
        run(
            "geometry.thickness_grid",
            cell_thickness_m=[[None]],
            cell_size_x_m=1.0,
            cell_size_y_m=1.0,
            reference_thickness_m=0.01,
            reporting_threshold_m=0.006,
        )


def test_galvanic_current_closes_circuit_and_enforces_linearity():
    inputs = dict(
        anodic_free_potential_V=-0.5,
        cathodic_free_potential_V=-0.4,
        anodic_area_m2=0.01,
        cathodic_area_m2=0.1,
        anodic_polarization_resistance_ohm_m2=0.01,
        cathodic_polarization_resistance_ohm_m2=0.1,
        electrolyte_resistance_ohm=8.0,
        maximum_linear_overpotential_V=0.02,
    )
    result = run("corrosion.galvanic_linear", **inputs)
    assert result.values["coupling_current_A"] == pytest.approx(0.01)
    assert result.values["anodic_overpotential_V"] + result.values[
        "cathodic_overpotential_magnitude_V"
    ] + 8 * result.values["coupling_current_A"] == pytest.approx(0.1)
    assert (
        run("corrosion.galvanic_linear", **(inputs | {"maximum_linear_overpotential_V": 0.001})).status
        == "out_of_scope"
    )


def test_stern_geary_has_explicit_decimal_tafel_units():
    result = run(
        "corrosion.stern_geary",
        anodic_tafel_slope_V_decade=0.12,
        cathodic_tafel_slope_V_decade=0.12,
        area_normalized_resistance_ohm_m2=2.0,
    )
    assert result.values["corrosion_current_density_A_m2"] == pytest.approx(0.06 / math.log(10) / 2)


def test_offset_yield_exact_intersection_and_unbracketed_status():
    inputs = dict(
        engineering_strain=[0.0, 0.001, 0.004],
        engineering_stress_Pa=[0.0, 200e6, 400e6],
        elastic_modulus_Pa=200e9,
        offset_strain=0.002,
    )
    result = run("materials.offset_yield", **inputs)
    assert result.values["offset_yield_stress_Pa"] == pytest.approx(400e6)
    assert run("materials.offset_yield", **(inputs | {"offset_strain": 0.01})).status == "needs_data"


def test_tofd_matches_independent_pythagorean_path_and_backwall_domain():
    separation, depth, speed = 0.04, 0.015, 5900.0
    delay = (2 * math.hypot(separation / 2, depth) - separation) / speed
    inputs = dict(
        probe_index_separation_m=separation,
        longitudinal_sound_speed_m_s=speed,
        delay_from_lateral_wave_s=delay,
        wall_thickness_m=0.025,
    )
    assert run("inspection.tofd_depth", **inputs).values["tip_depth_m"] == pytest.approx(depth)
    assert run("inspection.tofd_depth", **(inputs | {"wall_thickness_m": 0.01})).status == "out_of_scope"


def test_gas_inventory_does_not_misinterpret_cooling_as_a_leak():
    result = run(
        "inspection.gas_pressure_decay",
        rigid_volume_m3=0.1,
        initial_absolute_pressure_Pa=1e6,
        final_absolute_pressure_Pa=0.9e6,
        initial_temperature_K=300.0,
        final_temperature_K=270.0,
        initial_compressibility_factor=1.0,
        final_compressibility_factor=1.0,
        duration_s=100.0,
        reference_pressure_Pa=1e5,
        reference_temperature_K=300.0,
        reference_compressibility_factor=1.0,
    )
    assert result.values["net_molar_outflow_mol_s"] == pytest.approx(0.0, abs=1e-14)


def test_hardness_geometrical_unit_conversion():
    result = run("testing.vickers", test_force_N=9.80665, first_diagonal_m=1e-4, second_diagonal_m=1e-4)
    assert result.values["conventional_HV"] == pytest.approx(185.4367709)
    result = run(
        "testing.brinell", test_force_N=29419.95, ball_diameter_m=0.01, mean_indentation_diameter_m=0.004
    )
    area_mm2 = math.pi * 10 / 2 * (10 - math.sqrt(100 - 16))
    assert result.values["conventional_HBW"] == pytest.approx(3000 / area_mm2)


def test_cylindrical_heat_matches_series_resistances_without_radiation():
    result = run(
        "thermal.cylindrical_layers",
        radii_m=[0.05, 0.1],
        conductivity_W_m_K=[1.0],
        length_m=2.0,
        inner_fluid_temperature_K=400.0,
        ambient_temperature_K=300.0,
        radiative_environment_temperature_K=300.0,
        inner_convection_W_m2_K=100.0,
        outer_convection_W_m2_K=10.0,
        outer_emissivity=0.0,
    )
    resistance = (
        1 / (100 * 2 * math.pi * 0.05 * 2)
        + math.log(2) / (2 * math.pi * 2)
        + 1 / (10 * 2 * math.pi * 0.1 * 2)
    )
    assert result.values["heat_rate_outward_W"] == pytest.approx(100 / resistance)
    assert result.values["outer_balance_residual_W"] == pytest.approx(0.0, abs=1e-7)


def test_radiative_balance_with_colder_inner_boundary():
    result = run(
        "thermal.cylindrical_layers",
        radii_m=[0.05, 0.1],
        conductivity_W_m_K=[0.04],
        length_m=1.0,
        inner_fluid_temperature_K=100.0,
        ambient_temperature_K=300.0,
        radiative_environment_temperature_K=320.0,
        inner_convection_W_m2_K=1000.0,
        outer_convection_W_m2_K=10.0,
        outer_emissivity=0.8,
    )
    assert result.values["heat_rate_outward_W"] < 0
    assert result.values["outer_balance_residual_W"] == pytest.approx(0.0, abs=1e-6)


def test_heat_treatment_requires_simultaneous_continuous_hold():
    result = run(
        "welding.heat_treatment_history",
        time_s=[0.0, 10.0, 20.0, 30.0, 40.0],
        sensor_temperature_K=[[300.0, 900.0, 300.0, 900.0, 300.0], [300.0, 900.0, 300.0, 900.0, 300.0]],
        minimum_hold_temperature_K=600.0,
        maximum_hold_temperature_K=950.0,
    )
    assert np.asarray(result.values["simultaneous_hold_intervals_s"]) == pytest.approx(
        np.array([[5, 15], [25, 35]])
    )
    assert result.values["longest_continuous_hold_s"] == 10
    assert result.values["total_simultaneous_hold_s"] == 20


def test_strain_life_recovers_cycles_and_rejects_extrapolation():
    n = 12345.0
    elastic = 200e9
    strength = 1e9
    ductility = 0.5
    b = -0.1
    c = -0.5
    amplitude = strength / elastic * (2 * n) ** b + ductility * (2 * n) ** c
    inputs = dict(
        strain_amplitude=amplitude,
        elastic_modulus_Pa=elastic,
        fatigue_strength_coefficient_Pa=strength,
        fatigue_strength_exponent=b,
        fatigue_ductility_coefficient=ductility,
        fatigue_ductility_exponent=c,
        minimum_valid_cycles=1.0,
        maximum_valid_cycles=1e8,
    )
    assert run("fatigue.strain_life", **inputs).values["cycles_to_failure"] == pytest.approx(n)
    assert run("fatigue.strain_life", **(inputs | {"minimum_valid_cycles": 1e6})).status == "out_of_scope"
