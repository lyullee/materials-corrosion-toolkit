"""Transparent first-year atmospheric corrosion fitting and prediction."""

from __future__ import annotations

import math
from statistics import NormalDist
from typing import Literal

import numpy as np
from pydantic import Field, model_validator

from ..contracts import Calculation, Contract, Nonnegative, Positive, RunContext, canonical_digest
from ..registry import ModelSpec
from ..units import SECONDS_PER_YEAR


class AtmosphericFirstYearFitRow(Contract):
    observation_id: str = Field(min_length=1)
    source_group_id: str = Field(min_length=1)
    partition: Literal["calibration", "holdout"]
    first_year_loss_m: Positive
    temperature_K: Positive
    relative_humidity_fraction: float = Field(ge=0.0, le=1.0)
    chloride_deposition_mg_m2_day: Nonnegative
    sulfur_dioxide_deposition_mg_m2_day: Nonnegative
    source_content_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")


class AtmosphericSourceGroupMetric(Contract):
    source_group_id: str = Field(min_length=1)
    observation_count: int = Field(ge=1)
    log_rmse: Nonnegative
    absolute_log_bias: Nonnegative
    outside_support_count: int = Field(ge=0)
    outside_support_fraction: float = Field(ge=0.0, le=1.0)

    @model_validator(mode="after")
    def support_count_matches_fraction(self):
        if self.outside_support_count > self.observation_count:
            raise ValueError("atmospheric group support-exceedance count cannot exceed its observations")
        expected_fraction = self.outside_support_count / self.observation_count
        if not math.isclose(self.outside_support_fraction, expected_fraction, rel_tol=0.0, abs_tol=1e-12):
            raise ValueError("atmospheric group support-exceedance fraction must match its count")
        return self


