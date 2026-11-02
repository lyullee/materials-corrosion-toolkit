"""Reproduce authored heat/stress benchmarks and one bounded same-data experiment comparison."""

from __future__ import annotations

import hashlib
import json
import math
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

from matintegrity.contracts import RunContext
from matintegrity.registry import default_registry
from matintegrity.thermal_data import read_thermal_rod_fitted_results, read_thermal_rod_series

ROOT = Path(__file__).resolve().parents[1]
ARCHIVE = ROOT / "data/raw/thermal-rod-transient/sbcf36976g-1.zip"
THERMAL_MODEL = "thermal.transient_conduction_1d"
STRESS_MODEL = "mechanics.through_wall_thermal_stress"
CONTEXT = RunContext(asset_id="authored-benchmark", location_id="one-dimensional-domain", time_basis="s")


def slab_input(cells: int, maximum_step_s: float):
    return dict(
        geometry="planar",
        cell_edges_m=np.linspace(0.0, 1.0, cells + 1).tolist(),
        planar_area_m2=1.0,
        cylinder_length_m=None,
        materials=[
            dict(
                material_id="authored-unit-diffusivity",
                temperature_K=[300.0],
                conductivity_W_m_K=[1.0],
                volumetric_heat_capacity_J_m3_K=[1.0],
            )
        ],
        cell_material_ids=["authored-unit-diffusivity"] * cells,
        initial_temperature_K=[300.0] * cells,
        time_s=[0.0, 0.1],
        left_boundary=dict(boundary_id="hot", kind="prescribed_temperature", temperature_K=[400.0, 400.0]),
        right_boundary=dict(boundary_id="cold", kind="prescribed_temperature", temperature_K=[300.0, 300.0]),
        volumetric_heat_generation_W_m3=None,
        distributed_exchange=None,
        maximum_step_s=maximum_step_s,
        nonlinear_absolute_tolerance_K=1e-10,
        nonlinear_relative_tolerance=1e-12,
        maximum_nonlinear_iterations=20,
        maximum_relative_energy_balance_error=1e-8,
        one_dimensional_geometry_reviewed=True,
        material_property_support_reviewed=True,
        boundary_conditions_reviewed=True,
        phase_change_absent_or_included_in_capacity_reviewed=True,
    )


def exact_slab_cell_averages(cells: int):
    modes = np.arange(1, 401)[:, None]
    centres = (np.arange(cells) + 0.5) / cells
    average_sine = np.sin(np.pi * modes * centres) * np.sinc(modes / (2 * cells))
    transient = np.sum(2.0 / (np.pi * modes) * average_sine * np.exp(-(np.pi**2) * modes**2 * 0.1), axis=0)
    return 300.0 + 100.0 * (1.0 - centres - transient)


def calculate(model_id: str, inputs: dict, context: RunContext = CONTEXT):
    result = default_registry().run(model_id, inputs, context)
    if result.status != "computed":
        raise ValueError(f"{model_id} benchmark failed: {result.status} {result.notes}")
    return result


