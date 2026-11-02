from copy import deepcopy

import numpy as np
import pytest
from pydantic import ValidationError

from matintegrity import evaluate
from matintegrity.adapters import (
    gaussian_thickness_posterior_sample_inputs,
    sampled_linear_thickness_first_passage_inputs,
)
from matintegrity.contracts import RunContext
from matintegrity.models.reliability import GaussianThicknessPosteriorSampleDesign

CONTEXT = RunContext(asset_id="asset-1", location_id="cml-1", time_basis="elapsed seconds")


def sampling_input() -> dict:
    thickness_sd = 4.0e-4
    rate_sd = 1.0e-11
    correlation = -0.35
    return {
        "sample_design_id": "posterior-design-1",
        "asset_id": "asset-1",
        "location_id": "cml-1",
        "physical_scope_id": "circuit-1/cml-1",
        "physical_location_id": "cml-1",
        "time_basis": "elapsed seconds",
        "posterior_definition_id": "linear-gaussian-posterior-1",
        "posterior_source_sha256": "a" * 64,
        "posterior_reference_time_s": 0.0,
        "assessment_time_s": 0.0,
        "posterior_remaining_thickness_at_reference_mean_m": 0.012,
        "posterior_loss_rate_mean_m_s": 1.0e-10,
        "posterior_covariance": [
            [thickness_sd**2, correlation * thickness_sd * rate_sd],
            [correlation * thickness_sd * rate_sd, rate_sd**2],
        ],
        "required_thickness_m": 0.006,
        "requested_accepted_sample_count": 4000,
        "maximum_candidate_draw_multiplier": 2,
        "random_seed_uint64": 20261027,
        "covariance_symmetry_tolerance": 1e-24,
        "posterior_basis_reviewed": True,
        "covariance_reviewed": True,
        "assessment_conditioning_reviewed": True,
        "required_thickness_basis_reviewed": True,
        "deterministic_sampler_reviewed": True,
    }


def run(payload=None, context=CONTEXT):
    return evaluate(
        "reliability.gaussian_thickness_posterior_sample_design",
        sampling_input() if payload is None else payload,
        context,
    )


def test_deterministic_joint_draws_reproduce_reviewed_gaussian_moments_and_correlation():
    first = run()
    second = run()
    assert first.status == "computed"
    assert first.values["samples"] == second.values["samples"]
    assert first.values["joint_sample_source_sha256"] == second.values["joint_sample_source_sha256"]
    samples = first.values["samples"]
    observed = np.asarray(
        [[row["remaining_thickness_at_assessment_m"], row["nonnegative_loss_rate_m_s"]] for row in samples]
    )
    expected = sampling_input()
    assert np.mean(observed, axis=0) == pytest.approx(
        [
            expected["posterior_remaining_thickness_at_reference_mean_m"],
            expected["posterior_loss_rate_mean_m_s"],
        ],
        rel=0.015,
    )
    assert np.std(observed, axis=0, ddof=1) == pytest.approx(
        [
            expected["posterior_covariance"][0][0] ** 0.5,
            expected["posterior_covariance"][1][1] ** 0.5,
        ],
        rel=0.04,
    )
    assert np.corrcoef(observed.T)[0, 1] == pytest.approx(-0.35, abs=0.035)
    assert first.values["candidate_draw_count"] == len(samples)


