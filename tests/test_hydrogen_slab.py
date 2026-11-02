import copy
import json
import math

import numpy as np
import pytest
from scipy.integrate import solve_ivp

from matintegrity.models.hydrogen import HydrogenPartition, R_J_mol_K, partition
from matintegrity.models.hydrogen_kinetics import HydrogenSlab, slab_kinetic

EVIDENCE = {"source_id": "authored-test", "origin": "synthetic", "citation": "Independent synthetic test"}


def inputs(cells=4, times=None):
    times = [0.0, 1.0] if times is None else times
    return dict(
        material_condition_id="state",
        reference_lattice_id="lattice",
        elapsed_time_origin_id="synthetic-zero",
        thickness_m=1.0,
        cell_count=cells,
        lattice_site_density_mol_m3=1.0,
        initial_lattice_hydrogen_atoms_mol_m3=[0.2] * cells,
        elapsed_time_s=times,
        uniform_temperature_K=[300.0] * len(times),
        lattice_diffusivity_m2_s=[0.1] * len(times),
        left_boundary=dict(boundary_id="left", kind="no_flux", evidence=[EVIDENCE]),
        right_boundary=dict(boundary_id="right", kind="no_flux", evidence=[EVIDENCE]),
        traps=[],
        maximum_supported_lattice_occupancy=0.9,
        maximum_supported_total_trap_to_lattice_site_ratio=0.05,
        planar_geometry_reviewed=True,
        fixed_populations_and_uniform_temperature_reviewed=True,
        independent_single_occupancy_and_dilute_trap_regime_reviewed=True,
        negligible_stress_gradient_reviewed=True,
        detailed_balance_rate_ratio_reviewed=True,
    )


def trap(
    x,
    *,
    density=0.01,
    binding=0.0,
    capture=0.7,
    release=None,
    initial=0.8,
    name="trap",
    independent_reviewed=True,
):
    result = dict(
        population=dict(
            trap_id=name,
            material_condition_id=x["material_condition_id"],
            reference_lattice_id=x["reference_lattice_id"],
            site_density_mol_m3=density,
            binding_energy_J_mol=binding,
            maximum_supported_occupancy=1.0,
            evidence=[EVIDENCE],
        ),
        capture_frequency_per_s=[capture] * len(x["elapsed_time_s"]),
        initial_occupancy=[initial] * x["cell_count"],
        rate_evidence=[EVIDENCE],
    )
    if release is not None:
        result.update(
            rate_model="independent_frequencies",
            release_frequency_per_s=[release] * len(x["elapsed_time_s"]),
            independent_rate_histories_reviewed=independent_reviewed,
        )
    return result


def prescribed(x, side, values):
    x[side + "_boundary"].update(
        kind="prescribed_lattice_concentration", lattice_hydrogen_atoms_mol_m3=values
    )


def surface_transfer(x, side, equilibrium, coefficient):
    x[side + "_boundary"].update(
        kind="linear_surface_transfer",
        equilibrium_lattice_hydrogen_atoms_mol_m3=equilibrium,
        transfer_coefficient_m_s=coefficient,
    )


def run(x):
    result = slab_kinetic(HydrogenSlab.model_validate_json(json.dumps(x)))
    assert result.status == "computed", result.notes
    return result.values


def test_closed_zero_binding_exchange_matches_analytic_reaction_and_time_refinement():
    exact = 0.208 / 1.01 + (0.8 - 0.208 / 1.01) * math.exp(-0.7 * 1.01)
    errors = []
    for step in [0.04, 0.02, 0.01]:
        x = inputs(cells=2)
        x.update(traps=[trap(x)], maximum_step_s=step, relative_tolerance=0.01)
        values = run(x)
        observed = values["traps"][0]["final_occupancy"][0]
        errors.append(abs(observed - exact))
        assert values["hydrogen_inventory_mol_m2"] == pytest.approx([0.208, 0.208], abs=1e-13)
        assert values["final_lattice_hydrogen_atoms_mol_m3"][0] == pytest.approx(
            0.208 - 0.01 * observed, abs=1e-13
        )
    assert errors[0] / errors[1] > 1.8 and errors[1] / errors[2] > 1.8


