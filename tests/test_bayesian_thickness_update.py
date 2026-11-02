import copy
import math
from statistics import NormalDist

import numpy as np
import pytest
from pydantic import ValidationError

from matintegrity.contracts import RunContext
from matintegrity.registry import default_registry

MODEL_ID = "reliability.bayesian_linear_thickness_update"
CONTEXT = RunContext(asset_id="asset-1", location_id="course-a", time_basis="elapsed seconds")


def observation(
    observation_id: str,
    elapsed_time_s: float,
    thickness_m: float,
    *,
    partition: str = "update",
    source_group_id: str = "campaign-a",
) -> dict:
    return {
        "observation_id": observation_id,
        "campaign_id": source_group_id,
        "physical_location_id": "cml-17",
        "elapsed_time_s": elapsed_time_s,
        "remaining_thickness_m": thickness_m,
        "measurement_standard_deviation_m": 0.0002,
        "partition": partition,
        "source_group_id": source_group_id,
        "measurement_method_id": "ut-grid-reviewed",
        "calibration_id": "block-2026",
        "source_content_sha256": ("a" if source_group_id == "campaign-a" else "b") * 64,
        "test_validity_reviewed": True,
    }


def inputs() -> dict:
    return {
        "update_id": "linear-loss-1",
        "asset_id": "asset-1",
        "location_id": "course-a",
        "physical_scope_id": "pipe-course-a",
        "physical_location_id": "cml-17",
        "time_basis": "elapsed seconds",
        "reference_time_s": 0.0,
        "prior_remaining_thickness_mean_m": 0.012,
        "prior_loss_rate_mean_m_s": 1.0e-10,
        "prior_remaining_thickness_standard_deviation_m": 0.001,
        "prior_loss_rate_standard_deviation_m_s": 8.0e-10,
        "prior_thickness_loss_rate_correlation": 0.1,
        "prior_basis_id": "reviewed-prior-1",
        "prior_source_content_sha256": "c" * 64,
        "linear_model_basis_id": "constant-linear-reviewed-1",
        "measurement_error_model_id": "ut-error-reviewed-1",
        "prediction_support_id": "reviewed-time-support-1",
        "observations": [
            observation("u-1", 0.0, 0.0118),
            observation("u-2", 1.0e6, 0.0110),
            observation("h-1", 1.5e6, 0.01065, partition="holdout", source_group_id="campaign-b"),
        ],
        "measurement_error_covariance_m2": None,
        "measurement_errors_independent_declared": True,
        "prediction_times_s": [0.0, 2.0e6],
        "credible_level": 0.95,
        "required_thickness_m": 0.009,
        "prior_basis_reviewed": True,
        "constant_linear_model_reviewed": True,
        "observation_identities_reviewed": True,
        "measurement_error_model_reviewed": True,
        "prediction_support_reviewed": True,
        "required_thickness_basis_reviewed": True,
        "holdout_source_independence_reviewed": True,
        "covariance_symmetry_tolerance_m2": 1.0e-18,
    }


def analytic_posterior(payload: dict) -> tuple[np.ndarray, np.ndarray]:
    update_rows = [row for row in payload["observations"] if row["partition"] == "update"]
    mean = np.array([payload["prior_remaining_thickness_mean_m"], payload["prior_loss_rate_mean_m_s"]])
    sd_t = payload["prior_remaining_thickness_standard_deviation_m"]
    sd_r = payload["prior_loss_rate_standard_deviation_m_s"]
    covariance = np.array(
        [
            [sd_t**2, payload["prior_thickness_loss_rate_correlation"] * sd_t * sd_r],
            [payload["prior_thickness_loss_rate_correlation"] * sd_t * sd_r, sd_r**2],
        ]
    )
    design = np.array([[1.0, -(row["elapsed_time_s"] - payload["reference_time_s"])] for row in update_rows])
    values = np.array([row["remaining_thickness_m"] for row in update_rows])
    errors = np.diag([row["measurement_standard_deviation_m"] ** 2 for row in update_rows])
    precision = np.linalg.inv(covariance) + design.T @ np.linalg.solve(errors, design)
    posterior_covariance = np.linalg.inv(precision)
    posterior_mean = posterior_covariance @ (
        np.linalg.solve(covariance, mean) + design.T @ np.linalg.solve(errors, values)
    )
    return posterior_mean, posterior_covariance


def test_batch_update_matches_independent_information_form_and_probability_meanings():
    payload = inputs()
    expected_mean, expected_covariance = analytic_posterior(payload)
    result = default_registry().run(MODEL_ID, payload, CONTEXT)
    assert result.status == "computed"
    assert result.values["posterior_remaining_thickness_at_reference_mean_m"] == pytest.approx(
        expected_mean[0]
    )
    assert result.values["posterior_loss_rate_mean_m_s"] == pytest.approx(expected_mean[1])
    assert np.asarray(result.values["posterior_covariance"]) == pytest.approx(expected_covariance)
    assert result.probability_semantics == {
        "probability_loss_rate_positive": "posterior_parameter_probability",
        "probability_below_required_thickness": "point_in_time_state_probability",
    }


