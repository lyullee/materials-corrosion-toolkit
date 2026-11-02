"""Qualified signal-response POD calibration with explicit holdout diagnostics."""

from __future__ import annotations

import math
from typing import Literal

import numpy as np
from pydantic import Field, model_validator

from ..contracts import Calculation, Contract, Evidence, Positive
from ..registry import ModelSpec


class SignalResponseObservation(Contract):
    observation_id: str = Field(min_length=1)
    physical_specimen_id: str = Field(min_length=1)
    source_group_id: str = Field(min_length=1)
    independence_group_id: str = Field(min_length=1)
    partition: Literal["calibration", "holdout"]
    flaw_size_value: Positive
    flaw_size_definition_id: str = Field(min_length=1)
    flaw_size_unit_token: str = Field(min_length=1)
    signal_definition_id: str = Field(min_length=1)
    signal_unit_token: str = Field(min_length=1)
    observation_status: Literal["observed", "left_censored", "right_censored", "missing"]
    reported_signal_value: float | None = None
    censor_limit_value: float | None = None
    missing_or_censor_basis: str | None = None
    nominal_weight: Positive = 1.0
    provider_id: str = Field(min_length=1)
    provider_revision: str = Field(min_length=1)
    provider_state_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    result_digest: str | None = Field(default=None, pattern=r"^[a-f0-9]{64}$")
    record_valid: bool
    invalid_basis: str | None = None
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def coherent_observation(self):
        if self.observation_status == "observed":
            if self.reported_signal_value is None or self.censor_limit_value is not None:
                raise ValueError("observed signal-response records require only a reported signal")
            if self.result_digest is None:
                raise ValueError("observed signal-response records require a result digest")
        elif self.observation_status in {"left_censored", "right_censored"}:
            if self.censor_limit_value is None or self.reported_signal_value is not None:
                raise ValueError("censored signal-response records require only a censor limit")
            if not self.missing_or_censor_basis or self.result_digest is None:
                raise ValueError("censored signal-response records require a basis and result digest")
        else:
            if self.reported_signal_value is not None or self.censor_limit_value is not None:
                raise ValueError("missing signal-response records cannot carry a signal value")
            if not self.missing_or_censor_basis or self.result_digest is not None:
                raise ValueError("missing signal-response records require only a missingness basis")
        if not self.record_valid and not self.invalid_basis:
            raise ValueError("an invalid signal-response record requires a basis")
        return self


class SignalResponsePODEnvelope(Contract):
    envelope_id: str = Field(min_length=1)
    material_condition_id: str = Field(min_length=1)
    inspection_procedure_id: str = Field(min_length=1)
    inspection_procedure_revision: str = Field(min_length=1)
    flaw_size_definition_id: str = Field(min_length=1)
    flaw_size_unit_token: str = Field(min_length=1)
    minimum_supported_flaw_size: Positive
    maximum_supported_flaw_size: Positive
    signal_definition_id: str = Field(min_length=1)
    signal_unit_token: str = Field(min_length=1)
    fixed_detection_threshold: float
    regression_form: Literal["normal_residual_signal_linear_in_natural_log_size"]
    provider_id: str = Field(min_length=1)
    provider_revision: str = Field(min_length=1)
    provider_state_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    provider_configuration_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    data_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    minimum_calibration_physical_specimen_count: int = Field(ge=3)
    minimum_holdout_physical_specimen_count: int = Field(ge=1)
    minimum_calibration_source_group_count: int = Field(ge=1)
    minimum_holdout_source_group_count: int = Field(ge=1)
    qualification_basis: str = Field(min_length=1)
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def ordered_support(self):
        if self.maximum_supported_flaw_size <= self.minimum_supported_flaw_size:
            raise ValueError("signal-response flaw-size support must have positive width")
        return self


