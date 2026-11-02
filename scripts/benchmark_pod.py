"""Finite-sample coverage diagnostic under a known synthetic logistic experiment."""

import json
import math
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from scipy.stats import binomtest

from matintegrity import evaluate
from matintegrity.contracts import RunContext

ROOT = Path(__file__).resolve().parents[1]


def main():
    rng = np.random.default_rng(270626)
    sizes = np.repeat(0.001 * np.exp([-2.0, 0.0, 2.0]), 20)
    true_p = np.repeat([0.1, 0.5, 0.9], 20)
    true_target = 0.001 * math.exp(2)
    context = RunContext(
        asset_id="synthetic", location_id="synthetic", time_basis="independent synthetic trials"
    )
    statuses = Counter()
    finite = 0
    covered = 0
    pointwise_covered = 0
    for _ in range(250):
        inputs = dict(
            specimen_ids=[f"synthetic-{i}" for i in range(len(sizes))],
            flaw_size_m=sizes.tolist(),
            detected=(rng.random(len(sizes)) < true_p).tolist(),
            query_sizes_m=[0.001],
            target_probability=0.9,
            confidence_level=0.95,
            maximum_threshold_size_m=0.3,
            independent_trials_declared=True,
        )
        result = evaluate("inspection.hit_miss_pod", inputs, context)
        statuses[result.status] += 1
        if result.status != "computed":
            continue
        bound = result.values["target_size_upper_confidence_m"]
        if bound is not None:
            finite += 1
        covered += bound is None or bound >= true_target
        pointwise_covered += result.values["pointwise_lower_probability_of_detection"][0] <= 0.5
    n = statuses["computed"]
    interval = binomtest(covered, n).proportion_ci(confidence_level=0.95, method="exact")
    summary = dict(
        schema_version="matintegrity.synthetic_pod_diagnostic.v1",
        checked_at_utc=datetime.now(timezone.utc).isoformat(),
        seed=270626,
        replications=250,
        independent_trials_per_replication=len(sizes),
        known_probabilities=[0.1, 0.5, 0.9],
        nominal_confidence_level=0.95,
        true_target_size_m=true_target,
        fit_statuses=dict(statuses),
        finite_upper_bounds=finite,
        upper_size_coverage_among_identified_fits=covered / n,
        coverage_monte_carlo_95_interval=[float(interval.low), float(interval.high)],
        pointwise_lower_coverage_at_midpoint_among_identified_fits=pointwise_covered / n,
        interpretation="Synthetic finite-sample diagnostic conditional on identified fits. A nonbounded upper size within a search limit beyond the truth counts as covering the truth. Rejected designs are reported separately. This is not empirical inspection qualification or proof of exact nominal coverage.",
    )
    (ROOT / "validation/pod_synthetic_diagnostic.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
