"""Hardness reference-block bias and repeatability calibration."""

from __future__ import annotations

import math
from typing import Literal

import numpy as np
from pydantic import Field, model_validator

from ..contracts import Calculation, Contract, Evidence, Nonnegative, Positive
from ..registry import ModelSpec


class HardnessReferenceObservation(Contract):
    observation_id: str = Field(min_length=1)
    physical_reference_block_id: str = Field(min_length=1)
    source_group_id: str = Field(min_length=1)
    independence_group_id: str = Field(min_length=1)
    partition: Literal["calibration", "holdout"]
    reference_block_condition_id: str = Field(min_length=1)
    method_id: str = Field(min_length=1)
    scale_id: str = Field(min_length=1)
    indenter_id: str = Field(min_length=1)
    applied_load_value: Positive
    applied_load_unit_token: str = Field(min_length=1)
    dwell_time_s: Positive
    instrument_id: str = Field(min_length=1)
    instrument_configuration_id: str = Field(min_length=1)
    instrument_configuration_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    specimen_temperature_K: Positive
    certified_hardness_value: float
    certified_standard_uncertainty: Nonnegative
    certificate_weight: Positive
    observed_hardness_value: float
    hardness_unit_token: str = Field(min_length=1)
    certificate_provider_id: str = Field(min_length=1)
    certificate_revision: str = Field(min_length=1)
    certificate_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    result_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    record_valid: bool
    invalid_basis: str | None = None
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def valid_record(self):
        if not self.record_valid and not self.invalid_basis:
            raise ValueError("an invalid hardness reference-block record requires a basis")
        return self


class HardnessReferenceBlockCalibration(Contract):
    calibration_id: str = Field(min_length=1)
    asset_id: str = Field(min_length=1)
    location_id: str = Field(min_length=1)
    physical_scope_id: str = Field(min_length=1)
    reference_block_condition_id: str = Field(min_length=1)
    method_id: str = Field(min_length=1)
    scale_id: str = Field(min_length=1)
    indenter_id: str = Field(min_length=1)
    applied_load_value: Positive
    applied_load_unit_token: str = Field(min_length=1)
    dwell_time_s: Positive
    dwell_time_tolerance_s: Nonnegative
    instrument_id: str = Field(min_length=1)
    instrument_configuration_id: str = Field(min_length=1)
    instrument_configuration_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    hardness_unit_token: str = Field(min_length=1)
    temperature_support_tolerance_K: Nonnegative
    observations: tuple[HardnessReferenceObservation, ...] = Field(min_length=8)
    minimum_calibration_record_count: int = Field(ge=6)
    minimum_calibration_physical_block_count: int = Field(ge=3)
    minimum_holdout_record_count: int = Field(ge=2)
    method_scale_indenter_load_and_dwell_reviewed: bool
    instrument_identity_configuration_and_digest_reviewed: bool
    reference_block_condition_and_temperature_reviewed: bool
    certificate_values_uncertainties_and_weights_reviewed: bool
    specimen_source_and_independence_partitions_reviewed: bool
    certificate_and_result_digests_reviewed: bool
    calibration_holdout_support_reviewed: bool
    bias_and_repeatability_model_reviewed: bool
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def unique_partitioned_records(self):
        observation_ids = [row.observation_id for row in self.observations]
        if len(observation_ids) != len(set(observation_ids)):
            raise ValueError("hardness reference observation identifiers must be unique")
        for attribute, label in (
            ("physical_reference_block_id", "physical reference block"),
            ("source_group_id", "source group"),
            ("independence_group_id", "independence group"),
        ):
            calibration = {
                getattr(row, attribute) for row in self.observations if row.partition == "calibration"
            }
            holdout = {getattr(row, attribute) for row in self.observations if row.partition == "holdout"}
            if calibration & holdout:
                raise ValueError(f"hardness {label} cannot cross calibration and holdout")
        return self


def _negative_log_likelihood(parameters, residual, certificate_uncertainty, weights):
    bias = float(parameters[0])
    repeatability = math.exp(float(parameters[1]))
    variance = repeatability**2 + certificate_uncertainty**2
    return float(
        np.dot(
            weights,
            0.5 * (residual - bias) ** 2 / variance + 0.5 * np.log(variance) + 0.5 * math.log(2 * math.pi),
        )
    )