def test_rejection_conditioned_samples_compose_with_first_passage_without_reconditioning():
    payload = sampling_input()
    payload.update(
        posterior_loss_rate_mean_m_s=0.0,
        posterior_covariance=[[4e-8, 0.0], [0.0, 1e-20]],
        assessment_time_s=1.0e6,
        requested_accepted_sample_count=100,
        maximum_candidate_draw_multiplier=10,
    )
    sampled = run(payload)
    assert sampled.status == "computed"
    assert sampled.values["negative_loss_rate_candidate_count"] > 0
    assert all(row["nonnegative_loss_rate_m_s"] >= 0.0 for row in sampled.values["samples"])
    assert all(
        row["remaining_thickness_at_assessment_m"] > payload["required_thickness_m"]
        for row in sampled.values["samples"]
    )
    forecast = evaluate(
        "reliability.sampled_linear_thickness_first_passage",
        {
            "forecast_id": "forecast-from-posterior-samples",
            "asset_id": payload["asset_id"],
            "location_id": payload["location_id"],
            "physical_scope_id": payload["physical_scope_id"],
            "physical_location_id": payload["physical_location_id"],
            "time_basis": payload["time_basis"],
            "assessment_time_s": payload["assessment_time_s"],
            "conditioning": sampled.values["conditioning_definition"],
            "event_id": "minimum-thickness-first-crossing",
            "event_definition": "first crossing of the reviewed required thickness",
            "required_thickness_m": payload["required_thickness_m"],
            "distribution_definition_id": sampled.values["distribution_definition_id"],
            "sample_design_id": sampled.values["sample_design_id"],
            "joint_sample_source_sha256": sampled.values["joint_sample_source_sha256"],
            "samples": sampled.values["samples"],
            "candidate_horizon_end_s": [2.0e6, 5.0e7],
            "maximum_weight_sum_error": 1e-12,
            "samples_conditioned_on_survival_to_assessment": sampled.values[
                "samples_conditioned_on_survival_to_assessment"
            ],
            "constant_nonnegative_loss_model_reviewed": True,
            "joint_sample_distribution_reviewed": True,
            "required_thickness_basis_reviewed": True,
            "candidate_horizons_reviewed": True,
        },
        CONTEXT,
    )
    assert forecast.status == "computed"
    assert forecast.values["sample_count"] == 100
    assert forecast.values["failed_samples_discarded"] is False


def test_fixed_candidate_budget_withholds_partial_sample_set():
    payload = sampling_input()
    payload.update(
        posterior_loss_rate_mean_m_s=-1.0,
        posterior_covariance=[[1e-8, 0.0], [0.0, 1e-8]],
        requested_accepted_sample_count=10,
        maximum_candidate_draw_multiplier=1,
    )
    result = run(payload)
    assert result.status == "needs_data"
    assert result.values["sample_design_state"] == "insufficient_accepted_draws"
    assert result.values["accepted_sample_count"] == 0
    assert "samples" not in result.values


def test_review_gate_withholds_draws_but_preserves_identity():
    payload = sampling_input()
    payload["covariance_reviewed"] = False
    result = run(payload)
    assert result.status == "needs_data"
    assert result.values["sample_design_state"] == "review_required"
    assert result.values["missing_review_gates"] == ["covariance_reviewed"]
    assert result.values["posterior_source_sha256"] == "a" * 64


@pytest.mark.parametrize(
    ("mutate", "message"),
    [
        (lambda value: value.update(posterior_covariance=[[1.0]]), "two-by-two"),
        (
            lambda value: value.update(posterior_covariance=[[1e-8, 1e-9], [0.0, 1e-8]]),
            "symmetric",
        ),
        (
            lambda value: value.update(assessment_time_s=-1.0),
            "greater than or equal to 0",
        ),
        (
            lambda value: value.update(
                requested_accepted_sample_count=100_000,
                maximum_candidate_draw_multiplier=1000,
            ),
            "two million",
        ),
    ],
)
def test_invalid_sample_design_is_rejected(mutate, message):
    payload = sampling_input()
    mutate(payload)
    with pytest.raises(ValidationError, match=message):
        GaussianThicknessPosteriorSampleDesign.model_validate(payload)


def test_non_positive_definite_covariance_is_reported_without_draws():
    payload = sampling_input()
    payload["posterior_covariance"] = [[1e-8, 2e-8], [2e-8, 1e-8]]
    result = run(payload)
    assert result.status == "needs_data"
    assert result.values["sample_design_state"] == "invalid_covariance"
    assert "samples" not in result.values


def test_context_identity_and_time_basis_are_enforced():
    with pytest.raises(ValueError, match="asset and location"):
        run(context=RunContext(asset_id="asset-2", location_id="cml-1", time_basis="elapsed seconds"))
    with pytest.raises(ValueError, match="time basis"):
        run(context=RunContext(asset_id="asset-1", location_id="cml-1", time_basis="calendar seconds"))


def test_input_is_not_mutated_and_seed_changes_sample_digest():
    payload = sampling_input()
    original = deepcopy(payload)
    first = run(payload)
    assert payload == original
    payload["random_seed_uint64"] += 1
    second = run(payload)
    assert first.values["joint_sample_source_sha256"] != second.values["joint_sample_source_sha256"]


