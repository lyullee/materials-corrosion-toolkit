import copy
import math

import pytest
from pydantic import ValidationError

from matintegrity.adapters import probability_event
from matintegrity.contracts import RunContext
from matintegrity.registry import default_registry

CONTEXT = RunContext(asset_id="asset", location_id="system", time_basis="mission seconds")


def inputs(*, failure_rate: float = 0.1, repair_rate: float = 0.2) -> dict:
    return {
        "chain_id": "two-state",
        "asset_id": "asset",
        "location_id": "system",
        "physical_scope_id": "train",
        "time_basis": "mission seconds",
        "horizon_start_s": 5.0,
        "horizon_end_s": 15.0,
        "conditioning": "train operational at mission time 5 s",
        "top_event_id": "first-entry-failed",
        "top_event_definition": "first entry into failed during the interval",
        "state_ids": ["operational", "failed"],
        "state_definitions": ["operational", "failed with modeled repair"],
        "initial_state_probabilities": [1.0, 0.0],
        "generator_per_s": [
            [-failure_rate, failure_rate],
            [repair_rate, -repair_rate],
        ],
        "top_event_state_ids": ["failed"],
        "provider_id": "test",
        "provider_version": "1",
        "source_content_sha256": "c" * 64,
        "common_cause_group_ids": [],
        "generator_time_homogeneous_declared": True,
        "state_semantics_reviewed": True,
        "transition_rates_reviewed": True,
        "normalization_tolerance": 1e-12,
        "generator_row_sum_tolerance_per_s": 1e-12,
        "numerical_probability_tolerance": 1e-12,
    }


def test_repairable_two_state_chain_separates_occupancy_and_first_entry():
    result = default_registry().run("reliability.continuous_time_markov_chain", inputs(), CONTEXT)
    duration = 10.0
    failure_rate = 0.1
    repair_rate = 0.2
    total_rate = failure_rate + repair_rate
    expected_failed = failure_rate / total_rate * (1.0 - math.exp(-total_rate * duration))
    expected_first_hit = 1.0 - math.exp(-failure_rate * duration)
    expected_failed_time = (
        failure_rate / total_rate * (duration - (1.0 - math.exp(-total_rate * duration)) / total_rate)
    )
    assert result.values["state_probabilities_at_horizon"] == pytest.approx(
        [1.0 - expected_failed, expected_failed]
    )
    assert result.values["top_event_state_occupancy_probability"] == pytest.approx(expected_failed)
    assert result.values["probability_given_survival"] == pytest.approx(expected_first_hit)
    assert result.values["expected_top_event_state_occupancy_s"] == pytest.approx(expected_failed_time)
    assert result.values["expected_state_occupancy_s"] == pytest.approx(
        [duration - expected_failed_time, expected_failed_time]
    )
    assert result.values["expected_transition_counts"][0][1] == pytest.approx(
        0.1 * (duration - expected_failed_time)
    )
    assert result.values["expected_transition_counts"][1][0] == pytest.approx(0.2 * expected_failed_time)


def test_absorbing_failure_makes_occupancy_equal_first_entry():
    result = default_registry().run(
        "reliability.continuous_time_markov_chain", inputs(repair_rate=0.0), CONTEXT
    )
    expected = 1.0 - math.exp(-1.0)
    assert result.values["probability_given_survival"] == pytest.approx(expected)
    assert result.values["top_event_state_occupancy_probability"] == pytest.approx(expected)


@pytest.mark.parametrize(
    "field",
    [
        "generator_time_homogeneous_declared",
        "state_semantics_reviewed",
        "transition_rates_reviewed",
    ],
)
def test_unreviewed_markov_chain_stops(field):
    payload = inputs()
    payload[field] = False
    result = default_registry().run("reliability.continuous_time_markov_chain", payload, CONTEXT)
    assert result.status == "needs_data"
    assert result.values == {}


@pytest.mark.parametrize(
    ("mutator", "message"),
    [
        (lambda x: x["state_ids"].append("duplicate"), "definitions must align"),
        (lambda x: x["initial_state_probabilities"].__setitem__(0, 0.8), "sum to one"),
        (lambda x: x["generator_per_s"][0].__setitem__(1, -0.1), "off-diagonal"),
        (lambda x: x["generator_per_s"][0].__setitem__(0, -0.2), "row must sum"),
        (lambda x: x.update(top_event_state_ids=["unknown"]), "must belong"),
        (lambda x: x["initial_state_probabilities"].__setitem__(1, 0.1), "sum to one"),
    ],
)
def test_markov_chain_refuses_invalid_state_probability_and_generator(mutator, message):
    payload = inputs()
    mutator(payload)
    with pytest.raises(ValidationError, match=message):
        default_registry().run("reliability.continuous_time_markov_chain", payload, CONTEXT)


def test_markov_chain_refuses_initial_top_event_mass_after_normalization():
    payload = inputs()
    payload["initial_state_probabilities"] = [0.9, 0.1]
    with pytest.raises(ValidationError, match="zero initial top-event mass"):
        default_registry().run("reliability.continuous_time_markov_chain", payload, CONTEXT)


def test_markov_event_adapter_preserves_period_and_semantics():
    result = default_registry().run("reliability.continuous_time_markov_chain", inputs(), CONTEXT)
    arguments = {
        "event_id": "first-entry-failed",
        "physical_scope_id": "train",
        "failure_mode": "declared failure state first entry",
        "horizon_start_s": 5.0,
        "horizon_end_s": 15.0,
        "conditioning": "train operational at mission time 5 s",
        "common_cause_groups": (),
    }
    event = probability_event(result, **arguments)
    assert event.probability_given_survival == pytest.approx(1.0 - math.exp(-1.0))
    with pytest.raises(ValueError, match="first-failure"):
        probability_event(
            result,
            **(arguments | {"probability_key": "top_event_state_occupancy_probability"}),
        )
    invalid_cases = [
        ({"event_id": "other"}, "event identity"),
        ({"physical_scope_id": "other"}, "physical scope"),
        ({"conditioning": "other"}, "conditioning"),
        ({"horizon_end_s": 16.0}, "Markov-chain interval"),
        ({"common_cause_groups": ("other",)}, "common-cause groups"),
    ]
    for overrides, message in invalid_cases:
        with pytest.raises(ValueError, match=message):
            probability_event(result, **(arguments | overrides))


def test_markov_context_identity_is_preserved():
    for changed_context in (
        CONTEXT.model_copy(update={"asset_id": "other"}),
        CONTEXT.model_copy(update={"location_id": "other"}),
        CONTEXT.model_copy(update={"time_basis": "other"}),
    ):
        with pytest.raises(ValueError, match="Markov-chain"):
            default_registry().run(
                "reliability.continuous_time_markov_chain",
                copy.deepcopy(inputs()),
                changed_context,
            )
