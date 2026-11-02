import copy
import json
import math

import numpy as np
import pytest
from pydantic import ValidationError

from matintegrity.contracts import RunContext
from matintegrity.models.thermal_transient import ThroughWallThermalStress, TransientConduction1D
from matintegrity.registry import default_registry

CONTEXT = RunContext(asset_id="test", location_id="section", time_basis="elapsed seconds")


@pytest.mark.parametrize(
    "model,kind",
    [
        ("thermal.transient_conduction_1d", "conduction"),
        ("mechanics.through_wall_thermal_stress", "stress"),
    ],
)
def test_scope_revalidation_python_json_execution(model, kind):
    inputs = conduction_input() if kind == "conduction" else stress_input()
    registry = default_registry()
    direct = registry.run(model, inputs, CONTEXT)
    encoded = registry.run_json(model, json.dumps(inputs), CONTEXT)
    assert direct.model_dump() == encoded.model_dump()


def conduction_input(cells=4):
    return dict(
        geometry="planar",
        cell_edges_m=np.linspace(0.0, 0.02, cells + 1).tolist(),
        planar_area_m2=0.5,
        cylinder_length_m=None,
        materials=[
            dict(
                material_id="authored-constant",
                temperature_K=[300.0],
                conductivity_W_m_K=[20.0],
                volumetric_heat_capacity_J_m3_K=[4.0e6],
            )
        ],
        cell_material_ids=["authored-constant"] * cells,
        initial_temperature_K=[300.0] * cells,
        time_s=[0.0, 2.0],
        left_boundary=dict(boundary_id="left", kind="adiabatic"),
        right_boundary=dict(boundary_id="right", kind="adiabatic"),
        volumetric_heat_generation_W_m3=None,
        distributed_exchange=None,
        maximum_step_s=0.05,
        nonlinear_absolute_tolerance_K=1e-9,
        nonlinear_relative_tolerance=1e-11,
        maximum_nonlinear_iterations=80,
        maximum_relative_energy_balance_error=1e-8,
        one_dimensional_geometry_reviewed=True,
        material_property_support_reviewed=True,
        boundary_conditions_reviewed=True,
        phase_change_absent_or_included_in_capacity_reviewed=True,
    )


def stress_input():
    return dict(
        profile_id="authored-profile",
        position_m=[0.0, 0.005, 0.01],
        temperature_K=[400.0, 350.0, 300.0],
        reference_temperature_K=300.0,
        secant_thermal_expansion_1_K=[1.0e-5] * 3,
        elastic_modulus_Pa=[200.0e9] * 3,
        poisson_ratio=[0.3] * 3,
        elastic_limit_Pa=[1.0e9] * 3,
        plane_condition="uniaxial_plane_stress",
        control="resultant_controlled",
        membrane_force_N_m=0.0,
        bending_moment_N=0.0,
        midplane_total_strain=None,
        curvature_1_m=None,
        plane_sections_reviewed=True,
        linear_elastic_response_reviewed=True,
        property_profiles_reviewed=True,
        applied_resultants_or_kinematics_reviewed=True,
    )


def run(model_id, inputs):
    return default_registry().run(model_id, inputs, CONTEXT)


def test_models_are_registered_with_units():
    registry = default_registry()
    assert "thermal.transient_conduction_1d" in registry.list_models()
    assert "mechanics.through_wall_thermal_stress" in registry.list_models()
    assert (
        registry.describe("thermal.transient_conduction_1d")["output_units"]["temperature_history_K"] == "K"
    )


def test_adiabatic_uniform_temperature_remains_constant():
    result = run("thermal.transient_conduction_1d", conduction_input())
    assert result.status == "computed"
    assert result.values["temperature_history_K"][-1] == pytest.approx([300.0] * 4, abs=1e-10)
    assert result.values["cumulative_boundary_energy_into_solid_J"] == pytest.approx([0.0, 0.0])


def test_uniform_generation_matches_enthalpy_gain():
    inputs = conduction_input()
    inputs["volumetric_heat_generation_W_m3"] = [[1000.0] * 4, [1000.0] * 4]
    result = run("thermal.transient_conduction_1d", inputs)
    expected = 300.0 + 1000.0 * 2.0 / 4.0e6
    assert result.values["temperature_history_K"][-1] == pytest.approx([expected] * 4, abs=2e-10)
    assert result.values["cumulative_generated_energy_J"] == pytest.approx(20.0)
    assert result.values["maximum_relative_discrete_energy_balance_error"] < 1e-8


def test_prescribed_flux_sign_and_energy_are_retained():
    inputs = conduction_input()
    inputs["left_boundary"] = dict(
        boundary_id="left", kind="prescribed_heat_flux", heat_flux_into_solid_W_m2=[200.0, 200.0]
    )
    result = run("thermal.transient_conduction_1d", inputs)
    assert result.values["cumulative_boundary_energy_into_solid_J"] == pytest.approx([200.0, 0.0])
    assert np.mean(result.values["temperature_history_K"][-1]) > 300.0
    assert result.values["boundary_heat_rate_into_solid_W"][-1][0] == pytest.approx(100.0)


