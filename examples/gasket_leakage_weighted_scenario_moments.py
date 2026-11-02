"""Synthetic input wiring for descriptive weighted gasket leakage scenarios."""

import json

from matintegrity.contracts import canonical_digest
from matintegrity.gasket_correlated_uncertainty import (
    GasketLeakageCorrelatedScenario,
    GasketLeakageWeightedScenarioMoments,
    evaluate_gasket_leakage_weighted_scenario_moments,
)


def build_synthetic_request() -> GasketLeakageWeightedScenarioMoments:
    """Create digest-consistent synthetic inputs; no material data are included."""
    scenarios = (
        GasketLeakageCorrelatedScenario.model_validate({
            "scenario_id": "synthetic-low",
            "node_contact_pressure_Pa": [0.5e6],
            "common_differential_pressure_Pa": 0.5e6,
            "node_area_m2": [0.01],
            "calibration_flux_by_contact_pressure_and_delta": [[0.0, 4e-9], [0.0, 2e-9]],
        }),
        GasketLeakageCorrelatedScenario.model_validate({
            "scenario_id": "synthetic-high",
            "node_contact_pressure_Pa": [1.5e6],
            "common_differential_pressure_Pa": 1.5e6,
            "node_area_m2": [0.012],
            "calibration_flux_by_contact_pressure_and_delta": [[0.0, 6e-9], [0.0, 3e-9]],
        }),
    )
    scenario_rows = [row.model_dump(mode="json") for row in scenarios]
    scenario_digest = canonical_digest(scenario_rows)
    calibration_digest = "1" * 64
    weight_digest = "2" * 64
    license_id = "synthetic-example-only"
    return GasketLeakageWeightedScenarioMoments.model_validate({
        "scenario_envelope": {
            "assessment_id": "synthetic-weighted-gasket-example",
            "asset_id": "synthetic-asset",
            "joint_id": "synthetic-joint",
            "physical_scope_id": "synthetic-gasket-scope",
            "time_s": 0.0,
            "node_ids": ["synthetic-node"],
            "calibration": {
                "differential_pressure_Pa": [0.0, 1.0e6],
                "rows": [
                    {"contact_pressure_Pa": 0.0, "molar_leak_flux_by_delta_pressure_mol_s_m2": [0.0, 1e-8]},
                    {"contact_pressure_Pa": 2e6, "molar_leak_flux_by_delta_pressure_mol_s_m2": [0.0, 1e-9]},
                ],
            },
            "calibration_provider_id": "synthetic-calibration-provider",
            "calibration_provider_revision": "example-v1",
            "calibration_record_sha256": calibration_digest,
            "scenario_provider_id": "synthetic-scenario-provider",
            "scenario_provider_revision": "example-v1",
            "scenario_set_sha256": scenario_digest,
            "scenarios": scenario_rows,
            "evidence": [
                {"source_id": "synthetic-calibration-provider", "origin": "synthetic",
                 "citation": "Synthetic API wiring values; no gasket performance is claimed.",
                 "sha256": calibration_digest},
                {"source_id": "synthetic-scenario-provider", "origin": "synthetic",
                 "citation": "Synthetic joint scenario manifest for API wiring only.",
                 "sha256": scenario_digest},
            ],
            "usage_rights_evidence": [{
                "source_id": "synthetic-example-rights", "origin": "synthetic",
                "citation": "Synthetic values authored for this example; no third-party data included.",
                "license_id": license_id,
            }],
            "usage_license_id": license_id,
            "joint_scenario_correlation_reviewed": True,
            "scenario_coverage_and_bounds_reviewed": True,
            "calibration_and_joint_match_reviewed": True,
            "area_partition_and_units_reviewed": True,
            "usage_rights_reviewed": True,
            "computational_use_authorized": True,
        },
        "scenario_weights": [0.25, 0.75],
        "weight_semantics": "user_declared_weight",
        "weight_provider_id": "synthetic-weight-provider",
        "weight_provider_revision": "example-v1",
        "weight_record_sha256": weight_digest,
        "weight_evidence": {
            "source_id": "synthetic-weight-provider", "origin": "synthetic",
            "citation": "Synthetic weights authored for API wiring only.", "sha256": weight_digest,
        },
        "weight_usage_rights_evidence": [{
            "source_id": "synthetic-weight-rights", "origin": "synthetic",
            "citation": "Synthetic weights authored for this example.", "license_id": license_id,
        }],
        "weight_usage_license_id": license_id,
        "weight_meaning_reviewed": True,
        "weight_usage_rights_reviewed": True,
        "weight_computational_use_authorized": True,
    })


def main() -> None:
    result = evaluate_gasket_leakage_weighted_scenario_moments(build_synthetic_request())
    print(json.dumps(result.model_dump(mode="json"), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