def hardness_reference_block_calibration(x: HardnessReferenceBlockCalibration) -> Calculation:
    from scipy.optimize import minimize

    missing_reviews = [
        name
        for name in (
            "method_scale_indenter_load_and_dwell_reviewed",
            "instrument_identity_configuration_and_digest_reviewed",
            "reference_block_condition_and_temperature_reviewed",
            "certificate_values_uncertainties_and_weights_reviewed",
            "specimen_source_and_independence_partitions_reviewed",
            "certificate_and_result_digests_reviewed",
            "calibration_holdout_support_reviewed",
            "bias_and_repeatability_model_reviewed",
        )
        if not getattr(x, name)
    ]
    invalid_observation_ids = [row.observation_id for row in x.observations if not row.record_valid]
    incompatible_observation_ids = [
        row.observation_id
        for row in x.observations
        if row.reference_block_condition_id != x.reference_block_condition_id
        or row.method_id != x.method_id
        or row.scale_id != x.scale_id
        or row.indenter_id != x.indenter_id
        or row.applied_load_value != x.applied_load_value
        or row.applied_load_unit_token != x.applied_load_unit_token
        or abs(row.dwell_time_s - x.dwell_time_s) > x.dwell_time_tolerance_s
        or row.instrument_id != x.instrument_id
        or row.instrument_configuration_id != x.instrument_configuration_id
        or row.instrument_configuration_digest != x.instrument_configuration_digest
        or row.hardness_unit_token != x.hardness_unit_token
    ]
    if missing_reviews or invalid_observation_ids or incompatible_observation_ids:
        return Calculation(
            status="needs_data",
            values={
                "calibration_id": x.calibration_id,
                "missing_reviews": missing_reviews,
                "invalid_observation_ids": invalid_observation_ids,
                "incompatible_observation_ids": incompatible_observation_ids,
            },
            notes=(
                "Reviewed exact hardness configuration, certificates and partition records are required.",
            ),
        )

    calibration = [row for row in x.observations if row.partition == "calibration"]
    holdout = [row for row in x.observations if row.partition == "holdout"]
    calibration_blocks = {row.physical_reference_block_id for row in calibration}
    if (
        len(calibration) < x.minimum_calibration_record_count
        or len(calibration_blocks) < x.minimum_calibration_physical_block_count
        or len(holdout) < x.minimum_holdout_record_count
    ):
        return Calculation(
            status="needs_data",
            values={
                "calibration_id": x.calibration_id,
                "calibration_record_count": len(calibration),
                "calibration_physical_block_count": len(calibration_blocks),
                "holdout_record_count": len(holdout),
            },
            notes=(
                "The reviewed minimum calibration-block, calibration-record and holdout counts are unmet.",
            ),
        )

    residual = np.asarray(
        [row.observed_hardness_value - row.certified_hardness_value for row in calibration],
        dtype=float,
    )
    certificate_uncertainty = np.asarray(
        [row.certified_standard_uncertainty for row in calibration], dtype=float
    )
    weights = np.asarray([row.certificate_weight for row in calibration], dtype=float)
    initial_bias = float(np.average(residual, weights=weights))
    initial_repeatability = max(
        math.sqrt(float(np.average((residual - initial_bias) ** 2, weights=weights))), 1e-6
    )
    fitted = minimize(
        _negative_log_likelihood,
        [initial_bias, math.log(initial_repeatability)],
        args=(residual, certificate_uncertainty, weights),
        method="L-BFGS-B",
        bounds=[(None, None), (-20.0, 20.0)],
        options={"ftol": 1e-13, "gtol": 1e-9, "maxiter": 2000},
    )
    if not fitted.success or not np.isfinite(fitted.x).all():
        return Calculation(
            status="needs_data",
            values={"calibration_id": x.calibration_id},
            notes=("The certificate-aware bias and repeatability likelihood did not converge.",),
        )
    bias = float(fitted.x[0])
    repeatability = math.exp(float(fitted.x[1]))
    if repeatability <= math.exp(-19.99) or repeatability >= math.exp(19.99):
        return Calculation(
            status="needs_data",
            values={"calibration_id": x.calibration_id, "repeatability_standard_deviation": repeatability},
            notes=("The repeatability estimate reached a computational bound.",),
        )

    minimum_certified_value = min(row.certified_hardness_value for row in calibration)
    maximum_certified_value = max(row.certified_hardness_value for row in calibration)
    minimum_temperature_K = min(row.specimen_temperature_K for row in calibration)
    maximum_temperature_K = max(row.specimen_temperature_K for row in calibration)
    outside_support_holdout_ids = [
        row.observation_id
        for row in holdout
        if not minimum_certified_value <= row.certified_hardness_value <= maximum_certified_value
        or row.specimen_temperature_K < minimum_temperature_K - x.temperature_support_tolerance_K
        or row.specimen_temperature_K > maximum_temperature_K + x.temperature_support_tolerance_K
    ]
    holdout_rows = []
    weight_sum = 0.0
    weighted_error = 0.0
    weighted_squared_error = 0.0
    weighted_nll = 0.0
    for row in holdout:
        if row.observation_id in outside_support_holdout_ids:
            continue
        raw_residual = row.observed_hardness_value - row.certified_hardness_value
        bias_corrected_error = raw_residual - bias
        variance = repeatability**2 + row.certified_standard_uncertainty**2
        standardized_error = bias_corrected_error / math.sqrt(variance)
        log_likelihood = -0.5 * standardized_error**2 - 0.5 * math.log(variance) - 0.5 * math.log(2 * math.pi)
        weight_sum += row.certificate_weight
        weighted_error += row.certificate_weight * bias_corrected_error
        weighted_squared_error += row.certificate_weight * bias_corrected_error**2
        weighted_nll += row.certificate_weight * (-log_likelihood)
        holdout_rows.append(
            {
                "observation_id": row.observation_id,
                "physical_reference_block_id": row.physical_reference_block_id,
                "certified_hardness_value": row.certified_hardness_value,
                "observed_hardness_value": row.observed_hardness_value,
                "bias_corrected_hardness_value": row.observed_hardness_value - bias,
                "bias_corrected_error": bias_corrected_error,
                "standardized_error_including_certificate_uncertainty": standardized_error,
                "log_likelihood": log_likelihood,
            }
        )
    return Calculation(
        status="out_of_scope" if outside_support_holdout_ids else "computed",
        values={
            "calibration_id": x.calibration_id,
            "physical_scope_id": x.physical_scope_id,
            "method_id": x.method_id,
            "scale_id": x.scale_id,
            "instrument_configuration_id": x.instrument_configuration_id,
            "hardness_unit_token": x.hardness_unit_token,
            "estimated_bias_observed_minus_certified": bias,
            "repeatability_standard_deviation": repeatability,
            "weighted_calibration_negative_log_likelihood": float(fitted.fun),
            "calibration_record_count": len(calibration),
            "calibration_physical_block_count": len(calibration_blocks),
            "calibration_certified_hardness_range": [
                minimum_certified_value,
                maximum_certified_value,
            ],
            "calibration_temperature_range_K": [minimum_temperature_K, maximum_temperature_K],
            "outside_support_holdout_ids": outside_support_holdout_ids,
            "holdout_rows": holdout_rows,
            "holdout_weighted_bias_corrected_error": (weighted_error / weight_sum if weight_sum else None),
            "holdout_weighted_bias_corrected_rmse": (
                math.sqrt(weighted_squared_error / weight_sum) if weight_sum else None
            ),
            "holdout_weighted_mean_negative_log_likelihood": (
                weighted_nll / weight_sum if weight_sum else None
            ),
        },
        notes=(
            "Certificate standard uncertainty is combined with repeatability in the record likelihood; weights remain caller supplied.",
            "Holdout blocks outside the calibrated certified-value or temperature support are not extrapolated.",
            "No hardness-scale conversion, material-strength inference, acceptance or failure probability is produced.",
        ),
    )