def test_independent_equal_rates_match_analytic_exchange_and_ignore_binding_temperature():
    x = inputs(cells=2)
    x["uniform_temperature_K"] = [300.0, 900.0]
    x["detailed_balance_rate_ratio_reviewed"] = False
    x["traps"] = [trap(x, binding=1e9, capture=0.7, release=0.7)]
    x.update(maximum_step_s=0.01, relative_tolerance=0.01)
    exact = 0.208 / 1.01 + (0.8 - 0.208 / 1.01) * math.exp(-0.7 * 1.01)
    values = run(x)
    assert values["traps"][0]["final_occupancy"] == pytest.approx([exact] * 2, abs=0.002)
    assert values["traps"][0]["rate_model"] == "independent_frequencies"
    assert len(values["traps"][0]["rate_history_digest"]) == 64
    assert values["relative_mass_balance_error"] < 1e-10


def test_independent_release_can_be_nonzero_when_capture_is_zero():
    x = inputs(times=[0.0, 0.2])
    x["detailed_balance_rate_ratio_reviewed"] = False
    x["traps"] = [trap(x, capture=0.0, release=1.0)]
    values = run(x)
    assert values["traps"][0]["final_occupancy"][0] < 0.8
    assert values["lattice_mean_hydrogen_atoms_mol_m3"][-1] > 0.2
    assert values["hydrogen_inventory_mol_m2"] == pytest.approx([0.208, 0.208], abs=1e-12)


def cell_average_step_solution(cells, time):
    centers = (np.arange(cells) + 0.5) / cells
    modes = np.arange(1, 161)[:, None]
    average_sine = np.sin(math.pi * modes * centers) * np.sinc(modes / (2 * cells))
    return 0.1 * (
        1
        - centers
        - np.sum(2 / (math.pi * modes) * average_sine * np.exp(-(math.pi**2) * modes**2 * time), axis=0)
    )


def test_untrapped_slab_matches_fourier_cell_averages_and_mesh_refinement():
    errors = []
    for cells in [12, 24]:
        x = inputs(cells=cells, times=[0.0, 0.1])
        x.update(
            initial_lattice_hydrogen_atoms_mol_m3=[0.0] * cells,
            lattice_diffusivity_m2_s=[1.0, 1.0],
            maximum_step_s=1e-4,
            relative_tolerance=0.01,
        )
        prescribed(x, "left", [0.1, 0.1])
        prescribed(x, "right", [0.0, 0.0])
        values = run(x)
        errors.append(
            float(
                np.max(
                    np.abs(
                        np.asarray(values["final_lattice_hydrogen_atoms_mol_m3"])
                        - cell_average_step_solution(cells, 0.1)
                    )
                )
            )
        )
        assert values["relative_mass_balance_error"] < 1e-9
        modes = np.arange(1, 161)
        exact_outward = 0.1 * (1 + 2 * np.sum((-1.0) ** modes * np.exp(-(math.pi**2) * modes**2 * 0.1)))
        assert -values["right_inward_flux_mol_m2_s"][-1] == pytest.approx(exact_outward, rel=0.02)
    assert errors[1] < errors[0] / 2.5 and errors[0] < 0.001


def test_two_traps_temperature_history_matches_independent_reduced_ode():
    times = [0.0, 0.4, 1.0, 2.0]
    x = inputs(cells=3, times=times)
    x["uniform_temperature_K"] = [300.0, 350.0, 450.0, 600.0]
    x["initial_lattice_hydrogen_atoms_mol_m3"] = [0.1] * 3
    x["traps"] = [
        trap(x, binding=R_J_mol_K * 300 * math.log(3), capture=1.0, initial=0.5, name="one"),
        trap(x, density=0.02, binding=R_J_mol_K * 300 * math.log(20), capture=3.0, initial=0.2, name="two"),
    ]
    x["traps"][0]["capture_frequency_per_s"] = [1.0, 2.0, 1.5, 1.0]
    x.update(relative_tolerance=1e-6, absolute_occupancy_tolerance=1e-11)
    total = 0.1 + 0.01 * 0.5 + 0.02 * 0.2

    def ode(time, occupancy):
        lattice = total - np.dot([0.01, 0.02], occupancy)
        temperature = np.interp(time, times, x["uniform_temperature_K"])
        capture = np.asarray([np.interp(time, times, t["capture_frequency_per_s"]) for t in x["traps"]])
        release = capture * np.exp(
            -np.asarray([t["population"]["binding_energy_J_mol"] for t in x["traps"]])
            / (R_J_mol_K * temperature)
        )
        return capture * lattice * (1 - occupancy) - release * occupancy * (1 - lattice)

    expected = solve_ivp(ode, [0, 2], [0.5, 0.2], method="DOP853", t_eval=times, atol=1e-13, rtol=1e-11)
    assert expected.success
    values = run(x)
    observed = (
        np.asarray([t["mean_hydrogen_atoms_mol_m3"] for t in values["traps"]])
        / np.asarray([0.01, 0.02])[:, None]
    )
    np.testing.assert_allclose(observed, expected.y, atol=0.0003, rtol=0)
    np.testing.assert_allclose(values["hydrogen_inventory_mol_m2"], total, atol=1e-12, rtol=0)
    assert values["cumulative_left_exchange_mol_m2"] == [0.0] * len(times)


