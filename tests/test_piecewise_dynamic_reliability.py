import copy

import numpy as np
import pytest
from pydantic import ValidationError
from scipy.linalg import expm

from matintegrity.adapters import probability_event
from matintegrity.contracts import RunContext
from matintegrity.registry import default_registry

MODEL_ID = "reliability.piecewise_continuous_time_markov_chain"
CONTEXT = RunContext(asset_id="asset", location_id="system", time_basis="mission seconds")


def segment(
    segment_id: str,
    start_s: float,
    end_s: float,
    generator: list[list[float]],
    *,
    reviewed: bool = True,
) -> dict:
    return {
        "segment_id": segment_id,
        "start_s": start_s,
        "end_s": end_s,
        "generator_per_s": generator,
        "transition_basis_id": f"basis:{segment_id}",
        "provider_revision": "1",
        "source_content_sha256": ("a" if segment_id == "first" else "b") * 64,
        "rates_reviewed": reviewed,
    }


def inputs() -> dict:
    return {
        "chain_id": "piecewise-three-state",
        "asset_id": "asset",
        "location_id": "system",
        "physical_scope_id": "train",
        "time_basis": "mission seconds",
        "horizon_start_s": 0.0,
        "horizon_end_s": 10.0,
        "conditioning": "train operational at mission start",
        "top_event_id": "first-entry-failed",
        "top_event_definition": "first entry into failed during the interval",
        "state_ids": ["operational", "degraded", "failed"],
        "state_definitions": ["operational", "degraded", "failed with modeled repair"],
        "initial_state_probabilities": [1.0, 0.0, 0.0],
        "segments": [
            segment(
                "first",
                0.0,
                4.0,
                [[-0.1, 0.1, 0.0], [0.0, -0.2, 0.2], [0.05, 0.0, -0.05]],
            ),
            segment(
                "second",
                4.0,
                10.0,
                [[-0.3, 0.0, 0.3], [0.1, -0.1, 0.0], [0.0, 0.2, -0.2]],
            ),
        ],
        "top_event_state_ids": ["failed"],
        "provider_id": "test",
        "provider_version": "1",
        "source_content_sha256": "c" * 64,
        "common_cause_group_ids": ["shared-power"],
        "state_semantics_reviewed": True,
        "segment_sequence_reviewed": True,
        "normalization_tolerance": 1e-12,
        "generator_row_sum_tolerance_per_s": 1e-12,
        "boundary_time_tolerance_s": 1e-12,
        "numerical_probability_tolerance": 1e-12,
    }


def test_piecewise_chain_matches_manual_sequential_matrix_exponentials():
    payload = inputs()
    result = default_registry().run(MODEL_ID, payload, CONTEXT)
    q1 = np.asarray(payload["segments"][0]["generator_per_s"])
    q2 = np.asarray(payload["segments"][1]["generator_per_s"])
    initial = np.asarray(payload["initial_state_probabilities"])
    expected = initial @ expm(q1 * 4.0) @ expm(q2 * 6.0)
    a1 = q1.copy()
    a2 = q2.copy()
    a1[2, :] = 0.0
    a2[2, :] = 0.0
    expected_first_hit = float((initial @ expm(a1 * 4.0) @ expm(a2 * 6.0))[2])
    assert result.values["state_probabilities_at_horizon"] == pytest.approx(expected)
    assert result.values["probability_given_survival"] == pytest.approx(expected_first_hit)
    assert result.values["segment_ids"] == ["first", "second"]
    assert result.values["boundary_times_s"] == [0.0, 4.0, 10.0]
    assert result.values["first_hit_probability_at_boundaries"][0] == 0.0


def test_constant_generator_split_matches_homogeneous_model():
    generator = [[-0.1, 0.1], [0.2, -0.2]]
    piecewise = inputs()
    piecewise.update(
        state_ids=["operational", "failed"],
        state_definitions=["operational", "failed with repair"],
        initial_state_probabilities=[1.0, 0.0],
        segments=[
            segment("first", 0.0, 3.0, generator),
            segment("second", 3.0, 10.0, generator),
        ],
    )
    homogeneous = {
        key: value
        for key, value in piecewise.items()
        if key
        not in {
            "segments",
            "segment_sequence_reviewed",
            "boundary_time_tolerance_s",
        }
    }
    homogeneous.update(
        generator_per_s=generator,
        generator_time_homogeneous_declared=True,
        transition_rates_reviewed=True,
    )
    piecewise_result = default_registry().run(MODEL_ID, piecewise, CONTEXT)
    homogeneous_result = default_registry().run(
        "reliability.continuous_time_markov_chain", homogeneous, CONTEXT
    )
    for key in (
        "probability_given_survival",
        "state_probabilities_at_horizon",
        "expected_state_occupancy_s",
        "total_expected_transition_count",
    ):
        assert piecewise_result.values[key] == pytest.approx(homogeneous_result.values[key])
    assert np.asarray(piecewise_result.values["expected_transition_counts"]) == pytest.approx(
        np.asarray(homogeneous_result.values["expected_transition_counts"])
    )


