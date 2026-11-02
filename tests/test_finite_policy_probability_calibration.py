import math
from copy import deepcopy

import pytest
from pydantic import ValidationError

from matintegrity import evaluate
from matintegrity.adapters import finite_policy_epoch_from_probability_calibration
from matintegrity.contracts import RunContext
from matintegrity.models.inspection import FinitePolicyProbabilityCalibration

CONTEXT = RunContext(asset_id="calibration-study", location_id="reviewed-lab", time_basis="seconds")


def observation(record_id, sequence_id, group_id, partition, state, label, weight=1.0):
    return {
        "record_id": record_id,
        "sequence_id": sequence_id,
        "source_group_id": group_id,
        "partition": partition,
        "observation_time_s": 1.0,
        "true_state_id": state,
        "observed_label_id": label,
        "weight": weight,
    }


def transition(
    record_id,
    sequence_id,
    group_id,
    partition,
    from_state,
    action,
    to_state,
    weight=1.0,
):
    return {
        "record_id": record_id,
        "sequence_id": sequence_id,
        "source_group_id": group_id,
        "partition": partition,
        "interval_start_s": 1.0,
        "interval_end_s": 2.0,
        "from_state_id": from_state,
        "action_id": action,
        "to_state_id": to_state,
        "weight": weight,
    }


def calibration_input():
    return {
        "calibration_id": "reviewed-policy-table-fit-1",
        "states": [
            {"state_id": "healthy", "state_definition": "reviewed healthy state", "is_failure_state": False},
            {
                "state_id": "degraded",
                "state_definition": "reviewed degraded state",
                "is_failure_state": False,
            },
            {"state_id": "failure", "state_definition": "reviewed failure state", "is_failure_state": True},
        ],
        "observation_labels": [
            {"observation_id": "clear", "observation_definition": "reviewed clear label"},
            {"observation_id": "alert", "observation_definition": "reviewed alert label"},
        ],
        "actions": [
            {"action_id": "monitor", "action_definition": "reviewed monitoring action"},
            {"action_id": "repair", "action_definition": "reviewed repair action"},
        ],
        "observation_records": [
            observation("o1", "fit-o-h", "fit-group-o-h", "calibration", "healthy", "clear", 3.0),
            observation("o2", "fit-o-h", "fit-group-o-h", "calibration", "healthy", "alert"),
            observation("o3", "fit-o-d", "fit-group-o-d", "calibration", "degraded", "clear"),
            observation("o4", "fit-o-d", "fit-group-o-d", "calibration", "degraded", "alert", 3.0),
            observation("oh1", "hold-o-h", "hold-group-o-h", "holdout", "healthy", "clear"),
            observation("oh2", "hold-o-d", "hold-group-o-d", "holdout", "degraded", "alert"),
        ],
        "transition_records": [
            transition(
                "t1", "fit-t-hm", "fit-group-t-hm", "calibration", "healthy", "monitor", "healthy", 4.0
            ),
            transition("t2", "fit-t-hm", "fit-group-t-hm", "calibration", "healthy", "monitor", "failure"),
            transition("t3", "fit-t-hr", "fit-group-t-hr", "calibration", "healthy", "repair", "healthy"),
            transition(
                "t4", "fit-t-dm", "fit-group-t-dm", "calibration", "degraded", "monitor", "degraded", 3.0
            ),
            transition(
                "t5", "fit-t-dm", "fit-group-t-dm", "calibration", "degraded", "monitor", "failure", 2.0
            ),
            transition("t6", "fit-t-dr", "fit-group-t-dr", "calibration", "degraded", "repair", "healthy"),
            transition("th1", "hold-t-h", "hold-group-t-h", "holdout", "healthy", "monitor", "healthy"),
            transition("th2", "hold-t-d", "hold-group-t-d", "holdout", "degraded", "monitor", "failure"),
        ],
        "symmetric_pseudocount": 0.0,
        "state_definitions_reviewed": True,
        "physical_state_truth_reviewed": True,
        "observation_labels_reviewed": True,
        "action_assignments_reviewed": True,
        "calibration_holdout_partition_reviewed": True,
        "smoothing_basis_reviewed": True,
        "evidence": [
            {
                "source_id": "authored-policy-calibration-test",
                "origin": "synthetic",
                "citation": "independently authored finite calibration table",
            }
        ],
    }


def run(payload=None):
    return evaluate(
        "inspection.finite_policy_probability_calibration",
        calibration_input() if payload is None else payload,
        CONTEXT,
    )


def test_weighted_tables_and_holdout_metrics_are_exact_and_finite():
    result = run()
    assert result.status == "computed"
    observations = {
        (row["state_id"], row["observation_id"]): row["probability_given_state"]
        for row in result.values["observation_probabilities"]
    }
    transitions = {
        (row["from_state_id"], row["action_id"], row["to_state_id"]): row[
            "probability_given_state_and_action"
        ]
        for row in result.values["transition_probabilities"]
    }
    assert observations[("healthy", "clear")] == pytest.approx(0.75)
    assert observations[("degraded", "alert")] == pytest.approx(0.75)
    assert transitions[("healthy", "monitor", "failure")] == pytest.approx(0.2)
    assert transitions[("degraded", "monitor", "failure")] == pytest.approx(0.4)
    assert result.values["observation_holdout_metrics"]["mean_negative_log_likelihood"] == pytest.approx(
        -math.log(0.75)
    )
    assert result.values["transition_holdout_metrics"]["zero_probability_record_ids"] == []
    assert result.values["record_independence_inferred"] is False
    assert result.values["confidence_intervals_computed"] is False


