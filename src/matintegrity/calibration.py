"""Observation fitting that retains the likelihood contribution of runouts."""

from __future__ import annotations

import math

import numpy as np

from .contracts import check_finite


def fit_censored_sn(stress_range_Pa, cycles, runout, *, reference_range_Pa: float = 1e8) -> dict:
    from scipy.optimize import minimize
    from scipy.special import log_ndtr

    stress = np.asarray(stress_range_Pa, dtype=float)
    life = np.asarray(cycles, dtype=float)
    censor = np.asarray(runout)
    if stress.ndim != 1 or stress.shape != life.shape or stress.shape != censor.shape or len(stress) < 5:
        raise ValueError("at least five aligned fatigue observations required")
    if not np.isin(censor, [False, True, 0, 1]).all():
        raise ValueError("runout flags must be binary")
    censor = censor.astype(bool)
    if (
        not np.isfinite(stress).all()
        or not np.isfinite(life).all()
        or np.any(stress <= 0)
        or np.any(life <= 0)
    ):
        raise ValueError("positive finite stress ranges and lives required")
    if not math.isfinite(reference_range_Pa) or reference_range_Pa <= 0:
        raise ValueError("positive reference stress required")
    if (~censor).sum() < 3 or np.unique(stress).size < 2:
        raise ValueError("fit needs at least three failures and two stress levels")
    x = np.log(stress / reference_range_Pa)
    y = np.log(life)

    def objective(parameters):
        intercept, exponent, log_sigma = parameters
        sigma = np.exp(log_sigma)
        z = (y - (intercept - exponent * x)) / sigma
        likelihood = np.where(censor, log_ndtr(-z), -0.5 * z * z - log_sigma - 0.5 * math.log(2 * math.pi))
        return -float(likelihood.sum())

    fits = [
        minimize(
            objective,
            [float(np.median(y)) + m * float(np.median(x)), m, 0.0],
            method="L-BFGS-B",
            bounds=[(0, 100), (0.01, 50), (-8, 4)],
        )
        for m in (2.0, 4.0, 8.0)
    ]
    successful = [fit for fit in fits if fit.success and np.isfinite(fit.fun)]
    if not successful:
        raise RuntimeError("censored S-N likelihood optimization did not converge")
    fit = min(successful, key=lambda item: item.fun)
    intercept, exponent, log_sigma = (float(v) for v in fit.x)
    if exponent < 0.011 or exponent > 49.99 or abs(log_sigma + 8) < 0.01 or abs(log_sigma - 4) < 0.01:
        raise ValueError("fit reached parameter bounds; additional evidence or another model is required")
    result = dict(
        schema_version="matintegrity.censored_sn.v1",
        reference_range_Pa=reference_range_Pa,
        median_reference_cycles=math.exp(intercept),
        exponent=exponent,
        log_life_sigma=math.exp(log_sigma),
        negative_log_likelihood=float(fit.fun),
        observations=int(len(stress)),
        failures=int((~censor).sum()),
        runouts=int(censor.sum()),
        converged=True,
        assumptions=[
            "Independent specimens; lognormal life at fixed stress range.",
            "Runouts are right-censored; stress range and processing condition are consistent.",
        ],
    )
    check_finite(result)
    return result
