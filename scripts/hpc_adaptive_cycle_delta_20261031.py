"""Focused synthetic/reference and callback-contract checks for cycle-block ODEs."""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
import math
import os
from pathlib import Path

from matintegrity.adaptive_cycle_block_damage import (
    INTERFACE_ID, SOURCE_ID, AdaptiveCycleBlockDamageRequest,
    CycleBlockLawParameter, IntegerCycleDamageBlock,
    evaluate_adaptive_cycle_block_damage, specifications,
)
from matintegrity.contracts import RunContext
from matintegrity.registry import ModelRegistry

ROOT = Path(__file__).resolve().parents[1]


def request(blocks=None, **changes):
    base = {"analysis_id": "synthetic-adaptive-check", "physical_scope_id": "synthetic-only",
        "material_condition_id": "synthetic-material", "cycle_count_basis_id": "synthetic-integer-cycle",
        "provider_id": "synthetic-law", "provider_revision": "1", "provider_configuration_sha256": "a"*64,
        "calibration_sha256": "b"*64, "state_variable_ids": ["z"], "state_units": ["1"],
        "initial_state": [1.0], "minimum_state": [0.0], "maximum_state": [100.0],
        "blocks": blocks if blocks is not None else [block("b0", 10)],
        "initial_step_cycles": 1.0, "minimum_step_cycles": 1e-8, "maximum_step_cycles": 4.0,
        "state_absolute_tolerance": [1e-9], "state_relative_tolerance": 1e-9,
        "damage_absolute_tolerance": 1e-9, "damage_relative_tolerance": 1e-9,
        "ordered_integer_blocks_and_cycle_count_basis_reviewed": True,
        "state_law_and_nonnegative_damage_rate_reviewed": True,
        "initialization_bounds_and_event_meaning_reviewed": True,
        "deterministic_repeat_evaluation_reviewed": True, "adaptive_controls_and_local_error_meaning_reviewed": True,
        "material_calibration_and_usage_rights_reviewed": True, "computational_use_authorized": True,
        "evidence": [{"source_id": "synthetic-law", "origin": "synthetic", "citation": "Fabricated cycle-domain verification laws; no material calibration.", "sha256": "b"*64, "license_id": "CC0-1.0"}]}
    return AdaptiveCycleBlockDamageRequest.model_validate_json(json.dumps(base | changes))


def block(name, count, loading="synthetic"):
    return {"block_id": name, "cycle_population_id": "synthetic-population", "loading_state_id": loading,
            "cycle_count": count, "source_sha256": "c"*64}


def provider_for(x, law):
    def provider(n, state, item):
        derivative, damage = law(n, state[0], item)
        return {"state_derivative_per_cycle": (derivative,), "damage_rate_per_cycle": damage}
    provider.provider_id = x.provider_id
    provider.revision = x.provider_revision
    provider.configuration_sha256 = x.provider_configuration_sha256
    provider.calibration_sha256 = x.calibration_sha256
    provider.state_variable_ids = x.state_variable_ids
    provider.state_units = x.state_units
    provider.cycle_count_basis_id = x.cycle_count_basis_id
    provider.damage_unit = "1"
    return provider


def solve(x, law):
    return evaluate_adaptive_cycle_block_damage(x, provider_for(x, law))


