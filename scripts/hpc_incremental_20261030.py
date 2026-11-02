"""Focused synthetic model and public-contract checks for the two new APIs.

This command is intended for an isolated compute-node snapshot. It does not
download observations, fit service data, or qualify a physical application.
"""
from __future__ import annotations

import argparse
import ast
import json
import math
from pathlib import Path
import sys

from pydantic import ValidationError

from matintegrity.contracts import canonical_digest
from matintegrity.models.gasket_leakage_map_fit import (
    GasketLeakageFitObservation,
    GasketLeakageMapFit,
    fit_gasket_leakage_map,
)
from matintegrity.models.scale_moving_boundary import (
    PlanarScaleDiffusionReactionHistory,
    ScaleDiffusionReactionInterval,
    planar_scale_diffusion_reaction_history,
)

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
MODEL_IDS = (
    "chemistry.planar_scale_diffusion_reaction_history",
    "fabrication.gasket_leakage_map_fit",
)


def scale_checks():
    from scipy.integrate import solve_ivp

    base = {
        "assessment_id": "synthetic-check", "physical_scope_id": "synthetic-only",
        "clock_id": "synthetic-seconds", "scale_phase_id": "synthetic-phase",
        "transported_species_id": "synthetic-species", "provider_id": "synthetic",
        "provider_revision": "1", "configuration_sha256": "a" * 64,
        "initial_thickness_m": 1e-6, "scale_molar_volume_m3_mol": 1e-5,
        "temperature_support_min_K": 290.0, "temperature_support_max_K": 310.0,
        "fixed_planar_area_dense_single_phase_reviewed": True,
        "quasi_steady_series_resistance_and_reservoir_reviewed": True,
        "signed_driving_force_and_one_to_one_molar_balance_reviewed": True,
        "interval_properties_and_temperature_support_reviewed": True,
        "computational_use_authorized": True,
        "evidence": [{"source_id": "synthetic", "origin": "synthetic", "citation": "Fabricated numerical checks only."}],
    }
    def request(driving, end=10000.0):
        row = {"interval_id": "i0", "start_time_s": 0.0, "end_time_s": end,
               "effective_diffusivity_m2_s": 1e-12, "interface_transfer_coefficient_m_s": 1e-5,
               "signed_reservoir_driving_concentration_mol_m3": driving, "temperature_K": 300.0}
        return PlanarScaleDiffusionReactionHistory.model_validate_json(json.dumps(base | {"intervals": [row]}))
    records = []
    for driving in (0.0, 0.01, 0.1, 1.0, 10.0, -0.01, -0.1):
        req = request(driving)
        result = planar_scale_diffusion_reaction_history(req)
        assert result.status == "computed" and result.values["full_requested_history_completed"]
        coefficient = 1e-5 * 1e-12 * driving
        ref = solve_ivp(lambda t, y: [coefficient / (y[0] + 1e-7)], (0.0, 10000.0), [1e-6], rtol=1e-11, atol=1e-18)
        assert ref.success
        actual, expected = result.values["final_thickness_m"], float(ref.y[0, -1])
        assert math.isclose(actual, expected, rel_tol=2e-9, abs_tol=1e-17), (driving, actual, expected)
        records.append({"driving": driving, "actual_m": actual, "independent_ode_reference_m": expected})
    req = request(-1.0, 100000.0)
    result = planar_scale_diffusion_reaction_history(req)
    expected_depletion_time = (1e-6 * (1e-6 + 2e-7)) / (2e-17)
    assert result.status == "computed" and result.values["termination"] == "scale_depleted"
    assert result.values["final_thickness_m"] == 0.0
    assert math.isclose(result.values["history"][0]["end_time_s"], expected_depletion_time, rel_tol=1e-12)
    payload = request(1.0).model_dump(mode="json")
    payload["computational_use_authorized"] = False
    assert planar_scale_diffusion_reaction_history(PlanarScaleDiffusionReactionHistory.model_validate_json(json.dumps(payload))).status == "needs_data"
    unsupported = request(1.0).model_dump(mode="json")
    unsupported["intervals"][0]["temperature_K"] = 400.0
    try:
        PlanarScaleDiffusionReactionHistory.model_validate_json(json.dumps(unsupported))
    except ValidationError:
        pass
    else:
        raise AssertionError("unsupported interval temperature accepted")
    return {"ode_cases": records, "depletion_time_s": expected_depletion_time,
            "review_gate_checked": True, "temperature_support_rejection_checked": True}


