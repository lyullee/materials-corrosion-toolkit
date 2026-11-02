"""Condition-bounded lognormal rupture lives with independent right censoring."""

from __future__ import annotations

import math
from typing import Literal

import numpy as np
from pydantic import Field, model_validator

from ..contracts import Calculation, Contract, Evidence, Nonnegative, Positive, canonical_digest
from ..registry import ModelSpec

R_J_mol_K = 8.31446261815324
StressBasis = Literal["initial_nominal_constant_load", "constant_true_stress"]
TemperatureBasis = Literal["nominal_specified", "measured_representative"]
LifeFamily = Literal["stress_only", "arrhenius_stress"]


class CreepLifeFit(Contract):
    material_condition_id: str = Field(min_length=1)
    stress_basis: StressBasis
    temperature_basis: TemperatureBasis
    family: LifeFamily
    specimen_id: list[str] = Field(min_length=8, max_length=100000)
    initial_stress_Pa: list[Positive]
    temperature_K: list[Positive]
    endpoint_time_s: list[Positive]
    right_censored: list[bool]
    temperature_tolerance_K: Nonnegative
    independent_specimens_confirmed: bool
    common_mechanism_and_condition_confirmed: bool
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def aligned(self):
        vectors = (
            self.specimen_id,
            self.initial_stress_Pa,
            self.temperature_K,
            self.endpoint_time_s,
            self.right_censored,
        )
        if len({len(v) for v in vectors}) != 1:
            raise ValueError("one aligned record per physical specimen is required")
        if any(not s.strip() for s in self.specimen_id) or len(set(self.specimen_id)) != len(
            self.specimen_id
        ):
            raise ValueError("unique nonempty physical specimen IDs are required")
        return self


class CreepLifeModel(Contract):
    schema_version: Literal["matintegrity.creep_life.v1"] = "matintegrity.creep_life.v1"
    family: LifeFamily
    material_condition_id: str = Field(min_length=1)
    stress_basis: StressBasis
    temperature_basis: TemperatureBasis
    reference_stress_Pa: Positive
    reference_temperature_K: Positive
    log_reference_median_time_s: float
    stress_exponent: Positive
    activation_energy_J_mol: Positive | None
    log_life_sigma: Positive
    temperature_tolerance_K: Nonnegative
    # Aggregate condition support; no specimen lives are embedded in this contract.
    support_stress_Pa: list[Positive] = Field(min_length=2)
    support_temperature_K: list[Positive] = Field(min_length=2)
    longest_observed_failure_time_s: Positive
    training_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    observations: int = Field(ge=8)
    failures: int = Field(ge=5)
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def coherent(self):
        if len(self.support_stress_Pa) != len(self.support_temperature_K):
            raise ValueError("aligned support conditions required")
        if self.failures > self.observations:
            raise ValueError("failures cannot exceed observations")
        if (self.family == "stress_only") != (self.activation_energy_J_mol is None):
            raise ValueError("single-temperature fitting must leave activation energy unestimated")
        if self.family == "stress_only" and any(
            abs(t - self.reference_temperature_K) > self.temperature_tolerance_K + 1e-10
            for t in self.support_temperature_K
        ):
            raise ValueError("stress-only support must share the declared temperature band")
        design = _design(
            self.support_stress_Pa,
            self.support_temperature_K,
            self.reference_stress_Pa,
            self.reference_temperature_K,
            self.family,
        )
        if np.linalg.matrix_rank(design) != design.shape[1]:
            raise ValueError("support conditions do not identify this model family")
        return self


class CreepLifePrediction(Contract):
    model: CreepLifeModel
    material_condition_id: str = Field(min_length=1)
    stress_basis: StressBasis
    temperature_basis: TemperatureBasis
    initial_stress_Pa: Positive
    temperature_K: Positive
    current_age_s: Nonnegative
    horizon_s: Positive
    maximum_time_extrapolation_factor: Positive
    constant_conditions_since_fresh_material_confirmed: bool
    applicability_reviewed: bool


