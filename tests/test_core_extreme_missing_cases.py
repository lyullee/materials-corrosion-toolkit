"""Explicit extreme and boundary cases for previously unconfirmed calculation groups."""

import copy
import json
from pathlib import Path

import pytest
import scipy.integrate
import scipy.optimize
from pydantic import ValidationError

from matintegrity.registry import default_registry

ROOT = Path(__file__).resolve().parents[1]
B = json.loads((ROOT / "tests/data/core_physics_valid_input_baselines.json").read_text(encoding="utf8"))[
    "model_inputs"
]
E = json.loads((ROOT / "examples/model_inputs.json").read_text(encoding="utf8"))["models"]
CASES = [
    (6, "degradation.crevice_nernst_potential_history", {"temperature_K": [1e308] * 3}),
    (8, "corrosion.atmospheric_first_year_prediction", {"temperature_K": 1e308}),
    (10, "degradation.scc_crack_velocity_history", {"initial_crack_advance_m": 1e308}),
    (13, "chemistry.competitive_solid_equilibrium", {"maximum_absolute_log_saturation_residual": 1e-300}),
    (14, "chemistry.crevice_aqueous_kinetic_network", {"control_volume_m3": 1e-300}),
    (16, "chemistry.caller_scale_coverage_kinetics", {"initial_covered_area_fraction": 1.0}),
    (17, "chemistry.layered_scale_diffusion_limit", {"bare_diffusivity_m2_s": 1e-300}),
    (
        18,
        "degradation.wet_co2_two_film_transfer",
        {"gas_film_coefficient_mol_m2_s_Pa": 1e-300, "co2_fugacity_Pa": 10.0, "bulk_co2star_mol_m3": 2.0},
    ),
    (19, "integration.wet_co2_cylindrical_transient_transport", {"maximum_step_s": 1e308}),
    (
        21,
        "chemistry.crevice_steady_wall_sink",
        {"wall_transfer_velocity_m_s": 1e308, "mouth_concentration_mol_m3": 2.0},
    ),
    (22, "transport.crevice_activity_corrected_nernst_planck_1d", {"cross_section_area_m2": 1e-300}),
    (24, "corrosion.planar_slit_transient_hydraulic_history", {"initial_volumetric_flow_m3_s": 1e-300}),
    (27, "mechanics.plane_stress", {"stress_x_Pa": 1e308, "stress_y_Pa": -1e308, "shear_xy_Pa": 1e308}),
    (30, "fabrication.nonlinear_bolt_gasket_contact", {"external_separating_force_N": 1e308}),
    (31, "fabrication.gasket_prony_joint_history", {"initial_compressive_strain": 0.0}),
    (
        32,
        "fabrication.gasket_calibrated_leakage_history",
        {"differential_pressure_history_Pa": [1e308, 1e308]},
    ),
    (37, "creep.norton", {"stress_Pa": 1e308}),
    (39, "creep.time_fraction", {"exposure_s": [0.0, 0.0]}),
    (40, "fatigue.basquin", {"stress_range_Pa": 1e308}),
    (42, "fatigue.miner", {"cycle_counts": [0.0, 0.0]}),
    (44, "fatigue.multiaxial_crossland_proportional_limit_screen", {"caller_limit_beta_Pa": 1e308}),
    (45, "fatigue.itoh_nonproportional_strain_life", {}),
    (
        46,
        "fatigue.j2_prager_strain_history",
        {"strain_tensor_components": [[0, 0, 0, 0, 0, 0], [1e308, 0, 0, 0, 0, 0]]},
    ),
    (48, "fatigue.hysteresis_path", {}),
    (51, "welding.rosenthal_3d_point_source_temperature", {"absorbed_power_W": 1e308}),
    (52, "thermo.co2_fugacity_coolprop", {"temperature_K": 1e300}),
    (53, "integration.wet_co2_gas_film_condensation_transfer_history", {}),
    (55, "degradation.archard_wear", {"normal_force_N": 1e308}),
    (60, "protection.cathodic_budget", {"installed_anodes": 0}),
]


@pytest.mark.parametrize("group,model,changes", CASES, ids=[f"group-{r[0]:02d}" for r in CASES])
def test_explicit_extreme_or_boundary_is_controlled_and_finite(group, model, changes):
    p = copy.deepcopy(B.get(model, E.get(model)))
    assert p is not None, model
    p.update(changes)
    if group == 45:
        p["parameter_request"]["hardening_coefficient_alpha"] = 1e308
    if group == 48:
        # A closed zero-strain path must not acquire spurious work.
        p["strain_fraction"] = [0.0 for _ in p["strain_fraction"]]
    if group == 53:
        p["intervals"][0]["bulk_water_vapor_fugacity_Pa"] = 0.0
    spec = default_registry()._models[model]
    try:
        request = spec.input_type.model_validate_json(json.dumps(p, allow_nan=False))
    except ValidationError as error:
        # Explicit input-domain guards are distinguished from runtime behavior.
        assert not any("digest" in e["msg"].lower() or "tuple_type" == e["type"] for e in error.errors())
        outcome = "input_domain_rejected"
    else:
        dependencies = {name: scipy for name in spec.runtime_dependency_names}
        result = spec.evaluator(request, **dependencies)
        assert result.status in {"computed", "out_of_scope", "needs_data"}
        json.dumps(result.model_dump(mode="json"), allow_nan=False)
        if result.status == "computed":
            if group == 16:
                assert 0 <= result.values["final_covered_area_fraction"] <= 1
            if group == 17:
                assert result.values["area_average_flux_limit_mol_m2_s"] > 0
            if group == 18:
                assert result.values["signed_gas_to_liquid_CO2_flux_mol_m2_s"] > 0
            if group == 39:
                assert result.values["time_fraction_damage"] == 0
            if group == 40:
                assert result.values["cycles_to_failure"] > 0
            if group == 42:
                assert result.values["damage"] == 0
            if group == 48:
                assert result.values["signed_recorded_path_work_J_m3"] == 0
                assert result.values["signed_closed_cycle_work_J_m3"] == 0
            if group == 53:
                assert result.values["final_water_areal_inventory_kg_m2"] == 0
        outcome = "runtime_" + result.status
    output = ROOT / "artifacts/validation/extreme_missing"
    output.mkdir(parents=True, exist_ok=True)
    (output / f"{group:02d}.json").write_text(
        json.dumps({"group": group, "model_id": model, "outcome": outcome}) + "\n", encoding="utf8"
    )