class AtmosphericFirstYearModel(Contract):
    schema_version: Literal["matintegrity.atmospheric_first_year_model.v1"] = (
        "matintegrity.atmospheric_first_year_model.v1"
    )
    model_id: str = Field(min_length=1)
    fit_id: str = Field(min_length=1)
    feature_definition: Literal[
        "intercept,T_K_minus_288.15_over_10,RH_minus_0.75_over_0.1,log1p_Cl_mg_m2_day,log1p_SO2_mg_m2_day"
    ] = "intercept,T_K_minus_288.15_over_10,RH_minus_0.75_over_0.1,log1p_Cl_mg_m2_day,log1p_SO2_mg_m2_day"
    coefficient_log_m: float
    coefficient_temperature_per_10_K: float
    coefficient_relative_humidity_per_0_1: float
    coefficient_log1p_chloride: float
    coefficient_log1p_sulfur_dioxide: float
    coefficient_covariance: list[list[float]]
    residual_standard_deviation_log_m: Nonnegative
    calibration_support_temperature_K: list[Positive] = Field(min_length=2, max_length=2)
    calibration_support_relative_humidity_fraction: list[float] = Field(min_length=2, max_length=2)
    calibration_support_chloride_mg_m2_day: list[Nonnegative] = Field(min_length=2, max_length=2)
    calibration_support_sulfur_dioxide_mg_m2_day: list[Nonnegative] = Field(min_length=2, max_length=2)
    calibration_observation_count: int = Field(ge=6)
    calibration_source_group_ids: list[str] = Field(min_length=2)
    calibration_input_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    holdout_input_digest: str | None = Field(default=None, pattern=r"^[a-f0-9]{64}$")
    holdout_observation_count: int = Field(ge=1)
    holdout_log_rmse: Nonnegative
    holdout_absolute_log_bias: Nonnegative
    holdout_outside_support_fraction: float = Field(ge=0.0, le=1.0)
    holdout_source_group_metrics: list[AtmosphericSourceGroupMetric] = Field(default_factory=list)
    maximum_holdout_source_group_log_rmse: Nonnegative | None = None
    maximum_holdout_source_group_absolute_log_bias: Nonnegative | None = None
    source_group_transfer_criteria_met: bool = False
    maximum_holdout_log_rmse: Positive
    maximum_absolute_holdout_log_bias: Positive
    maximum_holdout_outside_support_fraction: float = Field(ge=0.0, le=1.0)
    transfer_criteria_met: bool
    parameter_uncertainty_scope: Literal["conditional_ols_given_fixed_covariates_and_model_form"] = (
        "conditional_ols_given_fixed_covariates_and_model_form"
    )

    @model_validator(mode="after")
    def valid_model(self):
        covariance = np.asarray(self.coefficient_covariance, dtype=float)
        if covariance.shape != (5, 5) or not np.isfinite(covariance).all():
            raise ValueError("atmospheric coefficient covariance must be a finite five-by-five matrix")
        if not np.allclose(covariance, covariance.T, rtol=0.0, atol=1e-12):
            raise ValueError("atmospheric coefficient covariance must be symmetric")
        eigenvalues = np.linalg.eigvalsh(covariance)
        covariance_scale = max(float(np.max(np.abs(eigenvalues))), np.finfo(float).tiny)
        psd_tolerance = 128.0 * np.finfo(float).eps * covariance_scale
        if float(np.min(eigenvalues)) < -psd_tolerance:
            raise ValueError("atmospheric coefficient covariance must be positive semidefinite")
        supports = (
            self.calibration_support_temperature_K,
            self.calibration_support_relative_humidity_fraction,
            self.calibration_support_chloride_mg_m2_day,
            self.calibration_support_sulfur_dioxide_mg_m2_day,
        )
        if any(bounds[1] < bounds[0] for bounds in supports):
            raise ValueError("atmospheric model support bounds must be ordered")
        if len(set(self.calibration_source_group_ids)) != len(self.calibration_source_group_ids):
            raise ValueError("atmospheric calibration source-group identifiers must be unique")
        if self.holdout_source_group_metrics:
            if self.holdout_input_digest is None:
                raise ValueError("source-group transfer diagnostics require a holdout input digest")
            holdout_group_ids = [item.source_group_id for item in self.holdout_source_group_metrics]
            if len(set(holdout_group_ids)) != len(holdout_group_ids):
                raise ValueError("atmospheric holdout source-group identifiers must be unique")
            if set(holdout_group_ids) & set(self.calibration_source_group_ids):
                raise ValueError("atmospheric calibration and holdout source groups cannot overlap")
            if (
                sum(item.observation_count for item in self.holdout_source_group_metrics)
                != self.holdout_observation_count
            ):
                raise ValueError("atmospheric holdout group metrics must partition every holdout observation")
            group_outside_count = sum(
                item.outside_support_count for item in self.holdout_source_group_metrics
            )
            expected_outside_fraction = group_outside_count / self.holdout_observation_count
            if not math.isclose(
                self.holdout_outside_support_fraction,
                expected_outside_fraction,
                rel_tol=0.0,
                abs_tol=1e-12,
            ):
                raise ValueError("atmospheric holdout support fraction must match group diagnostics")
            if self.maximum_holdout_source_group_log_rmse != max(
                item.log_rmse for item in self.holdout_source_group_metrics
            ):
                raise ValueError("maximum holdout source-group RMSE must match its diagnostics")
            if self.maximum_holdout_source_group_absolute_log_bias != max(
                item.absolute_log_bias for item in self.holdout_source_group_metrics
            ):
                raise ValueError("maximum holdout source-group bias must match its diagnostics")
            expected_group_gate = bool(
                self.maximum_holdout_source_group_log_rmse <= self.maximum_holdout_log_rmse
                and self.maximum_holdout_source_group_absolute_log_bias
                <= self.maximum_absolute_holdout_log_bias
            )
            if self.source_group_transfer_criteria_met != expected_group_gate:
                raise ValueError("source-group transfer flag must match its declared error limits")
            expected_transfer_gate = bool(
                self.holdout_log_rmse <= self.maximum_holdout_log_rmse
                and self.holdout_absolute_log_bias <= self.maximum_absolute_holdout_log_bias
                and expected_group_gate
                and self.holdout_outside_support_fraction <= self.maximum_holdout_outside_support_fraction
            )
            if self.transfer_criteria_met != expected_transfer_gate:
                raise ValueError("overall atmospheric transfer flag must match all stored diagnostics")
        elif (
            self.maximum_holdout_source_group_log_rmse is not None
            or self.maximum_holdout_source_group_absolute_log_bias is not None
            or self.source_group_transfer_criteria_met
        ):
            raise ValueError("group-transfer qualification requires source-group metric diagnostics")
        return self


