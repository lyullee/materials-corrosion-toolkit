"""Actual physical-result to declared-rule module connections for all 63 groups."""

import importlib
import json
import re
from functools import lru_cache
from pathlib import Path

import pytest

from matintegrity.contracts import AssessmentResult, RunContext
from matintegrity.registry import default_registry
from matintegrity.rules import Rule, evaluate_rules

CASES = json.loads(
    (Path(__file__).parent / "data/core_physics_rule_handoff_cases.json").read_text(encoding="utf8")
)["cases"]


@lru_cache(maxsize=1)
def registry():
    return default_registry()


def quantity_at(value, path):
    for part in path.split("."):
        if part == "*":
            value = next(iter(value.values()))
            continue
        match = re.fullmatch(r"([^\[]+)((?:\[\])*)", part)
        if match is None:
            raise KeyError(part)
        value = value[match[1]]
        for _ in range(match[2].count("[]")):
            value = value[0]
    return value


@pytest.mark.parametrize("case", CASES, ids=[f"group-{c['group']:02d}" for c in CASES])
def test_physical_result_reaches_rule_consumer_with_unit_and_source_link(case):
    spec = registry()._models[case["model_id"]]
    dependencies = {name: importlib.import_module(name) for name in spec.runtime_dependency_names}
    if "scipy" in dependencies:
        importlib.import_module("scipy.integrate")
        importlib.import_module("scipy.optimize")
    context = RunContext.model_validate_json(json.dumps(case["context"]))
    result = registry().run_json(
        case["model_id"], json.dumps(case["inputs"]), context, runtime_dependencies=dependencies
    )
    assert result.status == "computed", result.values
    received = AssessmentResult.model_validate_json(result.model_dump_json())
    assert received.context == context
    assert received.input_digest == result.input_digest
    assert received.source_ids == result.source_ids
    assert received.units[case["field"]] == case["unit"]
    actual = quantity_at(received.values, case["field"])
    assert actual == pytest.approx(case["reference_value"], rel=1e-6, abs=1e-12)
    # A caller-authored software threshold demonstrates an actual downstream
    # module call. It does not assert material or equipment acceptance.
    limit = case["reference_value"] + abs(case["reference_value"]) * 1e-5 + 1e-10
    rule = Rule(
        id=f"group-{case['group']}-handoff",
        field=case["field"],
        operator="le",
        expected=limit,
        unit=case["unit"],
        source_id=received.model_id + ":" + received.input_digest,
        rationale="Project-authored numerical handoff test threshold only",
    )
    outcome = evaluate_rules([rule], {case["field"]: actual}, {case["field"]: received.units[case["field"]]})
    assert outcome["outcome"] == "satisfied"
    assert outcome["rules"][0]["source_id"] == rule.source_id
    wrong_unit = evaluate_rules(
        [rule], {case["field"]: actual}, {case["field"]: "deliberately_incompatible_unit"}
    )
    assert wrong_unit["outcome"] == "unknown"
    missing_value = evaluate_rules([rule], {}, {case["field"]: case["unit"]})
    assert missing_value["outcome"] == "unknown"