def test_negative_prescribed_flux_cools_without_absolute_value_conversion():
    inputs = conduction_input()
    inputs["left_boundary"] = dict(
        boundary_id="left", kind="prescribed_heat_flux", heat_flux_into_solid_W_m2=[-100.0, -100.0]
    )
    result = run("thermal.transient_conduction_1d", inputs)
    assert result.values["cumulative_boundary_energy_into_solid_J"][0] == pytest.approx(-100.0)
    assert np.mean(result.values["temperature_history_K"][-1]) < 300.0


def test_distributed_convection_keeps_spatially_uniform_solution():
    inputs = conduction_input()
    inputs["initial_temperature_K"] = [400.0] * 4
    inputs["distributed_exchange"] = dict(
        area_per_volume_m_inv=[20.0] * 4,
        convection_W_m2_K=[50.0, 50.0],
        ambient_temperature_K=[300.0, 300.0],
    )
    inputs["maximum_step_s"] = 2.0
    result = run("thermal.transient_conduction_1d", inputs)
    backward_euler = (400.0 + 2.0 * 50.0 * 20.0 / 4.0e6 * 300.0) / (1.0 + 2.0 * 50.0 * 20.0 / 4.0e6)
    assert result.values["temperature_history_K"][-1] == pytest.approx([backward_euler] * 4)
    assert result.values["distributed_heat_rate_into_solid_W"][-1] < 0


def test_convection_and_radiation_report_surface_between_solid_and_environment():
    inputs = conduction_input(2)
    inputs["initial_temperature_K"] = [500.0, 500.0]
    inputs["left_boundary"] = dict(
        boundary_id="left",
        kind="convection_radiation",
        convection_W_m2_K=[10.0, 10.0],
        ambient_temperature_K=[300.0, 300.0],
        emissivity=0.8,
        radiative_environment_temperature_K=[290.0, 290.0],
    )
    result = run("thermal.transient_conduction_1d", inputs)
    surface = result.values["boundary_surface_temperature_K"][-1][0]
    cell = result.values["temperature_history_K"][-1][0]
    assert 290.0 < surface < cell < 500.0
    assert result.values["boundary_heat_rate_into_solid_W"][-1][0] < 0


def test_temperature_dependent_capacity_uses_integrated_enthalpy():
    inputs = conduction_input(2)
    inputs["materials"][0].update(
        temperature_K=[290.0, 310.0],
        conductivity_W_m_K=[20.0, 20.0],
        volumetric_heat_capacity_J_m3_K=[2.0e6, 6.0e6],
    )
    inputs["volumetric_heat_generation_W_m3"] = [[2.0e6, 2.0e6], [2.0e6, 2.0e6]]
    inputs["maximum_step_s"] = 0.02
    result = run("thermal.transient_conduction_1d", inputs)
    final = result.values["temperature_history_K"][-1][0]
    assert 300.0 < final < 302.0
    assert result.values["maximum_relative_discrete_energy_balance_error"] < 1e-8


def test_property_support_is_not_extrapolated():
    inputs = conduction_input(2)
    inputs["materials"][0].update(
        temperature_K=[295.0, 305.0],
        conductivity_W_m_K=[20.0, 20.0],
        volumetric_heat_capacity_J_m3_K=[4e6, 4e6],
    )
    inputs["left_boundary"] = dict(
        boundary_id="left", kind="prescribed_temperature", temperature_K=[500.0, 500.0]
    )
    result = run("thermal.transient_conduction_1d", inputs)
    assert result.status == "out_of_scope"
    assert "outside" in result.notes[0]


def test_cylindrical_geometry_conserves_flux_energy():
    inputs = conduction_input(3)
    inputs.update(
        geometry="cylindrical",
        cell_edges_m=[0.01, 0.012, 0.016, 0.02],
        planar_area_m2=None,
        cylinder_length_m=0.4,
        cell_material_ids=["authored-constant"] * 3,
        initial_temperature_K=[300.0] * 3,
    )
    inputs["left_boundary"] = dict(
        boundary_id="inside", kind="prescribed_heat_flux", heat_flux_into_solid_W_m2=[100.0, 100.0]
    )
    result = run("thermal.transient_conduction_1d", inputs)
    expected = 100.0 * 2 * math.pi * 0.01 * 0.4 * 2.0
    assert result.status == "computed"
    assert result.values["cumulative_boundary_energy_into_solid_J"][0] == pytest.approx(expected)


def test_review_flags_stop_solver_before_substitution():
    inputs = conduction_input()
    inputs["boundary_conditions_reviewed"] = False
    result = run("thermal.transient_conduction_1d", inputs)
    assert result.status == "needs_data"
    assert "material_property_lineage" in result.values
    assert "temperature_history_K" not in result.values
    assert "cumulative_boundary_energy_into_solid_J" not in result.values


