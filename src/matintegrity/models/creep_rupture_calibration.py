"""Partitioned accelerated lognormal creep-rupture calibration."""

from __future__ import annotations

import math
from typing import Literal

import numpy as np
from pydantic import Field, model_validator

from ..contracts import Calculation, Contract, Evidence, Positive
from ..registry import ModelSpec


class CreepRuptureObservation(Contract):
    observation_id: str = Field(min_length=1)
    physical_specimen_id: str = Field(min_length=1)
    source_group_id: str = Field(min_length=1)
    independence_group_id: str = Field(min_length=1)
    partition: Literal["calibration", "holdout"]
    material_condition_id: str = Field(min_length=1)
    load_control_id: str = Field(min_length=1)
    stress_convention: Literal["initial_nominal_constant_load", "constant_true_stress"]
    stress_value_Pa: Positive
    stress_unit_token: Literal["Pa"]
    temperature_K: Positive
    temperature_unit_token: Literal["K"]
    endpoint_time_s: Positive
    time_unit_token: Literal["s"]
    endpoint_status: Literal["rupture", "right_censored"]
    nominal_weight: Positive = 1.0
    provider_id: str = Field(min_length=1)
    provider_revision: str = Field(min_length=1)
    provider_state_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    result_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    record_valid: bool
    invalid_basis: str | None = None
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def valid_record(self):
        if not self.record_valid and not self.invalid_basis:
            raise ValueError("an invalid creep-rupture record requires a basis")
        return self


class CreepRuptureFit(Contract):
    fit_id: str = Field(min_length=1)
    asset_id: str = Field(min_length=1)
    location_id: str = Field(min_length=1)
    physical_scope_id: str = Field(min_length=1)
    material_condition_id: str = Field(min_length=1)
    load_control_id: str = Field(min_length=1)
    stress_convention: Literal["initial_nominal_constant_load", "constant_true_stress"]
    regression_form: Literal["log_time_intercept_plus_log_inverse_stress_plus_reciprocal_temperature"]
    reference_stress_Pa: Positive
    reference_temperature_K: Positive
    observations: tuple[CreepRuptureObservation, ...] = Field(min_length=10)
    minimum_calibration_record_count: int = Field(ge=8)
    minimum_calibration_rupture_count: int = Field(ge=5)
    minimum_holdout_record_count: int = Field(ge=2)
    material_load_and_stress_convention_reviewed: bool
    specimen_source_and_independence_partitions_reviewed: bool
    stress_temperature_time_units_reviewed: bool
    rupture_and_right_censor_definitions_reviewed: bool
    censoring_independence_and_weights_reviewed: bool
    common_mechanism_over_support_reviewed: bool
    calibration_support_hull_reviewed: bool
    provider_lineage_and_digests_reviewed: bool
    regression_form_and_minimum_counts_reviewed: bool
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def unique_partitioned_records(self):
        observation_ids = [row.observation_id for row in self.observations]
        if len(observation_ids) != len(set(observation_ids)):
            raise ValueError("creep-rupture observation identifiers must be unique")
        for attribute, label in (
            ("physical_specimen_id", "physical specimen"),
            ("source_group_id", "source group"),
            ("independence_group_id", "independence group"),
        ):
            calibration = {
                getattr(row, attribute) for row in self.observations if row.partition == "calibration"
            }
            holdout = {getattr(row, attribute) for row in self.observations if row.partition == "holdout"}
            if calibration & holdout:
                raise ValueError(f"creep-rupture {label} cannot cross calibration and holdout")
        return self


def _negative_log_likelihood(parameters, design, log_time, censored, weights):
    from scipy.special import log_ndtr

    sigma = math.exp(float(parameters[-1]))
    mean = design @ parameters[:-1]
    z = (log_time - mean) / sigma
    failure_nll = 0.5 * z**2 + math.log(sigma) + 0.5 * math.log(2 * math.pi) + log_time
    censored_nll = -log_ndtr(-z)
    return float(np.dot(weights, np.where(censored, censored_nll, failure_nll)))


