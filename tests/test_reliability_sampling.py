"""Unrun deterministic contracts for the native subset-simulation API."""

import pytest

from matintegrity.reliability_sampling import (
    SubsetSimulationRequest,
    run_subset_simulation,
    subset_simulation_event_probability,
)


def _request(**updates):
    values = {
        "estimate_id": "synthetic-subset-run",
        "event_id": "synthetic-limit-state-event",
        "event_definition": "scalar limit state g(z) <= 0",
        "failure_mode": "synthetic first-failure mode",
        "asset_id": "synthetic-asset",
        "location_id": "synthetic-location",
        "physical_scope_id": "synthetic-pressure-boundary",
        "time_basis": "authored demonstration horizon",
        "horizon_start_s": 0.0,
        "horizon_end_s": 100.0,
        "conditioning": "asset survived to horizon start",
        "latent_variable_ids": ("standard-normal-load",),
        "evaluator_id": "authored-linear-limit-state",
        "evaluator_revision": "1",
        "evaluator_configuration_sha256": "c" * 64,
        "random_seed": 7341,
        "samples_per_level": 1200,
        "conditional_probability": 0.1,
        "pcn_beta": 0.6,
        "maximum_levels": 8,
        "latent_mapping_reviewed": True,
        "event_semantics_reviewed": True,
        "event_is_first_failure_in_period_reviewed": True,
        "deterministic_evaluator_declared": True,
    }
    values.update(updates)
    return SubsetSimulationRequest(**values)


def test_pcn_subset_simulation_is_reproducible_and_reports_rare_event():
    request = _request()
    evaluator = lambda z: 2.0 - z[0]
    first = run_subset_simulation(evaluator, request)
    second = run_subset_simulation(evaluator, request)

    assert first.status == "computed"
    assert first.probability_estimate is not None
    assert 0.0 < first.probability_estimate < 1.0
    assert first.level_count >= 2
    assert first.probability_estimate == second.probability_estimate
    assert first.levels == second.levels
    assert first.uncertainty_status == "not_estimated"


def test_incomplete_reviews_withhold_sampling():
    request = _request(latent_mapping_reviewed=False)
    result = run_subset_simulation(lambda z: 1.0 - z[0], request)
    assert result.status == "needs_data"
    assert result.total_limit_state_evaluations == 0
    assert result.probability_estimate is None


def test_reviewed_period_first_failure_exports_neutral_event_contract():
    result = run_subset_simulation(lambda z: 1.0 - z[0], _request())
    event = subset_simulation_event_probability(result)
    assert event.event_id == result.event_id
    assert event.physical_scope_id == result.physical_scope_id
    assert event.probability_given_survival == result.probability_estimate
    assert event.model_result_digest


def test_static_state_probability_cannot_be_promoted_to_period_first_failure():
    request = _request(event_is_first_failure_in_period_reviewed=False)
    result = run_subset_simulation(lambda z: 1.0 - z[0], request)
    with pytest.raises(ValueError, match="first failure"):
        subset_simulation_event_probability(result)


def test_stagnant_threshold_does_not_return_false_rare_event_probability():
    result = run_subset_simulation(lambda z: 1.0, _request())
    assert result.status == "needs_data"
    assert result.probability_estimate is None
    assert result.level_count >= 1


def test_limit_state_must_return_one_finite_real_scalar():
    with pytest.raises(ValueError, match="one scalar"):
        run_subset_simulation(lambda z: [1.0, 2.0], _request())
    with pytest.raises(ValueError, match="non-finite"):
        run_subset_simulation(lambda z: float("nan"), _request())
