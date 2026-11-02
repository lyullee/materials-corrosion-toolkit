"""Reproduce analytical and CoolProp winterization checks."""

from __future__ import annotations

import hashlib
import json
import math
from datetime import datetime, timezone
from pathlib import Path

from matintegrity.models import fabrication
from matintegrity.models.fabrication import WinterizationInventory, winterization_inventory
from matintegrity.thermo import winterization_inputs_from_coolprop

ROOT = Path(__file__).resolve().parents[1]


def main():
    mass, heat_capacity, conductance = 100.0, 4180.0, 50.0
    initial, ambient, threshold, duration = 300.0, 260.0, 280.0, 10000.0
    request = WinterizationInventory(
        case_id="authored-closed-form",
        fluid_id="authored-fluid",
        pressure_Pa_abs=101325.0,
        inventory_mass_kg=mass,
        initial_bulk_temperature_K=initial,
        minimum_allowable_temperature_K=threshold,
        time_s=[0.0, duration],
        interval_ambient_temperature_K=[ambient],
        interval_heat_loss_conductance_W_K=[conductance],
        interval_heat_tracing_power_W=[0.0],
        interval_effective_isobaric_heat_capacity_J_kg_K=[heat_capacity],
        property_evaluation_temperature_K=[290.0],
        property_phase=["liquid"],
        property_provider_id="authored-constant-cp",
        property_provider_version="1",
        property_history_digest="0" * 64,
        inventory_and_mixing_reviewed=True,
        conductance_history_reviewed=True,
        heat_tracing_history_reviewed=True,
        property_states_reviewed=True,
        minimum_temperature_reviewed=True,
    )
    calculation = winterization_inventory(request)
    expected_temperature = ambient + (initial - ambient) * math.exp(
        -conductance * duration / (mass * heat_capacity)
    )
    expected_crossing = (
        -mass * heat_capacity / conductance * math.log((threshold - ambient) / (initial - ambient))
    )
    temperature_error = abs(calculation.values["bulk_temperature_K"][-1] - expected_temperature)
    crossing_error = abs(calculation.values["first_minimum_temperature_crossing_s"] - expected_crossing)
    stored_energy = mass * heat_capacity * (expected_temperature - initial)
    energy_residual = abs(
        calculation.values["cumulative_heat_tracing_energy_J"]
        - calculation.values["cumulative_environment_heat_loss_J"]
        - stored_energy
    )

    coolprop_payload = winterization_inputs_from_coolprop(
        case_id="coolprop-water-check",
        fluid="Water",
        pressure_Pa_abs=101325.0,
        inventory_mass_kg=mass,
        initial_bulk_temperature_K=initial,
        minimum_allowable_temperature_K=threshold,
        time_s=[0.0, 1000.0],
        interval_ambient_temperature_K=[270.0],
        interval_heat_loss_conductance_W_K=[20.0],
        interval_heat_tracing_power_W=[100.0],
        property_evaluation_temperature_K=[290.0],
    )
    coolprop_result = winterization_inventory(WinterizationInventory(**coolprop_payload))
    if temperature_error > 1e-12 or crossing_error > 1e-9 or energy_residual > 1e-8:
        raise AssertionError("winterization closed-form validation tolerance exceeded")
    if coolprop_result.status != "computed":
        raise AssertionError("CoolProp-composed winterization case did not compute")

    record = {
        "schema_version": "matintegrity.winterization_validation.v1",
        "checked_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "passed",
        "model_source_sha256": hashlib.sha256(Path(fabrication.__file__).read_bytes()).hexdigest(),
        "validation_source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "closed_form_temperature_absolute_error_K": temperature_error,
        "closed_form_crossing_time_absolute_error_s": crossing_error,
        "energy_balance_absolute_residual_J": energy_residual,
        "coolprop_provider_id": coolprop_payload["property_provider_id"],
        "coolprop_provider_version": coolprop_payload["property_provider_version"],
        "coolprop_phase": coolprop_payload["property_phase"],
        "coolprop_heat_capacity_J_kg_K": coolprop_payload["interval_effective_isobaric_heat_capacity_J_kg_K"],
        "qualification": (
            "Authored constant-coefficient analytical and energy-balance checks plus a CoolProp API "
            "composition check. This is not freeze, phase-change, heat-tracing, field or code validation."
        ),
    }
    target = ROOT / "validation/winterization_math.json"
    target.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(target)


if __name__ == "__main__":
    main()
