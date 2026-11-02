"""Finite-sample diagnostic for parameter intervals under one known area-maxima law."""

import copy
import hashlib
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
    algorithm_path = ROOT / "src/matintegrity/models/pitting.py"
    algorithm_digest = hashlib.sha256(algorithm_path.read_bytes()).hexdigest()
    inputs = json.loads((ROOT / "examples/model_inputs.json").read_text(encoding="utf-8"))["models"][
        "corrosion.gumbel_area_maximum"
    ]
    rng = np.random.default_rng(281026)
    context = RunContext(asset_id="synthetic", location_id="synthetic", time_basis="one synthetic exposure")
    true_mu, true_beta = 0.002, 0.0002
    true_quantile = true_mu + true_beta * (
        math.log(inputs["target_block_count"]) - math.log(-math.log(inputs["quantile_probability"]))
    )
    true_probability = -math.expm1(
        -inputs["target_block_count"] * math.exp(-(inputs["depth_threshold_m"] - true_mu) / true_beta)
    )
    statuses = Counter()
    quantile_covered = probability_covered = 0
    for _ in range(150):
        request = copy.deepcopy(inputs)
        request["maximum_depth_m"] = rng.gumbel(true_mu, true_beta, len(inputs["block_ids"])).tolist()
        request["parameter_resamples"] = 199
        request["seed"] = int(rng.integers(0, 2**32))
        result = evaluate("corrosion.gumbel_area_maximum", request, context)
        statuses[result.status] += 1
        if result.status != "computed":
            continue
        interval = result.values["depth_quantile_parameter_interval_m"]
        quantile_covered += interval[0] <= true_quantile <= interval[1]
        interval = result.values["exceedance_probability_parameter_interval"]
        probability_covered += interval[0] <= true_probability <= interval[1]
    count = statuses["computed"]

    def coverage(successes):
        if not count:
            return dict(covered=successes, fits=0, coverage=None, monte_carlo_95_interval=None)
        interval = binomtest(successes, count).proportion_ci(method="exact")
        return dict(
            covered=successes,
            fits=count,
            coverage=successes / count,
            monte_carlo_95_interval=[float(interval.low), float(interval.high)],
        )

    if hashlib.sha256(algorithm_path.read_bytes()).hexdigest() != algorithm_digest:
        raise RuntimeError("algorithm changed during the diagnostic; rerun against one stable source")
    summary = dict(
        schema_version="matintegrity.synthetic_pitting_diagnostic.v1",
        algorithm_source_sha256=algorithm_digest,
        model_version=result.model_version,
        runtime=result.runtime,
        checked_at_utc=datetime.now(timezone.utc).isoformat(),
        seed=281026,
        replications=150,
        independent_blocks_per_replication=40,
        target_blocks=400,
        nominal_confidence_level=0.95,
        gof_resamples=99,
        parameter_resamples=199,
        true_block_location_m=true_mu,
        true_block_scale_m=true_beta,
        true_area_maximum_quantile_m=true_quantile,
        true_area_exceedance_probability=true_probability,
        fit_statuses=dict(statuses),
        quantile_parameter_coverage=coverage(quantile_covered),
        exceedance_parameter_coverage=coverage(probability_covered),
        interpretation="Synthetic diagnostic conditional on admitted fits and the declared Gumbel law. Percentile parameter intervals are approximate; these results do not prove exact nominal coverage, spatial independence, field sizing validity or a future structural-failure probability.",
    )
    (ROOT / "validation/pitting_synthetic_diagnostic.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
