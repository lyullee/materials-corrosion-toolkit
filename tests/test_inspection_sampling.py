import json

import pytest

from matintegrity.contracts import RunContext
from matintegrity.models.inspection_sampling import InspectionLotSampling, inspection_lot_sampling
from matintegrity.registry import default_registry

E = {"source_id": "authored", "origin": "synthetic", "citation": "authored lot plan"}


def outcome(unit, result="pass", stage="initial"):
    return {
        "record_id": f"{unit}-{stage}",
        "physical_unit_id": unit,
        "stage": stage,
        "outcome": result,
        "unresolved_basis": "unresolved observation" if result in ("missing", "inconclusive") else None,
        "record_digest": "a" * 64,
        "evidence": [E],
    }


def payload():
    return {
        "asset_id": "asset",
        "location_id": "location",
        "lot_id": "lot",
        "method_id": "method",
        "criterion_id": "criterion",
        "physical_unit_ids": ["a", "b", "c", "d"],
        "selected_initial_unit_ids": ["a", "b"],
        "mandatory_initial_unit_ids": ["a"],
        "outcomes": [outcome("a"), outcome("b")],
        "selected_plan": {
            "plan_id": "plan",
            "initial_sample_fraction": 0.5,
            "minimum_initial_sample_count": 1,
            "failure_count_trigger": 1,
            "expanded_inspection_fraction": 1.0,
            "reuse_initial_definitive_outcomes_for_expanded_coverage": True,
            "basis": "authored plan",
            "evidence": [E],
        },
        "physical_lot_membership_and_sample_selection_reviewed": True,
        "common_method_criterion_and_outcome_authority_reviewed": True,
        "sampling_plan_and_escalation_authority_reviewed": True,
        "evidence": [E],
    }


def calculate(raw):
    return inspection_lot_sampling(InspectionLotSampling.model_validate_json(json.dumps(raw)))


def test_initial_coverage_without_failure_is_complete():
    result = calculate(payload())
    assert result.status == "computed"
    assert result.values["required_initial_count"] == 2
    assert result.values["required_inspection_coverage_complete"]
    assert not result.values["reported_failure_trigger_reached"]


def test_failure_expands_population_and_missing_records_remain_incomplete():
    raw = payload()
    raw["outcomes"][0]["outcome"] = "fail"
    result = calculate(raw)
    assert result.status == "needs_data"
    assert result.values["reported_failed_unit_ids"] == ["a"]
    assert result.values["expanded_units_without_definitive_coverage"] == ["c", "d"]
    raw["outcomes"] += [outcome("c", stage="expanded"), outcome("d", stage="expanded")]
    result = calculate(raw)
    assert result.status == "computed"
    assert result.values["required_inspection_coverage_complete"]
    assert result.values["reported_failed_unit_ids"] == ["a"]


def test_later_pass_never_erases_original_failure_or_trigger():
    raw = payload()
    raw["outcomes"][0]["outcome"] = "fail"
    raw["outcomes"] += [
        outcome("a", stage="expanded"),
        outcome("c", stage="expanded"),
        outcome("d", stage="expanded"),
    ]
    assert calculate(raw).values["reported_failed_unit_ids"] == ["a"]
    assert calculate(raw).values["reported_failure_trigger_reached"]


@pytest.mark.parametrize("status", ["missing", "inconclusive"])
def test_unresolved_outcomes_never_count_as_definitive(status):
    raw = payload()
    raw["outcomes"][0] = outcome("a", status)
    result = calculate(raw)
    assert result.status == "needs_data"
    assert result.values["definitive_initial_count"] == 1


def test_initial_outcome_reuse_policy_is_explicit():
    raw = payload()
    raw["selected_plan"]["reuse_initial_definitive_outcomes_for_expanded_coverage"] = False
    raw["outcomes"][0]["outcome"] = "fail"
    raw["outcomes"] += [outcome("c", stage="expanded"), outcome("d", stage="expanded")]
    result = calculate(raw)
    assert result.status == "needs_data"
    assert result.values["definitive_expanded_coverage_count"] == 2


def test_decimal_fraction_ceiling_does_not_invent_extra_unit():
    raw = payload()
    units = [f"unit-{i}" for i in range(100)]
    raw.update(
        physical_unit_ids=units,
        selected_initial_unit_ids=units[:7],
        mandatory_initial_unit_ids=[],
        outcomes=[outcome(unit) for unit in units[:7]],
    )
    raw["selected_plan"]["initial_sample_fraction"] = 0.07
    result = calculate(raw)
    assert result.status == "computed"
    assert result.values["required_initial_count"] == 7


@pytest.mark.parametrize("mutation", ["duplicate_unit", "orphan", "duplicate_result", "initial_not_selected"])
def test_invalid_membership_and_record_identity_are_rejected(mutation):
    raw = payload()
    if mutation == "duplicate_unit":
        raw["physical_unit_ids"].append("a")
    elif mutation == "orphan":
        raw["outcomes"].append(outcome("outside", stage="expanded"))
    elif mutation == "duplicate_result":
        raw["outcomes"].append(outcome("a"))
    else:
        raw["outcomes"].append(outcome("c"))
    with pytest.raises(ValueError):
        calculate(raw)


def test_mandatory_unit_missing_review_and_impossible_minimum():
    raw = payload()
    raw["mandatory_initial_unit_ids"] = ["c"]
    assert calculate(raw).status == "needs_data"
    raw = payload()
    raw["sampling_plan_and_escalation_authority_reviewed"] = False
    assert not calculate(raw).values["required_inspection_coverage_complete"]
    raw = payload()
    raw["selected_plan"]["minimum_initial_sample_count"] = 5
    assert calculate(raw).status == "out_of_scope"


def test_registry_python_json_and_context():
    registry = default_registry()
    value = InspectionLotSampling.model_validate_json(json.dumps(payload()))
    context = RunContext(asset_id="asset", location_id="location", time_basis="synthetic")
    result = registry.run("inspection.lot_sampling_escalation", value, context)
    assert (
        result.model_dump()
        == registry.run_json(
            "inspection.lot_sampling_escalation", value.model_dump_json(), context
        ).model_dump()
    )
    with pytest.raises(ValueError, match="must match"):
        registry.run(
            "inspection.lot_sampling_escalation", value, context.model_copy(update={"asset_id": "other"})
        )