def analytical_checks():
    spatial = []
    for cells in (12, 24, 48):
        result = calculate(THERMAL_MODEL, slab_input(cells, 2.5e-5))
        actual = np.asarray(result.values["temperature_history_K"][-1])
        error = float(np.max(np.abs(actual - exact_slab_cell_averages(cells))))
        spatial.append(
            dict(
                cells=cells,
                maximum_cell_average_error_K=error,
                relative_energy_balance_error=result.values["maximum_relative_discrete_energy_balance_error"],
            )
        )
    time = []
    for step in (0.02, 0.01, 0.005):
        result = calculate(THERMAL_MODEL, slab_input(120, step))
        actual = np.asarray(result.values["temperature_history_K"][-1])
        error = float(np.max(np.abs(actual - exact_slab_cell_averages(120))))
        time.append(dict(maximum_step_s=step, maximum_cell_average_error_K=error))
    spatial_ratios = [
        spatial[index]["maximum_cell_average_error_K"] / spatial[index + 1]["maximum_cell_average_error_K"]
        for index in range(2)
    ]
    time_ratios = [
        time[index]["maximum_cell_average_error_K"] / time[index + 1]["maximum_cell_average_error_K"]
        for index in range(2)
    ]
    free = calculate(
        STRESS_MODEL,
        dict(
            profile_id="linear-free-gradient",
            position_m=[0.0, 0.005, 0.01],
            temperature_K=[400.0, 350.0, 300.0],
            reference_temperature_K=300.0,
            secant_thermal_expansion_1_K=[1e-5] * 3,
            elastic_modulus_Pa=[200e9] * 3,
            poisson_ratio=[0.3] * 3,
            elastic_limit_Pa=[1e9] * 3,
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
        ),
    )
    fixed_inputs = dict(free.inputs)
    fixed_inputs.update(
        profile_id="uniform-fixed-heating",
        temperature_K=[350.0] * 3,
        control="kinematic_controlled",
        membrane_force_N_m=None,
        bending_moment_N=None,
        midplane_total_strain=0.0,
        curvature_1_m=0.0,
    )
    fixed = calculate(STRESS_MODEL, fixed_inputs)
    stress_error = max(abs(value + 100e6) for value in fixed.values["stress_Pa"])
    free_stress = max(abs(value) for value in free.values["stress_Pa"])
    if min(spatial_ratios) <= 3.0 or min(time_ratios) <= 1.7 or stress_error > 1e-5 or free_stress > 1e-4:
        raise ValueError("authored thermal-gradient analytical criteria no longer pass")
    return dict(
        planar_fourier_cell_average=spatial,
        spatial_error_reduction=spatial_ratios,
        backward_euler_time=time,
        temporal_error_reduction=time_ratios,
        free_linear_gradient_maximum_stress_Pa=free_stress,
        fixed_uniform_heating_maximum_stress_error_Pa=stress_error,
    )