def _design(stress, temperature, ref_s, ref_t, family):
    stress = np.asarray(stress, dtype=float)
    temperature = np.asarray(temperature, dtype=float)
    columns = [np.ones_like(stress), -(np.log(stress) - math.log(ref_s))]
    if family == "arrhenius_stress":
        columns.append(1 / temperature - 1 / ref_t)
    matrix = np.column_stack(columns)
    matrix[:, 1:] /= np.maximum(np.ptp(matrix[:, 1:], axis=0), np.finfo(float).tiny)
    return matrix


def _mills(z):
    from scipy.special import erfcx, log_ndtr

    z = np.asarray(z, dtype=float)
    out = np.empty_like(z)
    upper = z >= 0
    out[upper] = math.sqrt(2 / math.pi) / erfcx(z[upper] / math.sqrt(2))
    out[~upper] = np.exp(-0.5 * z[~upper] ** 2 - 0.5 * math.log(2 * math.pi) - log_ndtr(-z[~upper]))
    return out


def _likelihood(parameters, design, y, censored):
    from scipy.special import log_ndtr

    sigma = math.exp(float(parameters[-1]))
    z = (y - design @ parameters[:-1]) / sigma
    lam = _mills(z)
    nll = np.where(censored, -log_ndtr(-z), 0.5 * z * z + parameters[-1] + 0.5 * math.log(2 * math.pi))
    d_mu = -np.where(censored, lam, z) / sigma
    d_scale = np.where(censored, -lam * z, 1 - z * z)
    gradient = np.r_[design.T @ d_mu, d_scale.sum()]
    return float(nll.sum()), gradient


def fit_life(x: CreepLifeFit) -> Calculation:
    from scipy.optimize import minimize

    if not x.independent_specimens_confirmed or not x.common_mechanism_and_condition_confirmed:
        return Calculation(
            status="needs_data",
            values={},
            notes=(
                "Confirm specimen independence and a common material condition, mechanism and stress-control basis.",
            ),
        )
    stress = np.asarray(x.initial_stress_Pa)
    temperature = np.asarray(x.temperature_K)
    y = np.log(x.endpoint_time_s)
    censored = np.asarray(x.right_censored)
    if (~censored).sum() < 5 or np.unique(stress).size < 2:
        return Calculation(
            status="needs_data",
            values={},
            notes=("At least five observed failures and two stress levels are required.",),
        )
    ref_s = math.exp(float(np.mean(np.log(stress))))
    ref_t = 1 / float(np.mean(1 / temperature))
    if x.family == "stress_only" and np.max(np.abs(temperature - ref_t)) > x.temperature_tolerance_K + 1e-10:
        return Calculation(
            status="needs_data",
            values={},
            notes=("Stress-only observations exceed the declared single-temperature band.",),
        )
    design = _design(stress, temperature, ref_s, ref_t, x.family)
    if np.linalg.matrix_rank(design) != design.shape[1] or np.linalg.cond(design) > 1e8:
        return Calculation(
            status="needs_data",
            values={},
            notes=(
                "Temperature and stress effects are not separately identifiable; one temperature cannot determine an activation energy.",
            ),
        )
    initial = np.linalg.lstsq(design[~censored], y[~censored], rcond=None)[0]
    initial[1:] = np.maximum(initial[1:], 0.1)
    bounds = [(None, None)] + [(1e-8, 1000.0)] * (design.shape[1] - 1) + [(-12.0, 5.0)]
    fits = [
        minimize(
            _likelihood,
            np.r_[initial, math.log(s)],
            args=(design, y, censored),
            jac=True,
            method="L-BFGS-B",
            bounds=bounds,
            options={"ftol": 1e-13, "gtol": 1e-8, "maxiter": 3000},
        )
        for s in (0.1, 0.5, 1.5)
    ]
    successful = [f for f in fits if f.success and np.isfinite(f.fun)]
    if not successful:
        return Calculation(
            status="needs_data", values={}, notes=("Censored life likelihood did not converge.",)
        )
    fitted = min(successful, key=lambda f: f.fun)
    coefficients = fitted.x[:-1]
    sigma = math.exp(float(fitted.x[-1]))
    if (
        np.any(coefficients[1:] < 1e-7)
        or np.any(coefficients[1:] > 999.9)
        or not -11.99 < fitted.x[-1] < 4.99
    ):
        return Calculation(
            status="needs_data",
            values={},
            notes=("The likelihood reached a computational bound; this is not an identified physical fit.",),
        )
    z = (y - design @ coefficients) / sigma
    lam = _mills(z)
    lam_prime = lam * (lam - z)
    weights = np.where(censored, lam_prime, 1) / sigma**2
    cross = design.T @ (np.where(censored, z * lam_prime + lam, 2 * z) / sigma)
    scale_info = np.where(censored, lam_prime * z**2 + lam * z, 2 * z**2).sum()
    information = np.block(
        [[design.T @ (weights[:, None] * design), cross[:, None]], [cross[None, :], np.array([[scale_info]])]]
    )
    eig = np.linalg.eigvalsh(information)
    if eig.min() <= 0 or eig.max() / eig.min() > 1e12:
        return Calculation(
            status="needs_data",
            values={},
            notes=(
                "Observed information is singular or ill-conditioned; more informative observations are needed.",
            ),
        )
    condition = np.unique(np.column_stack([stress, temperature]), axis=0)
    n = float(coefficients[1] / np.ptp(np.log(stress)))
    q = None if x.family == "stress_only" else float(coefficients[2] / np.ptp(1 / temperature) * R_J_mol_K)
    model = CreepLifeModel(
        family=x.family,
        material_condition_id=x.material_condition_id,
        stress_basis=x.stress_basis,
        temperature_basis=x.temperature_basis,
        reference_stress_Pa=ref_s,
        reference_temperature_K=ref_t,
        log_reference_median_time_s=float(coefficients[0]),
        stress_exponent=n,
        activation_energy_J_mol=q,
        log_life_sigma=sigma,
        temperature_tolerance_K=x.temperature_tolerance_K,
        support_stress_Pa=condition[:, 0].tolist(),
        support_temperature_K=condition[:, 1].tolist(),
        longest_observed_failure_time_s=float(np.asarray(x.endpoint_time_s)[~censored].max()),
        training_digest=canonical_digest(x.model_dump(mode="json")),
        observations=len(stress),
        failures=int((~censored).sum()),
        evidence=x.evidence,
    )
    # Add the failure-only Jacobian to report the likelihood on seconds, not log-seconds.
    return Calculation(
        values=dict(
            model=model.model_dump(mode="json"),
            negative_log_likelihood_seconds=float(fitted.fun + y[~censored].sum()),
            information_condition_number=float(eig.max() / eig.min()),
            right_censored=int(censored.sum()),
            parameter_uncertainty_included=False,
        ),
        notes=(
            "Maximum likelihood uses the failure density and right-censored survival. Independent noninformative censoring, positive stress/thermal effects and constant log-life scatter are assumed. This fit is not independent experimental qualification.",
        ),
    )