class SignalResponsePODCalibration(Contract):
    calibration_id: str = Field(min_length=1)
    asset_id: str = Field(min_length=1)
    location_id: str = Field(min_length=1)
    physical_scope_id: str = Field(min_length=1)
    material_condition_id: str = Field(min_length=1)
    inspection_procedure_id: str = Field(min_length=1)
    inspection_procedure_revision: str = Field(min_length=1)
    observations: tuple[SignalResponseObservation, ...] = Field(min_length=4)
    qualification_envelope: SignalResponsePODEnvelope
    query_flaw_sizes: tuple[Positive, ...] = Field(min_length=1, max_length=100)
    target_probability_of_detection: float = Field(gt=0, lt=1)
    specimen_source_and_independence_partitions_reviewed: bool
    flaw_size_definition_and_units_reviewed: bool
    signal_definition_threshold_and_units_reviewed: bool
    censoring_missingness_and_weights_reviewed: bool
    support_range_reviewed: bool
    provider_lineage_configuration_and_digests_reviewed: bool
    calibration_holdout_design_reviewed: bool
    normal_residual_log_size_model_reviewed: bool
    qualification_envelope_authority_reviewed: bool
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def unique_partitioned_records(self):
        observation_ids = [row.observation_id for row in self.observations]
        if len(observation_ids) != len(set(observation_ids)):
            raise ValueError("signal-response observation identifiers must be unique")
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
                raise ValueError(f"signal-response {label} cannot cross calibration and holdout")
        return self


