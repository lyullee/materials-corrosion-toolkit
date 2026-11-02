import copy
import math

import pytest
from pydantic import ValidationError

from matintegrity.contracts import RunContext
from matintegrity.registry import default_registry

CONTEXT = RunContext(asset_id="asset", location_id="segment", time_basis="mission seconds")


def inputs() -> dict:
    return {
        "estimate_id": "estimate-1",
        "asset_id": "asset",
        "location_id": "segment",
        "physical_scope_id": "pressure-boundary-1",
        "time_basis": "mission seconds",
        "horizon_start_s": 10.0,
        "horizon_end_s": 20.0,
        "conditioning": "pressure boundary survived to mission time 10 s",
        "event_id": "first-loss-of-integrity",
        "event_definition": "first loss of pressure-boundary integrity in the interval",
        "event_probability_meaning": "conditional_first_failure_in_period",
        "latent_variable_ids": ["z1"],
        "proposal_shift": [0.0],
        "sample_ids": ["s0", "s1", "s2", "s3"],
        "proposal_samples": [[-1.0], [0.0], [1.0], [2.0]],
        "event_indicators": [False, False, True, True],
        "design_id": "design-1",
        "design_content_sha256": "a" * 64,
        "proposal_generator_id": "numpy-pcg64",
        "proposal_generator_revision": "2",
        "latent_mapping_id": "mapping-1",
        "latent_mapping_revision": "1",
        "latent_mapping_configuration_sha256": "b" * 64,
        "evaluator_id": "limit-state-1",
        "evaluator_revision": "1",
        "evaluator_configuration_sha256": "c" * 64,
        "confidence_level": 0.95,
        "samples_drawn_from_declared_proposal": True,
        "sample_alignment_reviewed": True,
        "latent_mapping_reviewed": True,
        "event_indicator_reviewed": True,
        "deterministic_evaluator_declared": True,
    }


def test_zero_shift_reduces_exactly_to_crude_monte_carlo():
    result = default_registry().run("reliability.gaussian_mean_shift_importance_sampling", inputs(), CONTEXT)
    assert result.values["probability_given_survival"] == pytest.approx(0.5)
    assert result.values["raw_importance_estimate"] == pytest.approx(0.5)
    assert result.values["importance_weight_mean"] == pytest.approx(1.0)
    assert result.values["effective_sample_size"] == pytest.approx(4.0)
    assert result.values["event_weight_effective_sample_size"] == pytest.approx(2.0)
    assert result.values["probability_standard_error"] == pytest.approx(math.sqrt(1 / 12))
    assert result.probability_semantics == {
        "probability_given_survival": "conditional_first_failure_in_period"
    }


def test_shifted_weights_match_direct_likelihood_ratio():
    payload = inputs()
    payload["proposal_shift"] = [1.0]
    result = default_registry().run("reliability.gaussian_mean_shift_importance_sampling", payload, CONTEXT)
    weights = [math.exp(-row[0] + 0.5) for row in payload["proposal_samples"]]
    expected = (weights[2] + weights[3]) / 4
    assert result.values["raw_importance_estimate"] == pytest.approx(expected)
    assert result.values["self_normalized_probability_diagnostic"] == pytest.approx(
        (weights[2] + weights[3]) / sum(weights)
    )
    assert result.values["importance_weight_mean"] == pytest.approx(sum(weights) / 4)


def test_zero_observed_events_does_not_emit_a_normal_interval():
    payload = inputs()
    payload["event_indicators"] = [False] * 4
    result = default_registry().run("reliability.gaussian_mean_shift_importance_sampling", payload, CONTEXT)
    assert result.values["probability_given_survival"] == 0.0
    assert result.values["normal_confidence_interval_bounded"] is None
    assert result.values["event_weight_effective_sample_size"] == 0.0
    assert any("does not establish zero" in note for note in result.notes)


@pytest.mark.parametrize(
    "field",
    [
        "samples_drawn_from_declared_proposal",
        "sample_alignment_reviewed",
        "latent_mapping_reviewed",
        "event_indicator_reviewed",
        "deterministic_evaluator_declared",
    ],
)
def test_unreviewed_importance_sampling_inputs_stop(field):
    payload = inputs()
    payload[field] = False
    result = default_registry().run("reliability.gaussian_mean_shift_importance_sampling", payload, CONTEXT)
    assert result.status == "needs_data"
    assert result.values == {}


@pytest.mark.parametrize(
    ("mutator", "message"),
    [
        (lambda value: value.update(horizon_end_s=10.0), "positive duration"),
        (lambda value: value.update(latent_variable_ids=["z1", "z1"]), "identifiers must be unique"),
        (lambda value: value.update(proposal_shift=[0.0, 1.0]), "proposal shift must align"),
        (lambda value: value.update(sample_ids=["s0"] * 4), "sample identifiers must be unique"),
        (lambda value: value.update(event_indicators=[True, False]), "must align"),
        (lambda value: value["proposal_samples"].__setitem__(0, [0.0, 1.0]), "must align"),
        (lambda value: value["proposal_shift"].__setitem__(0, math.inf), "finite"),
    ],
)
def test_contract_rejects_misaligned_or_nonfinite_inputs(mutator, message):
    payload = inputs()
    mutator(payload)
    with pytest.raises(ValidationError, match=message):
        default_registry().run("reliability.gaussian_mean_shift_importance_sampling", payload, CONTEXT)


def test_registry_context_must_match_asset_location_and_clock():
    for context in (
        CONTEXT.model_copy(update={"asset_id": "other"}),
        CONTEXT.model_copy(update={"location_id": "other"}),
        CONTEXT.model_copy(update={"time_basis": "calendar seconds"}),
    ):
        with pytest.raises(ValueError, match="must match"):
            default_registry().run(
                "reliability.gaussian_mean_shift_importance_sampling",
                copy.deepcopy(inputs()),
                context,
            )