def specifications():
    def same_identity(x, context):
        if (x.asset_id, x.location_id) != (context.asset_id, context.location_id):
            raise ValueError("hardness reference calibration asset and location must match the run context")

    return [
        ModelSpec(
            "inspection.hardness_reference_block_calibration",
            HardnessReferenceBlockCalibration,
            hardness_reference_block_calibration,
            {
                "calibration_id": "1",
                "physical_scope_id": "1",
                "method_id": "1",
                "scale_id": "1",
                "instrument_configuration_id": "1",
                "hardness_unit_token": "1",
                "estimated_bias_observed_minus_certified": "hardness unit",
                "repeatability_standard_deviation": "hardness unit",
                "calibration_certified_hardness_range": "hardness unit",
                "calibration_temperature_range_K": "K",
                "outside_support_holdout_ids": "1",
                "holdout_rows": "mixed",
                "holdout_weighted_bias_corrected_error": "hardness unit",
                "holdout_weighted_bias_corrected_rmse": "hardness unit",
                "holdout_weighted_mean_negative_log_likelihood": "1",
            },
            (
                "One exact method, scale, indenter, load, dwell and instrument configuration is calibrated.",
                "Reference certificate standard uncertainty and caller weight enter the likelihood explicitly.",
                "Calibration and holdout block, source and independence groups are disjoint.",
            ),
            ("authored_hardness_reference_block_bias_repeatability_calibration",),
            context_validator=same_identity,
        )
    ]
