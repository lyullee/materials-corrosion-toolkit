"""Reproduce independent annular-section and pressure-boundary checks."""

from __future__ import annotations

import json
import math
from pathlib import Path

from matintegrity.contracts import RunContext
from matintegrity.registry import default_registry

ROOT = Path(__file__).resolve().parents[1]


def relative_error(actual: float, expected: float) -> float:
    return abs(actual - expected) / max(abs(expected), 1.0)


def validate() -> dict:
    inner_radius = 0.006
    outer_radius = 0.008
    axial_amplitude = 10_000.0
    torque_amplitude = 100.0
    internal_pressure = 60e6
    inputs = {
        "reference_section_id": "synthetic-net-annulus",
        "load_case_id": "synthetic-validation",
        "inner_radius_m": inner_radius,
        "outer_radius_m": outer_radius,
        "pressure_evaluation_radius_m": inner_radius,
        "external_axial_force_mean_N": 0.0,
        "external_axial_force_amplitude_N": axial_amplitude,
        "torque_mean_N_m": 0.0,
        "torque_amplitude_N_m": torque_amplitude,
        "axial_torsion_phase_rad": math.pi / 2,
        "internal_pressure_Pa": internal_pressure,
        "external_pressure_Pa": 0.0,
        "closed_ends": True,
    }
    context = RunContext(
        asset_id="synthetic-annulus",
        location_id="declared-reference-section",
        time_basis="static algebraic verification",
    )
    registry = default_registry()
    inner = registry.run("fatigue.pressurized_annulus_load_state", inputs, context).values
    outer = registry.run(
        "fatigue.pressurized_annulus_load_state",
        inputs | {"pressure_evaluation_radius_m": outer_radius},
        context,
    ).values

    area = math.pi * (outer_radius**2 - inner_radius**2)
    polar = math.pi * (outer_radius**4 - inner_radius**4) / 2
    expected = {
        "reference_area_m2": area,
        "polar_second_moment_m4": polar,
        "external_axial_amplitude_Pa": axial_amplitude / area,
        "torsional_shear_amplitude_Pa": torque_amplitude * outer_radius / polar,
        "inner_radial_stress_Pa": -internal_pressure,
        "outer_radial_stress_Pa": 0.0,
        "closed_end_axial_stress_Pa": internal_pressure
        * inner_radius**2
        / (outer_radius**2 - inner_radius**2),
    }
    actual = {
        "reference_area_m2": inner["reference_area_m2"],
        "polar_second_moment_m4": inner["polar_second_moment_m4"],
        "external_axial_amplitude_Pa": inner["external_axial_amplitude_Pa"],
        "torsional_shear_amplitude_Pa": inner["torsional_shear_amplitude_Pa"],
        "inner_radial_stress_Pa": inner["pressure_radial_mean_Pa"],
        "outer_radial_stress_Pa": outer["pressure_radial_mean_Pa"],
        "closed_end_axial_stress_Pa": inner["pressure_axial_mean_Pa"],
    }
    errors = {key: relative_error(actual[key], value) for key, value in expected.items()}
    maximum_error = max(errors.values())
    if maximum_error > 1e-12:
        raise ValueError(f"annular load-state verification exceeded tolerance: {maximum_error}")
    return {
        "schema_version": "matintegrity.pressurized_annulus_math.v1",
        "model_id": "fatigue.pressurized_annulus_load_state",
        "input_case": inputs,
        "expected": expected,
        "actual": actual,
        "relative_errors": errors,
        "maximum_relative_error": maximum_error,
        "tolerance": 1e-12,
        "qualification": (
            "Independent algebraic checks of annular area, polar second moment, nominal axial and "
            "torsional stress, and Lamé radial/closed-end boundary values. This does not validate a "
            "fatigue criterion, notch field, strength curve, life model or physical experiment."
        ),
    }


if __name__ == "__main__":
    target = ROOT / "validation/pressurized_annulus_math.json"
    target.write_text(json.dumps(validate(), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(target)