def experimental_comparison():
    raw = read_thermal_rod_series(ARCHIVE, "50ss1")
    fitted = read_thermal_rod_fitted_results(ARCHIVE).set_index("run_id").loc["50ss1"]
    selected = list(range(0, len(raw), 10))
    if selected[-1] != len(raw) - 1:
        selected.append(len(raw) - 1)
    clock = raw.time_s.iloc[selected].astype(float).tolist()
    diameter = 0.003175
    length = 0.150
    density = 8030.0
    heat_capacity = 502.0
    ambient = 293.65
    area = math.pi * diameter**2 / 4
    perimeter = math.pi * diameter
    power = [
        fitted.fitted_steady_power_W
        * (1 - math.exp(-fitted.fitted_boundary_ramp_rate_1_s * (time + fitted.fitted_boundary_delay_s)))
        for time in clock
    ]

    def solve(cells, step):
        inputs = dict(
            geometry="planar",
            cell_edges_m=np.linspace(0.0, length, cells + 1).tolist(),
            planar_area_m2=area,
            cylinder_length_m=None,
            materials=[
                dict(
                    material_id="source-same-data-fit",
                    temperature_K=[ambient],
                    conductivity_W_m_K=[float(fitted.fitted_conductivity_W_m_K)],
                    volumetric_heat_capacity_J_m3_K=[density * heat_capacity],
                )
            ],
            cell_material_ids=["source-same-data-fit"] * cells,
            initial_temperature_K=[ambient] * cells,
            time_s=clock,
            left_boundary=dict(
                boundary_id="heated-end",
                kind="prescribed_heat_flux",
                heat_flux_into_solid_W_m2=[value / area for value in power],
            ),
            right_boundary=dict(boundary_id="adiabatic-tip", kind="adiabatic"),
            volumetric_heat_generation_W_m3=None,
            distributed_exchange=dict(
                area_per_volume_m_inv=[perimeter / area] * cells,
                convection_W_m2_K=[float(fitted.fitted_convection_W_m2_K)] * len(clock),
                ambient_temperature_K=[ambient] * len(clock),
            ),
            maximum_step_s=step,
            nonlinear_absolute_tolerance_K=1e-9,
            nonlinear_relative_tolerance=1e-11,
            maximum_nonlinear_iterations=20,
            maximum_relative_energy_balance_error=1e-8,
            one_dimensional_geometry_reviewed=True,
            material_property_support_reviewed=True,
            boundary_conditions_reviewed=True,
            phase_change_absent_or_included_in_capacity_reviewed=True,
        )
        result = calculate(
            THERMAL_MODEL,
            inputs,
            RunContext(
                asset_id="thermal-rod-transient",
                location_id="50ss1",
                time_basis="source elapsed seconds downsampled for stored outputs",
            ),
        )
        centres = np.asarray(result.values["cell_centers_m"])
        history = np.asarray(result.values["temperature_history_K"])
        surfaces = np.asarray(result.values["boundary_surface_temperature_K"])[:, 0]
        positions = [0.0, 0.007, 0.014, 0.021, 0.028, 0.035]
        prediction = [surfaces]
        prediction.extend(
            np.asarray([np.interp(position, centres, row) for row in history]) for position in positions[1:]
        )
        return result, np.asarray(prediction).T

    coarse, coarse_prediction = solve(50, 0.4)
    fine, prediction = solve(100, 0.2)
    observations = (
        raw.iloc[selected][[f"tc{index}_excess_temperature_K" for index in range(1, 7)]].to_numpy() + ambient
    )
    residual = prediction - observations
    rmse = float(np.sqrt(np.mean(residual**2)))
    grid_time_difference = float(np.sqrt(np.mean((prediction - coarse_prediction) ** 2)))
    if rmse > 1.0 or grid_time_difference > 0.25:
        raise ValueError(
            "bounded same-data thermal comparison no longer meets declared reproduction criteria"
        )
    return dict(
        dataset_id="thermal-rod-transient",
        run_id="50ss1",
        source_archive_sha256=hashlib.sha256(ARCHIVE.read_bytes()).hexdigest(),
        observations=int(observations.size),
        output_times=len(clock),
        sensor_positions_m=[0.0, 0.007, 0.014, 0.021, 0.028, 0.035],
        fine_cells=100,
        fine_maximum_step_s=0.2,
        root_mean_square_temperature_residual_K=rmse,
        sensor_rmse_K=np.sqrt(np.mean(residual**2, axis=0)).tolist(),
        maximum_absolute_temperature_residual_K=float(np.max(np.abs(residual))),
        coarse_fine_prediction_rms_difference_K=grid_time_difference,
        fine_relative_discrete_energy_balance_error=fine.values[
            "maximum_relative_discrete_energy_balance_error"
        ],
        coarse_relative_discrete_energy_balance_error=coarse.values[
            "maximum_relative_discrete_energy_balance_error"
        ],
        source_reported_same_fit_standard_error_K=float(fitted.fitted_standard_error_K),
        qualification=(
            "External finite-volume reproduction using h, k, boundary-ramp and power fitted by the source "
            "to this same 50ss1 run. This is not an independent calibration holdout, structural thermal-"
            "stress validation, material-property qualification or service prediction."
        ),
    )


def main():
    record = dict(
        schema_version="matintegrity.thermal_gradient_verification.v1",
        checked_at_utc=datetime.now(timezone.utc).isoformat(),
        model_ids=[THERMAL_MODEL, STRESS_MODEL],
        thermal_model_source_sha256=hashlib.sha256(
            (ROOT / "src/matintegrity/models/thermal_transient.py").read_bytes()
        ).hexdigest(),
        reader_source_sha256=hashlib.sha256(
            (ROOT / "src/matintegrity/thermal_data.py").read_bytes()
        ).hexdigest(),
        status="passed",
        analytical=analytical_checks(),
        experiment=experimental_comparison(),
        qualification=(
            "Fourier and thermoelastic checks are authored mathematical verification. The experiment is "
            "a same-data reproduction with source-fitted coefficients and is not independent validation."
        ),
    )
    target = ROOT / "validation/thermal_gradient_math.json"
    target.write_text(json.dumps(record, indent=2, allow_nan=False), encoding="utf-8")
    print(json.dumps(record, indent=2, allow_nan=False))


if __name__ == "__main__":
    main()