def test_caller_segment_order_is_material_and_never_sorted():
    forward = inputs()
    reversed_rates = copy.deepcopy(forward)
    first_generator = reversed_rates["segments"][0]["generator_per_s"]
    second_generator = reversed_rates["segments"][1]["generator_per_s"]
    reversed_rates["segments"][0]["generator_per_s"] = second_generator
    reversed_rates["segments"][1]["generator_per_s"] = first_generator
    forward_result = default_registry().run(MODEL_ID, forward, CONTEXT)
    reverse_result = default_registry().run(MODEL_ID, reversed_rates, CONTEXT)
    assert forward_result.values["state_probabilities_at_horizon"] != pytest.approx(
        reverse_result.values["state_probabilities_at_horizon"]
    )


@pytest.mark.parametrize(
    ("mutator", "message"),
    [
        (lambda x: x["segments"][0].update(start_s=0.1), "must start"),
        (lambda x: x["segments"][1].update(start_s=4.1), "contiguous chronological order"),
        (lambda x: x["segments"][1].update(start_s=3.9), "contiguous chronological order"),
        (lambda x: x["segments"][1].update(end_s=9.9), "must end"),
        (lambda x: x["segments"][1].update(segment_id="first"), "identifiers must be unique"),
        (lambda x: x["segments"][0].update(start_s=5.0, end_s=4.0), "positive duration"),
        (
            lambda x: x["segments"][0]["generator_per_s"][0].__setitem__(1, -0.1),
            "off-diagonal",
        ),
        (
            lambda x: x["segments"][0]["generator_per_s"][0].__setitem__(0, -0.2),
            "row must sum",
        ),
    ],
)
def test_piecewise_chain_refuses_invalid_boundaries_and_generators(mutator, message):
    payload = inputs()
    mutator(payload)
    with pytest.raises(ValidationError, match=message):
        default_registry().run(MODEL_ID, payload, CONTEXT)


@pytest.mark.parametrize("field", ["state_semantics_reviewed", "segment_sequence_reviewed"])
def test_unreviewed_piecewise_chain_stops(field):
    payload = inputs()
    payload[field] = False
    result = default_registry().run(MODEL_ID, payload, CONTEXT)
    assert result.status == "needs_data"
    assert result.values == {}


def test_unreviewed_segment_rates_stop_the_whole_chain():
    payload = inputs()
    payload["segments"][1]["rates_reviewed"] = False
    result = default_registry().run(MODEL_ID, payload, CONTEXT)
    assert result.status == "needs_data"
    assert result.values == {}


def test_piecewise_event_adapter_preserves_identity_and_probability_semantics():
    result = default_registry().run(MODEL_ID, inputs(), CONTEXT)
    arguments = {
        "event_id": "first-entry-failed",
        "physical_scope_id": "train",
        "failure_mode": "declared failure state first entry",
        "horizon_start_s": 0.0,
        "horizon_end_s": 10.0,
        "conditioning": "train operational at mission start",
        "common_cause_groups": ("shared-power",),
    }
    event = probability_event(result, **arguments)
    assert event.probability_given_survival == result.values["probability_given_survival"]
    with pytest.raises(ValueError, match="first-failure"):
        probability_event(
            result,
            **(arguments | {"probability_key": "top_event_state_occupancy_probability"}),
        )
    for overrides, message in (
        ({"event_id": "other"}, "event identity"),
        ({"physical_scope_id": "other"}, "physical scope"),
        ({"conditioning": "other"}, "conditioning"),
        ({"horizon_end_s": 11.0}, "Markov-chain interval"),
        ({"common_cause_groups": ()}, "common-cause groups"),
    ):
        with pytest.raises(ValueError, match=message):
            probability_event(result, **(arguments | overrides))


def test_piecewise_context_identity_is_preserved():
    for changed_context in (
        CONTEXT.model_copy(update={"asset_id": "other"}),
        CONTEXT.model_copy(update={"location_id": "other"}),
        CONTEXT.model_copy(update={"time_basis": "other"}),
    ):
        with pytest.raises(ValueError, match="piecewise Markov-chain"):
            default_registry().run(MODEL_ID, copy.deepcopy(inputs()), changed_context)
