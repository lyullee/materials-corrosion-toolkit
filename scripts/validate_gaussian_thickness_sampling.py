"""Validate the versioned Gaussian thickness posterior sampling path."""

from __future__ import annotations

import json
import math
from pathlib import Path

from matintegrity import evaluate
from matintegrity.contracts import RunContext

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "validation/gaussian_thickness_posterior_sampling_math.json"
MASK = 2**64 - 1


def splitmix64(state: int) -> tuple[int, int]:
    state = (state + 0x9E3779B97F4A7C15) & MASK
    value = state
    value = ((value ^ (value >> 30)) * 0xBF58476D1CE4E5B9) & MASK
    value = ((value ^ (value >> 27)) * 0x94D049BB133111EB) & MASK
    return state, (value ^ (value >> 31)) & MASK


def reference_rows(payload: dict) -> tuple[list[dict], int]:
    covariance = payload["posterior_covariance"]
    first_cholesky = math.sqrt(covariance[0][0])
    off_diagonal_cholesky = covariance[1][0] / first_cholesky
    second_cholesky = math.sqrt(covariance[1][1] - off_diagonal_cholesky**2)
    elapsed = payload["assessment_time_s"] - payload["posterior_reference_time_s"]
    state = payload["random_seed_uint64"]
    rows = []
    candidates = 0
    maximum = payload["requested_accepted_sample_count"] * payload["maximum_candidate_draw_multiplier"]
    for index in range(maximum):
        state, first_bits = splitmix64(state)
        state, second_bits = splitmix64(state)
        first_uniform = ((first_bits >> 11) + 0.5) / 2**53
        second_uniform = ((second_bits >> 11) + 0.5) / 2**53
        radius = math.sqrt(-2.0 * math.log(first_uniform))
        angle = 2.0 * math.pi * second_uniform
        first_normal = radius * math.cos(angle)
        second_normal = radius * math.sin(angle)
        reference_thickness = (
            payload["posterior_remaining_thickness_at_reference_mean_m"] + first_cholesky * first_normal
        )
        loss_rate = (
            payload["posterior_loss_rate_mean_m_s"]
            + off_diagonal_cholesky * first_normal
            + second_cholesky * second_normal
        )
        assessment_thickness = reference_thickness - loss_rate * elapsed
        candidates = index + 1
        if loss_rate < 0.0 or assessment_thickness <= payload["required_thickness_m"]:
            continue
        rows.append(
            {
                "sample_id": f"{payload['sample_design_id']}-s{len(rows):06d}",
                "remaining_thickness_at_assessment_m": assessment_thickness,
                "nonnegative_loss_rate_m_s": loss_rate,
                "normalized_weight": 1.0 / payload["requested_accepted_sample_count"],
            }
        )
        if len(rows) == payload["requested_accepted_sample_count"]:
            break
    return rows, candidates


def main() -> None:
    payload = {
        "sample_design_id": "authored-validation-design",
        "asset_id": "synthetic",
        "location_id": "cml-validation",
        "physical_scope_id": "synthetic/cml-validation",
        "physical_location_id": "cml-validation",
        "time_basis": "synthetic elapsed seconds",
        "posterior_definition_id": "authored-linear-gaussian-posterior",
        "posterior_source_sha256": "a" * 64,
        "posterior_reference_time_s": 0.0,
        "assessment_time_s": 1.0e6,
        "posterior_remaining_thickness_at_reference_mean_m": 0.012,
        "posterior_loss_rate_mean_m_s": 0.0,
        "posterior_covariance": [[1.6e-7, -1.4e-14], [-1.4e-14, 1e-20]],
        "required_thickness_m": 0.006,
        "requested_accepted_sample_count": 4096,
        "maximum_candidate_draw_multiplier": 4,
        "random_seed_uint64": 20261027,
        "covariance_symmetry_tolerance": 1e-24,
        "posterior_basis_reviewed": True,
        "covariance_reviewed": True,
        "assessment_conditioning_reviewed": True,
        "required_thickness_basis_reviewed": True,
        "deterministic_sampler_reviewed": True,
    }
    context = RunContext(
        asset_id="synthetic",
        location_id="cml-validation",
        time_basis="synthetic elapsed seconds",
    )
    result = evaluate("reliability.gaussian_thickness_posterior_sample_design", payload, context)
    expected_rows, expected_candidate_count = reference_rows(payload)
    if result.status != "computed":
        raise AssertionError(result)
    if result.values["samples"] != expected_rows:
        raise AssertionError("registered model differs from independently evaluated integer/RNG transform")
    if result.values["candidate_draw_count"] != expected_candidate_count:
        raise AssertionError("candidate count differs from direct rejection traversal")
    thickness = [row["remaining_thickness_at_assessment_m"] for row in expected_rows]
    rates = [row["nonnegative_loss_rate_m_s"] for row in expected_rows]
    if min(thickness) <= payload["required_thickness_m"] or min(rates) < 0.0:
        raise AssertionError("conditional sample contains an inadmissible row")
    report = {
        "schema_version": "matintegrity.validation.gaussian_thickness_posterior_sampling.v1",
        "status": "passed",
        "sample_count": len(expected_rows),
        "candidate_draw_count": expected_candidate_count,
        "negative_loss_rate_candidate_count": result.values["negative_loss_rate_candidate_count"],
        "non_surviving_candidate_count": result.values["non_surviving_candidate_count"],
        "empirical_acceptance_fraction": result.values["empirical_acceptance_fraction"],
        "first_three_samples": expected_rows[:3],
        "joint_sample_source_sha256": result.values["joint_sample_source_sha256"],
        "checks": [
            "independent direct SplitMix64/Box-Muller/Cholesky/rejection traversal",
            "exact accepted-row and candidate-count equality",
            "strict assessment survival and nonnegative rate",
        ],
        "qualification": (
            "Authored deterministic mathematics and interface validation only; not field calibration, "
            "posterior-model validation, process-noise validation or constant-rate qualification."
        ),
    }
    OUTPUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(OUTPUT)


if __name__ == "__main__":
    main()
