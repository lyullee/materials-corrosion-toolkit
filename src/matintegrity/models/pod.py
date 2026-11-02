"""Binomial inspection evidence and monotonic hit/miss likelihood inference."""

from __future__ import annotations

import math

import numpy as np
from pydantic import Field, model_validator

from ..contracts import Calculation, Contract, Positive
from ..registry import ModelSpec


class HitMissPOD(Contract):
    specimen_ids: list[str] = Field(min_length=6)
    flaw_size_m: list[Positive] = Field(min_length=6)
    detected: list[bool] = Field(min_length=6)
    query_sizes_m: list[Positive] = Field(min_length=1, max_length=100)
    target_probability: float = Field(gt=0, lt=1)
    confidence_level: float = Field(gt=0.5, lt=1)
    maximum_threshold_size_m: Positive
    independent_trials_declared: bool

    @model_validator(mode="after")
    def aligned(self):
        if len({len(self.specimen_ids), len(self.flaw_size_m), len(self.detected)}) != 1:
            raise ValueError("aligned flaw, hit/miss and specimen vectors required")
        if any(not value.strip() for value in self.specimen_ids) or len(set(self.specimen_ids)) != len(
            self.specimen_ids
        ):
            raise ValueError(
                "specimen IDs must be nonempty and unique; repeated inspections require a clustered model"
            )
        if any(not min(self.flaw_size_m) <= a <= max(self.flaw_size_m) for a in self.query_sizes_m):
            raise ValueError("pointwise POD queries must stay inside the observed size domain")
        return self


def hit_miss_pod(x: HitMissPOD) -> Calculation:
    from scipy.optimize import brentq, minimize
    from scipy.special import expit, logit
    from scipy.stats import chi2

    if not x.independent_trials_declared:
        return Calculation(
            status="needs_data",
            values={},
            notes=("A declared independent trial design or a separate clustered model is required.",),
        )
    y = np.asarray(x.detected, dtype=float)
    a = np.asarray(x.flaw_size_m, dtype=float)
    if min(int(y.sum()), int((1 - y).sum())) < 2 or np.unique(a).size < 3:
        return Calculation(
            status="needs_data",
            values={},
            notes=("Finite slope inference needs both outcomes and at least three distinct sizes.",),
        )
    if min(a[y == 1]) >= max(a[y == 0]) or min(a[y == 0]) >= max(a[y == 1]):
        return Calculation(
            status="needs_data",
            values={},
            notes=(
                "Complete or quasi separation prevents a finite unpenalized logistic fit; no artificial slope cap is substituted.",
            ),
        )
    log_a = np.log(a)
    center = float(log_a.mean())
    scale = float(log_a.std())
    z = (log_a - center) / scale
    design = np.column_stack((np.ones(len(z)), z))

    def objective(beta):
        eta = design @ beta
        return float(np.sum(np.logaddexp(0, eta) - y * eta))

    def gradient(beta):
        return design.T @ (expit(design @ beta) - y)

    def hessian(beta):
        p = expit(design @ beta)
        return design.T @ ((p * (1 - p))[:, None] * design)

    fitted = minimize(
        objective,
        [float(logit(y.mean())), 1.0],
        jac=gradient,
        hess=hessian,
        method="trust-exact",
        options={"gtol": 1e-9, "maxiter": 300},
    )
    b0, b1 = (float(v) for v in fitted.x)
    score = float(np.max(np.abs(gradient(fitted.x))))
    information = hessian(fitted.x)
    condition = float(np.linalg.cond(information))
    if (
        not np.isfinite(fitted.x).all()
        or score > 1e-6
        or b1 <= 1e-8
        or not math.isfinite(condition)
        or condition > 1e12
    ):
        return Calculation(
            status="needs_data",
            values={"score_norm": score if math.isfinite(score) else None},
            notes=(
                "A stable increasing POD curve was not identified; investigate design, procedure, grouping and model choice.",
            ),
        )
    minimum_nll = objective(fitted.x)
    cutoff = float(chi2.ppf(2 * x.confidence_level - 1, 1))

    def profile(theta, z0):
        delta = z - z0

        def derivative(slope):
            return float(np.dot(expit(theta + slope * delta) - y, delta))

        if derivative(0) >= 0:
            slope = 0.0
        else:
            upper = max(b1, 1.0)
            for _ in range(60):
                if derivative(upper) >= 0:
                    break
                upper *= 2
            else:
                raise RuntimeError("POD nuisance profile could not be bracketed")
            slope = brentq(derivative, 0.0, upper, xtol=1e-12)
        eta = theta + slope * delta
        return float(np.sum(np.logaddexp(0, eta) - y * eta))

    def likelihood_gap(theta, z0):
        return 2 * (profile(theta, z0) - minimum_nll) - cutoff

    predictions = []
    for size in x.query_sizes_m:
        z0 = (math.log(size) - center) / scale
        theta = b0 + b1 * z0
        step = 1.0
        for _ in range(60):
            lower = theta - step
            if likelihood_gap(lower, z0) >= 0:
                break
            step *= 2
        else:
            raise RuntimeError("POD lower confidence profile could not be bracketed")
        boundary = brentq(lambda value, z_ref=z0: likelihood_gap(value, z_ref), lower, theta, xtol=1e-10)
        predictions.append(
            dict(
                size_m=size,
                probability=float(expit(theta)),
                pointwise_lower_confidence_probability=float(expit(boundary)),
            )
        )
    target_theta = float(logit(x.target_probability))
    threshold_z = (target_theta - b0) / b1
    threshold_log_m = center + scale * threshold_z

    def finite_size(log_value):
        return (
            math.exp(log_value)
            if math.log(np.nextafter(0.0, 1.0)) <= log_value <= math.log(np.finfo(float).max)
            else None
        )

    estimate = finite_size(threshold_log_m)
    maximum_z = (math.log(x.maximum_threshold_size_m) - center) / scale
    upper_size = None
    bound_status = "not_bounded_within_declared_search_domain"
    if maximum_z > threshold_z and likelihood_gap(target_theta, maximum_z) >= 0:
        boundary = brentq(
            lambda value: likelihood_gap(target_theta, value), threshold_z, maximum_z, xtol=1e-10
        )
        upper_size = math.exp(center + scale * boundary)
        bound_status = "bounded"
    return Calculation(
        values=dict(
            observations=len(a),
            hits=int(y.sum()),
            misses=int((1 - y).sum()),
            log_size_center_relative_to_1_m=center,
            standardization_log_size_scale=scale,
            logistic_midpoint_size_m=finite_size(center - b0 * scale / b1),
            logistic_log_size_scale=scale / b1,
            intercept_standardized=b0,
            slope_standardized=b1,
            information_condition_number=condition,
            score_norm=score,
            negative_log_likelihood=minimum_nll,
            parameter_covariance_standardized=np.linalg.inv(information).tolist(),
            observed_size_domain_m=[float(a.min()), float(a.max())],
            predictions=predictions,
            probability_of_detection=[p["probability"] for p in predictions],
            pointwise_lower_probability_of_detection=[
                p["pointwise_lower_confidence_probability"] for p in predictions
            ],
            target_probability=x.target_probability,
            target_size_estimate_m=estimate,
            target_size_estimate_extrapolated=estimate is None or not a.min() <= estimate <= a.max(),
            target_size_upper_confidence_m=upper_size,
            upper_confidence_bound_extrapolated=upper_size is not None
            and not a.min() <= upper_size <= a.max(),
            upper_confidence_bound_status=bound_status,
            confidence_level=x.confidence_level,
            confidence_method="one-sided asymptotic profile likelihood, positive-slope nuisance domain",
            likelihood_ratio_cutoff=cutoff,
        ),
        notes=(
            "Confidence is pointwise and asymptotic, not a simultaneous band or a procedure qualification.",
            "One independent observation per specimen; operator, material, geometry, access and false calls need separate evidence.",
            "An unbounded threshold is retained as missing; a fitted threshold beyond observed sizes is explicitly flagged.",
        ),
    )


