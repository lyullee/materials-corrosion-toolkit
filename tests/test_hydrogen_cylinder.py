import copy
import json
import math

import numpy as np
import pytest
from scipy.special import jn_zeros

from matintegrity.models.hydrogen import R_J_mol_K
from matintegrity.models.hydrogen_cylinder import HydrogenFiniteCylinder, finite_cylinder_kinetic

EVIDENCE = {"source_id": "authored-test", "origin": "synthetic", "citation": "Synthetic test"}


def inputs(nr=4, nz=5, times=None):
    times = [0.0, 0.2] if times is None else times
    cells = nr * nz
    boundary = lambda name: dict(boundary_id=name, kind="no_flux", evidence=[EVIDENCE])
    return dict(
        material_condition_id="state",
        reference_lattice_id="lattice",
        elapsed_time_origin_id="synthetic-zero",
        radius_m=1.0,
        length_m=2.0,
        radial_cell_count=nr,
        axial_cell_count=nz,
        lattice_site_density_mol_m3=1.0,
        initial_lattice_hydrogen_atoms_mol_m3=[0.2] * cells,
        elapsed_time_s=times,
        uniform_temperature_K=[300.0] * len(times),
        lattice_diffusivity_m2_s=[0.1] * len(times),
        curved_surface_boundary=boundary("curved"),
        lower_end_boundary=boundary("lower"),
        upper_end_boundary=boundary("upper"),
        traps=[],
        maximum_supported_lattice_occupancy=0.9,
        maximum_supported_total_trap_to_lattice_site_ratio=0.05,
        finite_axisymmetric_geometry_reviewed=True,
        azimuthally_uniform_state_reviewed=True,
        fixed_populations_and_uniform_temperature_reviewed=True,
        independent_single_occupancy_and_dilute_trap_regime_reviewed=True,
        negligible_stress_gradient_reviewed=True,
        detailed_balance_rate_ratio_reviewed=True,
    )


def prescribed(x, name, values):
    x[name + "_boundary"].update(
        kind="prescribed_lattice_concentration", lattice_hydrogen_atoms_mol_m3=values
    )


def surface_transfer(x, name, equilibrium, coefficient):
    x[name + "_boundary"].update(
        kind="linear_surface_transfer",
        equilibrium_lattice_hydrogen_atoms_mol_m3=equilibrium,
        transfer_coefficient_m_s=coefficient,
    )


def trap(x, capture=0.7, release=None, initial=0.8, binding=0.0, independent_reviewed=True):
    cells = x["radial_cell_count"] * x["axial_cell_count"]
    result = dict(
        population=dict(
            trap_id="trap",
            material_condition_id="state",
            reference_lattice_id="lattice",
            site_density_mol_m3=0.01,
            binding_energy_J_mol=binding,
            maximum_supported_occupancy=1.0,
            evidence=[EVIDENCE],
        ),
        capture_frequency_per_s=[capture] * len(x["elapsed_time_s"]),
        initial_occupancy=[initial] * cells,
        rate_evidence=[EVIDENCE],
    )
    if release is not None:
        result.update(
            rate_model="independent_frequencies",
            release_frequency_per_s=[release] * len(x["elapsed_time_s"]),
            independent_rate_histories_reviewed=independent_reviewed,
        )
    return result


def run(x):
    result = finite_cylinder_kinetic(HydrogenFiniteCylinder.model_validate_json(json.dumps(x)))
    assert result.status == "computed", result.notes
    return result.values


def test_closed_uniform_cylinder_preserves_concentration_and_total_atom_moles():
    x = inputs()
    values = run(x)
    volume = 2 * math.pi
    assert values["cylinder_volume_m3"] == pytest.approx(volume)
    assert values["final_lattice_hydrogen_atoms_mol_m3"] == pytest.approx([0.2] * 20)
    assert values["hydrogen_inventory_mol"] == pytest.approx([0.2 * volume] * 2)
    assert values["relative_mass_balance_error"] < 1e-12
    assert all(series == [0.0, 0.0] for series in values["inward_surface_flow_mol_s"].values())


def test_axial_linear_steady_state_keeps_end_surfaces_distinct_and_conservative():
    x = inputs(nr=3, nz=8, times=[0.0, 1.0])
    x["lattice_diffusivity_m2_s"] = [0.2, 0.2]
    dz = x["length_m"] / x["axial_cell_count"]
    axial = [0.3 - 0.2 * (index + 0.5) * dz / x["length_m"] for index in range(8)]
    x["initial_lattice_hydrogen_atoms_mol_m3"] = axial * 3
    prescribed(x, "lower_end", [0.3, 0.3])
    prescribed(x, "upper_end", [0.1, 0.1])
    values = run(x)
    assert values["final_lattice_hydrogen_atoms_mol_m3"] == pytest.approx(
        x["initial_lattice_hydrogen_atoms_mol_m3"], abs=1e-12
    )
    expected = 0.2 * (0.3 - 0.1) / 2.0 * math.pi
    assert values["inward_surface_flow_mol_s"]["lower_end"][-1] == pytest.approx(expected)
    assert values["inward_surface_flow_mol_s"]["upper_end"][-1] == pytest.approx(-expected)
    assert values["inward_surface_flow_mol_s"]["curved_surface"] == [0.0, 0.0]
    assert values["relative_mass_balance_error"] < 1e-11