class AtmosphericFirstYearFit(Contract):
    fit_id: str = Field(min_length=1)
    model_id: str = Field(min_length=1)
    observations: list[AtmosphericFirstYearFitRow] = Field(min_length=12)
    minimum_calibration_source_groups: int = Field(default=2, ge=2)
    minimum_holdout_source_groups: int = Field(default=2, ge=2)
    maximum_holdout_log_rmse: Positive
    maximum_absolute_holdout_log_bias: Positive
    maximum_holdout_outside_support_fraction: float = Field(ge=0.0, le=1.0)
    source_group_partition_reviewed: bool
    first_year_endpoint_reviewed: bool
    atmospheric_carbon_steel_scope_reviewed: bool
    covariate_origin_reviewed: bool
    aggregate_analysis_authorized: bool
    pointwise_redistribution_authorized: bool

    @model_validator(mode="after")
    def valid_partition(self):
        if len({row.observation_id for row in self.observations}) != len(self.observations):
            raise ValueError("atmospheric observation identifiers must be unique")
        calibration = [row for row in self.observations if row.partition == "calibration"]
        holdout = [row for row in self.observations if row.partition == "holdout"]
        if len(calibration) <= 5 or not holdout:
            raise ValueError("atmospheric fit requires more than five calibration rows and holdout rows")
        calibration_groups = {row.source_group_id for row in calibration}
        holdout_groups = {row.source_group_id for row in holdout}
        if len(calibration_groups) < self.minimum_calibration_source_groups:
            raise ValueError("atmospheric calibration source-group count is below the declared minimum")
        if len(holdout_groups) < self.minimum_holdout_source_groups:
            raise ValueError("atmospheric holdout source-group count is below the declared minimum")
        if calibration_groups & holdout_groups:
            raise ValueError("atmospheric source groups cannot cross calibration and holdout partitions")
        return self


def _features(row) -> list[float]:
    return [
        1.0,
        (row.temperature_K - 288.15) / 10.0,
        (row.relative_humidity_fraction - 0.75) / 0.1,
        math.log1p(row.chloride_deposition_mg_m2_day),
        math.log1p(row.sulfur_dioxide_deposition_mg_m2_day),
    ]


def _metrics(observed: np.ndarray, predicted: np.ndarray) -> dict[str, float]:
    residual = predicted - observed
    denominator = float(np.sum((observed - np.mean(observed)) ** 2))
    return {
        "count": int(observed.size),
        "log_rmse": float(np.sqrt(np.mean(residual**2))),
        "log_mae": float(np.mean(np.abs(residual))),
        "log_bias_predicted_minus_observed": float(np.mean(residual)),
        "geometric_rmse_factor": float(math.exp(np.sqrt(np.mean(residual**2)))),
        "r_squared": float(1.0 - np.sum(residual**2) / denominator) if denominator > 0 else None,
    }


