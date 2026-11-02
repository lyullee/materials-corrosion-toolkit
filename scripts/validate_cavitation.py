"""Reproduce independent cavitation-margin identities and CoolProp composition."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from matintegrity.contracts import RunContext
from matintegrity.registry import default_registry
from matintegrity.thermo import (
    cavitation_history_inputs_from_coolprop,
    cavitation_inputs_from_coolprop,
)

ROOT = Path(__file__).resolve().parents[1]
MODEL_SOURCE = ROOT / "src/matintegrity/models/degradation.py"
THERMO_SOURCE = ROOT / "src/matintegrity/thermo.py"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate() -> dict:
    inputs = cavitation_inputs_from_coolprop(
        fluid="Water",
        temperature_K=300.0,
        local_static_pressure_Pa=80_000.0,
        characteristic_velocity_m_s=12.0,
        local_pressure_definition="authored local absolute static pressure",
        velocity_definition="authored section mean velocity",
    )
    result = default_registry().run(
        "degradation.cavitation_margin",
        inputs,
        RunContext(
            asset_id="authored-loop",
            location_id="authored-throat",
            time_basis="steady authored screening point",
        ),
    )
    margin = inputs["local_static_pressure_Pa"] - inputs["vapor_pressure_Pa"]
    dynamic = 0.5 * inputs["liquid_density_kg_m3"] * inputs["characteristic_velocity_m_s"] ** 2
    expected = {
        "static_pressure_margin_Pa": margin,
        "static_head_margin_m": margin / (inputs["liquid_density_kg_m3"] * 9.80665),
        "characteristic_dynamic_pressure_Pa": dynamic,
        "local_cavitation_number": margin / dynamic,
    }
    errors = {key: abs(result.values[key] - value) for key, value in expected.items()}
    if max(errors.values()) > 1e-12:
        raise ValueError(f"cavitation identity check failed: {errors}")
    vapor_pressure = inputs["vapor_pressure_Pa"]
    history_inputs = cavitation_history_inputs_from_coolprop(
        history_id="authored-linear-pressure-dip",
        asset_id="authored-loop",
        location_id="authored-throat",
        clock_id="authored-two-second-clock",
        history_origin="synthetic",
        hydraulic_source_digest="e" * 64,
        fluid="Water",
        sample_ids=["t0", "t1", "t2"],
        time_s=[0.0, 1.0, 2.0],
        temperature_K=[300.0, 300.0, 300.0],
        local_static_pressure_Pa=[
            vapor_pressure + 1_000.0,
            vapor_pressure - 1_000.0,
            vapor_pressure + 1_000.0,
        ],
        characteristic_velocity_m_s=[12.0, 12.0, 12.0],
        sample_valid=[True, True, True],
        local_pressure_definition="authored local absolute static pressure",
        velocity_definition="authored section mean velocity",
    )
    history = default_registry().run(
        "degradation.cavitation_history",
        history_inputs,
        RunContext(
            asset_id="authored-loop",
            location_id="authored-throat",
            time_basis="two-second authored linear pressure dip",
        ),
    )
    expected_history = {
        "thermodynamic_possible_intervals_s": [[0.5, 1.5]],
        "total_thermodynamic_possible_duration_s": 1.0,
        "thermodynamic_possible_time_fraction": 0.5,
        "pressure_deficit_exposure_Pa_s": 500.0,
    }
    actual_history = {key: history.values[key] for key in expected_history}
    history_errors = {
        "interval_start_s": abs(actual_history["thermodynamic_possible_intervals_s"][0][0] - 0.5),
        "interval_end_s": abs(actual_history["thermodynamic_possible_intervals_s"][0][1] - 1.5),
        "duration_s": abs(actual_history["total_thermodynamic_possible_duration_s"] - 1.0),
        "fraction": abs(actual_history["thermodynamic_possible_time_fraction"] - 0.5),
        "deficit_Pa_s": abs(actual_history["pressure_deficit_exposure_Pa_s"] - 500.0),
    }
    if len(actual_history["thermodynamic_possible_intervals_s"]) != 1 or max(history_errors.values()) > 1e-12:
        raise ValueError(f"cavitation history check failed: {history_errors}")
    return {
        "schema_version": "matintegrity.cavitation_math.v1",
        "checked_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "passed",
        "model_id": "degradation.cavitation_margin",
        "model_source_sha256": digest(MODEL_SOURCE),
        "thermo_source_sha256": digest(THERMO_SOURCE),
        "property_provider_id": inputs["property_provider_id"],
        "property_provider_version": inputs["property_provider_version"],
        "property_state_digest": inputs["property_state_digest"],
        "temperature_K": inputs["temperature_K"],
        "vapor_pressure_Pa": inputs["vapor_pressure_Pa"],
        "saturated_liquid_density_kg_m3": inputs["liquid_density_kg_m3"],
        "expected": expected,
        "actual": {key: result.values[key] for key in expected},
        "absolute_errors": errors,
        "history_check": {
            "property_history_digest": history_inputs["property_history_digest"],
            "property_state_digests": history_inputs["property_state_digests"],
            "expected": expected_history,
            "actual": actual_history,
            "absolute_errors": history_errors,
        },
        "qualification": (
            "Independent algebraic pressure/head/cavitation-number identities composed with a "
            "versioned CoolProp saturated-liquid state plus exact linear crossing and clipped-deficit "
            "integration checks. This is not validation of nuclei, unsampled transient pressure, inception, "
            "bubble collapse, erosion, material damage, life or experiment agreement."
        ),
    }


if __name__ == "__main__":
    target = ROOT / "validation/cavitation_math.json"
    target.write_text(json.dumps(validate(), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(target)
