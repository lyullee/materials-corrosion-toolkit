import json
import math

import pytest

from matintegrity.contracts import RunContext
from matintegrity.models.hydrogen_cylinder import HydrogenFiniteCylinder, finite_cylinder_kinetic
from matintegrity.models.hydrogen_kinetics import HydrogenSlab, LatticeBoundary, slab_kinetic
from matintegrity.models.hydrogen_surface import (
    HydrogenDissociativeSurfaceRates,
    dissociative_surface_rates,
)
from matintegrity.registry import default_registry

EVIDENCE = {
    "source_id": "authored-test",
    "origin": "synthetic",
    "citation": "Independent reduced surface-reaction test",
}


def law(name, capacity, energy=0.0):
    return {
        "rate_id": name,
        "pre_exponential_capacity_flux_mol_m2_s": capacity,
        "activation_energy_J_mol": energy,
        "evidence": [EVIDENCE],
    }


def inputs():
    return {
        "boundary_id": "gas-face",
        "material_condition_id": "state-a",
        "reference_lattice_id": "lattice-a",
        "surface_condition_id": "clean-synthetic-face",
        "hydrogen_species_id": "H2",
        "gas_state_provider_id": "reviewed-fugacity-table-a",
        "elapsed_time_origin_id": "exposure-start",
        "elapsed_time_s": [0.0, 10.0],
        "temperature_K": [300.0, 600.0],
        "hydrogen_gas_driver_Pa": [1.0e5, 4.0e5],
        "gas_driver_kind": "fugacity",
        "reference_fugacity_Pa": 1.0e5,
        "supported_temperature_K": [250.0, 700.0],
        "supported_hydrogen_gas_driver_Pa": [0.0, 1.0e6],
        "absorption": law("absorption", 4.0, 0.0),
        "desorption": law("desorption", 1.0, 0.0),
        "temperature_history_reviewed": True,
        "gas_driver_history_reviewed": True,
        "surface_parameterizations_reviewed": True,
        "lattice_surface_state_mapping_reviewed": True,
    }


def calculate(payload):
    contract = HydrogenDissociativeSurfaceRates.model_validate_json(json.dumps(payload))
    return dissociative_surface_rates(contract)


def test_capacity_histories_use_arrhenius_and_square_root_fugacity_driver():
    result = calculate(inputs())
    assert result.status == "computed"
    assert result.values["absorption_capacity_flux_mol_m2_s"] == pytest.approx([4.0, 8.0])
    assert result.values["desorption_capacity_flux_mol_m2_s"] == pytest.approx([1.0, 1.0])
    assert result.values["zero_net_surface_occupancy"] == pytest.approx([0.8, 8 / 9])
    assert len(result.values["boundary_history_digest"]) == 64


def test_exact_zero_fugacity_retains_zero_absorption_without_clipping_desorption():
    payload = inputs()
    payload["hydrogen_gas_driver_Pa"] = [0.0, 0.0]
    result = calculate(payload)
    assert result.status == "computed"
    assert result.values["absorption_capacity_flux_mol_m2_s"] == [0.0, 0.0]
    assert result.values["zero_net_surface_occupancy"] == [0.0, 0.0]
    assert result.values["log_absorption_capacity_flux_mol_m2_s"] == [None, None]


@pytest.mark.parametrize(
    "flag",
    [
        "temperature_history_reviewed",
        "gas_driver_history_reviewed",
        "surface_parameterizations_reviewed",
        "lattice_surface_state_mapping_reviewed",
    ],
)
def test_unreviewed_surface_inputs_do_not_produce_boundary_histories(flag):
    payload = inputs()
    payload[flag] = False
    result = calculate(payload)
    assert result.status == "needs_data" and result.values == {}


def test_partial_pressure_needs_separate_ideal_gas_review():
    payload = inputs()
    payload["gas_driver_kind"] = "ideal_gas_partial_pressure_approximation"
    assert calculate(payload).status == "needs_data"
    payload["ideal_gas_approximation_reviewed"] = True
    assert calculate(payload).status == "computed"


def test_fugacity_mode_rejects_an_inapplicable_ideal_gas_review_flag():
    payload = inputs()
    payload["ideal_gas_approximation_reviewed"] = True
    with pytest.raises(ValueError, match="not applicable"):
        HydrogenDissociativeSurfaceRates.model_validate_json(json.dumps(payload))


def test_support_and_positive_floating_point_range_are_not_extrapolated_or_clipped():
    outside = inputs()
    outside["hydrogen_gas_driver_Pa"][-1] = 1.1e6
    assert calculate(outside).status == "out_of_scope"

    underflow = inputs()
    underflow["desorption"]["activation_energy_J_mol"] = 1e9
    result = calculate(underflow)
    assert result.status == "out_of_scope"
    assert result.values["log_desorption_capacity_flux_mol_m2_s"][0] < -1000


@pytest.mark.parametrize("mutation", ["clock", "support", "identity", "capacity"])
def test_surface_contract_rejects_misaligned_or_ambiguous_inputs(mutation):
    payload = inputs()
    if mutation == "clock":
        payload["temperature_K"].pop()
    if mutation == "support":
        payload["supported_hydrogen_gas_driver_Pa"] = [10.0, 1.0]
    if mutation == "identity":
        payload["desorption"]["rate_id"] = payload["absorption"]["rate_id"]
    if mutation == "capacity":
        payload["absorption"]["pre_exponential_capacity_flux_mol_m2_s"] = 0.0
    with pytest.raises(ValueError):
        HydrogenDissociativeSurfaceRates.model_validate_json(json.dumps(payload))