def atmospheric_first_year_fit(x: AtmosphericFirstYearFit) -> Calculation:
    reviews = (
        x.source_group_partition_reviewed,
        x.first_year_endpoint_reviewed,
        x.atmospheric_carbon_steel_scope_reviewed,
        x.covariate_origin_reviewed,
        x.aggregate_analysis_authorized,
    )
    if not all(reviews):
        return Calculation(
            status="needs_data",
            values={},
            notes=(
                "Reviewed source-group partition, endpoint, material/environment scope, covariate origin and aggregate-analysis authority are required.",
            ),
        )
    calibration = [row for row in x.observations if row.partition == "calibration"]
    holdout = [row for row in x.observations if row.partition == "holdout"]
    design = np.asarray([_features(row) for row in calibration], dtype=float)
    response = np.log(np.asarray([row.first_year_loss_m for row in calibration], dtype=float))
    coefficients, _, rank, singular_values = np.linalg.lstsq(design, response, rcond=None)
    if rank != design.shape[1]:
        return Calculation(
            status="needs_data",
            values={"design_rank": int(rank), "required_design_rank": design.shape[1]},
            notes=("Atmospheric calibration design is rank deficient; coefficients are not identified.",),
        )
    calibration_prediction = design @ coefficients
    residual = response - calibration_prediction
    degrees_of_freedom = len(calibration) - design.shape[1]
    residual_variance = float(np.sum(residual**2) / degrees_of_freedom)
    covariance = residual_variance * np.linalg.inv(design.T @ design)
    holdout_design = np.asarray([_features(row) for row in holdout], dtype=float)
    holdout_response = np.log(np.asarray([row.first_year_loss_m for row in holdout], dtype=float))
    holdout_prediction = holdout_design @ coefficients
    support_fields = (
        "temperature_K",
        "relative_humidity_fraction",
        "chloride_deposition_mg_m2_day",
        "sulfur_dioxide_deposition_mg_m2_day",
    )
    support = {
        field: [
            min(float(getattr(row, field)) for row in calibration),
            max(float(getattr(row, field)) for row in calibration),
        ]
        for field in support_fields
    }
    outside_ids = [
        row.observation_id
        for row in holdout
        if any(
            not support[field][0] <= float(getattr(row, field)) <= support[field][1]
            for field in support_fields
        )
    ]
    calibration_metrics = _metrics(response, calibration_prediction)
    holdout_metrics = _metrics(holdout_response, holdout_prediction)
    group_metrics = []
    for source_group_id in sorted({row.source_group_id for row in holdout}):
        indices = [index for index, row in enumerate(holdout) if row.source_group_id == source_group_id]
        metrics = _metrics(holdout_response[indices], holdout_prediction[indices])
        group_outside_count = sum(holdout[index].observation_id in outside_ids for index in indices)
        group_metrics.append(
            AtmosphericSourceGroupMetric(
                source_group_id=source_group_id,
                observation_count=len(indices),
                log_rmse=metrics["log_rmse"],
                absolute_log_bias=abs(metrics["log_bias_predicted_minus_observed"]),
                outside_support_count=group_outside_count,
                outside_support_fraction=group_outside_count / len(indices),
            )
        )
    maximum_group_rmse = max(item.log_rmse for item in group_metrics)
    maximum_group_absolute_bias = max(item.absolute_log_bias for item in group_metrics)
    source_group_transfer_met = bool(
        maximum_group_rmse <= x.maximum_holdout_log_rmse
        and maximum_group_absolute_bias <= x.maximum_absolute_holdout_log_bias
    )
    outside_fraction = len(outside_ids) / len(holdout)
    transfer_criteria_met = bool(
        holdout_metrics["log_rmse"] <= x.maximum_holdout_log_rmse
        and abs(holdout_metrics["log_bias_predicted_minus_observed"]) <= x.maximum_absolute_holdout_log_bias
        and source_group_transfer_met
        and outside_fraction <= x.maximum_holdout_outside_support_fraction
    )
    calibration_groups = sorted({row.source_group_id for row in calibration})
    model = AtmosphericFirstYearModel(
        model_id=x.model_id,
        fit_id=x.fit_id,
        coefficient_log_m=float(coefficients[0]),
        coefficient_temperature_per_10_K=float(coefficients[1]),
        coefficient_relative_humidity_per_0_1=float(coefficients[2]),
        coefficient_log1p_chloride=float(coefficients[3]),
        coefficient_log1p_sulfur_dioxide=float(coefficients[4]),
        coefficient_covariance=covariance.tolist(),
        residual_standard_deviation_log_m=math.sqrt(residual_variance),
        calibration_support_temperature_K=support["temperature_K"],
        calibration_support_relative_humidity_fraction=support["relative_humidity_fraction"],
        calibration_support_chloride_mg_m2_day=support["chloride_deposition_mg_m2_day"],
        calibration_support_sulfur_dioxide_mg_m2_day=support["sulfur_dioxide_deposition_mg_m2_day"],
        calibration_observation_count=len(calibration),
        calibration_source_group_ids=calibration_groups,
        calibration_input_digest=canonical_digest([row.model_dump(mode="json") for row in calibration]),
        holdout_input_digest=canonical_digest([row.model_dump(mode="json") for row in holdout]),
        holdout_observation_count=len(holdout),
        holdout_log_rmse=holdout_metrics["log_rmse"],
        holdout_absolute_log_bias=abs(holdout_metrics["log_bias_predicted_minus_observed"]),
        holdout_outside_support_fraction=outside_fraction,
        holdout_source_group_metrics=[item.model_dump(mode="json") for item in group_metrics],
        maximum_holdout_source_group_log_rmse=maximum_group_rmse,
        maximum_holdout_source_group_absolute_log_bias=maximum_group_absolute_bias,
        source_group_transfer_criteria_met=source_group_transfer_met,
        maximum_holdout_log_rmse=x.maximum_holdout_log_rmse,
        maximum_absolute_holdout_log_bias=x.maximum_absolute_holdout_log_bias,
        maximum_holdout_outside_support_fraction=x.maximum_holdout_outside_support_fraction,
        transfer_criteria_met=transfer_criteria_met,
    )
    return Calculation(
        values={
            "model": model.model_dump(mode="json"),
            "calibration_metrics": calibration_metrics,
            "holdout_metrics": holdout_metrics,
            "holdout_source_group_metrics": [item.model_dump(mode="json") for item in group_metrics],
            "holdout_input_digest": canonical_digest([row.model_dump(mode="json") for row in holdout]),
            "maximum_holdout_source_group_log_rmse": maximum_group_rmse,
            "maximum_holdout_source_group_absolute_log_bias": maximum_group_absolute_bias,
            "source_group_transfer_criteria_met": source_group_transfer_met,
            "holdout_observation_count": len(holdout),
            "holdout_source_group_ids": sorted({row.source_group_id for row in holdout}),
            "holdout_outside_calibration_support_count": len(outside_ids),
            "holdout_outside_calibration_support_observation_ids": outside_ids,
            "design_rank": int(rank),
            "design_condition_number": float(singular_values[0] / singular_values[-1]),
            "pointwise_redistribution_authorized": x.pointwise_redistribution_authorized,
            "transfer_criteria_met": transfer_criteria_met,
        },
        notes=(
            "The fit is an independently specified conditional log-linear screening model; programme and holdout source groups remain disjoint.",
            "Holdout metrics are source-separated transfer diagnostics, not proof of physical-specimen independence, long-term growth, localized corrosion or structural reliability.",
            "Conditional OLS covariance excludes covariate measurement, source compilation, model-form and population uncertainty.",
        ),
    )


