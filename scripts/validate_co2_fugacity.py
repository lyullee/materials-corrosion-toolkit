"""Run bounded, non-experimental software checks for the CoolProp CO2 fugacity adapter."""

from __future__ import annotations

import json
import math
from datetime import datetime, timezone
from pathlib import Path

import CoolProp

from matintegrity.contracts import Evidence
from matintegrity.models.co2_fugacity import (
    CoolPropCo2FugacityRequest,
    CoolPropCo2MixtureFugacityRequest,
    coolprop_co2_fugacity_to_aquasoldb_fields,
    coolprop_co2_fugacity_to_carbonate_fields,
    coolprop_co2_gas_fugacity,
    coolprop_co2_mixture_fugacity_to_aquasoldb_fields,
    coolprop_co2_mixture_fugacity_to_carbonate_fields,
    coolprop_co2_mixture_gas_fugacity,
)

ROOT = Path(__file__).resolve().parents[1]


def _request(case_id: str, temperature_K: float, pressure_Pa: float):
    return CoolPropCo2FugacityRequest(
        assessment_id=case_id,
        temperature_K=temperature_K,
        co2_partial_pressure_Pa=pressure_Pa,
        backend="HEOS",
        pure_component_approximation_reviewed=True,
        single_phase_gas_or_supercritical_reviewed=True,
        review_id=f"synthetic-validation:{case_id}",
        evidence=(
            Evidence(
                source_id="coolprop-low-level-api",
                origin="synthetic",
                citation="Synthetic software check; no experimental data",
            ),
        ),
    )


