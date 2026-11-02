import json
from functools import lru_cache

import pytest

from matintegrity.contracts import RunContext
from matintegrity.models.hydrogen_inverse import (
    HydrogenSlabFlowMultiplierFit,
    fit_slab_flow_multiplier,
)
from matintegrity.models.hydrogen_kinetics import HydrogenSlab, slab_kinetic
from matintegrity.registry import default_registry

EVIDENCE = {
    "source_id": "authored-test",
    "origin": "synthetic",
    "citation": "Independent synthetic slab-flow inverse test",
}


def slab(diffusivity=0.1):
    times = [0.0, 0.05, 0.1, 0.2, 0.4, 0.8]
    return {
        "material_condition_id": "state-a",
        "reference_lattice_id": "lattice-a",
        "elapsed_time_origin_id": "charging-start",
        "thickness_m": 1.0,
        "cell_count": 2,
        "lattice_site_density_mol_m3": 1.0,
        "initial_lattice_hydrogen_atoms_mol_m3": [0.0] * 2,
        "elapsed_time_s": times,
        "uniform_temperature_K": [300.0] * len(times),
        "lattice_diffusivity_m2_s": [diffusivity] * len(times),
        "left_boundary": {
            "boundary_id": "entry",
            "kind": "prescribed_lattice_concentration",
            "lattice_hydrogen_atoms_mol_m3": [1.0] * len(times),
            "evidence": [EVIDENCE],
        },
        "right_boundary": {
            "boundary_id": "exit",
            "kind": "prescribed_lattice_concentration",
            "lattice_hydrogen_atoms_mol_m3": [0.0] * len(times),
            "evidence": [EVIDENCE],
        },
        "traps": [],
        "maximum_supported_lattice_occupancy": 1.0,
        "maximum_supported_total_trap_to_lattice_site_ratio": 0.05,
        "planar_geometry_reviewed": True,
        "fixed_populations_and_uniform_temperature_reviewed": True,
        "independent_single_occupancy_and_dilute_trap_regime_reviewed": True,
        "negligible_stress_gradient_reviewed": True,
        "detailed_balance_rate_ratio_reviewed": True,
        "relative_tolerance": 1e-4,
        "absolute_occupancy_tolerance": 1e-11,
        "maximum_step_s": 0.05,
    }


@lru_cache(maxsize=1)
def truth_flow():
    result = slab_kinetic(HydrogenSlab.model_validate_json(json.dumps(slab(0.2))))
    assert result.status == "computed"
    return tuple(-value for value in result.values["right_inward_flux_mol_m2_s"])


def inputs():
    times = slab()["elapsed_time_s"]
    return {
        "fit_id": "fit-a",
        "observation_series_id": "series-a",
        "specimen_id": "specimen-a",
        "detector_calibration_id": "ideal-flow-a",
        "observed_surface": "right",
        "observed_surface_id": "exit",
        "base_slab": slab(),
        "physical_surface_area_m2": 1.0,
        "observation_id": [f"point-{index}" for index in range(len(times))],
        "source_group_id": ["holdout-a", "cal-a", "cal-a", "holdout-a", "cal-a", "cal-a"],
        "partition": ["holdout", "calibration", "calibration", "holdout", "calibration", "calibration"],
        "elapsed_time_s": times,
        "outward_hydrogen_atoms_mol_s": list(truth_flow()),
        "residual_scale_mol_s": 0.001,
        "parameter_target": "lattice_diffusivity",
        "parameter_target_id": "lattice-a",
        "initial_multiplier": 1.0,
        "multiplier_bounds": [0.25, 4.0],
        "minimum_calibration_jacobian_norm": 1e-6,
        "maximum_function_evaluations": 60,
        "observation_conversion_reviewed": True,
        "physical_surface_area_reviewed": True,
        "fixed_inputs_independent_of_holdout_reviewed": True,
        "one_parameter_scope_reviewed": True,
        "holdout_partition_predeclared": True,
        "evidence": [EVIDENCE],
    }


def calculate(payload):
    contract = HydrogenSlabFlowMultiplierFit.model_validate_json(json.dumps(payload))
    return fit_slab_flow_multiplier(contract)


def test_fit_recovers_diffusivity_multiplier_and_reusable_slab_contract():
    result = calculate(inputs())
    assert result.status == "computed", result.notes
    assert result.values["fitted_multiplier"] == pytest.approx(2.0, rel=2e-4)
    assert result.values["fitted_target_history"] == pytest.approx([0.2] * 6, rel=2e-4)
    assert result.values["calibration_flow_rmse_mol_s"] < 1e-7
    assert result.values["holdout_flow_rmse_mol_s"] < 1e-7
    assert result.values["forward_relative_mass_balance_error"] < 1e-9
    fitted = HydrogenSlab.model_validate_json(json.dumps(result.values["fitted_slab_contract"]))
    assert fitted.reference_lattice_id == "lattice-a"
    assert fitted.lattice_diffusivity_m2_s == pytest.approx([0.2] * 6, rel=2e-4)