class AtmosphericFirstYearPrediction(Contract):
    prediction_id: str = Field(min_length=1)
    asset_id: str = Field(min_length=1)
    location_id: str = Field(min_length=1)
    physical_scope_id: str = Field(min_length=1)
    material_condition_id: str = Field(min_length=1)
    exposure_environment_id: str = Field(min_length=1)
    time_basis: str = Field(min_length=1)
    exposure_start_s: Nonnegative
    exposure_duration_s: Positive
    model: AtmosphericFirstYearModel
    temperature_K: Positive
    relative_humidity_fraction: float = Field(ge=0.0, le=1.0)
    chloride_deposition_mg_m2_day: Nonnegative
    sulfur_dioxide_deposition_mg_m2_day: Nonnegative
    confidence_level: float = Field(default=0.95, gt=0.0, lt=1.0)
    first_year_atmospheric_carbon_steel_scope_reviewed: bool
    covariates_reviewed: bool
    model_applicability_reviewed: bool
    extrapolation_reviewed: bool = False
    limited_transfer_override_reviewed: bool = False

    @model_validator(mode="after")
    def first_year(self):
        if not math.isclose(self.exposure_duration_s, SECONDS_PER_YEAR, rel_tol=0.0, abs_tol=1.0):
            raise ValueError("atmospheric prediction is restricted to one declared first-year exposure")
        return self