def test_sequential_and_batch_updates_are_equivalent():
    batch_payload = inputs()
    batch_payload["observations"] = batch_payload["observations"][:2]
    batch = default_registry().run(MODEL_ID, batch_payload, CONTEXT)

    first_payload = copy.deepcopy(batch_payload)
    first_payload["observations"] = [first_payload["observations"][0]]
    first = default_registry().run(MODEL_ID, first_payload, CONTEXT)
    first_covariance = np.asarray(first.values["posterior_covariance"])
    second_payload = copy.deepcopy(batch_payload)
    second_payload["observations"] = [second_payload["observations"][1]]
    second_payload["prior_remaining_thickness_mean_m"] = first.values[
        "posterior_remaining_thickness_at_reference_mean_m"
    ]
    second_payload["prior_loss_rate_mean_m_s"] = first.values["posterior_loss_rate_mean_m_s"]
    second_payload["prior_remaining_thickness_standard_deviation_m"] = math.sqrt(first_covariance[0, 0])
    second_payload["prior_loss_rate_standard_deviation_m_s"] = math.sqrt(first_covariance[1, 1])
    second_payload["prior_thickness_loss_rate_correlation"] = first_covariance[0, 1] / math.sqrt(
        first_covariance[0, 0] * first_covariance[1, 1]
    )
    sequential = default_registry().run(MODEL_ID, second_payload, CONTEXT)
    assert sequential.values["posterior_remaining_thickness_at_reference_mean_m"] == pytest.approx(
        batch.values["posterior_remaining_thickness_at_reference_mean_m"]
    )
    assert sequential.values["posterior_loss_rate_mean_m_s"] == pytest.approx(
        batch.values["posterior_loss_rate_mean_m_s"]
    )
    assert np.asarray(sequential.values["posterior_covariance"]) == pytest.approx(
        np.asarray(batch.values["posterior_covariance"]), rel=1e-10, abs=1e-20
    )


def test_holdout_values_do_not_change_posterior_but_remain_in_provenance_digest():
    first_payload = inputs()
    second_payload = inputs()
    second_payload["observations"][-1]["remaining_thickness_m"] = 0.004
    first = default_registry().run(MODEL_ID, first_payload, CONTEXT)
    second = default_registry().run(MODEL_ID, second_payload, CONTEXT)
    assert np.asarray(first.values["posterior_covariance"]) == pytest.approx(
        np.asarray(second.values["posterior_covariance"])
    )
    assert first.values["posterior_loss_rate_mean_m_s"] == pytest.approx(
        second.values["posterior_loss_rate_mean_m_s"]
    )
    assert first.values["holdout_residuals_m"] != second.values["holdout_residuals_m"]
    assert first.input_digest != second.input_digest


def test_correlated_measurement_covariance_is_supported_and_checked():
    payload = inputs()
    payload["measurement_errors_independent_declared"] = False
    variance = 0.0002**2
    payload["measurement_error_covariance_m2"] = [
        [variance, 0.25 * variance],
        [0.25 * variance, variance],
    ]
    result = default_registry().run(MODEL_ID, payload, CONTEXT)
    assert result.status == "computed"
    assert result.values["measurement_error_basis"] == "caller_supplied_full_covariance"

    asymmetric = copy.deepcopy(payload)
    asymmetric["measurement_error_covariance_m2"][1][0] = 0.0
    with pytest.raises(ValidationError, match="symmetric"):
        default_registry().run(MODEL_ID, asymmetric, CONTEXT)


@pytest.mark.parametrize(
    "field",
    [
        "prior_basis_reviewed",
        "constant_linear_model_reviewed",
        "observation_identities_reviewed",
        "measurement_error_model_reviewed",
        "prediction_support_reviewed",
        "required_thickness_basis_reviewed",
    ],
)
def test_missing_review_gate_stops_update(field):
    payload = inputs()
    payload[field] = False
    result = default_registry().run(MODEL_ID, payload, CONTEXT)
    assert result.status == "needs_data"
    assert result.values == {}


def test_invalid_or_duplicate_observation_identity_is_rejected():
    duplicate = inputs()
    duplicate["observations"][1]["observation_id"] = "u-1"
    with pytest.raises(ValidationError, match="identifiers must be unique"):
        default_registry().run(MODEL_ID, duplicate, CONTEXT)
    wrong_location = inputs()
    wrong_location["observations"][1]["physical_location_id"] = "cml-18"
    with pytest.raises(ValidationError, match="physical location"):
        default_registry().run(MODEL_ID, wrong_location, CONTEXT)


def test_context_identity_is_enforced():
    for context in (
        CONTEXT.model_copy(update={"asset_id": "other"}),
        CONTEXT.model_copy(update={"location_id": "other"}),
        CONTEXT.model_copy(update={"time_basis": "other"}),
    ):
        with pytest.raises(ValueError, match="Bayesian thickness-update"):
            default_registry().run(MODEL_ID, inputs(), context)


def test_prediction_intervals_and_point_state_probability_follow_normal_identities():
    result = default_registry().run(MODEL_ID, inputs(), CONTEXT)
    z = NormalDist().inv_cdf(0.975)
    for mean, standard_deviation, lower, upper, probability in zip(
        result.values["predicted_remaining_thickness_mean_m"],
        result.values["predicted_remaining_thickness_standard_deviation_m"],
        result.values["predicted_remaining_thickness_credible_lower_m"],
        result.values["predicted_remaining_thickness_credible_upper_m"],
        result.values["probability_below_required_thickness"],
        strict=True,
    ):
        assert lower == pytest.approx(mean - z * standard_deviation)
        assert upper == pytest.approx(mean + z * standard_deviation)
        assert probability == pytest.approx(NormalDist().cdf((0.009 - mean) / standard_deviation))
    assert any("not period first-failure" in note for note in result.notes)


def test_holdout_source_overlap_is_preserved_not_called_independent():
    payload = inputs()
    payload["observations"][-1]["source_group_id"] = "campaign-a"
    result = default_registry().run(MODEL_ID, payload, CONTEXT)
    assert result.values["holdout_source_independence_status"] == ("not_independent_source_group_overlap")
    assert result.values["overlapping_holdout_source_group_ids"] == ["campaign-a"]