def fit_checks():
    base = {"assessment_id": "synthetic-fit", "joint_scope_id": "synthetic-only", "calibration_id": "synthetic-map",
            "contact_pressure_knots_Pa": [0.0, 1e6], "differential_pressure_knots_Pa": [0.0, 1e5],
            "observation_units_and_scope_reviewed": True, "predeclared_partition_and_source_independence_reviewed": True,
            "bilinear_nonnegative_surface_and_residual_scale_reviewed": True, "pointwise_computational_use_authorized": True,
            "evidence": [{"source_id": "synthetic", "origin": "synthetic", "citation": "Fabricated bilinear function, no observations."}]}
    observations = []
    for i, (u, v) in enumerate(((0.0, 0.0), (0.0, 1.0), (1.0, 0.0), (1.0, 1.0), (0.5, 0.5))):
        observations.append({"observation_id": str(i), "physical_specimen_id": "spec-" + str(i),
            "source_group_id": "group-" + str(i), "source_sha256": "b" * 64,
            "role": "calibration" if i < 4 else "holdout", "contact_pressure_Pa": u * 1e6,
            "differential_pressure_Pa": v * 1e5, "molar_leak_flux_mol_s_m2": 1.0 + 2*u + 3*v + 4*u*v,
            "residual_scale_mol_s_m2": 1.0})
    payload = base | {"observations": observations}
    request = GasketLeakageMapFit.model_validate_json(json.dumps(payload))
    result = fit_gasket_leakage_map(request)
    assert result.status == "computed" and result.values["design_rank"] == 4
    assert result.values["holdout_observation_count"] == 1
    assert max(abs(row["signed_residual_mol_s_m2"]) for row in result.values["observation_results"]) < 1e-9
    changed = json.loads(json.dumps(payload))
    changed["observations"][-1]["molar_leak_flux_mol_s_m2"] = 1000.0
    alternate = fit_gasket_leakage_map(GasketLeakageMapFit.model_validate_json(json.dumps(changed)))
    assert alternate.status == "computed"
    assert alternate.values["calibration_map"] == result.values["calibration_map"], "holdout contaminated fitted map"
    invalid = json.loads(json.dumps(payload))
    invalid["observations"][-1]["source_group_id"] = "group-0"
    try:
        GasketLeakageMapFit.model_validate_json(json.dumps(invalid))
    except ValidationError:
        pass
    else:
        raise AssertionError("cross-partition source group accepted")
    deficient = json.loads(json.dumps(payload))
    for row in deficient["observations"]:
        row["contact_pressure_Pa"] = 0.0
    rank_result = fit_gasket_leakage_map(GasketLeakageMapFit.model_validate_json(json.dumps(deficient)))
    assert rank_result.status == "needs_data" and rank_result.values["design_rank"] < 4
    return {"calibration_map": result.values["calibration_map"], "holdout_noninterference": True,
            "partition_rejection": True, "rank_deficiency_status": rank_result.status}


def schema_checks():
    checked = []
    for contract in (PlanarScaleDiffusionReactionHistory, ScaleDiffusionReactionInterval, GasketLeakageMapFit, GasketLeakageFitObservation):
        path = ROOT / "docs/schemas" / (contract.__name__ + ".json")
        actual = json.loads(path.read_text(encoding="utf-8"))
        assert actual == contract.model_json_schema(), str(path)
        checked.append({"contract": contract.__name__, "schema_sha256": canonical_digest(actual)})
    return {"contracts": checked}


def catalog_checks():
    from matintegrity.registry import default_registry

    registry = default_registry()
    catalog = json.loads((ROOT / "data/catalogs/capabilities.json").read_text(encoding="utf-8"))
    rows = {row["id"]: row for row in catalog["capabilities"]}
    checked = []
    for identifier in MODEL_IDS:
        assert identifier in registry.list_models() and identifier in rows
        assert registry.describe(identifier)["input_schema"] == rows[identifier]["input_schema"]
        parents = [row["id"] for row in rows.values() if row["id"] != identifier and identifier in json.dumps(row)]
        assert parents, "model lacks a parent capability link: " + identifier
        checked.append({"model_id": identifier, "parents": parents})
    for name in ("capabilities", "datasets", "sources"):
        assert (ROOT / "data/catalogs" / (name + ".json")).read_bytes() == (ROOT / "src/matintegrity/catalog_data" / (name + ".json")).read_bytes()
    return {"models": checked, "package_catalog_sync": True}


def source_checks():
    for name in ("scale_moving_boundary.py", "gasket_leakage_map_fit.py"):
        path = ROOT / "src/matintegrity/models" / name
        ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    from scripts.hpc_run_task import source_tree_digest
    digest, count = source_tree_digest(ROOT)
    return {"source_tree_sha256": digest, "source_file_count": count, "ast_checked": list(MODEL_IDS)}


def main():
    tasks = {"scale": scale_checks, "fit": fit_checks, "schemas": schema_checks, "catalog": catalog_checks, "source": source_checks}
    parser = argparse.ArgumentParser()
    parser.add_argument("--task", choices=tasks, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    try:
        details = tasks[args.task]()
    except Exception as exc:
        args.output.write_text(json.dumps({"task": args.task, "status": "failed", "exception_type": type(exc).__name__, "message": str(exc)}, indent=2), encoding="utf-8")
        raise
    args.output.write_text(json.dumps({"task": args.task, "status": "passed", "details": details,
                                       "meaning": "synthetic numerical/software contract checks only; no physical validation"}, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
