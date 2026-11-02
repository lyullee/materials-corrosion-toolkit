"""Verify the linear-Gaussian thickness update against an independent information form."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

from matintegrity.contracts import RunContext
from matintegrity.registry import default_registry

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    source_digest = hashlib.sha256(b"authored independent thickness observations").hexdigest()
    observations = [
        {
            "observation_id": "update-0",
            "campaign_id": "campaign-a",
            "physical_location_id": "cml-1",
            "elapsed_time_s": 0.0,
            "remaining_thickness_m": 0.0118,
            "measurement_standard_deviation_m": 0.0002,
            "partition": "update",
            "source_group_id": "campaign-a",
            "measurement_method_id": "authored-ut",
            "calibration_id": "authored-block",
            "source_content_sha256": source_digest,
            "test_validity_reviewed": True,
        },
        {
            "observation_id": "update-1",
            "campaign_id": "campaign-a",
            "physical_location_id": "cml-1",
            "elapsed_time_s": 1.0e6,
            "remaining_thickness_m": 0.0110,
            "measurement_standard_deviation_m": 0.0002,
            "partition": "update",
            "source_group_id": "campaign-a",
            "measurement_method_id": "authored-ut",
            "calibration_id": "authored-block",
            "source_content_sha256": source_digest,
            "test_validity_reviewed": True,
        },
        {
            "observation_id": "holdout-0",
            "campaign_id": "campaign-b",
            "physical_location_id": "cml-1",
            "elapsed_time_s": 1.5e6,
            "remaining_thickness_m": 0.01065,
            "measurement_standard_deviation_m": 0.0002,
            "partition": "holdout",
            "source_group_id": "campaign-b",
            "measurement_method_id": "authored-ut",
            "calibration_id": "authored-block",
            "source_content_sha256": source_digest,
            "test_validity_reviewed": True,
        },
    ]
    payload = {
        "update_id": "authored-linear-update",
        "asset_id": "authored",
        "location_id": "course-a",
        "physical_scope_id": "pipe-course-a",
        "physical_location_id": "cml-1",
        "time_basis": "authored elapsed seconds",
        "reference_time_s": 0.0,
        "prior_remaining_thickness_mean_m": 0.012,
        "prior_loss_rate_mean_m_s": 1.0e-10,
        "prior_remaining_thickness_standard_deviation_m": 0.001,
        "prior_loss_rate_standard_deviation_m_s": 8.0e-10,
        "prior_thickness_loss_rate_correlation": 0.1,
        "prior_basis_id": "authored-prior",
        "prior_source_content_sha256": source_digest,
        "linear_model_basis_id": "authored-constant-linear",
        "measurement_error_model_id": "authored-independent-ut-error",
        "prediction_support_id": "authored-two-million-second-support",
        "observations": observations,
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
    result = default_registry().run(
        "reliability.bayesian_linear_thickness_update",
        payload,
        RunContext(
            asset_id="authored",
            location_id="course-a",
            time_basis="authored elapsed seconds",
            metadata={"source_content_sha256": source_digest},
        ),
    )

    prior_mean = np.array([0.012, 1.0e-10])
    prior_covariance = np.array([[1.0e-6, 8.0e-14], [8.0e-14, 6.4e-19]])
    design = np.array([[1.0, 0.0], [1.0, -1.0e6]])
    measurement_covariance = np.diag([4.0e-8, 4.0e-8])
    observed = np.array([0.0118, 0.0110])
    precision = np.linalg.inv(prior_covariance) + design.T @ np.linalg.solve(measurement_covariance, design)
    expected_covariance = np.linalg.inv(precision)
    expected_mean = expected_covariance @ (
        np.linalg.solve(prior_covariance, prior_mean)
        + design.T @ np.linalg.solve(measurement_covariance, observed)
    )
    actual_mean = np.array(
        [
            result.values["posterior_remaining_thickness_at_reference_mean_m"],
            result.values["posterior_loss_rate_mean_m_s"],
        ]
    )
    actual_covariance = np.asarray(result.values["posterior_covariance"])
    mean_absolute_errors = np.abs(actual_mean - expected_mean)
    covariance_absolute_errors = np.abs(actual_covariance - expected_covariance)
    if np.max(mean_absolute_errors) > 1e-15 or np.max(covariance_absolute_errors) > 1e-18:
        raise AssertionError("Bayesian thickness update does not match the information-form solution")
    record = {
        "schema_version": "matintegrity.validation.bayesian_thickness_update.v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "qualification": (
            "Authored linear-Gaussian arithmetic and partition-contract verification; not calibration "
            "of corrosion growth, measurement error, POD, model form or field performance."
        ),
        "model_id": result.model_id,
        "input_digest": result.input_digest,
        "expected_posterior_mean": expected_mean.tolist(),
        "actual_posterior_mean": actual_mean.tolist(),
        "maximum_mean_absolute_error": float(np.max(mean_absolute_errors)),
        "expected_posterior_covariance": expected_covariance.tolist(),
        "actual_posterior_covariance": actual_covariance.tolist(),
        "maximum_covariance_absolute_error": float(np.max(covariance_absolute_errors)),
        "holdout_observation_ids": result.values["holdout_observation_ids"],
        "holdout_source_independence_status": result.values["holdout_source_independence_status"],
        "probability_semantics": result.probability_semantics,
        "source_sha256": hashlib.sha256(
            (ROOT / "src/matintegrity/models/reliability.py").read_bytes()
        ).hexdigest(),
    }
    target = ROOT / "validation/bayesian_thickness_update_math.json"
    target.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
    print(target)


if __name__ == "__main__":
    main()
