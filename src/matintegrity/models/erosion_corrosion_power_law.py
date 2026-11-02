"""Partitioned erosion-corrosion power-law calibration on measured loss rates."""

from __future__ import annotations

import math
from typing import Literal

import numpy as np
from pydantic import Field, model_validator

from ..contracts import Calculation, Contract, Evidence, Positive
from ..registry import ModelSpec


class ErosionCorrosionPowerLawObservation(Contract):
    observation_id: str = Field(min_length=1)
    physical_specimen_id: str = Field(min_length=1)
    source_group_id: str = Field(min_length=1)
    independence_group_id: str = Field(min_length=1)
    partition: Literal["calibration", "holdout"]
    material_condition_id: str = Field(min_length=1)
    fluid_condition_id: str = Field(min_length=1)
    geometry_condition_id: str = Field(min_length=1)
    mechanism_scope_id: str = Field(min_length=1)
    velocity_value: Positive
    velocity_unit_token: str = Field(min_length=1)
    particle_concentration_value: Positive
    particle_concentration_unit_token: str = Field(min_length=1)
    measured_loss_rate_value: Positive
    loss_rate_unit_token: str = Field(min_length=1)
    nominal_weight: Positive = 1.0
    provider_id: str = Field(min_length=1)
    provider_revision: str = Field(min_length=1)
    provider_state_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    input_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    result_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    record_valid: bool
    invalid_basis: str | None = None
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def valid_record(self):
        if not self.record_valid and not self.invalid_basis:
            raise ValueError("an invalid erosion-corrosion observation requires a basis")
        return self


class ErosionCorrosionPowerLawCalibration(Contract):
    calibration_id: str = Field(min_length=1)
    asset_id: str = Field(min_length=1)
    location_id: str = Field(min_length=1)
    physical_scope_id: str = Field(min_length=1)
    material_condition_id: str = Field(min_length=1)
    fluid_condition_id: str = Field(min_length=1)
    geometry_condition_id: str = Field(min_length=1)
    mechanism_scope_id: str = Field(min_length=1)
    regression_form: Literal["log_loss_rate_intercept_plus_log_velocity_plus_log_particle_concentration"]
    velocity_unit_token: str = Field(min_length=1)
    particle_concentration_unit_token: str = Field(min_length=1)
    loss_rate_unit_token: str = Field(min_length=1)
    reference_velocity_value: Positive
    reference_particle_concentration_value: Positive
    observations: tuple[ErosionCorrosionPowerLawObservation, ...] = Field(min_length=8)
    provider_id: str = Field(min_length=1)
    provider_revision: str = Field(min_length=1)
    provider_state_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    provider_configuration_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    calibration_dataset_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    holdout_dataset_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    minimum_calibration_record_count: int = Field(ge=6)
    minimum_holdout_record_count: int = Field(ge=2)
    material_fluid_geometry_and_mechanism_scope_reviewed: bool
    specimen_source_and_independence_partitions_reviewed: bool
    velocity_particle_and_loss_rate_units_reviewed: bool
    weights_and_positive_measurements_reviewed: bool
    calibration_support_hull_reviewed: bool
    provider_lineage_and_digests_reviewed: bool
    regression_form_and_minimum_counts_reviewed: bool
    common_power_law_regime_reviewed: bool
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def unique_partitioned_records(self):
        observation_ids = [row.observation_id for row in self.observations]
        if len(observation_ids) != len(set(observation_ids)):
            raise ValueError("erosion-corrosion observation identifiers must be unique")
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
                raise ValueError(f"erosion-corrosion {label} cannot cross calibration and holdout")
        return self


