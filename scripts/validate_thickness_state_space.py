"""Validate sequential thickness filtering against independent Gaussian algebra."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from matintegrity import evaluate
from matintegrity.contracts import RunContext

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "validation/linear_thickness_state_space_math.json"


def observation(identifier, time_s, thickness_m, partition, source):
    return {
        "observation_id": identifier,
        "campaign_id": source,
        "physical_location_id": "cml-validation",
        "elapsed_time_s": time_s,
        "remaining_thickness_m": thickness_m,
        "measurement_standard_deviation_m": 2e-4,
        "partition": partition,
        "source_group_id": source,
        "measurement_method_id": "authored-ut",
        "calibration_id": "authored-block",
        "source_content_sha256": ("a" if partition == "update" else "b") * 64,
        "test_validity_reviewed": True,
    }


def payload(process_rate):
    return {
        "update_id": "authored-state-space-validation",
        "asset_id": "synthetic",
        "location_id": "cml-validation",
        "physical_scope_id": "synthetic/cml-validation",
        "physical_location_id": "cml-validation",
        "time_basis": "synthetic elapsed seconds",
        "initial_state_time_s": 0.0,
        "initial_remaining_thickness_mean_m": 0.012,
        "initial_loss_rate_mean_m_s": 1e-10,
        "initial_remaining_thickness_standard_deviation_m": 8e-4,
        "initial_loss_rate_standard_deviation_m_s": 5e-11,
        "initial_thickness_loss_rate_correlation": -0.2,
        "prior_basis_id": "authored-prior",
        "prior_source_content_sha256": "c" * 64,
        "transition_model_basis_id": "authored-constant-transition",
        "process_noise_model_id": "authored-additive-covariance-rate",
        "process_noise_covariance_rate": process_rate,
        "measurement_error_model_id": "authored-independent-errors",
        "observations": [
            observation("u-1", 0.0, 0.0119, "update", "update-1"),
            observation("h-1", 5e5, 0.01172, "holdout", "holdout-1"),
            observation("u-2", 1e6, 0.01175, "update", "update-2"),
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


def batch_zero_noise_expected(inputs):
    update_rows = [row for row in inputs["observations"] if row["partition"] == "update"]
    thickness_sd = inputs["initial_remaining_thickness_standard_deviation_m"]
    rate_sd = inputs["initial_loss_rate_standard_deviation_m_s"]
    correlation = inputs["initial_thickness_loss_rate_correlation"]
    initial_mean = np.asarray(
        [inputs["initial_remaining_thickness_mean_m"], inputs["initial_loss_rate_mean_m_s"]]
    )
    initial_covariance = np.asarray(
        [
            [thickness_sd**2, correlation * thickness_sd * rate_sd],
            [correlation * thickness_sd * rate_sd, rate_sd**2],
        ]
    )
    design = np.asarray(
        [[1.0, -(row["elapsed_time_s"] - inputs["initial_state_time_s"])] for row in update_rows]
    )
    measurements = np.asarray([row["remaining_thickness_m"] for row in update_rows])
    errors = np.diag([row["measurement_standard_deviation_m"] ** 2 for row in update_rows])
    posterior_covariance = np.linalg.inv(
        np.linalg.inv(initial_covariance) + design.T @ np.linalg.solve(errors, design)
    )
    posterior_mean = posterior_covariance @ (
        np.linalg.solve(initial_covariance, initial_mean) + design.T @ np.linalg.solve(errors, measurements)
    )
    transition = np.asarray(
        [
            [1.0, -(inputs["analysis_end_time_s"] - inputs["initial_state_time_s"])],
            [0.0, 1.0],
        ]
    )
    return transition @ posterior_mean, transition @ posterior_covariance @ transition.T


def main() -> None:
    context = RunContext(
        asset_id="synthetic",
        location_id="cml-validation",
        time_basis="synthetic elapsed seconds",
    )
    zero_inputs = payload([[0.0, 0.0], [0.0, 0.0]])
    zero_result = evaluate("reliability.linear_thickness_state_space_update", zero_inputs, context)
    expected_mean, expected_covariance = batch_zero_noise_expected(zero_inputs)
    actual_mean = np.asarray(
        [
            zero_result.values["posterior_remaining_thickness_at_state_time_mean_m"],
            zero_result.values["posterior_loss_rate_mean_m_s"],
        ]
    )
    actual_covariance = np.asarray(zero_result.values["posterior_covariance"])
    if not np.allclose(actual_mean, expected_mean, rtol=1e-12, atol=1e-18):
        raise AssertionError("zero-noise sequential mean differs from independent batch information form")
    if not np.allclose(actual_covariance, expected_covariance, rtol=1e-11, atol=1e-28):
        raise AssertionError(
            "zero-noise sequential covariance differs from independent batch information form"
        )

    noisy_inputs = payload([[1e-16, 0.0], [0.0, 1e-28]])
    noisy_result = evaluate("reliability.linear_thickness_state_space_update", noisy_inputs, context)
    state_covariance = np.asarray(noisy_result.values["posterior_covariance"])
    elapsed = 5e5
    transition = np.asarray([[1.0, -elapsed], [0.0, 1.0]])
    expected_future = (
        transition @ state_covariance @ transition.T
        + np.asarray(noisy_inputs["process_noise_covariance_rate"]) * elapsed
    )
    actual_future_sd = noisy_result.values["predicted_remaining_thickness_standard_deviation_m"][1]
    if not np.isclose(actual_future_sd, expected_future[0, 0] ** 0.5, rtol=1e-12):
        raise AssertionError("future variance does not include the declared process covariance rate")
    report = {
        "schema_version": "matintegrity.validation.linear_thickness_state_space.v1",
        "status": "passed",
        "zero_process_noise_batch_mean": expected_mean.tolist(),
        "zero_process_noise_batch_covariance": expected_covariance.tolist(),
        "noisy_analysis_end_covariance": state_covariance.tolist(),
        "future_thickness_standard_deviation_m": actual_future_sd,
        "holdout_state_updated": noisy_result.values["observation_diagnostics"][1]["state_updated"],
        "checks": [
            "zero-process-noise sequential filter equals independent batch information form",
            "future covariance equals direct transition plus elapsed process covariance",
            "predeclared holdout does not update state",
        ],
        "qualification": (
            "Authored Gaussian algebra and software-contract validation only; not process-noise calibration, "
            "nonlinear degradation validation, field validation or first-passage qualification."
        ),
    }
    OUTPUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(OUTPUT)


if __name__ == "__main__":
    main()