def test_review_gate_returns_needs_data_without_mutating_input():
    payload = calibration_input()
    payload["physical_state_truth_reviewed"] = False
    original = deepcopy(payload)
    result = run(payload)
    assert result.status == "needs_data"
    assert result.values["calibration_state"] == "review_required"
    assert payload == original


def test_partition_leakage_is_rejected_for_sequence_and_source_group():
    payload = calibration_input()
    payload["observation_records"][-1]["sequence_id"] = "fit-o-d"
    with pytest.raises(ValidationError, match="sequence_id cannot cross"):
        FinitePolicyProbabilityCalibration.model_validate(payload)

    payload = calibration_input()
    payload["transition_records"][-1]["source_group_id"] = "fit-group-t-dm"
    with pytest.raises(ValidationError, match="source_group_id cannot cross"):
        FinitePolicyProbabilityCalibration.model_validate(payload)


def test_unsupported_conditioning_row_requires_data_or_reviewed_smoothing():
    payload = calibration_input()
    payload["transition_records"] = [
        row
        for row in payload["transition_records"]
        if not (row["partition"] == "calibration" and row["action_id"] == "repair")
    ]
    result = run(payload)
    assert result.status == "needs_data"
    assert result.values["calibration_state"] == "unsupported_conditioning_rows"

    payload["symmetric_pseudocount"] = 0.5
    result = run(payload)
    assert result.status == "computed"
    assert len(result.values["transition_probabilities"]) == 12


def test_zero_probability_holdout_event_is_reported_without_clipping():
    payload = calibration_input()
    payload["observation_records"] = [
        row
        for row in payload["observation_records"]
        if not (
            row["partition"] == "calibration"
            and row["true_state_id"] == "healthy"
            and row["observed_label_id"] == "alert"
        )
    ]
    payload["observation_records"][-2]["observed_label_id"] = "alert"
    result = run(payload)
    metrics = result.values["observation_holdout_metrics"]
    assert metrics["mean_negative_log_likelihood"] is None
    assert metrics["zero_probability_record_ids"] == ["oh1"]


def test_unknown_labels_and_nonpositive_intervals_are_rejected():
    payload = calibration_input()
    payload["observation_records"][0]["observed_label_id"] = "unknown"
    with pytest.raises(ValidationError, match="unknown observation label"):
        FinitePolicyProbabilityCalibration.model_validate(payload)

    payload = calibration_input()
    payload["transition_records"][0]["interval_end_s"] = 1.0
    with pytest.raises(ValidationError, match="positive duration"):
        FinitePolicyProbabilityCalibration.model_validate(payload)


def test_calibration_result_composes_into_a_finite_policy_epoch():
    result = run()
    epoch = finite_policy_epoch_from_probability_calibration(
        result,
        stage_id="epoch-1",
        stage_time_s=100.0,
        decision_rules=[
            {"observation_id": "clear", "action_id": "monitor"},
            {"observation_id": "alert", "action_id": "repair"},
        ],
        actions=[
            {
                "action_id": "monitor",
                "action_definition": "reviewed monitoring action",
                "action_model_id": "synthetic.monitor",
                "action_model_revision": "1",
                "action_model_configuration_sha256": "1" * 64,
                "action_model_input_sha256": "2" * 64,
                "cost_components": [],
            },
            {
                "action_id": "repair",
                "action_definition": "reviewed repair action",
                "action_model_id": "synthetic.repair",
                "action_model_revision": "1",
                "action_model_configuration_sha256": "3" * 64,
                "action_model_input_sha256": "4" * 64,
                "cost_components": [],
            },
        ],
        failure_consequence_present_value_factor_by_state_id={"failure": 0.9},
    )
    assert len(epoch["observation_probabilities"]) == 4
    assert len(epoch["transition_probabilities"]) == 12
    assert {row["action_id"] for row in epoch["transition_probabilities"]} == {"monitor", "repair"}
    assert all(
        (row["to_state_id"] == "failure") == (row["failure_consequence_present_value_factor"] is not None)
        for row in epoch["transition_probabilities"]
    )


def test_epoch_adapter_rejects_incomplete_or_misaligned_inputs():
    result = run()
    incomplete = result.model_copy(update={"status": "needs_data"})
    with pytest.raises(ValueError, match="noncomputed"):
        finite_policy_epoch_from_probability_calibration(
            incomplete,
            stage_id="epoch-1",
            stage_time_s=100.0,
            decision_rules=[],
            actions=[],
            failure_consequence_present_value_factor_by_state_id={"failure": 0.9},
        )
