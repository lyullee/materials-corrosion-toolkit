from copy import deepcopy

import numpy as np
import pytest
from pydantic import ValidationError

from matintegrity import evaluate
from matintegrity.adapters import gaussian_thickness_posterior_sample_inputs
from matintegrity.contracts import RunContext
from matintegrity.models.reliability import LinearThicknessStateSpaceUpdate

CONTEXT = RunContext(asset_id="asset-1", location_id="cml-1", time_basis="elapsed seconds")


def observation(identifier, time_s, thickness_m, partition="update", source="update-group"):
    return {
        "observation_id": identifier,
        "campaign_id": source,
        "physical_location_id": "cml-1",
        "elapsed_time_s": time_s,
        "remaining_thickness_m": thickness_m,
        "measurement_standard_deviation_m": 2e-4,
        "partition": partition,
        "source_group_id": source,
        "measurement_method_id": "ut-reviewed",
        "calibration_id": "block-1",
        "source_content_sha256": ("a" if source == "update-group" else "b") * 64,
        "test_validity_reviewed": True,
    }


def state_space_input() -> dict:
    return {
        "update_id": "state-space-1",
        "asset_id": "asset-1",
        "location_id": "cml-1",
        "physical_scope_id": "circuit-1/cml-1",
        "physical_location_id": "cml-1",
        "time_basis": "elapsed seconds",
        "initial_state_time_s": 0.0,
        "initial_remaining_thickness_mean_m": 0.012,
        "initial_loss_rate_mean_m_s": 1e-10,
        "initial_remaining_thickness_standard_deviation_m": 8e-4,
        "initial_loss_rate_standard_deviation_m_s": 5e-11,
        "initial_thickness_loss_rate_correlation": -0.2,
        "prior_basis_id": "reviewed-prior",
        "prior_source_content_sha256": "c" * 64,
        "transition_model_basis_id": "constant-linear-transition",
        "process_noise_model_id": "additive-state-covariance-rate",
        "process_noise_covariance_rate": [[1e-16, 0.0], [0.0, 1e-28]],
        "measurement_error_model_id": "independent-ut-errors",
        "observations": [
            observation("u-1", 0.0, 0.0119),
            observation("h-1", 5e5, 0.0117, "holdout", "holdout-group"),
            observation("u-2", 1e6, 0.01175),
        ],
        "measurement_errors_independent_declared": True,
        "analysis_end_time_s": 1.5e6,
        "prediction_times_s": [1.5e6, 2e6],
        "credible_level": 0.95,
        "required_thickness_m": 0.006,
        "prior_basis_reviewed": True,
        "transition_model_reviewed": True,
        "process_noise_model_reviewed": True,
        "observation_identities_reviewed": True,
        "measurement_error_model_reviewed": True,
        "prediction_support_reviewed": True,
        "required_thickness_basis_reviewed": True,
        "holdout_source_independence_reviewed": True,
    }


def run(payload=None, context=CONTEXT):
    return evaluate(
        "reliability.linear_thickness_state_space_update",
        state_space_input() if payload is None else payload,
        context,
    )


def test_zero_process_noise_matches_independent_batch_information_solution():
    payload = state_space_input()
    payload["process_noise_covariance_rate"] = [[0.0, 0.0], [0.0, 0.0]]
    result = run(payload)
    update_rows = [row for row in payload["observations"] if row["partition"] == "update"]
    initial_mean = np.asarray(
        [payload["initial_remaining_thickness_mean_m"], payload["initial_loss_rate_mean_m_s"]]
    )
    thickness_sd = payload["initial_remaining_thickness_standard_deviation_m"]
    rate_sd = payload["initial_loss_rate_standard_deviation_m_s"]
    correlation = payload["initial_thickness_loss_rate_correlation"]
    initial_covariance = np.asarray(
        [
            [thickness_sd**2, correlation * thickness_sd * rate_sd],
            [correlation * thickness_sd * rate_sd, rate_sd**2],
        ]
    )
    design = np.asarray(
        [[1.0, -(row["elapsed_time_s"] - payload["initial_state_time_s"])] for row in update_rows]
    )
    observed = np.asarray([row["remaining_thickness_m"] for row in update_rows])
    errors = np.diag([row["measurement_standard_deviation_m"] ** 2 for row in update_rows])
    posterior_covariance = np.linalg.inv(
        np.linalg.inv(initial_covariance) + design.T @ np.linalg.solve(errors, design)
    )
    posterior_mean = posterior_covariance @ (
        np.linalg.solve(initial_covariance, initial_mean) + design.T @ np.linalg.solve(errors, observed)
    )
    transition = np.asarray(
        [
            [1.0, -(payload["analysis_end_time_s"] - payload["initial_state_time_s"])],
            [0.0, 1.0],
        ]
    )
    assert result.values["posterior_covariance"] == pytest.approx(
        transition @ posterior_covariance @ transition.T
    )
    assert [
        result.values["posterior_remaining_thickness_at_state_time_mean_m"],
        result.values["posterior_loss_rate_mean_m_s"],
    ] == pytest.approx(transition @ posterior_mean)


