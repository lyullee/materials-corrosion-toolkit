from copy import deepcopy

import pytest
from pydantic import ValidationError

from matintegrity import evaluate
from matintegrity.contracts import RunContext
from matintegrity.models.inspection import ThresholdInspectionSchedule

CONTEXT = RunContext(asset_id="asset-1", location_id="cml-7", time_basis="elapsed seconds")


def schedule_input():
    return {
        "schedule_id": "schedule-1",
        "asset_id": "asset-1",
        "location_id": "cml-7",
        "physical_scope_id": "pipe-circuit-1/cml-7",
        "event_id": "minimum-thickness-first-crossing",
        "event_definition": "first crossing of the caller-declared minimum remaining thickness",
        "assessment_time_s": 1000.0,
        "conditioning": "asset survived without the declared crossing through t=1000 s",
        "event_probability_meaning": "conditional_first_failure_in_period",
        "forecast_model_id": "user.thickness-first-passage",
        "forecast_model_revision": "2026-10-27",
        "forecast_input_sha256": "a" * 64,
        "forecast_points": [
            {
                "forecast_point_id": "t1100",
                "horizon_end_s": 1100.0,
                "cumulative_probability_given_survival": 0.01,
                "cumulative_probability_upper_bound": 0.02,
            },
            {
                "forecast_point_id": "t1300",
                "horizon_end_s": 1300.0,
                "cumulative_probability_given_survival": 0.03,
                "cumulative_probability_upper_bound": 0.05,
            },
            {
                "forecast_point_id": "t1500",
                "horizon_end_s": 1500.0,
                "cumulative_probability_given_survival": 0.07,
                "cumulative_probability_upper_bound": 0.09,
            },
            {
                "forecast_point_id": "t1700",
                "horizon_end_s": 1700.0,
                "cumulative_probability_given_survival": 0.12,
                "cumulative_probability_upper_bound": 0.14,
            },
        ],
        "probability_basis": "estimate",
        "maximum_probability_before_inspection": 0.08,
        "minimum_notice_s": 100.0,
        "maximum_deferral_s": 700.0,
        "forecast_identity_reviewed": True,
        "event_scope_and_conditioning_reviewed": True,
        "cumulative_probability_curve_reviewed": True,
        "scheduling_criterion_user_approved": True,
        "evidence": [
            {
                "source_id": "authored-schedule-test",
                "origin": "synthetic",
                "citation": "independently authored monotone forecast",
            }
        ],
    }


def run(payload=None):
    return evaluate(
        "inspection.threshold_inspection_schedule",
        schedule_input() if payload is None else payload,
        CONTEXT,
    )


def test_latest_compliant_candidate_is_selected_without_interpolation():
    result = run()
    assert result.status == "computed"
    assert result.values["schedule_state"] == "criterion_limited"
    assert result.values["selected_forecast_point_id"] == "t1500"
    assert result.values["selected_inspection_time_s"] == 1500.0
    assert result.values["selected_probability_given_survival"] == 0.07
    assert result.values["next_noncompliant_candidate_time_s"] == 1700.0
    assert result.values["continuous_time_interpolation_performed"] is False
    assert result.values["consequence_optimization_performed"] is False
    assert (
        result.probability_semantics["selected_probability_given_survival"]
        == "conditional_first_failure_in_period"
    )


def test_upper_bound_basis_can_select_an_earlier_candidate():
    payload = schedule_input()
    payload["probability_basis"] = "upper_bound"
    result = run(payload)
    assert result.values["selected_forecast_point_id"] == "t1300"
    assert result.values["selected_probability_given_survival"] == 0.05
    assert result.values["selected_probability_estimate"] == 0.03
    assert result.values["next_noncompliant_candidate_probability"] == 0.09


def test_no_compliant_candidate_requires_an_earlier_forecast_or_user_decision():
    payload = schedule_input()
    payload["maximum_probability_before_inspection"] = 0.005
    result = run(payload)
    assert result.status == "needs_data"
    assert result.values["schedule_state"] == "criterion_exceeded_before_earliest_candidate"
    assert result.values["earliest_candidate_time_s"] == 1100.0
    assert "selected_inspection_time_s" not in result.values


def test_forecast_boundary_is_not_reported_as_an_unbounded_safe_deferral():
    payload = schedule_input()
    payload["maximum_probability_before_inspection"] = 0.2
    payload["maximum_deferral_s"] = 800.0
    result = run(payload)
    assert result.values["schedule_state"] == "forecast_boundary_limited"
    assert result.values["selected_inspection_time_s"] == 1700.0
    assert result.values["forecast_support_end_s"] == 1700.0

    payload["maximum_deferral_s"] = 500.0
    result = run(payload)
    assert result.values["schedule_state"] == "maximum_deferral_limited"
    assert result.values["selected_inspection_time_s"] == 1500.0


def test_missing_review_gate_or_candidate_window_withholds_a_schedule():
    payload = schedule_input()
    payload["forecast_identity_reviewed"] = False
    result = run(payload)
    assert result.status == "needs_data"
    assert result.values["schedule_state"] == "review_required"
    assert result.values["missing_review_gates"] == ["forecast_identity_reviewed"]

    payload = schedule_input()
    payload["minimum_notice_s"] = 10.0
    payload["maximum_deferral_s"] = 50.0
    result = run(payload)
    assert result.status == "needs_data"
    assert result.values["schedule_state"] == "no_candidate_in_allowed_window"


@pytest.mark.parametrize(
    ("mutate", "message"),
    [
        (
            lambda value: value["forecast_points"][1].update(horizon_end_s=1100.0),
            "strictly increase",
        ),
        (
            lambda value: value["forecast_points"][1].update(cumulative_probability_given_survival=0.005),
            "nondecreasing",
        ),
        (
            lambda value: value["forecast_points"][1].update(cumulative_probability_upper_bound=0.02),
            "upper bound cannot be below",
        ),
        (
            lambda value: value["forecast_points"][1].update(forecast_point_id="t1100"),
            "IDs must be unique",
        ),
    ],
)
def test_invalid_forecast_curves_are_rejected(mutate, message):
    payload = schedule_input()
    mutate(payload)
    with pytest.raises(ValidationError, match=message):
        ThresholdInspectionSchedule.model_validate(payload)


def test_upper_bound_basis_requires_complete_bounds_and_context_identity():
    payload = schedule_input()
    payload["probability_basis"] = "upper_bound"
    payload["forecast_points"][2]["cumulative_probability_upper_bound"] = None
    with pytest.raises(ValidationError, match="bound at every"):
        ThresholdInspectionSchedule.model_validate(payload)

    wrong_context = RunContext(asset_id="asset-2", location_id="cml-7", time_basis="elapsed seconds")
    with pytest.raises(ValueError, match="run context"):
        evaluate("inspection.threshold_inspection_schedule", schedule_input(), wrong_context)


def test_input_is_not_mutated_by_execution():
    payload = schedule_input()
    original = deepcopy(payload)
    run(payload)
    assert payload == original