def test_returned_fragment_validates_as_lattice_boundary():
    result = calculate(inputs())
    boundary = LatticeBoundary.model_validate_json(
        json.dumps({"boundary_id": "gas-face", **result.values["boundary_contract_fields"]})
    )
    assert boundary.kind == "dissociative_surface_reaction"
    assert boundary.absorption_capacity_flux_mol_m2_s == pytest.approx([4.0, 8.0])


def reaction_boundary(name, count=2):
    return {
        "boundary_id": name,
        "kind": "dissociative_surface_reaction",
        "absorption_capacity_flux_mol_m2_s": [4.0] * count,
        "desorption_capacity_flux_mol_m2_s": [1.0] * count,
        "evidence": [EVIDENCE],
    }


def no_flux(name):
    return {"boundary_id": name, "kind": "no_flux", "evidence": [EVIDENCE]}


def test_slab_surface_flux_matches_series_surface_and_half_cell_resistance():
    payload = {
        "material_condition_id": "state-a",
        "reference_lattice_id": "lattice-a",
        "elapsed_time_origin_id": "exposure-start",
        "thickness_m": 1.0,
        "cell_count": 2,
        "lattice_site_density_mol_m3": 10.0,
        "initial_lattice_hydrogen_atoms_mol_m3": [2.0, 2.0],
        "elapsed_time_s": [0.0, 0.001],
        "uniform_temperature_K": [300.0, 300.0],
        "lattice_diffusivity_m2_s": [2.0, 2.0],
        "left_boundary": reaction_boundary("left"),
        "right_boundary": no_flux("right"),
        "traps": [],
        "maximum_supported_lattice_occupancy": 0.9,
        "maximum_supported_total_trap_to_lattice_site_ratio": 0.05,
        "planar_geometry_reviewed": True,
        "fixed_populations_and_uniform_temperature_reviewed": True,
        "independent_single_occupancy_and_dilute_trap_regime_reviewed": True,
        "negligible_stress_gradient_reviewed": True,
        "detailed_balance_rate_ratio_reviewed": True,
    }
    result = slab_kinetic(HydrogenSlab.model_validate_json(json.dumps(payload)))
    assert result.status == "computed", result.notes
    surface_conductance = 4.0 + 1.0
    diffusion_conductance = 10.0 * 2.0 / 0.25
    combined = 1 / (1 / surface_conductance + 1 / diffusion_conductance)
    expected = combined * (4 / 5 - 2 / 10)
    assert result.values["left_inward_flux_mol_m2_s"][0] == pytest.approx(expected)
    assert result.values["relative_mass_balance_error"] < 1e-9


def test_cylinder_reaction_flow_uses_curved_area_and_same_series_resistance():
    payload = {
        "material_condition_id": "state-a",
        "reference_lattice_id": "lattice-a",
        "elapsed_time_origin_id": "exposure-start",
        "radius_m": 1.0,
        "length_m": 2.0,
        "radial_cell_count": 2,
        "axial_cell_count": 2,
        "lattice_site_density_mol_m3": 10.0,
        "initial_lattice_hydrogen_atoms_mol_m3": [2.0] * 4,
        "elapsed_time_s": [0.0, 0.001],
        "uniform_temperature_K": [300.0, 300.0],
        "lattice_diffusivity_m2_s": [2.0, 2.0],
        "curved_surface_boundary": reaction_boundary("curved"),
        "lower_end_boundary": no_flux("lower"),
        "upper_end_boundary": no_flux("upper"),
        "traps": [],
        "maximum_supported_lattice_occupancy": 0.9,
        "maximum_supported_total_trap_to_lattice_site_ratio": 0.05,
        "finite_axisymmetric_geometry_reviewed": True,
        "azimuthally_uniform_state_reviewed": True,
        "fixed_populations_and_uniform_temperature_reviewed": True,
        "independent_single_occupancy_and_dilute_trap_regime_reviewed": True,
        "negligible_stress_gradient_reviewed": True,
        "detailed_balance_rate_ratio_reviewed": True,
    }
    result = finite_cylinder_kinetic(HydrogenFiniteCylinder.model_validate_json(json.dumps(payload)))
    assert result.status == "computed", result.notes
    combined = 1 / (1 / 5.0 + 1 / (10.0 * 2.0 / 0.25))
    expected = combined * (0.8 - 0.2) * 2 * math.pi * 1.0 * 2.0
    assert result.values["inward_surface_flow_mol_s"]["curved_surface"][0] == pytest.approx(expected)
    assert result.values["relative_mass_balance_error"] < 1e-9


def test_registry_exposes_surface_model_units_sources_and_strict_json_execution():
    registry = default_registry()
    model_id = "transport.hydrogen_dissociative_surface_rates"
    description = registry.describe(model_id)
    assert description["output_units"]["absorption_capacity_flux_mol_m2_s"] == "mol/(m^2*s)"
    assert "iupac_fugacity_definition" in description["source_ids"]
    result = registry.run_json(
        model_id,
        json.dumps(inputs()),
        RunContext(asset_id="synthetic", location_id="gas-face", time_basis="elapsed seconds"),
    )
    assert result.status == "computed"


def test_reaction_boundary_rejects_foreign_fields_or_zero_combined_capacity():
    boundary = reaction_boundary("face")
    boundary["equilibrium_lattice_hydrogen_atoms_mol_m3"] = [1.0, 1.0]
    with pytest.raises(ValueError):
        LatticeBoundary.model_validate_json(json.dumps(boundary))
    zero = reaction_boundary("face")
    zero["absorption_capacity_flux_mol_m2_s"] = [0.0, 0.0]
    zero["desorption_capacity_flux_mol_m2_s"] = [0.0, 0.0]
    with pytest.raises(ValueError, match="positive combined"):
        LatticeBoundary.model_validate_json(json.dumps(zero))