def test_fast_kinetics_reaches_independently_solved_oriani_partition():
    x = inputs(cells=3, times=[0.0, 0.001, 1.0])
    x["initial_lattice_hydrogen_atoms_mol_m3"] = [0.05] * 3
    x["traps"] = [trap(x, binding=R_J_mol_K * 300 * math.log(100), capture=1e5, initial=0.0)]
    expected = partition(
        HydrogenPartition.model_validate_json(
            json.dumps(
                dict(
                    material_condition_id="state",
                    reference_lattice_id="lattice",
                    total_hydrogen_atoms_mol_m3=0.05,
                    lattice_site_density_mol_m3=1.0,
                    lattice_diffusivity_m2_s=0.1,
                    temperature_K=300.0,
                    maximum_supported_lattice_occupancy=0.9,
                    traps=[x["traps"][0]["population"]],
                    local_equilibrium_confirmed=True,
                    independent_single_occupancy_sites_confirmed=True,
                    fixed_trap_population_and_uniform_temperature_confirmed=True,
                )
            )
        )
    )
    assert expected.status == "computed"
    values = run(x)
    assert values["final_lattice_hydrogen_atoms_mol_m3"] == pytest.approx(
        [expected.values["lattice_hydrogen_atoms_mol_m3"]] * 3, abs=1e-7
    )
    assert values["traps"][0]["final_occupancy"] == pytest.approx(
        [expected.values["traps"][0]["occupancy"]] * 3, abs=1e-5
    )


def test_frozen_population_does_not_exchange_even_during_temperature_change():
    x = inputs(times=[0.0, 0.5, 1.0])
    x["uniform_temperature_K"] = [300.0, 400.0, 600.0]
    x["traps"] = [trap(x, capture=0.0)]
    values = run(x)
    assert values["traps"][0]["final_occupancy"] == [0.8] * 4
    assert values["lattice_mean_hydrogen_atoms_mol_m3"] == [0.2] * 3


def test_fast_initial_relaxation_remains_resolvable_with_a_distant_output_time():
    x = inputs(cells=2, times=[0.0, 1e8])
    x["traps"] = [trap(x, capture=1e10)]
    values = run(x)
    equilibrium = 0.208 / 1.01
    assert values["traps"][0]["final_occupancy"] == pytest.approx([equilibrium] * 2, abs=1e-10)
    assert values["solver"]["minimum_accepted_substep_s"] < 1e-10
    assert values["solver"]["step_attempts"] < 10000
    assert values["relative_mass_balance_error"] < 1e-9


def test_boundary_reflection_preserves_profiles_and_swaps_signed_exchanges():
    x = inputs(cells=8)
    x["initial_lattice_hydrogen_atoms_mol_m3"] = np.linspace(0.1, 0.2, 8).tolist()
    prescribed(x, "left", [0.3, 0.25])
    x["traps"] = [trap(x, capture=2.0, binding=2000.0, initial=0.0)]
    reflected = copy.deepcopy(x)
    reflected["initial_lattice_hydrogen_atoms_mol_m3"].reverse()
    reflected["left_boundary"], reflected["right_boundary"] = (
        reflected["right_boundary"],
        reflected["left_boundary"],
    )
    forward, backward = run(x), run(reflected)
    np.testing.assert_allclose(
        forward["final_lattice_hydrogen_atoms_mol_m3"],
        backward["final_lattice_hydrogen_atoms_mol_m3"][::-1],
        atol=1e-12,
    )
    assert forward["cumulative_left_exchange_mol_m2"] == pytest.approx(
        backward["cumulative_right_exchange_mol_m2"], abs=1e-12
    )
    assert forward["cumulative_right_exchange_mol_m2"] == [0.0, 0.0]