def main() -> None:
    low_pressure = coolprop_co2_gas_fugacity(_request("low-pressure-gas", 300.0, 100.0))
    if low_pressure.status != "computed":
        raise RuntimeError(f"low-pressure gas state did not compute: {low_pressure.model_dump_json()}")
    phi = low_pressure.values["fugacity_coefficient"]
    fugacity = low_pressure.values["co2_fugacity_Pa"]
    pressure = low_pressure.values["co2_partial_pressure_Pa"]
    if abs(phi - 1.0) > 1e-4:
        raise AssertionError(f"low-pressure gas fugacity coefficient is not near its ideal-gas limit: {phi}")
    if not math.isclose(fugacity, phi * pressure, rel_tol=1e-10, abs_tol=1e-12):
        raise AssertionError(
            "reported fugacity does not match fugacity coefficient times CO2 partial pressure"
        )

    supercritical = coolprop_co2_gas_fugacity(_request("supercritical", 400.0, 10.0e6))
    if supercritical.status != "computed" or supercritical.values["coolprop_phase"] != "supercritical":
        raise AssertionError(
            f"supercritical state was not classified as supported: {supercritical.model_dump_json()}"
        )

    liquid = coolprop_co2_gas_fugacity(_request("compressed-liquid", 280.0, 5.0e6))
    if liquid.status != "out_of_scope" or "co2_fugacity_Pa" in liquid.values:
        raise AssertionError(f"liquid state was not withheld: {liquid.model_dump_json()}")

    carbonate_fields = coolprop_co2_fugacity_to_carbonate_fields(low_pressure.values)
    comparison_fields = coolprop_co2_fugacity_to_aquasoldb_fields(low_pressure.values)
    if carbonate_fields["gas_fugacity_record_digest"] != comparison_fields["fugacity_record_digest"]:
        raise AssertionError("carbonate and AquaSolDB adapters do not preserve the same provider record")
    if comparison_fields["fugacity_temperature_K"] != low_pressure.values["temperature_K"]:
        raise AssertionError("AquaSolDB adapter does not preserve provider temperature")

    mixture_request = CoolPropCo2MixtureFugacityRequest(
        assessment_id="low-pressure-co2-nitrogen-mixture",
        temperature_K=300.0,
        total_pressure_Pa=100.0,
        components=("CarbonDioxide", "Nitrogen"),
        mole_fractions=(0.8, 0.2),
        backend="HEOS",
        mixture_composition_reviewed=True,
        mixture_eos_applicability_reviewed=True,
        single_phase_gas_or_supercritical_reviewed=True,
        review_id="synthetic-mixture-validation",
        evidence=(
            Evidence(
                source_id="coolprop-low-level-api",
                origin="synthetic",
                citation="Synthetic mixture-state software check; no experimental data",
            ),
        ),
    )
    mixture = coolprop_co2_mixture_gas_fugacity(mixture_request)
    if mixture.status != "computed":
        raise RuntimeError(f"low-pressure CO2/N2 mixture did not compute: {mixture.model_dump_json()}")
    mixture_values = mixture.values
    if mixture_values["coolprop_phase"] != "gas":
        raise AssertionError(
            f"low-pressure CO2/N2 mixture was not classified as gas: {mixture.model_dump_json()}"
        )
    if not math.isclose(
        mixture_values["co2_fugacity_Pa"],
        mixture_values["fugacity_coefficient"] * mixture_values["co2_partial_pressure_Pa"],
        rel_tol=1e-8,
        abs_tol=1e-10,
    ):
        raise AssertionError(
            "mixture CO2 fugacity does not match component phi times x_CO2 times total pressure"
        )
    mixture_carbonate = coolprop_co2_mixture_fugacity_to_carbonate_fields(mixture_values)
    mixture_comparison = coolprop_co2_mixture_fugacity_to_aquasoldb_fields(mixture_values)
    if mixture_carbonate["gas_fugacity_record_digest"] != mixture_comparison["fugacity_record_digest"]:
        raise AssertionError(
            "mixture carbonate and AquaSolDB adapters do not preserve the same provider record"
        )

    report = {
        "schema_version": "matintegrity.co2_fugacity_provider_validation.v1",
        "validated_at_utc": datetime.now(timezone.utc).isoformat(),
        "provider": {
            "name": "CoolProp",
            "version": CoolProp.__version__,
            "revision": CoolProp.__gitrevision__,
            "backend": "HEOS",
            "fluid": "CO2",
        },
        "checks": {
            "low_pressure_ideal_gas_limit": {
                "status": "passed",
                "input_temperature_K": 300.0,
                "input_co2_partial_pressure_Pa": 100.0,
                "acceptance_abs_phi_minus_one_max": 1e-4,
                "observed_fugacity_coefficient": phi,
                "observed_fugacity_Pa": fugacity,
                "configuration_digest": low_pressure.values["gas_fugacity_configuration_digest"],
                "record_digest": low_pressure.values["gas_fugacity_record_digest"],
            },
            "fugacity_coefficient_pressure_identity": {
                "status": "passed",
                "observed_co2_partial_pressure_Pa": pressure,
                "observed_fugacity_coefficient": phi,
                "observed_fugacity_Pa": fugacity,
                "relative_tolerance": 1e-10,
            },
            "supercritical_phase_supported": {
                "status": "passed",
                "input_temperature_K": 400.0,
                "input_co2_partial_pressure_Pa": 10.0e6,
                "phase": supercritical.values["coolprop_phase"],
                "observed_fugacity_Pa": supercritical.values["co2_fugacity_Pa"],
                "record_digest": supercritical.values["gas_fugacity_record_digest"],
            },
            "compressed_liquid_withheld": {
                "status": "passed",
                "input_temperature_K": 280.0,
                "input_co2_partial_pressure_Pa": 5.0e6,
                "phase": liquid.values["coolprop_phase"],
                "reason": liquid.values["reason"],
                "fugacity_emitted": "co2_fugacity_Pa" in liquid.values,
            },
            "low_pressure_co2_nitrogen_mixture": {
                "status": "passed",
                "components": list(mixture_request.components),
                "mole_fractions": list(mixture_request.mole_fractions),
                "input_temperature_K": mixture_request.temperature_K,
                "input_total_pressure_Pa": mixture_request.total_pressure_Pa,
                "phase": mixture_values["coolprop_phase"],
                "co2_partial_pressure_Pa": mixture_values["co2_partial_pressure_Pa"],
                "fugacity_coefficient": mixture_values["fugacity_coefficient"],
                "co2_fugacity_Pa": mixture_values["co2_fugacity_Pa"],
                "record_digest": mixture_values["gas_fugacity_record_digest"],
            },
            "carbonate_and_aquasoldb_lineage_preserved": {
                "status": "passed",
                "provider_record_digest": carbonate_fields["gas_fugacity_record_digest"],
                "aquasoldb_record_digest": comparison_fields["fugacity_record_digest"],
                "fugacity_temperature_K": comparison_fields["fugacity_temperature_K"],
            },
            "mixture_carbonate_and_aquasoldb_lineage_preserved": {
                "status": "passed",
                "provider_record_digest": mixture_carbonate["gas_fugacity_record_digest"],
                "aquasoldb_record_digest": mixture_comparison["fugacity_record_digest"],
                "fugacity_temperature_K": mixture_comparison["fugacity_temperature_K"],
            },
        },
        "qualification": "Synthetic software/limit checks only; not experimental EOS validation or mixture-fugacity qualification.",
    }
    target = ROOT / "validation/co2_fugacity_coolprop.json"
    target.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