def erosion_corrosion_power_law_calibration(
    x: ErosionCorrosionPowerLawCalibration,
) -> Calculation:
    from scipy.spatial import ConvexHull

    missing_reviews = [
        name
        for name in (
            "material_fluid_geometry_and_mechanism_scope_reviewed",
            "specimen_source_and_independence_partitions_reviewed",
            "velocity_particle_and_loss_rate_units_reviewed",
            "weights_and_positive_measurements_reviewed",
            "calibration_support_hull_reviewed",
            "provider_lineage_and_digests_reviewed",
            "regression_form_and_minimum_counts_reviewed",
            "common_power_law_regime_reviewed",
        )
        if not getattr(x, name)
    ]
    invalid_observation_ids = [row.observation_id for row in x.observations if not row.record_valid]
    identity_or_unit_mismatch_ids = [
        row.observation_id
        for row in x.observations
        if row.material_condition_id != x.material_condition_id
        or row.fluid_condition_id != x.fluid_condition_id
        or row.geometry_condition_id != x.geometry_condition_id
        or row.mechanism_scope_id != x.mechanism_scope_id
        or row.velocity_unit_token != x.velocity_unit_token
        or row.particle_concentration_unit_token != x.particle_concentration_unit_token
        or row.loss_rate_unit_token != x.loss_rate_unit_token
        or row.provider_id != x.provider_id
        or row.provider_revision != x.provider_revision
        or row.provider_state_digest != x.provider_state_digest
    ]
    if missing_reviews or invalid_observation_ids or identity_or_unit_mismatch_ids:
        return Calculation(
            status="needs_data",
            values={
                "calibration_id": x.calibration_id,
                "missing_reviews": missing_reviews,
                "invalid_observation_ids": invalid_observation_ids,
                "identity_or_unit_mismatch_ids": identity_or_unit_mismatch_ids,
            },
            notes=("Reviewed exact scope, units, partitions and provider lineage are required.",),
        )

    calibration = [row for row in x.observations if row.partition == "calibration"]
    holdout = [row for row in x.observations if row.partition == "holdout"]
    if len(calibration) < x.minimum_calibration_record_count or len(holdout) < x.minimum_holdout_record_count:
        return Calculation(
            status="needs_data",
            values={
                "calibration_id": x.calibration_id,
                "calibration_record_count": len(calibration),
                "holdout_record_count": len(holdout),
            },
            notes=("The reviewed minimum calibration and holdout counts are not satisfied.",),
        )

    def features(rows):
        return np.column_stack(
            (
                [math.log(row.velocity_value / x.reference_velocity_value) for row in rows],
                [
                    math.log(row.particle_concentration_value / x.reference_particle_concentration_value)
                    for row in rows
                ],
            )
        )

    calibration_features = features(calibration)
    center = calibration_features.mean(axis=0)
    scale = np.ptp(calibration_features, axis=0)
    if np.any(scale <= np.finfo(float).tiny):
        return Calculation(
            status="needs_data",
            values={"calibration_id": x.calibration_id, "feature_range": scale.tolist()},
            notes=("Multiple velocity and particle-concentration levels are required.",),
        )
    normalized = (calibration_features - center) / scale
    design = np.column_stack((np.ones(len(calibration)), normalized))
    condition_number = float(np.linalg.cond(design))
    if np.linalg.matrix_rank(design) < 3 or not math.isfinite(condition_number) or condition_number > 1e8:
        return Calculation(
            status="needs_data",
            values={"calibration_id": x.calibration_id, "design_condition_number": condition_number},
            notes=("Velocity and particle-concentration effects are not separately identifiable.",),
        )
    log_rate = np.log([row.measured_loss_rate_value for row in calibration])
    weights = np.asarray([row.nominal_weight for row in calibration], dtype=float)
    weighted_design = design * np.sqrt(weights)[:, None]
    weighted_response = log_rate * np.sqrt(weights)
    gamma, _, rank, _ = np.linalg.lstsq(weighted_design, weighted_response, rcond=None)
    if rank < 3 or gamma[1] <= 0 or gamma[2] <= 0:
        return Calculation(
            status="needs_data",
            values={
                "calibration_id": x.calibration_id,
                "normalized_velocity_exponent": float(gamma[1]),
                "normalized_particle_exponent": float(gamma[2]),
            },
            notes=("Positive identifiable velocity and particle exponents were not obtained.",),
        )
    fitted = design @ gamma
    residual = log_rate - fitted
    sigma = math.sqrt(float(np.dot(weights, residual**2) / weights.sum()))
    if sigma <= 0 or not math.isfinite(sigma):
        return Calculation(
            status="needs_data",
            values={"calibration_id": x.calibration_id, "log_loss_rate_sigma": sigma},
            notes=("Positive finite log-loss-rate scatter is required.",),
        )
    velocity_exponent = float(gamma[1] / scale[0])
    particle_exponent = float(gamma[2] / scale[1])
    log_reference_rate = float(gamma[0] - velocity_exponent * center[0] - particle_exponent * center[1])
    calibration_nll = float(
        np.dot(
            weights,
            0.5 * (residual / sigma) ** 2 + math.log(sigma) + 0.5 * math.log(2 * math.pi) + log_rate,
        )
    )

    hull = ConvexHull(normalized)
    holdout_features = features(holdout)
    normalized_holdout = (holdout_features - center) / scale
    inside = np.all(
        normalized_holdout @ hull.equations[:, :-1].T + hull.equations[:, -1] <= 1e-10,
        axis=1,
    )
    outside_holdout_ids = [
        row.observation_id for row, valid in zip(holdout, inside, strict=True) if not valid
    ]
    holdout_rows = []
    weight_sum = 0.0
    weighted_bias = 0.0
    weighted_squared_error = 0.0
    weighted_nll = 0.0
    for row, feature, valid in zip(holdout, holdout_features, inside, strict=True):
        if not valid:
            continue
        predicted_log_rate = float(
            log_reference_rate + velocity_exponent * feature[0] + particle_exponent * feature[1]
        )
        observed_log_rate = math.log(row.measured_loss_rate_value)
        error = observed_log_rate - predicted_log_rate
        log_likelihood_rate = (
            -0.5 * (error / sigma) ** 2 - math.log(sigma) - 0.5 * math.log(2 * math.pi) - observed_log_rate
        )
        weight_sum += row.nominal_weight
        weighted_bias += row.nominal_weight * error
        weighted_squared_error += row.nominal_weight * error**2
        weighted_nll += row.nominal_weight * (-log_likelihood_rate)
        holdout_rows.append(
            {
                "observation_id": row.observation_id,
                "inside_calibration_support_hull": True,
                "predicted_log_loss_rate": predicted_log_rate,
                "observed_log_loss_rate": observed_log_rate,
                "log_residual": error,
                "log_likelihood_loss_rate": log_likelihood_rate,
            }
        )
    return Calculation(
        status="out_of_scope" if outside_holdout_ids else "computed",
        values={
            "calibration_id": x.calibration_id,
            "physical_scope_id": x.physical_scope_id,
            "regression_form": x.regression_form,
            "reference_velocity_value": x.reference_velocity_value,
            "reference_particle_concentration_value": x.reference_particle_concentration_value,
            "log_reference_loss_rate": log_reference_rate,
            "velocity_exponent": velocity_exponent,
            "particle_concentration_exponent": particle_exponent,
            "log_loss_rate_sigma": sigma,
            "design_condition_number": condition_number,
            "weighted_calibration_negative_log_likelihood_loss_rate": calibration_nll,
            "calibration_record_count": len(calibration),
            "holdout_record_count": len(holdout),
            "calibration_velocity_range": [
                min(row.velocity_value for row in calibration),
                max(row.velocity_value for row in calibration),
            ],
            "calibration_particle_concentration_range": [
                min(row.particle_concentration_value for row in calibration),
                max(row.particle_concentration_value for row in calibration),
            ],
            "outside_support_holdout_ids": outside_holdout_ids,
            "holdout_rows": holdout_rows,
            "holdout_weighted_log_bias": weighted_bias / weight_sum if weight_sum else None,
            "holdout_weighted_log_rmse": (
                math.sqrt(weighted_squared_error / weight_sum) if weight_sum else None
            ),
            "holdout_weighted_mean_negative_log_likelihood_loss_rate": (
                weighted_nll / weight_sum if weight_sum else None
            ),
        },
        notes=(
            "The calibration describes combined measured loss rate in one reviewed regime; it does not separate pure erosion from corrosion.",
            "Holdout conditions outside the calibration convex hull in log velocity and log particle concentration are not extrapolated.",
            "No regime transition, service forecast, acceptance or probability is produced.",
        ),
    )