def test_curved_surface_transfer_uses_cylinder_area_and_series_resistance():
    x = inputs(nr=4, nz=3, times=[0.0, 0.1])
    surface_transfer(x, "curved_surface", [0.0, 0.0], [0.05, 0.05])
    values = run(x)
    half_cell = x["radius_m"] / x["radial_cell_count"] / 2
    effective_velocity = 1 / (1 / 0.05 + half_cell / 0.1)
    area = 2 * math.pi * x["radius_m"] * x["length_m"]
    assert values["inward_surface_flow_mol_s"]["curved_surface"][0] == pytest.approx(
        effective_velocity * (0.0 - 0.2) * area
    )
    assert values["cumulative_surface_exchange_mol"]["curved_surface"][-1] < 0
    assert values["relative_mass_balance_error"] < 1e-9


def test_radial_step_volume_mean_matches_bessel_series_and_refines():
    time = 0.05
    roots = jn_zeros(0, 120)
    exact = 0.1 * (1 - 4 * np.sum(np.exp(-(roots**2) * time) / roots**2))
    errors = []
    for nr in (10, 20):
        x = inputs(nr=nr, nz=2, times=[0.0, time])
        x["initial_lattice_hydrogen_atoms_mol_m3"] = [0.0] * (2 * nr)
        x["lattice_diffusivity_m2_s"] = [1.0, 1.0]
        x.update(relative_tolerance=0.005, maximum_step_s=2e-4)
        prescribed(x, "curved_surface", [0.1, 0.1])
        values = run(x)
        errors.append(abs(values["lattice_volume_mean_hydrogen_atoms_mol_m3"][-1] - exact))
        assert values["relative_mass_balance_error"] < 1e-9
    assert errors[1] < errors[0] / 2.5
    assert errors[0] < 0.001


def test_closed_zero_binding_trap_matches_spatially_uniform_analytic_exchange():
    x = inputs(times=[0.0, 1.0])
    x["traps"] = [trap(x)]
    x.update(maximum_step_s=0.01, relative_tolerance=0.01)
    exact = 0.208 / 1.01 + (0.8 - 0.208 / 1.01) * math.exp(-0.7 * 1.01)
    values = run(x)
    assert values["traps"][0]["final_occupancy"] == pytest.approx([exact] * 20, abs=0.002)
    expected_inventory = (0.2 + 0.01 * 0.8) * 2 * math.pi
    assert values["hydrogen_inventory_mol"] == pytest.approx([expected_inventory] * 2, abs=1e-11)


def test_independent_trap_rates_match_closed_reaction_in_finite_cylinder():
    x = inputs(times=[0.0, 1.0])
    x["uniform_temperature_K"] = [300.0, 900.0]
    x["detailed_balance_rate_ratio_reviewed"] = False
    x["traps"] = [trap(x, capture=0.7, release=0.7, binding=1e9)]
    x.update(maximum_step_s=0.01, relative_tolerance=0.01)
    exact = 0.208 / 1.01 + (0.8 - 0.208 / 1.01) * math.exp(-0.7 * 1.01)
    values = run(x)
    assert values["traps"][0]["final_occupancy"] == pytest.approx([exact] * 20, abs=0.002)
    assert values["traps"][0]["rate_model"] == "independent_frequencies"
    assert values["relative_mass_balance_error"] < 1e-10


@pytest.mark.parametrize(
    "key",
    [
        "finite_axisymmetric_geometry_reviewed",
        "azimuthally_uniform_state_reviewed",
        "fixed_populations_and_uniform_temperature_reviewed",
        "independent_single_occupancy_and_dilute_trap_regime_reviewed",
        "negligible_stress_gradient_reviewed",
    ],
)
def test_unreviewed_cylinder_physics_is_not_computed(key):
    x = inputs()
    x[key] = False
    result = finite_cylinder_kinetic(HydrogenFiniteCylinder.model_validate_json(json.dumps(x)))
    assert result.status == "needs_data" and result.values == {}


def test_cylinder_requires_review_for_the_selected_rate_convention():
    x = inputs()
    x["traps"] = [trap(x, release=0.7, independent_reviewed=False)]
    x["detailed_balance_rate_ratio_reviewed"] = False
    result = finite_cylinder_kinetic(HydrogenFiniteCylinder.model_validate_json(json.dumps(x)))
    assert result.status == "needs_data" and result.values == {}


@pytest.mark.parametrize("mutation", ["shape", "boundary_id", "trap_shape", "grid"])
def test_invalid_cylinder_contracts_are_rejected(mutation):
    x = inputs()
    if mutation == "shape":
        x["initial_lattice_hydrogen_atoms_mol_m3"].pop()
    if mutation == "boundary_id":
        x["upper_end_boundary"]["boundary_id"] = "lower"
    if mutation == "trap_shape":
        x["traps"] = [trap(x)]
        x["traps"][0]["initial_occupancy"].pop()
    if mutation == "grid":
        x.update(radial_cell_count=128, axial_cell_count=256)
    with pytest.raises(ValueError):
        HydrogenFiniteCylinder.model_validate(copy.deepcopy(x))


def test_fast_trap_release_remains_bounded_during_temperature_ramp():
    x = inputs(nr=2, nz=2, times=[0.0, 0.01, 0.1])
    x["uniform_temperature_K"] = [300.0, 500.0, 700.0]
    x["traps"] = [trap(x, capture=10.0, initial=0.5, binding=R_J_mol_K * 300 * math.log(20))]
    values = run(x)
    assert min(values["final_lattice_hydrogen_atoms_mol_m3"]) >= 0
    assert all(0 <= value <= 1 for value in values["traps"][0]["final_occupancy"])
    assert values["relative_mass_balance_error"] < 1e-9
