import json

import pytest

from matintegrity.contracts import RunContext
from matintegrity.models.forming_qualification import FormingProcessSequence, forming_process_sequence
from matintegrity.registry import default_registry

E = {"source_id": "authored", "origin": "synthetic", "citation": "authored process plan"}


def payload():
    return {
        "asset_id": "asset",
        "location_id": "location",
        "component_id": "component",
        "material_id": "material",
        "material_condition_id": "condition",
        "clock_id": "clock",
        "operations": [
            {
                "operation_id": "first",
                "start_time_s": 0.0,
                "end_time_s": 20.0,
                "minimum_temperature_K": 800.0,
                "maximum_temperature_K": 1000.0,
                "finish_temperature_K": 850.0,
                "evidence": [E],
            },
            {
                "operation_id": "last",
                "start_time_s": 40.0,
                "end_time_s": 60.0,
                "minimum_temperature_K": 800.0,
                "maximum_temperature_K": 900.0,
                "finish_temperature_K": 850.0,
                "evidence": [E],
            },
        ],
        "cooling_points": [{"record_id": "cool", "time_s": 30.0, "temperature_K": 500.0, "evidence": [E]}],
        "final_area_reduction_fraction": 0.1,
        "selected_plan": {
            "plan_id": "plan",
            "material_id": "material",
            "material_condition_id": "condition",
            "minimum_operation_count": 1,
            "maximum_operation_count": 3,
            "minimum_forming_temperature_K": 700.0,
            "maximum_forming_temperature_K": 1100.0,
            "maximum_last_operation_temperature_K": 950.0,
            "maximum_single_operation_duration_s": 30.0,
            "maximum_total_operation_duration_s": 50.0,
            "cooling_before_each_subsequent_operation_below_K": 600.0,
            "waiver_branches": [
                {
                    "branch_id": "finish-and-area",
                    "minimum_last_finish_temperature_K": 800.0,
                    "finish_boundary_inclusive": True,
                    "maximum_final_area_reduction_fraction": 0.2,
                    "basis": "authored conditions",
                }
            ],
            "basis": "authored process plan",
            "evidence": [E],
        },
        "operation_ranges_finish_temperatures_and_clock_reviewed": True,
        "cooling_point_location_and_measurement_reviewed": True,
        "final_area_change_and_selected_plan_authority_reviewed": True,
        "evidence": [E],
    }


def calculate(raw):
    return forming_process_sequence(FormingProcessSequence.model_validate_json(json.dumps(raw)))


def test_process_sequence_cooling_and_waiver():
    result = calculate(payload())
    assert result.status == "computed"
    assert result.values["eligible_caller_waiver_branch_ids"] == ["finish-and-area"]
    assert result.values["inter_operation_cooling"][0]["witness_record_ids"] == ["cool"]


@pytest.mark.parametrize("time,temperature", [(20.0, 500.0), (40.0, 500.0), (30.0, 600.0), (30.0, 700.0)])
def test_missing_or_unproven_inter_operation_cooling_does_not_waive(time, temperature):
    raw = payload()
    raw["cooling_points"][0].update(time_s=time, temperature_K=temperature)
    result = calculate(raw)
    assert result.status == "needs_data"
    assert result.values["declared_treatment_requirement"] == "undetermined"


@pytest.mark.parametrize("inclusive,expected", [(True, ["finish-and-area"]), (False, [])])
def test_waiver_finish_boundary_is_explicit(inclusive, expected):
    raw = payload()
    raw["selected_plan"]["waiver_branches"][0].update(
        minimum_last_finish_temperature_K=850.0, finish_boundary_inclusive=inclusive
    )
    result = calculate(raw)
    assert result.status == "computed"
    assert result.values["eligible_caller_waiver_branch_ids"] == expected


def test_missing_area_is_unknown_and_excess_area_requires_treatment():
    raw = payload()
    raw["final_area_reduction_fraction"] = None
    assert calculate(raw).status == "needs_data"
    raw["final_area_reduction_fraction"] = 0.3
    result = calculate(raw)
    assert result.status == "computed"
    assert result.values["declared_treatment_requirement"] == "treatment_required_under_selected_plan"


@pytest.mark.parametrize(
    "field,value",
    [
        ("maximum_total_operation_duration_s", 30.0),
        ("maximum_last_operation_temperature_K", 850.0),
        ("maximum_operation_count", 1),
    ],
)
def test_outside_process_support_cannot_waive(field, value):
    raw = payload()
    raw["selected_plan"][field] = value
    result = calculate(raw)
    assert result.status == "out_of_scope"
    assert result.values["eligible_caller_waiver_branch_ids"] == []


def test_clock_overlap_and_duplicate_operation_are_rejected():
    raw = payload()
    raw["operations"][1]["start_time_s"] = 10.0
    with pytest.raises(ValueError, match="cannot overlap"):
        calculate(raw)
    raw = payload()
    raw["operations"][1]["operation_id"] = "first"
    with pytest.raises(ValueError, match="unique"):
        calculate(raw)


def test_missing_review_and_material_mismatch():
    raw = payload()
    raw["cooling_point_location_and_measurement_reviewed"] = False
    assert calculate(raw).status == "needs_data"
    raw = payload()
    raw["selected_plan"]["material_id"] = "other"
    assert calculate(raw).status == "out_of_scope"


def test_registry_python_json_and_context():
    registry = default_registry()
    value = FormingProcessSequence.model_validate_json(json.dumps(payload()))
    context = RunContext(asset_id="asset", location_id="location", time_basis="synthetic")
    direct = registry.run("fabrication.forming_process_sequence", value, context)
    assert (
        direct.model_dump()
        == registry.run_json(
            "fabrication.forming_process_sequence", value.model_dump_json(), context
        ).model_dump()
    )
    with pytest.raises(ValueError, match="must match"):
        registry.run(
            "fabrication.forming_process_sequence", value, context.model_copy(update={"location_id": "other"})
        )
