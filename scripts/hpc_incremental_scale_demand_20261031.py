"""Focused compute-node checks for the new reduced scale-demand model.

No prior scale/gasket/GSA/crevice test bundle or raw archive is replayed here.
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
from matintegrity.models.scale_reaction_demand_balance import (
    FARADAY_C_MOL,
    PlanarScaleReactionDemandBalance,
    ScaleReactionDemandInterval,
    planar_scale_reaction_demand_balance,
)
from matintegrity.zenodo_deis_import import (
    DeisAdjacentColumnPairView,
    ZenodoDeisDepositorConditionSummary,
)

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
MODEL_ID = "chemistry.planar_scale_reaction_demand_balance"


def numerical_checks():
    import numpy as np
    from scipy.integrate import solve_ivp

    base = {"assessment_id": "synthetic-demand", "physical_scope_id": "synthetic-only",
        "clock_id": "synthetic-seconds", "scale_phase_id": "synthetic-scale",
        "transported_reactant_id": "synthetic-reactant", "demand_reaction_id": "synthetic-demand",
        "provider_id": "synthetic", "provider_revision": "1", "parameter_record_sha256": "e"*64,
        "initial_scale_thickness_m": 1e-6, "scale_molar_volume_m3_mol": 1e-5,
        "transported_reactant_moles_per_scale_mole": 1.0,
        "temperature_support_min_K": 290.0, "temperature_support_max_K": 310.0,
        "thickness_tolerance_m": 1e-16, "time_tolerance_s": 1e-10,
        "fixed_planar_dense_single_phase_and_area_reviewed": True,
        "quasi_steady_series_resistance_and_reservoir_reviewed": True,
        "stoichiometry_and_surface_consumption_balance_reviewed": True,
        "interval_parameter_temperature_support_reviewed": True, "computational_use_authorized": True,
        "evidence": [{"source_id": "synthetic", "origin": "synthetic", "citation": "Fabricated scale-demand reference cases only.", "sha256": "e"*64, "license_id": "CC0-1.0"}]}
    def payload(concentration=1.0, flux=1e-6, duration=20000.0, initial=1e-6):
        return base | {"initial_scale_thickness_m": initial, "intervals": [{
            "interval_id": "i0", "start_time_s": 0.0, "end_time_s": duration,
            "temperature_K": 300.0, "effective_diffusivity_m2_s": 1e-12,
            "interface_transfer_coefficient_m_s": 1e-5,
            "reservoir_driving_concentration_mol_m3": concentration,
            "scale_consumption_flux_mol_m2_s": flux}]}
    cases = []
    for name, concentration, flux, duration, initial in (
        ("supply-only", 1.0, 0.0, 20000.0, 1e-6),
        ("demand-only", 0.0, 1e-6, 20000.0, 1e-6),
        ("demand-only-depletion", 0.0, 1e-6, 200000.0, 1e-6),
        ("growth-to-equilibrium", 1.0, 0.5e-6, 20000.0, 1e-6),
        ("shrink-to-equilibrium", 1.0, 2e-6, 20000.0, 1e-6),
        ("supply-plus-demand-depletion", 0.01, 2e-6, 200000.0, 1e-6),
        ("equilibrium", 1.0, 1e-6, 20000.0, 1e-17/1e-11-1e-7),
    ):
        values = payload(concentration, flux, duration, initial)
        result = planar_scale_reaction_demand_balance(PlanarScaleReactionDemandBalance.model_validate_json(json.dumps(values)))
        assert result.status == "computed", (name, result.model_dump(mode="json"))
        def rhs(_time, state):
            supplied_flux = 0.0 if concentration == 0.0 else 1e-12*concentration/(state[0]+1e-7)
            return [1e-5*(supplied_flux-flux), supplied_flux, flux]
        def depletion(_time, state):
            return state[0]
        depletion.terminal = True
        depletion.direction = -1
        reference = solve_ivp(rhs, (0.0, duration), [initial, 0.0, 0.0], method="DOP853", rtol=1e-11, atol=[1e-19, 1e-12, 1e-12], max_step=min(duration/20.0, 1000.0), events=depletion)
        assert reference.success, name
        final = float(reference.y[0, -1])
        actual = result.values["final_thickness_m"]
        assert math.isclose(actual, max(final, 0.0), rel_tol=2e-8, abs_tol=5e-16), (name, actual, final)
        if reference.t_events[0].size:
            expected_time = float(reference.t_events[0][0])
            assert result.values["termination"] == "scale_depleted"
            assert math.isclose(result.values["termination_time_s"], expected_time, rel_tol=2e-8, abs_tol=1e-6)
            assert result.values["full_requested_history_completed"] is False
        else:
            assert result.values["full_requested_history_completed"] is True
        row = result.values["history"][0]
        assert np.allclose([row["supplied_scale_equivalent_mol_m2"], row["consumed_scale_mol_m2"]], reference.y[1:, -1], rtol=2e-7, atol=1e-9), name
        cases.append({"case": name, "actual_final_m": actual, "independent_ode_final_m": final,
                      "reference_end_time_s": float(reference.t[-1]), "termination": result.values["termination"]})
    steady = payload()
    flux_result = planar_scale_reaction_demand_balance(PlanarScaleReactionDemandBalance.model_validate_json(json.dumps(steady)))
    mapped = json.loads(json.dumps(steady))
    mapped.update({"electrons_per_reaction_extent": 2.0, "consumed_scale_moles_per_reaction_extent": 1.5,
                   "consuming_partial_current_sign": "negative", "signed_partial_current_mapping_reviewed": True})
    mapped["intervals"][0].pop("scale_consumption_flux_mol_m2_s")
    mapped["intervals"][0]["signed_partial_current_density_A_m2"] = -1e-6*2.0*FARADAY_C_MOL/1.5
    current_result = planar_scale_reaction_demand_balance(PlanarScaleReactionDemandBalance.model_validate_json(json.dumps(mapped)))
    assert current_result.status == "computed"
    assert math.isclose(current_result.values["final_thickness_m"], flux_result.values["final_thickness_m"], abs_tol=5e-16)
    wrong_sign = json.loads(json.dumps(mapped))
    wrong_sign["intervals"][0]["signed_partial_current_density_A_m2"] *= -1
    try:
        PlanarScaleReactionDemandBalance.model_validate_json(json.dumps(wrong_sign))
    except ValidationError:
        pass
    else:
        raise AssertionError("opposite consuming partial-current sign accepted")
    divided = json.loads(json.dumps(steady))
    divided["intervals"][0]["end_time_s"] = 10000.0
    second = dict(divided["intervals"][0], interval_id="i1", start_time_s=10000.0, end_time_s=20000.0)
    divided["intervals"].append(second)
    divided_result = planar_scale_reaction_demand_balance(PlanarScaleReactionDemandBalance.model_validate_json(json.dumps(divided)))
    assert divided_result.status == "computed"
    assert math.isclose(divided_result.values["final_thickness_m"], flux_result.values["final_thickness_m"], abs_tol=5e-16)
    absent = planar_scale_reaction_demand_balance(PlanarScaleReactionDemandBalance.model_validate_json(json.dumps(payload(0.0, 1e-6, initial=0.0))))
    assert absent.status == "computed" and absent.values["termination"] == "scale_absent"
    steady["computational_use_authorized"] = False
    assert planar_scale_reaction_demand_balance(PlanarScaleReactionDemandBalance.model_validate_json(json.dumps(steady))).status == "needs_data"
    extreme_cases = []
    for name, value in (("demand-underflow", 1e-300), ("demand-overflow", 1e5)):
        extreme = payload(concentration=0.0, flux=1e-100 if name.endswith("underflow") else 1e308)
        extreme["scale_molar_volume_m3_mol"] = value
        checked = planar_scale_reaction_demand_balance(PlanarScaleReactionDemandBalance.model_validate_json(json.dumps(extreme)))
        assert checked.status == "out_of_scope", (name, checked.model_dump(mode="json"))
        extreme_cases.append({"case": name, "status": checked.status})
    extreme = payload(concentration=1e-100, flux=0.0)
    extreme["scale_molar_volume_m3_mol"] = 1e-300
    checked = planar_scale_reaction_demand_balance(PlanarScaleReactionDemandBalance.model_validate_json(json.dumps(extreme)))
    assert checked.status == "out_of_scope"
    extreme_cases.append({"case": "supply-underflow", "status": checked.status})
    return {"cases": cases, "independent_reference": "DOP853 with independent supply/consumption integrals and zero-thickness event",
            "partial_current_equivalence": True, "opposite_current_sign_rejected": True,
            "interval_partition_invariance": True, "absent_scale_stop": True, "review_gate": True,
            "finite_numeric_boundary_cases": extreme_cases}


def metadata_checks():
    from matintegrity.registry import default_registry
    from scripts.hpc_run_task import source_tree_digest

    contracts = (PlanarScaleReactionDemandBalance, ScaleReactionDemandInterval,
                 DeisAdjacentColumnPairView, ZenodoDeisDepositorConditionSummary)
    schemas = []
    for contract in contracts:
        schema = json.loads((ROOT/"docs/schemas"/(contract.__name__+".json")).read_text(encoding="utf-8"))
        assert schema == contract.model_json_schema(), contract.__name__
        schemas.append({"contract": contract.__name__, "sha256": canonical_digest(schema)})
    catalog = json.loads((ROOT/"data/catalogs/capabilities.json").read_text(encoding="utf-8"))
    rows = {row["id"]: row for row in catalog["capabilities"]}
    registry = default_registry()
    assert registry.describe(MODEL_ID)["input_schema"] == rows[MODEL_ID]["input_schema"]
    source_ids = {row["id"] for row in json.loads((ROOT/"data/catalogs/sources.json").read_text(encoding="utf-8"))["sources"]}
    assert all(source in source_ids for source in rows[MODEL_ID]["source_ids"])
    parents = [row["id"] for row in rows.values() if row["id"] != MODEL_ID and MODEL_ID in json.dumps(row)]
    assert parents
    for name in ("capabilities", "datasets", "sources"):
        assert (ROOT/"data/catalogs"/(name+".json")).read_bytes() == (ROOT/"src/matintegrity/catalog_data"/(name+".json")).read_bytes()
    for relative in ("src/matintegrity/models/scale_reaction_demand_balance.py", "src/matintegrity/zenodo_deis_import.py"):
        ast.parse((ROOT/relative).read_text(encoding="utf-8"), filename=relative)
    digest, count = source_tree_digest(ROOT)
    assert not (ROOT/"data/raw/az-we43-az31-molybdate-eis/Dataset_CorSci.zip").exists()
    return {"schemas": schemas, "model_id": MODEL_ID, "parent_capabilities": parents,
            "source_tree_sha256": digest, "source_file_count": count, "raw_archive_absent_from_source": True}


def main():
    tasks = {"numerical": numerical_checks, "metadata": metadata_checks}
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
        "meaning": "limited numerical/software metadata checks; not protective-scale or corrosion qualification"}, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