def numerical_checks():
    from scipy.integrate import solve_ivp

    cases = []
    for name, law, expected_state, expected_damage in (
        ("constant", lambda n, z, b: (0.2, 0.03), 3.0, 0.3),
        ("exponential", lambda n, z, b: (0.03*z, 0.01*z), math.exp(0.3), (math.exp(0.3)-1.0)/3.0),
        ("quadratic-decay", lambda n, z, b: (-0.1*z*z, 0.05*z*z), 0.5, 0.25),
    ):
        result = solve(request(), law)
        assert result["status"] == "computed" and result["completed_integer_cycle_count"] == 10
        assert math.isclose(result["final_state"][0], expected_state, rel_tol=3e-7, abs_tol=2e-8), name
        assert math.isclose(result["final_damage"], expected_damage, rel_tol=3e-7, abs_tol=2e-8), name
        assert result["maximum_accepted_scaled_local_error"] <= 1.0
        cases.append({"case": name, "state_error": result["final_state"][0]-expected_state,
                      "damage_error": result["final_damage"]-expected_damage})
    nonlinear = lambda n, z, b: (0.01*math.sin(n)+0.02*z*z, 0.003*z*z)
    reference = solve_ivp(lambda n, y: [0.01*math.sin(n)+0.02*y[0]**2, 0.003*y[0]**2], (0.0, 8.0), [1.0, 0.0], method="DOP853", rtol=1e-12, atol=1e-14)
    assert reference.success
    errors = []
    for tolerance in (1e-5, 1e-7, 1e-9):
        x = request([block("nonlinear", 8)], initial_step_cycles=4.0, state_absolute_tolerance=[tolerance],
                    state_relative_tolerance=tolerance, damage_absolute_tolerance=tolerance, damage_relative_tolerance=tolerance)
        result = solve(x, nonlinear)
        assert result["status"] == "computed"
        error = max(abs(result["final_state"][0]-reference.y[0, -1]), abs(result["final_damage"]-reference.y[1, -1]))
        errors.append(float(error))
    assert errors[-1] < errors[0] and errors[-1] < 2e-7, errors
    same_law = lambda n, z, b: (-0.1*z*z, 0.05*z*z)
    split = solve(request([block("s0", 5), block("s1", 5)]), same_law)
    whole = solve(request(), same_law)
    assert split["status"] == whole["status"] == "computed"
    assert abs(split["final_state"][0]-whole["final_state"][0]) < 2e-7
    assert abs(split["final_damage"]-whole["final_damage"]) < 2e-7
    ordered = [block("add", 2, "add"), block("multiply", 3, "multiply")]
    order_law = lambda n, z, b: (1.0 if b.loading_state_id == "add" else 0.2*z, 0.01*z)
    forward = solve(request(ordered), order_law)
    reverse = solve(request(list(reversed(ordered))), order_law)
    assert forward["status"] == reverse["status"] == "computed"
    assert math.isclose(forward["final_state"][0], 3.0*math.exp(0.6), rel_tol=3e-7)
    assert math.isclose(reverse["final_state"][0], math.exp(0.6)+2.0, rel_tol=3e-7)
    assert abs(forward["final_state"][0]-reverse["final_state"][0]) > 1.0
    budget = solve(request([block("p0", 1), block("p1", 1)], initial_step_cycles=1.0, minimum_step_cycles=1.0,
                           maximum_step_cycles=1.0, maximum_function_evaluations=12), lambda n, z, b: (0.2, 0.03))
    assert budget["status"] == "out_of_scope" and budget["reason"] == "function_evaluation_budget_exhausted"
    assert budget["completed_integer_cycle_count"] == 1 and len(budget["completed_blocks"]) == 1
    assert budget["accepted_local_cycle_coordinate"] == 0.0 and math.isclose(budget["accepted_state"][0], 1.2)
    unresolved = solve(request([block("strict", 1)], initial_step_cycles=1.0, minimum_step_cycles=1.0, maximum_step_cycles=1.0,
        state_absolute_tolerance=[1e-16], state_relative_tolerance=1e-16, damage_absolute_tolerance=1e-16, damage_relative_tolerance=1e-16), lambda n, z, b: (z, 0.0))
    assert unresolved["status"] == "out_of_scope" and unresolved["reason"] == "local_error_tolerance_unresolved_at_step_or_rejection_limit"
    assert unresolved["accepted_steps"] == 0 and unresolved["accepted_state"] == [1.0]
    bound = solve(request([block("bound", 2)], initial_state=[0.0], maximum_state=[0.5], minimum_step_cycles=0.125,
                          initial_step_cycles=1.0, maximum_step_cycles=1.0), lambda n, z, b: (1.0, 0.0))
    assert bound["status"] == "out_of_scope" and bound["event_is_exact"] is False
    assert bound["completed_integer_cycle_count"] == 0 and bound["accepted_state"][0] <= 0.5
    assert bound["accepted_local_cycle_coordinate"] <= 0.5
    event = solve(request([block("damage-event", 2)], damage_event_threshold=0.3, initial_step_cycles=1.0,
                          maximum_step_cycles=1.0), lambda n, z, b: (0.0, 0.2))
    assert event["reason"] == "damage_threshold_bracketed" and event["event_is_exact"] is False
    assert event["accepted_damage"] < 0.3 <= event["trial_event_damage"]
    assert event["event_cycle_bracket"][0] <= 1.5 <= event["event_cycle_bracket"][1]
    assert event["completed_integer_cycle_count"] == 0
    return {"analytic_cases": cases, "DOP853_tolerance_sweep_errors": errors, "block_split": True,
            "block_order_noncommutativity": True, "completed_prefix_preserved": True,
            "function_budget": True, "unresolved_tolerance": True, "state_bound_bracket": True,
            "damage_event_bracket": True, "event_brackets_are_exact_roots": False}