def creep_rupture_fit(x: CreepRuptureFit) -> Calculation:
    from scipy.optimize import minimize
    from scipy.spatial import ConvexHull
    from scipy.special import log_ndtr

    missing_reviews = [
        name
        for name in (
            "material_load_and_stress_convention_reviewed",
            "specimen_source_and_independence_partitions_reviewed",
            "stress_temperature_time_units_reviewed",
            "rupture_and_right_censor_definitions_reviewed",
            "censoring_independence_and_weights_reviewed",
            "common_mechanism_over_support_reviewed",
            "calibration_support_hull_reviewed",
            "provider_lineage_and_digests_reviewed",
            "regression_form_and_minimum_counts_reviewed",
        )
        if not getattr(x, name)
    ]
    invalid_observation_ids = [row.observation_id for row in x.observations if not row.record_valid]
    identity_mismatch_ids = [
        row.observation_id
        for row in x.observations
        if row.material_condition_id != x.material_condition_id
        or row.load_control_id != x.load_control_id
        or row.stress_convention != x.stress_convention
    ]
    if missing_reviews or invalid_observation_ids or identity_mismatch_ids:
        return Calculation(
            status="needs_data",
            values={
                "fit_id": x.fit_id,
                "missing_reviews": missing_reviews,
                "invalid_observation_ids": invalid_observation_ids,
                "identity_mismatch_observation_ids": identity_mismatch_ids,
            },
            notes=("Reviewed identities, partitions, censoring and provider records are required.",),
        )

    calibration = [row for row in x.observations if row.partition == "calibration"]
    holdout = [row for row in x.observations if row.partition == "holdout"]
    calibration_failures = [row for row in calibration if row.endpoint_status == "rupture"]
    if (
        len(calibration) < x.minimum_calibration_record_count
        or len(calibration_failures) < x.minimum_calibration_rupture_count
        or len(holdout) < x.minimum_holdout_record_count
    ):
        return Calculation(
            status="needs_data",
            values={
                "fit_id": x.fit_id,
                "calibration_record_count": len(calibration),
                "calibration_rupture_count": len(calibration_failures),
                "holdout_record_count": len(holdout),
            },
            notes=("The reviewed minimum calibration, rupture and holdout counts are not satisfied.",),
        )

    def raw_features(rows):
        return np.column_stack(
            (
                [math.log(x.reference_stress_Pa / row.stress_value_Pa) for row in rows],
                [1 / row.temperature_K - 1 / x.reference_temperature_K for row in rows],
            )
        )

    calibration_features = raw_features(calibration)
    center = calibration_features.mean(axis=0)
    scale = np.ptp(calibration_features, axis=0)
    if np.any(scale <= np.finfo(float).tiny):
        return Calculation(
            status="needs_data",
            values={"fit_id": x.fit_id, "feature_range": scale.tolist()},
            notes=("Multiple identifiable stress and temperature levels are required.",),
        )
    normalized_calibration = (calibration_features - center) / scale
    design = np.column_stack((np.ones(len(calibration)), normalized_calibration))
    if np.linalg.matrix_rank(design) < 3 or np.linalg.cond(design) > 1e8:
        return Calculation(
            status="needs_data",
            values={"fit_id": x.fit_id, "design_condition_number": float(np.linalg.cond(design))},
            notes=("Stress and reciprocal-temperature effects are not separately identifiable.",),
        )

    log_time = np.log([row.endpoint_time_s for row in calibration])
    censored = np.asarray([row.endpoint_status == "right_censored" for row in calibration])
    weights = np.asarray([row.nominal_weight for row in calibration], dtype=float)
    failure_initial = np.linalg.lstsq(design[~censored], log_time[~censored], rcond=None)[0]
    failure_initial[1:] = np.maximum(failure_initial[1:], 0.1)
    failure_residual = log_time[~censored] - design[~censored] @ failure_initial
    initial_sigma = max(float(np.std(failure_residual)), 0.1)
    bounds = [(None, None), (1e-10, None), (1e-10, None), (-12.0, 5.0)]
    fits = [
        minimize(
            _negative_log_likelihood,
            np.r_[failure_initial, math.log(initial_sigma * factor)],
            args=(design, log_time, censored, weights),
            method="L-BFGS-B",
            bounds=bounds,
            options={"ftol": 1e-13, "gtol": 1e-8, "maxiter": 3000},
        )
        for factor in (0.5, 1.0, 2.0)
    ]
    successful = [fit for fit in fits if fit.success and np.isfinite(fit.fun)]
    if not successful:
        return Calculation(
            status="needs_data",
            values={"fit_id": x.fit_id},
            notes=("The weighted censored lognormal likelihood did not converge.",),
        )
    fitted = min(successful, key=lambda fit: fit.fun)
    gamma = fitted.x[:-1]
    sigma = math.exp(float(fitted.x[-1]))
    if gamma[1] <= 1e-8 or gamma[2] <= 1e-8 or sigma <= 1e-8:
        return Calculation(
            status="needs_data",
            values={
                "fit_id": x.fit_id,
                "normalized_stress_coefficient": float(gamma[1]),
                "normalized_reciprocal_temperature_coefficient": float(gamma[2]),
                "log_time_sigma": sigma,
            },
            notes=("Positive stress and reciprocal-temperature effects were not identified.",),
        )
    stress_coefficient = float(gamma[1] / scale[0])
    reciprocal_temperature_coefficient_K = float(gamma[2] / scale[1])
    intercept = float(
        gamma[0] - stress_coefficient * center[0] - reciprocal_temperature_coefficient_K * center[1]
    )

    support_hull = ConvexHull(normalized_calibration)
    holdout_features = raw_features(holdout)
    normalized_holdout = (holdout_features - center) / scale
    inside = np.all(
        normalized_holdout @ support_hull.equations[:, :-1].T + support_hull.equations[:, -1] <= 1e-10,
        axis=1,
    )
    outside_holdout_ids = [
        row.observation_id for row, valid in zip(holdout, inside, strict=True) if not valid
    ]
    holdout_rows = []
    weighted_negative_log_likelihood = 0.0
    supported_holdout_weight = 0.0
    failure_squared_standardized_residual = 0.0
    failure_weight = 0.0
    for row, features, valid in zip(holdout, holdout_features, inside, strict=True):
        if not valid:
            continue
        mean = float(
            intercept + stress_coefficient * features[0] + reciprocal_temperature_coefficient_K * features[1]
        )
        z = (math.log(row.endpoint_time_s) - mean) / sigma
        if row.endpoint_status == "rupture":
            log_likelihood_seconds = (
                -0.5 * z**2 - math.log(sigma) - 0.5 * math.log(2 * math.pi) - math.log(row.endpoint_time_s)
            )
            failure_squared_standardized_residual += row.nominal_weight * z**2
            failure_weight += row.nominal_weight
        else:
            log_likelihood_seconds = float(log_ndtr(-z))
        weighted_negative_log_likelihood += row.nominal_weight * (-log_likelihood_seconds)
        supported_holdout_weight += row.nominal_weight
        holdout_rows.append(
            {
                "observation_id": row.observation_id,
                "endpoint_status": row.endpoint_status,
                "inside_calibration_support_hull": True,
                "predicted_log_median_time_s": mean,
                "standardized_log_time": z,
                "log_likelihood_seconds": log_likelihood_seconds,
            }
        )
    return Calculation(
        status="out_of_scope" if outside_holdout_ids else "computed",
        values={
            "fit_id": x.fit_id,
            "physical_scope_id": x.physical_scope_id,
            "regression_form": x.regression_form,
            "reference_stress_Pa": x.reference_stress_Pa,
            "reference_temperature_K": x.reference_temperature_K,
            "log_time_intercept_at_reference_conditions": intercept,
            "log_inverse_stress_coefficient": stress_coefficient,
            "reciprocal_temperature_coefficient_K": reciprocal_temperature_coefficient_K,
            "log_time_sigma": sigma,
            "weighted_calibration_negative_log_likelihood_seconds": float(fitted.fun),
            "calibration_record_count": len(calibration),
            "calibration_rupture_count": len(calibration_failures),
            "calibration_stress_range_Pa": [
                min(row.stress_value_Pa for row in calibration),
                max(row.stress_value_Pa for row in calibration),
            ],
            "calibration_temperature_range_K": [
                min(row.temperature_K for row in calibration),
                max(row.temperature_K for row in calibration),
            ],
            "outside_support_holdout_ids": outside_holdout_ids,
            "holdout_rows": holdout_rows,
            "holdout_weighted_mean_negative_log_likelihood_seconds": (
                weighted_negative_log_likelihood / supported_holdout_weight
                if supported_holdout_weight
                else None
            ),
            "holdout_rupture_weighted_mean_squared_standardized_residual": (
                failure_squared_standardized_residual / failure_weight if failure_weight else None
            ),
        },
        notes=(
            "Rupture records use the lognormal density on seconds; right-censored records use survival likelihood.",
            "The support is the calibration convex hull in log inverse stress and reciprocal temperature, not a rectangular extrapolation range.",
            "The fit does not qualify mechanism transitions, variable histories, life acceptance or automatic failure-probability linkage.",
        ),
    )


