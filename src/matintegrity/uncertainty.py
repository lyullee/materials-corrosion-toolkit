"""Seeded limit-state evaluation with explicit sampling and first-crossing semantics."""

from __future__ import annotations

from collections.abc import Callable

import numpy as np
from pydantic import Field, model_validator

from .contracts import Contract


class UniformMarginal(Contract):
    name: str = Field(min_length=1)
    lower: float
    upper: float

    @model_validator(mode="after")
    def order(self):
        if self.upper <= self.lower:
            raise ValueError("nonzero ordered marginal range required")
        return self


def simulate_limit_state(
    marginals: list[UniformMarginal],
    evaluator: Callable[[dict[str, np.ndarray]], np.ndarray],
    *,
    samples: int,
    seed: int,
    independence_declared: bool,
    time_s: list[float],
) -> dict:
    """Evaluator returns margin[sample,time], positive while the component survives."""
    from scipy.stats import beta

    if isinstance(samples, bool) or samples < 100 or samples > 2_000_000:
        raise ValueError("sample count must be an integer from 100 to 2000000")
    if not independence_declared:
        raise ValueError("supply an explicit joint sampler for dependent marginals")
    if not marginals or len({m.name for m in marginals}) != len(marginals):
        raise ValueError("unique nonempty marginals required")
    time = np.asarray(time_s, dtype=float)
    if (
        time.ndim != 1
        or len(time) < 2
        or not np.isfinite(time).all()
        or time[0] != 0
        or np.any(np.diff(time) <= 0)
    ):
        raise ValueError("time starts at zero and increases over a declared assessment horizon")
    rng = np.random.default_rng(seed)
    draws = {m.name: rng.uniform(m.lower, m.upper, samples) for m in marginals}
    margin = np.asarray(evaluator(draws), dtype=float)
    if margin.shape != (samples, len(time)) or not np.isfinite(margin).all():
        raise ValueError("finite limit-state margins must have [sample,time] shape")
    survivors = margin[:, 0] > 0
    n = int(survivors.sum())
    if n == 0:
        raise ValueError("no samples survive at the conditioning time")
    failed = np.maximum.accumulate(margin[survivors] <= 0, axis=1)
    counts = failed.sum(axis=0).astype(int)
    intervals = []
    for k in counts:
        intervals.append(
            [
                0.0 if k == 0 else float(beta.ppf(0.025, k, n - k + 1)),
                1.0 if k == n else float(beta.ppf(0.975, k + 1, n - k)),
            ]
        )
    return dict(
        schema_version="matintegrity.limit_state_mc.v1",
        seed=seed,
        samples=samples,
        conditioned_survivors=n,
        initially_failed_samples=int(samples - n),
        time_s=time.tolist(),
        probability_of_failure_given_initial_survival=(counts / n).tolist(),
        failure_counts=counts.tolist(),
        binomial_95_intervals=intervals,
        assumptions=[
            "Independent declared uniform input marginals; correlated physics may still arise through the evaluator.",
            "First crossing is detected only on the supplied time grid; temporal discretization needs convergence checks.",
            "Binomial intervals quantify sampling uncertainty, not parameter or model validity.",
        ],
    )