def test_process_noise_expands_future_covariance_by_declared_rate():
    result = run()
    covariance = np.asarray(result.values["posterior_covariance"])
    elapsed = 5e5
    transition = np.asarray([[1.0, -elapsed], [0.0, 1.0]])
    process_rate = np.asarray(state_space_input()["process_noise_covariance_rate"])
    expected = transition @ covariance @ transition.T + process_rate * elapsed
    assert result.values["predicted_remaining_thickness_standard_deviation_m"][1] == pytest.approx(
        expected[0, 0] ** 0.5
    )
    assert (
        result.values["predicted_remaining_thickness_standard_deviation_m"][1]
        > result.values["predicted_remaining_thickness_standard_deviation_m"][0]
    )


def test_holdout_value_changes_diagnostics_but_never_filtered_state():
    first = run()
    payload = state_space_input()
    payload["observations"][1]["remaining_thickness_m"] = 0.009
    second = run(payload)
    assert first.values["posterior_covariance"] == second.values["posterior_covariance"]
    assert first.values["posterior_remaining_thickness_at_state_time_mean_m"] == pytest.approx(
        second.values["posterior_remaining_thickness_at_state_time_mean_m"]
    )
    first_holdout = first.values["observation_diagnostics"][1]
    second_holdout = second.values["observation_diagnostics"][1]
    assert first_holdout["state_updated"] is False
    assert first_holdout["residual_m"] != second_holdout["residual_m"]


def test_state_space_posterior_composes_with_joint_sampler_adapter():
    filtered = run()
    payload = gaussian_thickness_posterior_sample_inputs(
        filtered,
        sample_design_id="state-space-samples",
        assessment_time_s=2e6,
        required_thickness_m=0.006,
        requested_accepted_sample_count=64,
        maximum_candidate_draw_multiplier=20,
        random_seed_uint64=17,
        assessment_conditioning_reviewed=True,
        required_thickness_basis_reviewed=True,
        deterministic_sampler_reviewed=True,
    )
    sampled = evaluate("reliability.gaussian_thickness_posterior_sample_design", payload, CONTEXT)
    assert sampled.status == "computed"
    assert payload["posterior_reference_time_s"] == filtered.values["state_time_s"]
    assert len(sampled.values["samples"]) == 64


def test_review_and_test_validity_gates_withhold_filtering():
    payload = state_space_input()
    payload["process_noise_model_reviewed"] = False
    assert run(payload).status == "needs_data"
    payload = state_space_input()
    payload["observations"][0]["test_validity_reviewed"] = False
    assert run(payload).status == "needs_data"


@pytest.mark.parametrize(
    ("mutate", "message"),
    [
        (
            lambda value: value["observations"].reverse(),
            "strictly increasing",
        ),
        (
            lambda value: value.update(process_noise_covariance_rate=[[1.0]]),
            "two-by-two",
        ),
        (
            lambda value: value.update(process_noise_covariance_rate=[[1.0, 2.0], [2.0, 1.0]]),
            "positive semidefinite",
        ),
        (
            lambda value: value.update(measurement_errors_independent_declared=False),
            "independent measurement-error declaration",
        ),
        (
            lambda value: value.update(analysis_end_time_s=9e5),
            "final observation",
        ),
    ],
)
def test_invalid_state_space_contract_is_rejected(mutate, message):
    payload = state_space_input()
    mutate(payload)
    with pytest.raises(ValidationError, match=message):
        LinearThicknessStateSpaceUpdate.model_validate(payload)


def test_context_and_input_immutability():
    payload = state_space_input()
    original = deepcopy(payload)
    run(payload)
    assert payload == original
    with pytest.raises(ValueError, match="asset and location"):
        run(context=RunContext(asset_id="asset-2", location_id="cml-1", time_basis="elapsed seconds"))
    with pytest.raises(ValueError, match="time basis"):
        run(context=RunContext(asset_id="asset-1", location_id="cml-1", time_basis="calendar seconds"))