def specifications():
    def same_identity(x, context):
        if (x.asset_id, x.location_id) != (context.asset_id, context.location_id):
            raise ValueError("creep-rupture fit asset and location must match the run context")

    return [
        ModelSpec(
            "creep.accelerated_lognormal_rupture_fit",
            CreepRuptureFit,
            creep_rupture_fit,
            {
                "fit_id": "1",
                "physical_scope_id": "1",
                "reference_stress_Pa": "Pa",
                "reference_temperature_K": "K",
                "log_time_intercept_at_reference_conditions": "ln(s)",
                "log_inverse_stress_coefficient": "1",
                "reciprocal_temperature_coefficient_K": "K",
                "log_time_sigma": "1",
                "calibration_stress_range_Pa": "Pa",
                "calibration_temperature_range_K": "K",
                "outside_support_holdout_ids": "1",
                "holdout_rows": "mixed",
                "holdout_weighted_mean_negative_log_likelihood_seconds": "1",
                "holdout_rupture_weighted_mean_squared_standardized_residual": "1",
            },
            (
                "Log rupture time is linear in log(reference stress / stress) and reciprocal-temperature difference.",
                "Weighted rupture density and right-censored survival likelihood share one constant log-time scatter.",
                "Calibration and holdout specimen, source and independence groups are disjoint.",
            ),
            ("authored_partitioned_accelerated_lognormal_creep_rupture_likelihood",),
            context_validator=same_identity,
        )
    ]