def signal_response_pod_calibration(x: SignalResponsePODCalibration) -> Calculation:
    from scipy.special import log_ndtr
    from scipy.stats import norm

    envelope = x.qualification_envelope
    missing_reviews = [
        name
        for name in (
            "specimen_source_and_independence_partitions_reviewed",
            "flaw_size_definition_and_units_reviewed",
            "signal_definition_threshold_and_units_reviewed",
            "censoring_missingness_and_weights_reviewed",
            "support_range_reviewed",
            "provider_lineage_configuration_and_digests_reviewed",
            "calibration_holdout_design_reviewed",
            "normal_residual_log_size_model_reviewed",
            "qualification_envelope_authority_reviewed",
        )
        if not getattr(x, name)
    ]
    identity_mismatch_fields = [
        name
        for name in (
            "material_condition_id",
            "inspection_procedure_id",
            "inspection_procedure_revision",
        )
        if getattr(x, name) != getattr(envelope, name)
    ]
    invalid_observation_ids = [row.observation_id for row in x.observations if not row.record_valid]
    incompatible_observation_ids = [
        row.observation_id
        for row in x.observations
        if row.flaw_size_definition_id != envelope.flaw_size_definition_id
        or row.flaw_size_unit_token != envelope.flaw_size_unit_token
        or row.signal_definition_id != envelope.signal_definition_id
        or row.signal_unit_token != envelope.signal_unit_token
        or row.provider_id != envelope.provider_id
        or row.provider_revision != envelope.provider_revision
        or row.provider_state_digest != envelope.provider_state_digest
    ]
    if missing_reviews or identity_mismatch_fields or invalid_observation_ids or incompatible_observation_ids:
        return Calculation(
            status="needs_data",
            values={
                "calibration_id": x.calibration_id,
                "missing_reviews": missing_reviews,
                "identity_mismatch_fields": identity_mismatch_fields,
                "invalid_observation_ids": invalid_observation_ids,
                "incompatible_observation_ids": incompatible_observation_ids,
            },
            notes=("Reviewed exact identities, units, partitions and provider lineage are required.",),
        )

    outside_support_observation_ids = [
        row.observation_id
        for row in x.observations
        if not envelope.minimum_supported_flaw_size
        <= row.flaw_size_value
        <= envelope.maximum_supported_flaw_size
    ]
    outside_support_query_sizes = [
        size
        for size in x.query_flaw_sizes
        if not envelope.minimum_supported_flaw_size <= size <= envelope.maximum_supported_flaw_size
    ]
    if outside_support_observation_ids or outside_support_query_sizes:
        return Calculation(
            status="out_of_scope",
            values={
                "calibration_id": x.calibration_id,
                "outside_support_observation_ids": outside_support_observation_ids,
                "outside_support_query_sizes": outside_support_query_sizes,
                "supported_flaw_size_range": [
                    envelope.minimum_supported_flaw_size,
                    envelope.maximum_supported_flaw_size,
                ],
            },
            notes=("The qualified flaw-size support is not extrapolated.",),
        )

    calibration_observed = [
        row
        for row in x.observations
        if row.partition == "calibration" and row.observation_status == "observed"
    ]
    holdout_observed = [
        row for row in x.observations if row.partition == "holdout" and row.observation_status == "observed"
    ]
    calibration_specimens = {row.physical_specimen_id for row in calibration_observed}
    holdout_specimens = {row.physical_specimen_id for row in holdout_observed}
    calibration_sources = {row.source_group_id for row in calibration_observed}
    holdout_sources = {row.source_group_id for row in holdout_observed}
    distinct_calibration_sizes = {row.flaw_size_value for row in calibration_observed}
    insufficient_design = (
        len(calibration_specimens) < envelope.minimum_calibration_physical_specimen_count
        or len(holdout_specimens) < envelope.minimum_holdout_physical_specimen_count
        or len(calibration_sources) < envelope.minimum_calibration_source_group_count
        or len(holdout_sources) < envelope.minimum_holdout_source_group_count
        or len(distinct_calibration_sizes) < 3
    )
    if insufficient_design:
        return Calculation(
            status="needs_data",
            values={
                "calibration_id": x.calibration_id,
                "calibration_observed_count": len(calibration_observed),
                "holdout_observed_count": len(holdout_observed),
                "calibration_physical_specimen_count": len(calibration_specimens),
                "holdout_physical_specimen_count": len(holdout_specimens),
                "calibration_source_group_count": len(calibration_sources),
                "holdout_source_group_count": len(holdout_sources),
                "distinct_calibration_size_count": len(distinct_calibration_sizes),
            },
            notes=("The reviewed calibration/holdout design does not support the declared regression.",),
        )

    log_size = np.log([row.flaw_size_value for row in calibration_observed])
    signal = np.asarray([row.reported_signal_value for row in calibration_observed], dtype=float)
    weight = np.asarray([row.nominal_weight for row in calibration_observed], dtype=float)
    design = np.column_stack((np.ones(len(log_size)), log_size))
    weighted_design = design * np.sqrt(weight)[:, None]
    weighted_signal = signal * np.sqrt(weight)
    beta, _, rank, singular_values = np.linalg.lstsq(weighted_design, weighted_signal, rcond=None)
    fitted = design @ beta
    residual = signal - fitted
    residual_variance = float(np.dot(weight, residual**2) / weight.sum())
    residual_standard_deviation = math.sqrt(residual_variance)
    condition_number = float(singular_values[0] / singular_values[-1])
    if (
        rank < 2
        or not np.isfinite(beta).all()
        or beta[1] <= 0
        or residual_standard_deviation <= 0
        or not math.isfinite(condition_number)
        or condition_number > 1e12
    ):
        return Calculation(
            status="needs_data",
            values={
                "calibration_id": x.calibration_id,
                "design_rank": int(rank),
                "slope_signal_per_natural_log_size": float(beta[1]),
                "residual_standard_deviation": residual_standard_deviation,
                "design_condition_number": condition_number,
            },
            notes=("A stable increasing normal-residual signal-response model was not identified.",),
        )

    threshold = envelope.fixed_detection_threshold

    def detection_probability(size):
        mean = float(beta[0] + beta[1] * math.log(size))
        return float(norm.cdf((mean - threshold) / residual_standard_deviation))

    pod_curve = [
        {"flaw_size_value": size, "probability_of_detection": detection_probability(size)}
        for size in x.query_flaw_sizes
    ]
    target_normal_quantile = float(norm.ppf(x.target_probability_of_detection))
    target_log_size = (threshold + residual_standard_deviation * target_normal_quantile - beta[0]) / beta[1]
    target_size_unbounded = math.exp(target_log_size)
    target_within_support = (
        envelope.minimum_supported_flaw_size <= target_size_unbounded <= envelope.maximum_supported_flaw_size
    )

    holdout_rows = []
    weighted_brier_sum = 0.0
    weighted_log_score_sum = 0.0
    weighted_squared_residual_sum = 0.0
    holdout_weight_sum = 0.0
    correct_weight = 0.0
    for row in holdout_observed:
        mean = float(beta[0] + beta[1] * math.log(row.flaw_size_value))
        probability = float(norm.cdf((mean - threshold) / residual_standard_deviation))
        detected = row.reported_signal_value >= threshold
        predicted_detected = probability >= 0.5
        standardized_residual = (row.reported_signal_value - mean) / residual_standard_deviation
        if detected:
            log_probability = float(log_ndtr((mean - threshold) / residual_standard_deviation))
        else:
            log_probability = float(log_ndtr((threshold - mean) / residual_standard_deviation))
        brier = (probability - float(detected)) ** 2
        weighted_brier_sum += row.nominal_weight * brier
        weighted_log_score_sum += row.nominal_weight * (-log_probability)
        weighted_squared_residual_sum += row.nominal_weight * standardized_residual**2
        holdout_weight_sum += row.nominal_weight
        correct_weight += row.nominal_weight * float(predicted_detected == detected)
        holdout_rows.append(
            {
                "observation_id": row.observation_id,
                "flaw_size_value": row.flaw_size_value,
                "observed_detection": detected,
                "predicted_detection": predicted_detected,
                "probability_of_detection": probability,
                "standardized_signal_residual": standardized_residual,
            }
        )
    censored_ids = [
        row.observation_id
        for row in x.observations
        if row.observation_status in {"left_censored", "right_censored"}
    ]
    missing_ids = [row.observation_id for row in x.observations if row.observation_status == "missing"]
    return Calculation(
        status="computed" if target_within_support else "out_of_scope",
        values={
            "calibration_id": x.calibration_id,
            "physical_scope_id": x.physical_scope_id,
            "envelope_id": envelope.envelope_id,
            "calibration_observed_count": len(calibration_observed),
            "holdout_observed_count": len(holdout_observed),
            "censored_observation_ids_excluded_from_fit_and_metrics": censored_ids,
            "missing_observation_ids_excluded_from_fit_and_metrics": missing_ids,
            "intercept_signal_at_log_size_zero": float(beta[0]),
            "slope_signal_per_natural_log_size": float(beta[1]),
            "residual_standard_deviation": residual_standard_deviation,
            "design_condition_number": condition_number,
            "fixed_detection_threshold": threshold,
            "pod_curve": pod_curve,
            "probability_of_detection": [row["probability_of_detection"] for row in pod_curve],
            "target_probability_of_detection": x.target_probability_of_detection,
            "target_flaw_size_within_support": (target_size_unbounded if target_within_support else None),
            "target_flaw_size_unbounded_diagnostic": target_size_unbounded,
            "target_flaw_size_within_declared_support": target_within_support,
            "holdout_rows": holdout_rows,
            "holdout_weighted_classification_accuracy": correct_weight / holdout_weight_sum,
            "holdout_weighted_mean_log_score": weighted_log_score_sum / holdout_weight_sum,
            "holdout_weighted_brier_score": weighted_brier_sum / holdout_weight_sum,
            "holdout_weighted_mean_squared_standardized_residual": (
                weighted_squared_residual_sum / holdout_weight_sum
            ),
        },
        notes=(
            "Censored and missing signals are retained by identity but are not silently substituted into the fit or holdout metrics.",
            "POD is a fitted conditional detection curve for the declared procedure and support, not independent validation, code acceptance or field probability.",
            "The target size is withheld when its mathematical estimate is outside the caller-qualified flaw-size support.",
        ),
    )