def test_throughflow_exchange_error_is_controlled_when_state_is_stationary():
    x = inputs(cells=4)
    x["initial_lattice_hydrogen_atoms_mol_m3"] = (0.3 - 0.2 * (np.arange(4) + 0.5) / 4).tolist()
    x["lattice_diffusivity_m2_s"] = [0.1, 0.3]
    prescribed(x, "left", [0.3, 0.3])
    prescribed(x, "right", [0.1, 0.1])
    x.update(relative_tolerance=1e-6, absolute_occupancy_tolerance=1e-12)
    values = run(x)
    assert values["final_lattice_hydrogen_atoms_mol_m3"] == pytest.approx(
        x["initial_lattice_hydrogen_atoms_mol_m3"], abs=1e-12
    )
    expected = 0.2 * (0.1 + 0.3) / 2
    assert values["cumulative_left_exchange_mol_m2"][-1] == pytest.approx(expected, rel=0.002)
    assert values["cumulative_right_exchange_mol_m2"][-1] == pytest.approx(-expected, rel=0.002)
    assert values["solver"]["accepted_step_pairs"] > 50


def test_linear_surface_transfer_keeps_film_and_half_cell_resistances_in_series():
    x = inputs(cells=4, times=[0.0, 0.1])
    surface_transfer(x, "left", [0.0, 0.0], [0.05, 0.05])
    values = run(x)
    dx = x["thickness_m"] / x["cell_count"]
    effective_velocity = 1 / (1 / 0.05 + dx / (2 * 0.1))
    assert values["left_inward_flux_mol_m2_s"][0] == pytest.approx(effective_velocity * (0.0 - 0.2))
    assert values["cumulative_left_exchange_mol_m2"][-1] < 0
    assert values["relative_mass_balance_error"] < 1e-9


@pytest.mark.parametrize(
    "updates",
    [
        {"kind": "linear_surface_transfer"},
        {
            "kind": "linear_surface_transfer",
            "equilibrium_lattice_hydrogen_atoms_mol_m3": [0.0, 0.0],
        },
        {
            "kind": "linear_surface_transfer",
            "equilibrium_lattice_hydrogen_atoms_mol_m3": [0.0, 0.0],
            "transfer_coefficient_m_s": [0.1],
        },
    ],
)
def test_linear_surface_transfer_requires_aligned_equilibrium_and_coefficient_histories(updates):
    x = inputs()
    x["left_boundary"].update(updates)
    with pytest.raises(ValueError):
        HydrogenSlab.model_validate_json(json.dumps(x))


def test_nonuniform_closed_cells_conserve_total_inventory_under_diffusion_and_trapping():
    x = inputs(cells=10)
    x["initial_lattice_hydrogen_atoms_mol_m3"] = np.linspace(0.0, 0.3, 10).tolist()
    x["traps"] = [trap(x, capture=10.0, binding=1000.0, initial=0.0)]
    values = run(x)
    assert values["hydrogen_inventory_mol_m2"] == pytest.approx([0.15, 0.15], abs=1e-11)
    assert min(values["final_lattice_hydrogen_atoms_mol_m3"]) >= 0
    assert values["relative_mass_balance_error"] < 1e-9


def test_profile_storage_keeps_initial_and_final_states_with_explicit_units():
    x = inputs(cells=3)
    x["store_profiles"] = True
    x["traps"] = [trap(x, initial=0.0)]
    values = run(x)
    assert values["lattice_profiles_hydrogen_atoms_mol_m3"][0] == [0.2] * 3
    assert (
        values["lattice_profiles_hydrogen_atoms_mol_m3"][-1] == values["final_lattice_hydrogen_atoms_mol_m3"]
    )
    assert values["traps"][0]["occupancy_profiles"][-1] == values["traps"][0]["final_occupancy"]


@pytest.mark.parametrize(
    "key",
    [
        "planar_geometry_reviewed",
        "fixed_populations_and_uniform_temperature_reviewed",
        "independent_single_occupancy_and_dilute_trap_regime_reviewed",
        "negligible_stress_gradient_reviewed",
    ],
)
def test_unreviewed_physics_is_not_a_success(key):
    x = inputs()
    x[key] = False
    result = slab_kinetic(HydrogenSlab.model_validate_json(json.dumps(x)))
    assert result.status == "needs_data" and result.values == {}