def test_conduction_json_contract_is_strict_and_round_trips():
    inputs = conduction_input()
    parsed = TransientConduction1D.model_validate_json(json.dumps(inputs))
    assert TransientConduction1D.model_validate_json(parsed.model_dump_json()) == parsed
    invalid = copy.deepcopy(inputs)
    invalid["hidden_default"] = 1
    with pytest.raises(ValidationError):
        TransientConduction1D.model_validate_json(json.dumps(invalid))


@pytest.mark.parametrize(
    "change",
    [
        {"cell_edges_m": [0.0, 0.01, 0.005]},
        {"time_s": [0.0, 0.0]},
        {"cell_material_ids": ["missing"] * 4},
        {"planar_area_m2": None},
    ],
)
def test_conduction_alignment_errors_are_rejected(change):
    inputs = conduction_input()
    inputs.update(change)
    with pytest.raises(ValidationError):
        TransientConduction1D.model_validate(inputs)


def test_boundary_history_must_share_clock():
    inputs = conduction_input()
    inputs["left_boundary"] = dict(boundary_id="left", kind="prescribed_temperature", temperature_K=[300.0])
    with pytest.raises(ValidationError):
        TransientConduction1D.model_validate(inputs)


def test_linear_free_thermal_profile_has_zero_self_equilibrated_stress():
    result = run("mechanics.through_wall_thermal_stress", stress_input())
    assert result.status == "computed"
    assert result.values["midplane_total_strain"] == pytest.approx(5e-4)
    assert result.values["curvature_1_m"] == pytest.approx(-0.1)
    assert result.values["stress_Pa"] == pytest.approx([0.0, 0.0, 0.0], abs=1e-5)
    assert abs(result.values["membrane_force_residual_N_m"]) < 1e-8
    assert abs(result.values["bending_moment_residual_N"]) < 1e-10


def test_uniform_fully_restrained_uniaxial_stress():
    inputs = stress_input()
    inputs.update(
        temperature_K=[350.0] * 3,
        control="kinematic_controlled",
        membrane_force_N_m=None,
        bending_moment_N=None,
        midplane_total_strain=0.0,
        curvature_1_m=0.0,
    )
    result = run("mechanics.through_wall_thermal_stress", inputs)
    assert result.values["stress_Pa"] == pytest.approx([-100e6] * 3)
    assert result.values["membrane_force_N_m"] == pytest.approx(-1e6)


def test_equi_biaxial_plane_stress_uses_biaxial_modulus():
    inputs = stress_input()
    inputs.update(
        temperature_K=[350.0] * 3,
        plane_condition="equi_biaxial_plane_stress",
        control="kinematic_controlled",
        membrane_force_N_m=None,
        bending_moment_N=None,
        midplane_total_strain=0.0,
        curvature_1_m=0.0,
    )
    result = run("mechanics.through_wall_thermal_stress", inputs)
    assert result.values["stress_Pa"] == pytest.approx([-100e6 / 0.7] * 3)


def test_resultant_control_recovers_applied_force_and_moment():
    inputs = stress_input()
    inputs.update(temperature_K=[300.0] * 3, membrane_force_N_m=2.0e5, bending_moment_N=500.0)
    result = run("mechanics.through_wall_thermal_stress", inputs)
    assert result.values["membrane_force_N_m"] == pytest.approx(2.0e5, rel=1e-12)
    assert result.values["bending_moment_N"] == pytest.approx(500.0, rel=1e-12)


def test_nonlinear_temperature_profile_self_equilibrates_but_has_stress():
    inputs = stress_input()
    inputs["temperature_K"] = [400.0, 310.0, 300.0]
    result = run("mechanics.through_wall_thermal_stress", inputs)
    assert max(abs(value) for value in result.values["stress_Pa"]) > 1e6
    assert abs(result.values["membrane_force_N_m"]) < 1e-7
    assert abs(result.values["bending_moment_N"]) < 1e-9


def test_elastic_limit_exceedance_is_out_of_scope_not_clipped():
    inputs = stress_input()
    inputs.update(
        temperature_K=[400.0] * 3,
        elastic_limit_Pa=[50e6] * 3,
        control="kinematic_controlled",
        membrane_force_N_m=None,
        bending_moment_N=None,
        midplane_total_strain=0.0,
        curvature_1_m=0.0,
    )
    result = run("mechanics.through_wall_thermal_stress", inputs)
    assert result.status == "out_of_scope"
    assert result.values["maximum_evaluated_elastic_limit_utilization"] == pytest.approx(4.0)
    assert result.values["stress_Pa"] == pytest.approx([-200e6] * 3)


def test_stress_review_flags_require_data():
    inputs = stress_input()
    inputs["linear_elastic_response_reviewed"] = False
    result = run("mechanics.through_wall_thermal_stress", inputs)
    assert result.status == "needs_data"


@pytest.mark.parametrize(
    "change",
    [
        {"position_m": [0.0, 0.01, 0.005]},
        {"temperature_K": [300.0, 301.0]},
        {"curvature_1_m": 0.0},
    ],
)
def test_stress_contract_rejects_misalignment_and_mixed_control(change):
    inputs = stress_input()
    inputs.update(change)
    with pytest.raises(ValidationError):
        ThroughWallThermalStress.model_validate(inputs)