def predict_life(x: CreepLifePrediction) -> Calculation:
    from scipy.integrate import quad
    from scipy.spatial import ConvexHull
    from scipy.special import log_ndtr, ndtr

    m = x.model
    if not x.constant_conditions_since_fresh_material_confirmed or not x.applicability_reviewed:
        return Calculation(
            status="needs_data",
            values={},
            notes=(
                "Review applicability and confirm unchanged stress/temperature and the fresh-material age origin for the complete past and future interval.",
            ),
        )
    if (x.material_condition_id, x.stress_basis, x.temperature_basis) != (
        m.material_condition_id,
        m.stress_basis,
        m.temperature_basis,
    ):
        return Calculation(
            status="needs_data",
            values={},
            notes=("Material condition, stress-control and temperature bases must match the fitted model.",),
        )
    if m.family == "stress_only":
        inside = (
            min(m.support_stress_Pa) <= x.initial_stress_Pa <= max(m.support_stress_Pa)
            and abs(x.temperature_K - m.reference_temperature_K) <= m.temperature_tolerance_K + 1e-10
        )
    else:
        support = np.column_stack([np.log(m.support_stress_Pa), 1 / np.asarray(m.support_temperature_K)])
        center, scale = support.mean(axis=0), np.ptp(support, axis=0)
        hull = ConvexHull((support - center) / scale)
        query = (np.array([math.log(x.initial_stress_Pa), 1 / x.temperature_K]) - center) / scale
        inside = bool(np.all(hull.equations[:, :-1] @ query + hull.equations[:, -1] <= 1e-10))
    if not inside:
        return Calculation(
            status="out_of_scope",
            values={},
            notes=(
                "Prediction lies outside the observed temperature/stress support; multivariate support uses the convex hull, not a rectangular extrapolation.",
            ),
        )
    bound = m.longest_observed_failure_time_s * x.maximum_time_extrapolation_factor
    if not math.isfinite(bound) or x.current_age_s > bound or x.horizon_s > bound - x.current_age_s:
        return Calculation(
            status="out_of_scope",
            values={},
            notes=(
                "The interval exceeds the caller-declared multiple of the longest observed failure time.",
            ),
        )
    mu = m.log_reference_median_time_s - m.stress_exponent * (
        math.log(x.initial_stress_Pa) - math.log(m.reference_stress_Pa)
    )
    if m.activation_energy_J_mol is not None:
        mu += m.activation_energy_J_mol / R_J_mol_K * (1 / x.temperature_K - 1 / m.reference_temperature_K)
    if not math.isfinite(mu) or mu < math.log(math.ulp(0.0)):
        return Calculation(
            status="out_of_scope",
            values={},
            notes=("Predicted log lifetime is outside the finite numerical range.",),
        )
    sigma = m.log_life_sigma
    if x.current_age_s == 0:
        z_end = (math.log(x.horizon_s) - mu) / sigma
        if not math.isfinite(z_end):
            return Calculation(
                status="out_of_scope",
                values={},
                notes=("Standardized lifetime exceeds the finite numerical range.",),
            )
        probability = float(ndtr(z_end))
    else:
        z = (math.log(x.current_age_s) - mu) / sigma
        ratio = x.horizon_s / x.current_age_s
        dz = (
            math.log1p(ratio) if math.isfinite(ratio) else math.log(x.horizon_s) - math.log(x.current_age_s)
        ) / sigma
        if not math.isfinite(z) or not math.isfinite(dz) or not math.isfinite(z + dz):
            return Calculation(
                status="out_of_scope",
                values={},
                notes=("Standardized lifetime exceeds the finite numerical range.",),
            )
        if dz < 0.5:
            increment = dz * quad(lambda u: float(_mills(z + u * dz)), 0, 1, epsabs=1e-12, epsrel=1e-10)[0]
        else:
            increment = float(log_ndtr(-z) - log_ndtr(-(z + dz)))
        probability = -math.expm1(-max(0.0, increment))
    median = math.exp(mu) if mu <= math.log(bound) else None
    return Calculation(
        values=dict(
            median_life_s=median,
            log_median_life_s=mu,
            median_beyond_declared_time_support=median is None,
            probability_given_survival=probability,
            log_life_sigma=sigma,
            parameter_uncertainty_included=False,
            declared_time_bound_s=bound,
            model_digest=canonical_digest(m.model_dump(mode="json")),
        ),
        notes=(
            "Population lognormal scatter is included; parameter, mechanism and measurement uncertainty are not. The conditional period probability applies only to the declared constant-condition rupture mechanism. It does not accept variable histories, repair rejuvenation or creep-fatigue interaction.",
        ),
    )


def specifications():
    return [
        ModelSpec(
            "creep.lognormal_life_fit",
            CreepLifeFit,
            fit_life,
            {"negative_log_likelihood_seconds": "1", "information_condition_number": "1"},
            (
                "Independent constant-condition specimens with explicit right-censoring and one common rupture mechanism.",
            ),
            ("nist_lognormal", "nist_accelerated_mle", "scipy_minimize", "creep_aft_likelihood"),
        ),
        ModelSpec(
            "creep.conditional_life",
            CreepLifePrediction,
            predict_life,
            {
                "median_life_s": "s",
                "probability_given_survival": "1",
                "declared_time_bound_s": "s",
                "log_life_sigma": "1",
            },
            (
                "Condition-bounded lognormal population under unchanged conditions from a fresh-material age origin.",
            ),
            ("nist_lognormal", "creep_aft_likelihood"),
            probability_semantics={"probability_given_survival": "conditional_first_failure_in_period"},
        ),
    ]