def test_selected_rate_convention_must_be_reviewed():
    detailed = inputs()
    detailed["traps"] = [trap(detailed)]
    detailed["detailed_balance_rate_ratio_reviewed"] = False
    result = slab_kinetic(HydrogenSlab.model_validate_json(json.dumps(detailed)))
    assert result.status == "needs_data" and result.values == {}

    independent = inputs()
    independent["detailed_balance_rate_ratio_reviewed"] = False
    independent["traps"] = [trap(independent, release=0.7, independent_reviewed=False)]
    result = slab_kinetic(HydrogenSlab.model_validate_json(json.dumps(independent)))
    assert result.status == "needs_data" and result.values == {}


@pytest.mark.parametrize("mutation", ["missing", "length", "mixed", "contradictory_review"])
def test_rate_mode_contract_rejects_contradictory_or_misaligned_histories(mutation):
    x = inputs()
    candidate = trap(x, release=0.7)
    if mutation == "missing":
        candidate.pop("release_frequency_per_s")
    if mutation == "length":
        candidate["release_frequency_per_s"] = [0.7]
    if mutation == "mixed":
        candidate["rate_model"] = "binding_energy_ratio"
        candidate["independent_rate_histories_reviewed"] = False
    if mutation == "contradictory_review":
        candidate["rate_model"] = "binding_energy_ratio"
        candidate.pop("release_frequency_per_s")
    x["traps"] = [candidate]
    with pytest.raises(ValueError):
        HydrogenSlab.model_validate_json(json.dumps(x))


def test_occupancy_support_is_checked_during_the_trajectory():
    x = inputs()
    x["traps"] = [trap(x, capture=100.0, binding=10000.0, initial=0.0)]
    x["traps"][0]["population"]["maximum_supported_occupancy"] = 0.2
    result = slab_kinetic(HydrogenSlab.model_validate_json(json.dumps(x)))
    assert result.status == "out_of_scope" and "occupancy support" in result.notes[0]


@pytest.mark.parametrize("mutation", ["clock", "shape", "reference", "boundary", "duplicate"])
def test_invalid_identity_clock_and_boundary_contracts_are_rejected(mutation):
    x = inputs()
    x["traps"] = [trap(x)]
    if mutation == "clock":
        x["elapsed_time_s"] = [0.0, 0.0]
    if mutation == "shape":
        x["traps"][0]["capture_frequency_per_s"] = [1.0]
    if mutation == "reference":
        x["traps"][0]["population"]["reference_lattice_id"] = "another"
    if mutation == "boundary":
        x["left_boundary"]["lattice_hydrogen_atoms_mol_m3"] = [0.0, 0.0]
    if mutation == "duplicate":
        x["traps"].append(copy.deepcopy(x["traps"][0]))
    with pytest.raises(ValueError):
        HydrogenSlab.model_validate_json(json.dumps(x))


def test_exhausted_time_budget_returns_partial_status_without_full_trajectory():
    x = inputs()
    x["maximum_step_attempts"] = 1
    result = slab_kinetic(HydrogenSlab.model_validate_json(json.dumps(x)))
    assert result.status == "out_of_scope" and result.values["completed_elapsed_time_s"] < 1
    assert "hydrogen_inventory_mol_m2" not in result.values


@pytest.mark.parametrize(
    "case",
    [
        "site_ratio",
        "initial",
        "boundary",
        "length_underflow",
        "length_overflow",
        "release_underflow",
        "frequency_underflow",
    ],
)
def test_physical_or_numerical_scope_failures_remain_explicit(case):
    x = inputs()
    if case == "site_ratio":
        x["traps"] = [trap(x, density=0.1)]
    if case == "initial":
        x["initial_lattice_hydrogen_atoms_mol_m3"][0] = 1.0
    if case == "boundary":
        prescribed(x, "left", [0.99, 0.99])
    if case == "length_underflow":
        x["thickness_m"] = 1e-200
    if case == "length_overflow":
        x["thickness_m"] = 1e200
    if case == "release_underflow":
        x["traps"] = [trap(x, binding=1e9)]
    if case == "frequency_underflow":
        x.update(
            thickness_m=1e100,
            lattice_site_density_mol_m3=1e-100,
            initial_lattice_hydrogen_atoms_mol_m3=[2e-101] * x["cell_count"],
            lattice_diffusivity_m2_s=[1e-300, 1e-300],
        )
    result = slab_kinetic(HydrogenSlab.model_validate_json(json.dumps(x)))
    assert result.status == "out_of_scope"
