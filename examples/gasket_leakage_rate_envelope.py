"""Illustrate a bounded gasket leakage-rate request with synthetic values."""

import json

from matintegrity.models.gasket_leakage_calibration import (
    GasketLeakageRateEnvelope,
    evaluate_gasket_leakage_rate_envelope,
)


def main() -> None:
    request = GasketLeakageRateEnvelope.model_validate({
        "assessment_id": "synthetic-gasket-rate-envelope",
        "asset_id": "synthetic-asset",
        "joint_id": "synthetic-joint",
        "physical_scope_id": "synthetic-gasket-scope",
        "time_s": 0.0,
        "calibration": {
            "differential_pressure_Pa": [0.0, 1.0e6, 2.0e6],
            "rows": [
                {"contact_pressure_Pa": 0.0, "molar_leak_flux_by_delta_pressure_mol_s_m2": [0.0, 1.0e-8, 2.0e-8]},
                {"contact_pressure_Pa": 1.0e6, "molar_leak_flux_by_delta_pressure_mol_s_m2": [0.0, 5.0e-9, 1.0e-8]},
                {"contact_pressure_Pa": 2.0e6, "molar_leak_flux_by_delta_pressure_mol_s_m2": [0.0, 2.0e-9, 4.0e-9]},
            ],
        },
        "nodes": [{
            "node_id": "synthetic-node-1",
            "contact_area_m2": 0.01,
            "minimum_contact_pressure_Pa": 0.5e6,
            "maximum_contact_pressure_Pa": 1.5e6,
            "minimum_differential_pressure_Pa": 0.4e6,
            "maximum_differential_pressure_Pa": 1.6e6,
        }],
        "provider_id": "synthetic-calibration-provider",
        "provider_revision": "1",
        "provider_configuration_sha256": "0" * 64,
        "calibration_record_sha256": "1" * 64,
        "scope_transfer_and_uncertainty_bounds_reviewed": True,
        "calibration_and_joint_match_reviewed": True,
        "computational_use_authorized": True,
        "evidence": [{
            "source_id": "synthetic_gasket_leakage_envelope",
            "origin": "synthetic",
            "citation": "Synthetic API wiring example; no gasket performance is claimed.",
        }],
    })
    result = evaluate_gasket_leakage_rate_envelope(request)
    print(json.dumps(result.model_dump(mode="json"), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