def atmospheric_first_year_prediction(x: AtmosphericFirstYearPrediction) -> Calculation:
    if not (
        x.first_year_atmospheric_carbon_steel_scope_reviewed
        and x.covariates_reviewed
        and x.model_applicability_reviewed
    ):
        return Calculation(
            status="needs_data",
            values={},
            notes=("Reviewed first-year scope, covariates and model applicability are required.",),
        )
    if (
        not x.model.transfer_criteria_met or not x.model.source_group_transfer_criteria_met
    ) and not x.limited_transfer_override_reviewed:
        return Calculation(
            status="needs_data",
            values={
                "transfer_criteria_met": False,
                "source_group_transfer_criteria_met": x.model.source_group_transfer_criteria_met,
                "holdout_log_rmse": x.model.holdout_log_rmse,
                "holdout_absolute_log_bias": x.model.holdout_absolute_log_bias,
                "holdout_outside_support_fraction": x.model.holdout_outside_support_fraction,
            },
            notes=(
                "The source-separated holdout transfer criteria were not met; prediction requires an explicit limited-transfer override review.",
                "The source-group transfer criterion requires every independent holdout group to satisfy the caller-declared log-RMSE and absolute log-bias limits.",
            ),
        )
    support_checks = {
        "temperature_K": (
            x.model.calibration_support_temperature_K[0]
            <= x.temperature_K
            <= x.model.calibration_support_temperature_K[1]
        ),
        "relative_humidity_fraction": (
            x.model.calibration_support_relative_humidity_fraction[0]
            <= x.relative_humidity_fraction
            <= x.model.calibration_support_relative_humidity_fraction[1]
        ),
        "chloride_deposition_mg_m2_day": (
            x.model.calibration_support_chloride_mg_m2_day[0]
            <= x.chloride_deposition_mg_m2_day
            <= x.model.calibration_support_chloride_mg_m2_day[1]
        ),
        "sulfur_dioxide_deposition_mg_m2_day": (
            x.model.calibration_support_sulfur_dioxide_mg_m2_day[0]
            <= x.sulfur_dioxide_deposition_mg_m2_day
            <= x.model.calibration_support_sulfur_dioxide_mg_m2_day[1]
        ),
    }
    outside = [name for name, inside in support_checks.items() if not inside]
    if outside and not x.extrapolation_reviewed:
        return Calculation(
            status="out_of_scope",
            values={"support_checks": support_checks, "outside_support_fields": outside},
            notes=("Prediction inputs leave calibration support and extrapolation was not reviewed.",),
        )
    feature = np.asarray(_features(x), dtype=float)
    coefficients = np.asarray(
        [
            x.model.coefficient_log_m,
            x.model.coefficient_temperature_per_10_K,
            x.model.coefficient_relative_humidity_per_0_1,
            x.model.coefficient_log1p_chloride,
            x.model.coefficient_log1p_sulfur_dioxide,
        ]
    )
    covariance = np.asarray(x.model.coefficient_covariance, dtype=float)
    predicted_log_loss = float(feature @ coefficients)
    conditional_mean_variance = max(0.0, float(feature @ covariance @ feature))
    prediction_variance = conditional_mean_variance + x.model.residual_standard_deviation_log_m**2
    quantile = NormalDist().inv_cdf(0.5 + 0.5 * x.confidence_level)
    bounds_log = [
        predicted_log_loss - quantile * math.sqrt(prediction_variance),
        predicted_log_loss + quantile * math.sqrt(prediction_variance),
    ]
    try:
        loss = math.exp(predicted_log_loss)
        bounds = [math.exp(value) for value in bounds_log]
    except OverflowError:
        return Calculation(
            status="needs_data",
            values={"predicted_log_first_year_loss_m": predicted_log_loss},
            notes=("Atmospheric prediction is outside finite binary64 loss representation.",),
        )
    return Calculation(
        values={
            "predicted_first_year_loss_m": loss,
            "equivalent_first_year_rate_m_s": loss / x.exposure_duration_s,
            "predicted_log_first_year_loss_m": predicted_log_loss,
            "conditional_mean_standard_error_log_m": math.sqrt(conditional_mean_variance),
            "conditional_prediction_standard_deviation_log_m": math.sqrt(prediction_variance),
            "conditional_prediction_level": x.confidence_level,
            "conditional_prediction_interval_first_year_loss_m": bounds,
            "support_checks": support_checks,
            "outside_support_fields": outside,
            "extrapolation_used": bool(outside),
        },
        notes=(
            "The interval is conditional on fixed covariates and the selected log-linear model; it excludes covariate, source, model-form and population uncertainty.",
            "First-year average atmospheric loss is not localized penetration, multi-year growth, remaining life, acceptance or failure probability.",
        ),
    )