def test_bayesian_update_adapters_form_a_complete_first_passage_chain():
    update = evaluate(
        "reliability.bayesian_linear_thickness_update",
        {
            "update_id": "adapter-update-1",
            "asset_id": "asset-1",
            "location_id": "cml-1",
            "physical_scope_id": "circuit-1/cml-1",
            "physical_location_id": "cml-1",
            "time_basis": "elapsed seconds",
            "reference_time_s": 0.0,
            "prior_remaining_thickness_mean_m": 0.012,
            "prior_loss_rate_mean_m_s": 1e-10,
            "prior_remaining_thickness_standard_deviation_m": 0.001,
            "prior_loss_rate_standard_deviation_m_s": 5e-11,
            "prior_thickness_loss_rate_correlation": 0.0,
            "prior_basis_id": "reviewed-prior",
            "prior_source_content_sha256": "c" * 64,
            "linear_model_basis_id": "constant-linear",
            "measurement_error_model_id": "independent-ut-error",
            "prediction_support_id": "reviewed-support",
            "observations": [
                {
                    "observation_id": "u-1",
                    "campaign_id": "campaign-1",
                    "physical_location_id": "cml-1",
                    "elapsed_time_s": 0.0,
                    "remaining_thickness_m": 0.012,
                    "measurement_standard_deviation_m": 0.0002,
                    "partition": "update",
                    "source_group_id": "campaign-1",
                    "measurement_method_id": "ut",
                    "calibration_id": "block-1",
                    "source_content_sha256": "d" * 64,
                    "test_validity_reviewed": True,
                },
                {
                    "observation_id": "u-2",
                    "campaign_id": "campaign-2",
                    "physical_location_id": "cml-1",
                    "elapsed_time_s": 1e6,
                    "remaining_thickness_m": 0.0119,
                    "measurement_standard_deviation_m": 0.0002,
                    "partition": "update",
                    "source_group_id": "campaign-2",
                    "measurement_method_id": "ut",
                    "calibration_id": "block-1",
                    "source_content_sha256": "e" * 64,
                    "test_validity_reviewed": True,
                },
            ],
            "measurement_error_covariance_m2": None,
            "measurement_errors_independent_declared": True,
            "prediction_times_s": [0.0, 1e6],
            "credible_level": 0.95,
            "required_thickness_m": 0.006,
            "prior_basis_reviewed": True,
            "constant_linear_model_reviewed": True,
            "observation_identities_reviewed": True,
            "measurement_error_model_reviewed": True,
            "prediction_support_reviewed": True,
            "required_thickness_basis_reviewed": True,
            "holdout_source_independence_reviewed": False,
            "covariance_symmetry_tolerance_m2": 1e-24,
        },
        CONTEXT,
    )
    sampler_payload = gaussian_thickness_posterior_sample_inputs(
        update,
        sample_design_id="adapter-design-1",
        assessment_time_s=1e6,
        required_thickness_m=0.006,
        requested_accepted_sample_count=64,
        maximum_candidate_draw_multiplier=10,
        random_seed_uint64=7,
        assessment_conditioning_reviewed=True,
        required_thickness_basis_reviewed=True,
        deterministic_sampler_reviewed=True,
    )
    sampled = evaluate("reliability.gaussian_thickness_posterior_sample_design", sampler_payload, CONTEXT)
    forecast_payload = sampled_linear_thickness_first_passage_inputs(
        sampled,
        forecast_id="adapter-forecast-1",
        conditioning="survival above required thickness at assessment and nonnegative loss rate",
        event_id="minimum-thickness-first-crossing",
        event_definition="first crossing of reviewed required thickness",
        candidate_horizon_end_s=[2e6, 5e7, 1e8],
        maximum_weight_sum_error=1e-12,
        constant_nonnegative_loss_model_reviewed=True,
        joint_sample_distribution_reviewed=True,
        required_thickness_basis_reviewed=True,
        candidate_horizons_reviewed=True,
    )
    forecast = evaluate("reliability.sampled_linear_thickness_first_passage", forecast_payload, CONTEXT)
    assert update.status == sampled.status == forecast.status == "computed"
    assert forecast.values["sample_count"] == 64
    assert forecast.values["joint_sample_source_sha256"] == sampled.values["joint_sample_source_sha256"]