class BinomialInspection(Contract):
    opportunities: int = Field(gt=0)
    positive_responses: int = Field(ge=0)
    confidence_level: float = Field(gt=0.5, lt=1)
    response_kind: str = Field(pattern=r"^(detection_at_declared_size|false_call_on_blank)$")
    independent_trials_declared: bool

    @model_validator(mode="after")
    def counts(self):
        if self.positive_responses > self.opportunities:
            raise ValueError("responses cannot exceed opportunities")
        return self


def binomial_inspection(x: BinomialInspection) -> Calculation:
    from scipy.stats import beta

    if not x.independent_trials_declared:
        return Calculation(
            status="needs_data",
            values={},
            notes=("A binomial confidence bound requires independent comparable opportunities.",),
        )
    k, n = x.positive_responses, x.opportunities
    lower = 0.0 if k == 0 else float(beta.ppf(1 - x.confidence_level, k, n - k + 1))
    upper = 1.0 if k == n else float(beta.ppf(x.confidence_level, k + 1, n - k))
    return Calculation(
        values=dict(
            probability_estimate=k / n,
            one_sided_lower_probability=lower,
            one_sided_upper_probability=upper,
            confidence_level=x.confidence_level,
            response_kind=x.response_kind,
        ),
        notes=(
            "Lower and upper limits are separate exact one-sided binomial bounds, not a joint two-sided interval. A detection result applies only to its declared flaw size and test conditions.",
        ),
    )


def specifications():
    return [
        ModelSpec(
            "inspection.hit_miss_pod",
            HitMissPOD,
            hit_miss_pod,
            {
                "target_size_estimate_m": "m",
                "target_size_upper_confidence_m": "m",
                "logistic_midpoint_size_m": "m",
                "logistic_log_size_scale": "1",
                "probability_of_detection": "1",
                "pointwise_lower_probability_of_detection": "1",
                "confidence_level": "1",
                "likelihood_ratio_cutoff": "1",
            },
            (
                "Increasing logistic POD in log flaw size, independent hit/miss observations and profile-likelihood confidence inference.",
            ),
            ("nde_pod", "profile_likelihood_inference"),
            probability_semantics={"probability_of_detection": "detection_given_flaw_and_procedure"},
        ),
        ModelSpec(
            "inspection.binomial_evidence",
            BinomialInspection,
            binomial_inspection,
            {
                "probability_estimate": "1",
                "one_sided_lower_probability": "1",
                "one_sided_upper_probability": "1",
                "confidence_level": "1",
            },
            (
                "Independent homogeneous inspection opportunities with explicit detection/false-call semantics.",
            ),
            ("nist_instrument_confidence",),
        ),
    ]
