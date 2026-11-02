"""Bounded descriptive energy-transition fitting for one declared impact-test series."""

from __future__ import annotations

import math
from typing import Literal

import numpy as np
from pydantic import Field, model_validator

from ..contracts import Calculation, Contract, Nonnegative, Positive
from ..registry import ModelSpec


class ImpactTransition(Contract):
    series_id: str = Field(min_length=1)
    specimen_geometry_id: str = Field(min_length=1)
    material_condition_id: str = Field(min_length=1)
    orientation_id: str = Field(min_length=1)
    observational_unit_description: str = Field(min_length=1)
    observation_ids: list[str] = Field(min_length=8)
    temperature_K: list[Positive] = Field(min_length=8)
    absorbed_energy_J: list[Nonnegative] = Field(min_length=8)
    target_energy_J: Nonnegative
    minimum_relative_shelf_coverage: float = Field(gt=0.5, lt=1)
    loss: Literal["linear", "soft_l1"]
    residual_scale_J: Positive

    @model_validator(mode="after")
    def series(self):
        if len({len(self.observation_ids), len(self.temperature_K), len(self.absorbed_energy_J)}) != 1:
            raise ValueError("impact observations require aligned identities, temperatures and energies")
        if any(not i.strip() for i in self.observation_ids) or len(set(self.observation_ids)) != len(
            self.observation_ids
        ):
            raise ValueError("unique nonempty observation IDs are required")
        if len(set(self.temperature_K)) < 5:
            raise ValueError("at least five distinct test temperatures are required")
        return self


def impact_transition(x: ImpactTransition) -> Calculation:
    from scipy.optimize import least_squares
    from scipy.special import expit, logit

    temperature = np.asarray(x.temperature_K)
    energy = np.asarray(x.absorbed_energy_J)
    energy_scale = float(energy.max())
    if energy_scale <= 0:
        return Calculation(
            status="needs_data", values={}, notes=("No positive energy scale or transition was observed.",)
        )
    center = float(temperature.mean())
    scale = float(temperature.std())
    z = (temperature - center) / scale

    def prediction(parameters):
        lower, log_delta, midpoint, log_width = parameters
        return lower + np.exp(log_delta) * expit((z - midpoint) / np.exp(log_width))

    def residual(parameters):
        return (prediction(parameters) * energy_scale - energy) / x.residual_scale_J

    fits = []
    for midpoint in np.quantile(z, [0.25, 0.5, 0.75]):
        for width in (0.25, 1.0):
            fitted = least_squares(
                residual,
                [0.0, 0.0, float(midpoint), math.log(width)],
                bounds=([0, -18, -20, -8], [2, math.log(1000), 20, 8]),
                loss=x.loss,
                f_scale=1.0,
                xtol=1e-11,
                ftol=1e-11,
                gtol=1e-10,
                max_nfev=4000,
            )
            if fitted.success and np.isfinite(fitted.x).all():
                fits.append(fitted)
    if not fits:
        return Calculation(
            status="needs_data", values={}, notes=("Energy-transition optimization did not converge.",)
        )
    best = min(fits, key=lambda f: f.cost)
    lower, log_delta, midpoint, log_width = (float(v) for v in best.x)
    lower *= energy_scale
    delta = math.exp(log_delta) * energy_scale
    transition = center + scale * midpoint
    width = scale * math.exp(log_width)
    information = best.jac.T @ best.jac
    condition = float(np.linalg.cond(information))
    fractions = expit((temperature - transition) / width)
    shelves = (
        float(fractions.min()) <= 1 - x.minimum_relative_shelf_coverage
        and float(fractions.max()) >= x.minimum_relative_shelf_coverage
    )
    numeric_bounds = (
        abs(log_delta + 18) < 1e-5
        or abs(log_delta - math.log(1000)) < 1e-5
        or abs(midpoint) >= 19.99
        or abs(log_width) >= 7.99
    )
    identified = (
        shelves and math.isfinite(condition) and condition < 1e12 and not numeric_bounds and transition > 0
    )
    target = None
    if lower < x.target_energy_J < lower + delta:
        crossing = transition + width * float(logit((x.target_energy_J - lower) / delta))
        if temperature.min() <= crossing <= temperature.max():
            target = crossing
    predicted = prediction(best.x) * energy_scale
    return Calculation(
        status="computed" if identified else "needs_data",
        values=dict(
            lower_shelf_energy_J=lower,
            upper_shelf_energy_J=lower + delta,
            mid_shelf_temperature_K=transition,
            logistic_transition_width_K=width,
            target_energy_J=x.target_energy_J,
            target_energy_crossing_temperature_K=target,
            observed_temperature_domain_K=[float(temperature.min()), float(temperature.max())],
            relative_shelf_coverage=[float(fractions.min()), float(fractions.max())],
            shelf_coverage_satisfied=shelves,
            fitted_energy_J=predicted.tolist(),
            residual_rmse_J=float(np.sqrt(np.mean((predicted - energy) ** 2))),
            residual_J=(predicted - energy).tolist(),
            scaled_information_condition_number=condition if math.isfinite(condition) else None,
            numerical_parameter_bound_reached=numeric_bounds,
            loss=x.loss,
        ),
        notes=(
            "Descriptive increasing logistic energy-temperature curve for one caller-declared material, geometry, orientation and condition; no automatic specimen-size or irradiation conversion.",
            "Shelf coverage and numerical identifiability are checked. A missing target crossing is not extrapolated. No confidence level, fracture toughness or allowable service temperature is inferred.",
        ),
    )


def specifications():
    return [
        ModelSpec(
            "materials.impact_transition",
            ImpactTransition,
            impact_transition,
            {
                "lower_shelf_energy_J": "J",
                "upper_shelf_energy_J": "J",
                "mid_shelf_temperature_K": "K",
                "logistic_transition_width_K": "K",
                "target_energy_J": "J",
                "target_energy_crossing_temperature_K": "K",
                "fitted_energy_J": "J",
                "residual_rmse_J": "J",
                "residual_J": "J",
            },
            (
                "One declared impact-test series with bounded logistic shelves, explicit robust-loss choice and observed-domain crossing.",
            ),
            ("scipy_least_squares", "declared_impact_transition"),
        )
    ]