def specifications():
    def same_identity(x, context):
        if (x.asset_id, x.location_id) != (context.asset_id, context.location_id):
            raise ValueError(
                "erosion-corrosion power-law calibration asset and location must match the run context"
            )

    return [
        ModelSpec(
            "degradation.erosion_corrosion_power_law_calibration",
            ErosionCorrosionPowerLawCalibration,
            erosion_corrosion_power_law_calibration,
            {
                "calibration_id": "1",
                "physical_scope_id": "1",
                "reference_velocity_value": "velocity unit",
                "reference_particle_concentration_value": "particle-concentration unit",
                "log_reference_loss_rate": "ln(loss-rate unit)",
                "velocity_exponent": "1",
                "particle_concentration_exponent": "1",
                "log_loss_rate_sigma": "1",
                "calibration_velocity_range": "velocity unit",
                "calibration_particle_concentration_range": "particle-concentration unit",
                "outside_support_holdout_ids": "1",
                "holdout_rows": "mixed",
                "holdout_weighted_log_bias": "1",
                "holdout_weighted_log_rmse": "1",
                "holdout_weighted_mean_negative_log_likelihood_loss_rate": "1",
            },
            (
                "Log measured loss rate is linear in log velocity and log particle concentration in one reviewed regime.",
                "Calibration and holdout specimen, source and independence groups are disjoint.",
                "Units and material, fluid, geometry and mechanism-scope identities are exact caller tokens.",
            ),
            ("authored_weighted_erosion_corrosion_power_law_calibration",),
            context_validator=same_identity,
        )
    ]
