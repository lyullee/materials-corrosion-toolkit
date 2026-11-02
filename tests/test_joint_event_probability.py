import copy

import pytest
from pydantic import ValidationError

from matintegrity.adapters import probability_event
from matintegrity.contracts import RunContext
from matintegrity.registry import default_registry

CONTEXT = RunContext(asset_id="asset", location_id="system", time_basis="mission seconds")


def inputs() -> dict:
    return {
        "distribution_id": "joint-1",
        "asset_id": "asset",
        "location_id": "system",
        "physical_scope_id": "train-1",
        "time_basis": "mission seconds",
        "horizon_start_s": 10.0,
        "horizon_end_s": 20.0,
        "conditioning": "train survived to mission time 10 s",
        "top_event_id": "a-or-b",
        "top_event_definition": "A or B occurs",
        "event_ids": ["a", "b"],
        "event_definitions": ["A occurs", "B occurs"],
        "states": [
            {"event_occurs": [False, False], "probability": 0.75, "top_event_occurs": False},
            {"event_occurs": [True, False], "probability": 0.05, "top_event_occurs": True},
            {"event_occurs": [False, True], "probability": 0.15, "top_event_occurs": True},
            {"event_occurs": [True, True], "probability": 0.05, "top_event_occurs": True},
        ],
        "dependence_basis": "user_supplied_scenario_weights",
        "provider_id": "test",
        "provider_version": "1",
        "source_content_sha256": "a" * 64,
        "common_cause_group_ids": ["shared"],
        "state_space_complete_declared": True,
        "distribution_reviewed": True,
        "normalization_tolerance": 1e-12,
    }


def test_joint_distribution_preserves_dependence_and_top_event_truth_table():
    result = default_registry().run("reliability.joint_event_probability", inputs(), CONTEXT)
    assert result.values["probability_given_survival"] == pytest.approx(0.25)
    assert result.values["event_marginal_probabilities"] == pytest.approx([0.1, 0.2])
    assert result.values["pairwise_joint_probabilities"][0][1] == pytest.approx(0.05)
    assert result.values["pairwise_covariances"][0][1] == pytest.approx(0.03)
    assert result.values["pairwise_phi_coefficients"][0][1] == pytest.approx(0.25)
    assert result.values["independent_reference_probability"] == pytest.approx(0.28)
    assert result.values["dependence_probability_delta"] == pytest.approx(-0.03)


def test_joint_probability_converts_to_period_event_only_on_the_same_clock():
    result = default_registry().run("reliability.joint_event_probability", inputs(), CONTEXT)
    event = probability_event(
        result,
        event_id="a-or-b",
        physical_scope_id="train-1",
        failure_mode="declared-top-event",
        horizon_start_s=10.0,
        horizon_end_s=20.0,
        conditioning="train survived to mission time 10 s",
        common_cause_groups=("shared",),
    )
    assert event.probability_given_survival == pytest.approx(0.25)
    with pytest.raises(ValueError, match="joint distribution interval"):
        probability_event(
            result,
            event_id="a-or-b",
            physical_scope_id="train-1",
            failure_mode="declared-top-event",
            horizon_start_s=0.0,
            horizon_end_s=10.0,
            conditioning="wrong interval",
            common_cause_groups=("shared",),
        )


@pytest.mark.parametrize(
    ("overrides", "message"),
    [
        ({"event_id": "other"}, "event identity"),
        ({"physical_scope_id": "other"}, "physical scope"),
        ({"conditioning": "other"}, "conditioning"),
        ({"common_cause_groups": ()}, "common-cause groups"),
    ],
)
def test_joint_event_adapter_preserves_source_semantics(overrides, message):
    result = default_registry().run("reliability.joint_event_probability", inputs(), CONTEXT)
    arguments = {
        "event_id": "a-or-b",
        "physical_scope_id": "train-1",
        "failure_mode": "declared-top-event",
        "horizon_start_s": 10.0,
        "horizon_end_s": 20.0,
        "conditioning": "train survived to mission time 10 s",
        "common_cause_groups": ("shared",),
    }
    arguments.update(overrides)
    with pytest.raises(ValueError, match=message):
        probability_event(result, **arguments)


@pytest.mark.parametrize("field", ["state_space_complete_declared", "distribution_reviewed"])
def test_unreviewed_joint_distribution_stops(field):
    payload = inputs()
    payload[field] = False
    result = default_registry().run("reliability.joint_event_probability", payload, CONTEXT)
    assert result.status == "needs_data"
    assert result.values == {}


def test_joint_state_space_refuses_missing_duplicate_and_misaligned_states():
    missing = inputs()
    missing["states"] = missing["states"][:-1]
    with pytest.raises(ValidationError, match="enumerate every binary event state"):
        default_registry().run("reliability.joint_event_probability", missing, CONTEXT)
    duplicate = inputs()
    duplicate["states"][3]["event_occurs"] = [False, False]
    with pytest.raises(ValidationError, match="unique and exhaustive"):
        default_registry().run("reliability.joint_event_probability", duplicate, CONTEXT)
    misaligned = inputs()
    misaligned["event_definitions"] = ["A occurs"]
    with pytest.raises(ValidationError, match="identifiers and definitions must align"):
        default_registry().run("reliability.joint_event_probability", misaligned, CONTEXT)


def test_joint_distribution_refuses_bad_normalization_and_context_identity():
    bad = inputs()
    bad["states"][0]["probability"] = 0.70
    with pytest.raises(ValidationError, match="sum to one"):
        default_registry().run("reliability.joint_event_probability", bad, CONTEXT)
    for changed_context in (
        CONTEXT.model_copy(update={"asset_id": "other"}),
        CONTEXT.model_copy(update={"location_id": "other"}),
        CONTEXT.model_copy(update={"time_basis": "other"}),
    ):
        with pytest.raises(ValueError, match="joint-event"):
            default_registry().run(
                "reliability.joint_event_probability", copy.deepcopy(inputs()), changed_context
            )


def test_degenerate_marginal_keeps_undefined_phi_explicit():
    payload = inputs()
    payload["states"] = [
        {"event_occurs": [False, False], "probability": 0.8, "top_event_occurs": False},
        {"event_occurs": [True, False], "probability": 0.0, "top_event_occurs": True},
        {"event_occurs": [False, True], "probability": 0.2, "top_event_occurs": True},
        {"event_occurs": [True, True], "probability": 0.0, "top_event_occurs": True},
    ]
    result = default_registry().run("reliability.joint_event_probability", payload, CONTEXT)
    assert result.values["pairwise_phi_coefficients"][0][1] is None
    assert result.values["zero_probability_state_count"] == 2