def test_holdout_values_do_not_change_fitted_parameter_or_fitted_slab_digest():
    baseline = calculate(inputs())
    modified = inputs()
    for index, partition in enumerate(modified["partition"]):
        if partition == "holdout":
            modified["outward_hydrogen_atoms_mol_s"][index] += 10.0
    changed = calculate(modified)
    assert baseline.values["fitted_multiplier"] == pytest.approx(
        changed.values["fitted_multiplier"], abs=1e-12
    )
    assert baseline.values["fitted_slab_digest"] == changed.values["fitted_slab_digest"]
    assert changed.values["holdout_flow_rmse_mol_s"] > 1.0


@pytest.mark.parametrize(
    "flag",
    [
        "observation_conversion_reviewed",
        "physical_surface_area_reviewed",
        "fixed_inputs_independent_of_holdout_reviewed",
        "one_parameter_scope_reviewed",
        "holdout_partition_predeclared",
    ],
)
def test_unreviewed_inverse_inputs_return_needs_data(flag):
    payload = inputs()
    payload[flag] = False
    result = calculate(payload)
    assert result.status == "needs_data" and result.values == {}


def test_caller_supplied_uncertainties_replace_common_residual_scale():
    payload = inputs()
    payload.pop("residual_scale_mol_s")
    payload["outward_flow_standard_uncertainty_mol_s"] = [0.001] * 6
    result = calculate(payload)
    assert result.status == "computed"
    assert result.values["uncertainty_basis"] == "caller_supplied_observation_standard_uncertainty"
    assert result.values["calibration_residual_variance"] is None
    assert result.values["fitted_multiplier_standard_uncertainty"] > 0


@pytest.mark.parametrize(
    "mutation",
    ["clock", "surface", "partition", "scales", "bounds", "target", "duplicate"],
)
def test_fit_contract_rejects_misaligned_or_ambiguous_inputs(mutation):
    payload = inputs()
    if mutation == "clock":
        payload["elapsed_time_s"][-1] = 0.41
    if mutation == "surface":
        payload["observed_surface_id"] = "entry"
    if mutation == "partition":
        payload["partition"] = ["holdout"] * 6
    if mutation == "scales":
        payload["outward_flow_standard_uncertainty_mol_s"] = [0.001] * 6
    if mutation == "bounds":
        payload["multiplier_bounds"] = [4.0, 0.25]
    if mutation == "target":
        payload["parameter_target_id"] = "other-lattice"
    if mutation == "duplicate":
        payload["observation_id"][1] = payload["observation_id"][0]
    with pytest.raises(ValueError):
        HydrogenSlabFlowMultiplierFit.model_validate_json(json.dumps(payload))


def test_wrong_boundary_kind_is_not_accepted_as_a_surface_parameter_target():
    payload = inputs()
    payload.update(parameter_target="right_transfer_coefficient", parameter_target_id="exit")
    with pytest.raises(ValueError, match="linear_surface_transfer"):
        HydrogenSlabFlowMultiplierFit.model_validate_json(json.dumps(payload))


def test_registry_exposes_inverse_model_units_sources_and_strict_json_execution():
    registry = default_registry()
    model_id = "transport.hydrogen_slab_flow_multiplier_fit"
    description = registry.describe(model_id)
    assert description["output_units"]["holdout_flow_rmse_mol_s"] == "mol/s"
    assert "scipy_least_squares" in description["source_ids"]
    result = registry.run_json(
        model_id,
        json.dumps(inputs()),
        RunContext(asset_id="synthetic", location_id="exit", time_basis="elapsed seconds"),
    )
    assert result.status == "computed"


def test_holdout_source_overlap_is_reported_without_being_called_independent():
    payload = inputs()
    payload["source_group_id"] = ["same-source"] * 6
    result = calculate(payload)
    assert result.status == "computed"
    assert result.values["holdout_source_groups_disjoint"] is False


def test_zero_selected_history_returns_out_of_scope_instead_of_fake_identification():
    payload = inputs()
    count = len(payload["base_slab"]["elapsed_time_s"])
    payload["base_slab"]["left_boundary"] = {
        "boundary_id": "entry",
        "kind": "dissociative_surface_reaction",
        "absorption_capacity_flux_mol_m2_s": [0.0] * count,
        "desorption_capacity_flux_mol_m2_s": [1.0] * count,
        "evidence": [EVIDENCE],
    }
    payload.update(parameter_target="left_absorption_capacity", parameter_target_id="entry")
    result = calculate(payload)
    assert result.status == "out_of_scope"
    assert "no positive value" in result.notes[0]
