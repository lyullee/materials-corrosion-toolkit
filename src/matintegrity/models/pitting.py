"""Area maxima at one exposure, with explicit population assumptions and fit diagnostics."""

from __future__ import annotations

import math
from typing import Literal

import numpy as np
from pydantic import Field, model_validator

from ..contracts import Calculation, Contract, Fraction, Nonnegative, Positive
from ..registry import ModelSpec


class GumbelAreaMaximum(Contract):
    extreme_value_family: Literal["gumbel", "gev"] = "gumbel"
    population_id: str = Field(min_length=1)
    exposure_condition_id: str = Field(min_length=1)
    block_ids: list[str] = Field(min_length=8, max_length=5000)
    maximum_depth_m: list[Nonnegative] = Field(min_length=8, max_length=5000)
    block_area_m2: Positive
    target_block_count: int = Field(ge=1, le=10**12)
    independent_equivalent_blocks: bool
    same_exposure_and_surface_population: bool
    complete_uncensored_block_maxima: bool
    maximum_target_to_sampled_area_ratio: float = Field(ge=1)
    depth_threshold_m: Nonnegative
    quantile_probability: float = Field(gt=0, lt=1)
    confidence_level: float = Field(gt=0, lt=1)
    diagnostic_resamples: int = Field(ge=99, le=1999)
    parameter_resamples: int = Field(ge=99, le=1999)
    seed: int = Field(ge=0)
    minimum_goodness_of_fit_pvalue: float = Field(ge=0, lt=1)
    maximum_negative_depth_probability: Fraction

    @model_validator(mode="after")
    def align(self):
        if len(self.block_ids) != len(self.maximum_depth_m):
            raise ValueError("one observed maximum is required for each equal-area block")
        if len(set(self.block_ids)) != len(self.block_ids) or any(not i.strip() for i in self.block_ids):
            raise ValueError("block IDs must be unique and nonempty")
        return self


