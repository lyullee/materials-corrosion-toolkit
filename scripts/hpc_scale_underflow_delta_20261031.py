"""Tiny targeted scale depletion-underflow checks for an isolated HPC delta."""
from __future__ import annotations

import argparse
import ast
from decimal import Decimal, localcontext
import hashlib
import json
import math
import os
from pathlib import Path

from matintegrity.models.scale_reaction_demand_balance import (
    PlanarScaleReactionDemandBalance,
    ScaleReactionDemandInterval,
    _advance,
    planar_scale_reaction_demand_balance,
)

ROOT = Path(__file__).resolve().parents[1]


def numerical_checks():
    from scipy.integrate import quad

    base = {"assessment_id": "synthetic-depletion-underflow", "physical_scope_id": "synthetic-only",
        "clock_id": "synthetic-seconds", "scale_phase_id": "synthetic-scale", "transported_reactant_id": "synthetic-reactant",
        "demand_reaction_id": "synthetic-demand", "provider_id": "synthetic", "provider_revision": "1",
        "parameter_record_sha256": "f"*64, "initial_scale_thickness_m": 1e-300,
        "scale_molar_volume_m3_mol": 1.0, "transported_reactant_moles_per_scale_mole": 1.0,
        "temperature_support_min_K": 290.0, "temperature_support_max_K": 310.0,
        "fixed_planar_dense_single_phase_and_area_reviewed": True, "quasi_steady_series_resistance_and_reservoir_reviewed": True,
        "stoichiometry_and_surface_consumption_balance_reviewed": True, "interval_parameter_temperature_support_reviewed": True,
        "computational_use_authorized": True,
        "evidence": [{"source_id": "synthetic", "origin": "synthetic", "citation": "Fabricated floating-point boundary checks; not physical parameter support.", "sha256": "f"*64, "license_id": "CC0-1.0"}]}
    def request(concentration, demand=1e100, length=1e-300):
        values = base | {"initial_scale_thickness_m": length, "intervals": [{
            "interval_id": "i0", "start_time_s": 0.0, "end_time_s": 1.0, "temperature_K": 300.0,
            "effective_diffusivity_m2_s": 1.0, "interface_transfer_coefficient_m_s": 1.0,
            "reservoir_driving_concentration_mol_m3": concentration, "scale_consumption_flux_mol_m2_s": demand}]}
        return PlanarScaleReactionDemandBalance.model_validate_json(json.dumps(values))
    with localcontext() as context:
        context.prec = 80
        positive_lower_bound = Decimal("1e-300") / Decimal("1e100")
        assert positive_lower_bound > 0 and float(positive_lower_bound) == 0.0
    records = []
    for concentration, label in ((0.0, "zero-supply-depletion-time-underflow"), (1.0, "positive-supply-event-time-underflow")):
        result = planar_scale_reaction_demand_balance(request(concentration))
        assert result.status == "out_of_scope", result.model_dump(mode="json")
        assert result.values["computed_prefix"] == []
        assert "positive depletion time underflowed to zero" in result.values["reason"]
        try:
            _advance(1e-300, 1.0, concentration, 1e100, 1.0, 160, 1e-12, 1e-9)
        except ArithmeticError as exc:
            assert "positive depletion time underflowed to zero" in str(exc)
        else:
            raise AssertionError("positive depletion time silently returned as zero")
        records.append({"case": label, "status": result.status, "committed_interval_count": 0})
    normal = planar_scale_reaction_demand_balance(request(0.0, demand=2.0, length=1.0))
    assert normal.status == "computed" and normal.values["termination"] == "scale_depleted"
    assert math.isclose(normal.values["termination_time_s"], 0.5, rel_tol=1e-14)
    positive = planar_scale_reaction_demand_balance(request(0.5, demand=2.0, length=1.0))
    reference, error = quad(lambda length: (length+1.0)/(2.0*(length+1.0)-0.5), 0.0, 1.0, epsabs=1e-13, epsrel=1e-13)
    assert positive.status == "computed" and positive.values["termination"] == "scale_depleted"
    assert math.isclose(positive.values["termination_time_s"], reference, rel_tol=1e-12, abs_tol=1e-13)
    stationary = planar_scale_reaction_demand_balance(request(0.0, demand=0.0, length=1e-300))
    assert stationary.status == "computed" and stationary.values["final_thickness_m"] == 1e-300
    return {"underflow_cases": records, "strictly_positive_time_lower_bound_decimal_s": str(positive_lower_bound),
            "normal_zero_supply_event_time_s": 0.5, "positive_supply_independent_quadrature_s": reference,
            "quadrature_error_estimate_s": error, "zero_rate_subnormal_length_preserved": True,
            "premature_zero_thickness_guard_coverage": "static check only, not a demonstrated numeric trigger"}


def static_checks():
    source = (ROOT/"src/matintegrity/models/scale_reaction_demand_balance.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    strings = [node.value for node in ast.walk(tree) if isinstance(node, ast.Constant) and isinstance(node.value, str)]
    assert strings.count("positive depletion time underflowed to zero") == 2
    assert "positive thickness underflowed to zero before the depletion event" in strings
    for contract in (PlanarScaleReactionDemandBalance, ScaleReactionDemandInterval):
        schema = json.loads((ROOT/"docs/schemas"/(contract.__name__+".json")).read_text(encoding="utf-8"))
        assert schema == contract.model_json_schema()
    manifest_path = Path(os.environ["MATINTEGRITY_DELTA_FILE_MANIFEST"])
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    for row in manifest["files"]:
        path = ROOT/row["path"]
        content = path.read_bytes()
        assert len(content) == row["bytes"] and hashlib.sha256(content).hexdigest() == row["sha256"], row["path"]
    assert not (ROOT/"data/raw").exists() and not (ROOT/"data/evidence").exists()
    return {"positive_depletion_time_guard_occurrences": 2, "premature_zero_thickness_guard_present": True,
            "file_count": len(manifest["files"]), "snapshot_scope": "targeted runtime dependency closure, not full project",
            "archive_sha256": manifest["archive_sha256"], "file_manifest_sha256": hashlib.sha256(manifest_path.read_bytes()).hexdigest(),
            "raw_or_evidence_present": False}


def main():
    tasks = {"numeric": numerical_checks, "static": static_checks}
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
        "meaning": "targeted numerical range and source/schema checks; no physical qualification"}, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