def specifications():
    def same_identity(x, context):
        if (x.asset_id, x.location_id) != (context.asset_id, context.location_id):
            raise ValueError("signal-response POD calibration asset and location must match the run context")

    return [
        ModelSpec(
            "inspection.signal_response_pod_calibration",
            SignalResponsePODCalibration,
            signal_response_pod_calibration,
            {
                "calibration_id": "1",
                "physical_scope_id": "1",
                "envelope_id": "1",
                "residual_standard_deviation": "signal unit",
                "fixed_detection_threshold": "signal unit",
                "pod_curve": "mixed",
                "probability_of_detection": "1",
                "target_probability_of_detection": "1",
                "target_flaw_size_within_support": "flaw-size unit",
                "holdout_weighted_classification_accuracy": "1",
                "holdout_weighted_mean_log_score": "1",
                "holdout_weighted_brier_score": "1",
                "holdout_weighted_mean_squared_standardized_residual": "1",
            },
            (
                "Signal is linear in natural-log flaw size with independent normal residuals and caller weights.",
                "A fixed caller-reviewed threshold defines detection; calibration and holdout groups do not overlap.",
                "Only uncensored observed signals enter weighted fitting and holdout metrics.",
            ),
            ("reviewed_signal_response_pod_qualification_envelope",),
            probability_semantics={"probability_of_detection": "detection_given_flaw_and_procedure"},
            context_validator=same_identity,
        )
    ]