def gumbel_area_maximum(x: GumbelAreaMaximum) -> Calculation:
    if not all(
        (
            x.independent_equivalent_blocks,
            x.same_exposure_and_surface_population,
            x.complete_uncensored_block_maxima,
        )
    ):
        return Calculation(
            status="needs_data",
            values={},
            notes=(
                "Independent equivalent equal-area blocks at one exposure and uncensored maxima must be explicitly supported; repeated time points or selected deep pits do not meet this sampling contract.",
            ),
        )
    if x.target_block_count / len(x.block_ids) > x.maximum_target_to_sampled_area_ratio:
        return Calculation(
            status="out_of_scope",
            values={},
            notes=("Requested area exceeds the caller's declared target-to-observed-area bound.",),
        )
    if not all(math.isfinite(count * x.block_area_m2) for count in (len(x.block_ids), x.target_block_count)):
        return Calculation(
            status="out_of_scope",
            values={},
            notes=("Declared surface area exceeds the finite numerical range.",),
        )
    from scipy.stats import genextreme, goodness_of_fit, gumbel_r

    distribution = gumbel_r if x.extreme_value_family == "gumbel" else genextreme

    values = np.asarray(x.maximum_depth_m)
    reference = float(values.max())
    relative = values / reference if reference > 0 else values
    center_relative, spread_relative = float(relative.mean()), float(relative.std())
    center, spread = reference * center_relative, reference * spread_relative
    if spread == 0:
        return Calculation(
            status="needs_data",
            values={},
            notes=("Constant reported maxima do not identify a positive extreme-value scale.",),
        )
    normalized = (relative - center_relative) / spread_relative
    normalized_threshold = (x.depth_threshold_m / reference - center_relative) / spread_relative
    fitted = tuple(float(v) for v in distribution.fit(normalized))
    seeds = np.random.SeedSequence(x.seed).spawn(2)
    diagnostic = goodness_of_fit(
        distribution,
        normalized,
        statistic="ad",
        n_mc_samples=x.diagnostic_resamples,
        rng=np.random.default_rng(seeds[0]),
    )
    rng = np.random.default_rng(seeds[1])
    target_block_upper_tail = -math.expm1(math.log(x.quantile_probability) / x.target_block_count)

    def summaries(parameters):
        fitted_depth = float(distribution.isf(target_block_upper_tail, *parameters))
        block_logcdf = float(distribution.logcdf(normalized_threshold, *parameters))
        if not math.isfinite(fitted_depth) or math.isnan(block_logcdf):
            return math.nan, math.nan
        depth = center + spread * fitted_depth
        probability = -math.expm1(x.target_block_count * block_logcdf)
        return depth, probability

    boot = []
    for _ in range(x.parameter_resamples):
        replicate = distribution.rvs(*fitted, size=len(values), random_state=rng)
        replicate_fit = tuple(float(v) for v in distribution.fit(replicate))
        summary = summaries(replicate_fit)
        if not all(math.isfinite(v) for v in summary):
            return Calculation(
                status="out_of_scope",
                values={},
                notes=(
                    "A parameter replicate exceeds the finite numerical depth range; no replicate is silently discarded.",
                ),
            )
        boot.append(summary)
    tail = (1 - x.confidence_level) / 2
    intervals = np.quantile(boot, [tail, 1 - tail], axis=0)
    depth, probability = summaries(fitted)
    if x.extreme_value_family == "gumbel":
        shape, location, scale = 0.0, fitted[0], fitted[1]
    else:
        shape, location, scale = fitted
    mu, beta = center + spread * location, spread * scale
    if not all(math.isfinite(v) for v in (shape, mu, beta, depth, probability)) or beta <= 0:
        return Calculation(
            status="out_of_scope",
            values={},
            notes=("Fitted extreme-value parameters exceed the finite positive-scale numerical range.",),
        )
    # Fitted extreme-value families can assign probability to negative physical depth.
    negative_probability = float(distribution.cdf((0 - center) / spread, *fitted))
    diagnostic_ok = (
        diagnostic.pvalue >= x.minimum_goodness_of_fit_pvalue
        and negative_probability <= x.maximum_negative_depth_probability
        and depth >= 0
    )
    return Calculation(
        status="computed" if diagnostic_ok else "needs_data",
        values=dict(
            fitted_block_location_m=float(mu),
            fitted_block_scale_m=float(beta),
            extreme_value_family=x.extreme_value_family,
            fitted_shape_parameter_scipy=float(shape),
            observed_blocks=len(values),
            observed_area_m2=len(values) * x.block_area_m2,
            target_area_m2=x.target_block_count * x.block_area_m2,
            target_maximum_depth_quantile_m=depth,
            quantile_probability=x.quantile_probability,
            area_depth_exceedance_probability=probability,
            depth_quantile_parameter_interval_m=intervals[:, 0].tolist(),
            exceedance_probability_parameter_interval=intervals[:, 1].tolist(),
            confidence_level=x.confidence_level,
            anderson_darling_statistic=float(diagnostic.statistic),
            refitted_parametric_gof_pvalue=float(diagnostic.pvalue),
            gof_monte_carlo_resamples=x.diagnostic_resamples,
            parameter_resamples=x.parameter_resamples,
            fitted_negative_block_depth_probability=negative_probability,
            declared_diagnostic_outcome="satisfied" if diagnostic_ok else "unknown",
        ),
        notes=(
            "The target maximum CDF is the fitted block CDF raised to the integer number of equivalent independent blocks, at the same exposure. No exposure-time growth or future failure probability is inferred.",
            f"Anderson-Darling diagnostics refit each parametric replicate. Reported percentile intervals describe parameter sampling under the assumed {x.extreme_value_family} family, not model-form, dependence, sizing or detection uncertainty; they are not prediction intervals for one realized maximum.",
            "A non-rejected distribution and caller declarations do not establish independence or validate the physical tail. No negative fitted depth is clipped to zero.",
        ),
    )


def specifications():
    return [
        ModelSpec(
            "corrosion.gumbel_area_maximum",
            GumbelAreaMaximum,
            gumbel_area_maximum,
            {
                "fitted_block_location_m": "m",
                "fitted_block_scale_m": "m",
                "fitted_shape_parameter_scipy": "1",
                "observed_area_m2": "m^2",
                "target_area_m2": "m^2",
                "target_maximum_depth_quantile_m": "m",
                "depth_quantile_parameter_interval_m": "m",
                "area_depth_exceedance_probability": "1",
            },
            (
                "Equal-area complete independent block maxima from one declared surface population and exposure; caller-selected Gumbel or generalized extreme-value maximum approximation with explicit diagnostics.",
            ),
            ("nist_gumbel", "scipy_genextreme", "scipy_goodness_of_fit", "independent_area_maxima"),
            probability_semantics={
                "area_depth_exceedance_probability": "spatial_size_exceedance_at_one_exposure"
            },
        )
    ]