def metadata_checks():
    specs = specifications()
    assert len(specs) == 1 and specs[0].model_id == INTERFACE_ID
    assert specs[0].runtime_dependency_names == ("provider",) and specs[0].source_ids == (SOURCE_ID,)
    schemas = []
    for contract in (AdaptiveCycleBlockDamageRequest, CycleBlockLawParameter, IntegerCycleDamageBlock):
        schema = json.loads((ROOT/"docs/schemas"/(contract.__name__+".json")).read_text(encoding="utf-8"))
        assert schema == contract.model_json_schema(), contract.__name__
        schemas.append(contract.__name__)
    artifact = json.loads((ROOT/"metadata/adaptive_cycle_catalog_snapshot.json").read_text(encoding="utf-8"))
    for name in ("capabilities", "sources"):
        assert artifact["source_catalogs"][name] == artifact["package_catalogs"][name]
    capability = artifact["source_catalogs"]["capabilities"]["row"]
    assert capability["input_schema"] == AdaptiveCycleBlockDamageRequest.model_json_schema()
    assert capability["source_ids"] == [SOURCE_ID] and artifact["parent_capabilities"]
    assert artifact["source_catalogs"]["sources"]["row"]["id"] == SOURCE_ID
    tree = ast.parse((ROOT/"src/matintegrity/registry.py").read_text(encoding="utf-8"))
    assert any(isinstance(node, ast.For) and isinstance(node.iter, (ast.Tuple, ast.List)) and any(isinstance(item, ast.Name) and item.id == "adaptive_cycle_block_damage" for item in node.iter.elts) for node in ast.walk(tree))
    registry = ModelRegistry()
    registry.register(specs[0])
    x = request([block("registered", 1)])
    law = lambda n, z, b: (0.0, 0.01)
    context = RunContext(asset_id="synthetic", location_id="synthetic", time_basis="integer-cycle-count")
    callback = provider_for(x, law)
    result = registry.run(INTERFACE_ID, x, context, runtime_dependencies={"provider": callback})
    assert result.status == "computed" and result.values["damage_unit"] == "1"
    try:
        registry.run(INTERFACE_ID, x, context)
    except ValueError:
        pass
    else:
        raise AssertionError("missing runtime dependency accepted")
    callback.state_units = ("wrong-unit",)
    try:
        evaluate_adaptive_cycle_block_damage(x, callback)
    except ValueError:
        pass
    else:
        raise AssertionError("callback state-unit mismatch accepted")
    changed = provider_for(x, law)
    def mutating(n, state, item):
        mutating.calibration_sha256 = "d"*64
        return changed(n, state, item)
    for key in ("provider_id", "revision", "configuration_sha256", "calibration_sha256", "state_variable_ids", "state_units", "cycle_count_basis_id", "damage_unit"):
        setattr(mutating, key, getattr(changed, key))
    mutation = evaluate_adaptive_cycle_block_damage(x, mutating)
    assert mutation["status"] == "out_of_scope" and mutation["accepted_steps"] == 0
    assert mutation["failure_message"] == "provider_identity_changed"
    extra = provider_for(x, law)
    def extra_key(n, state, item):
        return extra(n, state, item) | {"status": "needs_data"}
    for key in ("provider_id", "revision", "configuration_sha256", "calibration_sha256", "state_variable_ids", "state_units", "cycle_count_basis_id", "damage_unit"):
        setattr(extra_key, key, getattr(extra, key))
    failed = evaluate_adaptive_cycle_block_damage(x, extra_key)
    assert failed["status"] == "out_of_scope" and failed["accepted_steps"] == 0
    assert not (ROOT/"data/raw").exists()
    ast.parse((ROOT/"src/matintegrity/adaptive_cycle_block_damage.py").read_text(encoding="utf-8"))
    snapshot = json.loads(Path(os.environ["MATINTEGRITY_DELTA_FILE_MANIFEST"]).read_text(encoding="utf-8"))
    for record in snapshot["files"]:
        content = (ROOT/record["path"]).read_bytes()
        assert len(content) == record["bytes"] and hashlib.sha256(content).hexdigest() == record["sha256"]
    return {"model_id": INTERFACE_ID, "schemas": schemas, "runtime_dependency_injection": True,
            "missing_dependency_rejected": True, "callback_unit_mismatch_rejected": True,
            "callback_calibration_mutation_rejected": True, "callback_extra_failure_key_rejected": True,
            "archive_sha256": snapshot["archive_sha256"], "source_file_count": len(snapshot["files"]),
            "parent_capabilities": artifact["parent_capabilities"],
            "catalog_parity_scope": "selected metadata and captured full-file hashes; full built-in registry is not executed"}


def main():
    tasks = {"numeric": numerical_checks, "metadata": metadata_checks}
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
        "meaning": "synthetic ODE/software contract checks, not fatigue law calibration or material qualification"}, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