def _prediction_context(x: AtmosphericFirstYearPrediction, context: RunContext) -> None:
    if x.asset_id != context.asset_id or x.location_id != context.location_id:
        raise ValueError("atmospheric prediction asset and location must match the evaluation context")
    if x.time_basis != context.time_basis:
        raise ValueError("atmospheric prediction time basis must match the evaluation context")


def specifications():
    return [
        ModelSpec(
            "corrosion.atmospheric_first_year_fit",
            AtmosphericFirstYearFit,
            atmospheric_first_year_fit,
            {
                "model": "1",
                "calibration_metrics": "1",
                "holdout_metrics": "1",
                "holdout_observation_count": "count",
                "holdout_source_group_ids": "1",
                "holdout_outside_calibration_support_count": "count",
                "holdout_outside_calibration_support_observation_ids": "1",
                "design_rank": "count",
                "design_condition_number": "1",
                "pointwise_redistribution_authorized": "1",
                "transfer_criteria_met": "1",
                "holdout_source_group_metrics": "mixed",
                "maximum_holdout_source_group_log_rmse": "1",
                "maximum_holdout_source_group_absolute_log_bias": "1",
                "source_group_transfer_criteria_met": "1",
            },
            (
                "Conditional log-linear first-year atmospheric carbon-steel loss model with temperature, relative humidity, chloride and sulfur-dioxide covariates.",
                "Calibration and holdout source groups are predeclared and disjoint; no physical-specimen independence, long-term growth or localized loss is inferred.",
            ),
            ("atmospheric_first_year_loglinear_fit_derivation",),
        ),
        ModelSpec(
            "corrosion.atmospheric_first_year_prediction",
            AtmosphericFirstYearPrediction,
            atmospheric_first_year_prediction,
            {
                "predicted_first_year_loss_m": "m",
                "equivalent_first_year_rate_m_s": "m/s",
                "predicted_log_first_year_loss_m": "log(m)",
                "conditional_mean_standard_error_log_m": "log(m)",
                "conditional_prediction_standard_deviation_log_m": "log(m)",
                "conditional_prediction_level": "1",
                "conditional_prediction_interval_first_year_loss_m": "m",
                "support_checks": "1",
                "outside_support_fields": "1",
                "extrapolation_used": "1",
            },
            (
                "Uses only a reviewed AtmosphericFirstYearModel over one first-year atmospheric carbon-steel exposure and explicit environmental covariates.",
                "Calibration-support departures stop unless extrapolation is explicitly reviewed; conditional intervals exclude model-form and covariate uncertainty.",
            ),
            ("atmospheric_first_year_loglinear_prediction_derivation",),
            context_validator=_prediction_context,
        ),
    ]
