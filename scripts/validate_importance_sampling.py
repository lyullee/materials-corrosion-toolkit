"""Verify Gaussian mean-shift importance sampling against a known normal tail."""

from __future__ import annotations

import json
from pathlib import Path
from statistics import NormalDist

import numpy as np

from matintegrity.contracts import RunContext, canonical_digest
from matintegrity.registry import default_registry

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    seed = 20261027
    sample_count = 32_768
    threshold = 4.0
    proposal_shift = 4.0
    generator = np.random.default_rng(seed)
    samples = generator.normal(loc=proposal_shift, scale=1.0, size=sample_count)
    sample_rows = [[float(value)] for value in samples]
    sample_ids = [f"sample-{index:05d}" for index in range(sample_count)]
    event_indicators = [bool(value > threshold) for value in samples]
    design_payload = {
        "generator": "numpy.default_rng.normal",
        "seed": seed,
        "target": "N(0,1)",
        "proposal": f"N({proposal_shift},1)",
        "sample_ids": sample_ids,
        "samples": sample_rows,
    }
    payload = {
        "estimate_id": "normal-tail-z-gt-4",
        "asset_id": "synthetic-asset",
        "location_id": "synthetic-limit-state",
        "physical_scope_id": "authored-normal-tail-verification",
        "time_basis": "synthetic interval seconds",
        "horizon_start_s": 0.0,
        "horizon_end_s": 1.0,
        "conditioning": "synthetic state starts outside the declared event",
        "event_id": "z-greater-than-four",
        "event_definition": "standard-normal latent value exceeds four",
        "event_probability_meaning": "conditional_first_failure_in_period",
        "latent_variable_ids": ["z"],
        "proposal_shift": [proposal_shift],
        "sample_ids": sample_ids,
        "proposal_samples": sample_rows,
        "event_indicators": event_indicators,
        "design_id": "numpy-pcg64-seed-20261027",
        "design_content_sha256": canonical_digest(design_payload),
        "proposal_generator_id": "numpy.default_rng.normal",
        "proposal_generator_revision": np.__version__,
        "latent_mapping_id": "identity-standard-normal",
        "latent_mapping_revision": "1",
        "latent_mapping_configuration_sha256": canonical_digest({"z": "identity"}),
        "evaluator_id": "greater-than-threshold",
        "evaluator_revision": "1",
        "evaluator_configuration_sha256": canonical_digest({"threshold": threshold}),
        "confidence_level": 0.95,
        "samples_drawn_from_declared_proposal": True,
        "sample_alignment_reviewed": True,
        "latent_mapping_reviewed": True,
        "event_indicator_reviewed": True,
        "deterministic_evaluator_declared": True,
    }
    context = RunContext(
        asset_id="synthetic-asset",
        location_id="synthetic-limit-state",
        time_basis="synthetic interval seconds",
    )
    result = default_registry().run("reliability.gaussian_mean_shift_importance_sampling", payload, context)
    exact_probability = NormalDist().cdf(-threshold)
    estimate = result.values["probability_given_survival"]
    standard_error = result.values["probability_standard_error"]
    absolute_error = abs(estimate - exact_probability)
    criterion = 6.0 * standard_error
    passed = (
        result.status == "computed"
        and absolute_error <= criterion
        and result.values["observed_event_count"] > 0
        and result.values["effective_sample_size"] > 0
    )
    report = {
        "schema_version": "matintegrity.validation.gaussian_mean_shift_importance_sampling.v1",
        "basis": "authored analytic standard-normal tail; no physical calibration claim",
        "seed": seed,
        "sample_count": sample_count,
        "threshold": threshold,
        "proposal_shift": proposal_shift,
        "design_content_sha256": payload["design_content_sha256"],
        "exact_probability": exact_probability,
        "estimated_probability": estimate,
        "estimated_standard_error": standard_error,
        "absolute_error": absolute_error,
        "acceptance_criterion": "absolute error <= 6 estimated Monte Carlo standard errors",
        "acceptance_limit": criterion,
        "observed_event_count": result.values["observed_event_count"],
        "proposal_event_fraction": result.values["proposal_event_fraction"],
        "importance_weight_mean": result.values["importance_weight_mean"],
        "effective_sample_size": result.values["effective_sample_size"],
        "event_weight_effective_sample_size": result.values["event_weight_effective_sample_size"],
        "passed": passed,
        "limitations": [
            "This verifies the likelihood-ratio estimator against one analytic one-dimensional tail.",
            "It does not validate a physical latent mapping, limit-state model, input distribution or failure probability.",
            "The normal interval covers Monte Carlo sampling only and is not a rare-event performance guarantee.",
        ],
    }
    target = ROOT / "validation/gaussian_mean_shift_importance_sampling.json"
    target.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if not passed:
        raise SystemExit("importance-sampling analytic verification did not meet its criterion")


if __name__ == "__main__":
    main()
