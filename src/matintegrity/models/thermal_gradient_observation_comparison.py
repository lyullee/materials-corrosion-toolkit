"""Reviewed comparison of measured and externally predicted transient temperatures."""

from __future__ import annotations

import math
from typing import Literal

from pydantic import Field, model_validator

from ..contracts import Calculation, Contract, Evidence, Nonnegative, Positive
from ..registry import ModelSpec

Partition = Literal["calibration", "holdout"]


class ThermalHistorySensor(Contract):
    sensor_id: str = Field(min_length=1)
    position_m: Nonnegative
    expanded_position_uncertainty_m: Nonnegative
    clock_id: str = Field(min_length=1)
    calibration_id: str = Field(min_length=1)
    calibration_provider_id: str = Field(min_length=1)
    calibration_provider_revision: str = Field(min_length=1)
    calibration_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    calibration_valid: bool
    invalid_or_missing_basis: str | None = None
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def invalid_calibration_has_basis(self):
        if not self.calibration_valid and not self.invalid_or_missing_basis:
            raise ValueError("invalid thermal-history sensor calibrations require a basis")
        return self


class ThermalHistoryProvider(Contract):
    provider_id: str = Field(min_length=1)
    solver_id: str = Field(min_length=1)
    solver_revision: str = Field(min_length=1)
    geometry_id: str = Field(min_length=1)
    geometry_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    boundary_condition_id: str = Field(min_length=1)
    boundary_condition_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    material_property_state_id: str = Field(min_length=1)
    configuration_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    input_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    result_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    minimum_supported_time_s: Nonnegative
    maximum_supported_time_s: Positive
    minimum_supported_position_m: Nonnegative
    maximum_supported_position_m: Positive
    support_definition: str = Field(min_length=1)
    support_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def ordered_support(self):
        if self.maximum_supported_time_s <= self.minimum_supported_time_s:
            raise ValueError("provider time support bounds must be ordered")
        if self.maximum_supported_position_m <= self.minimum_supported_position_m:
            raise ValueError("provider position support bounds must be ordered")
        return self


class ThermalHistoryObservationPair(Contract):
    pair_id: str = Field(min_length=1)
    partition: Partition
    sequence_id: str = Field(min_length=1)
    physical_specimen_id: str = Field(min_length=1)
    source_group_id: str = Field(min_length=1)
    independence_group_id: str = Field(min_length=1)
    sensor_id: str = Field(min_length=1)
    observation_clock_id: str = Field(min_length=1)
    measured_elapsed_time_s: Nonnegative
    predicted_elapsed_time_s: Nonnegative
    predicted_sensor_position_m: Nonnegative
    measured_temperature_K: Positive
    expanded_measured_temperature_uncertainty_K: Nonnegative
    predicted_temperature_K: Positive
    expanded_predicted_temperature_uncertainty_K: Nonnegative
    sample_weight: Positive
    measured_history_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    predicted_history_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    pair_record_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    record_available: bool
    record_valid: bool
    invalid_or_missing_basis: str | None = None
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def invalid_or_missing_has_basis(self):
        if (not self.record_available or not self.record_valid) and not self.invalid_or_missing_basis:
            raise ValueError("missing or invalid thermal-history pairs require a basis")
        return self


class ThermalGradientObservationComparison(Contract):
    comparison_id: str = Field(min_length=1)
    asset_id: str = Field(min_length=1)
    location_id: str = Field(min_length=1)
    component_id: str = Field(min_length=1)
    campaign_id: str = Field(min_length=1)
    material_id: str = Field(min_length=1)
    material_state_id: str = Field(min_length=1)
    physical_scope_definition: str = Field(min_length=1)
    time_basis: str = Field(min_length=1)
    provider: ThermalHistoryProvider
    sensors: tuple[ThermalHistorySensor, ...] = Field(min_length=1)
    observation_pairs: tuple[ThermalHistoryObservationPair, ...] = Field(min_length=2)
    maximum_time_alignment_error_s: Nonnegative
    maximum_position_alignment_error_m: Nonnegative
    minimum_calibration_pair_count: int = Field(ge=1)
    minimum_holdout_pair_count: int = Field(ge=1)
    minimum_calibration_sequence_count: int = Field(ge=1)
    minimum_holdout_sequence_count: int = Field(ge=1)
    minimum_holdout_independence_group_count: int = Field(ge=1)
    specimen_material_state_and_scope_reviewed: bool
    geometry_boundary_solver_and_property_state_reviewed: bool
    sensor_position_clock_calibration_and_uncertainty_reviewed: bool
    measured_and_predicted_history_units_reviewed: bool
    time_and_sensor_alignment_reviewed: bool
    calibration_holdout_partition_and_independence_reviewed: bool
    provider_support_and_holdout_interpolation_reviewed: bool
    source_and_result_digests_reviewed: bool
    missing_and_invalid_records_reviewed: bool
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def linked_histories_and_partitions(self):
        sensor_ids = [row.sensor_id for row in self.sensors]
        pair_ids = [row.pair_id for row in self.observation_pairs]
        if len(set(sensor_ids)) != len(sensor_ids):
            raise ValueError("thermal-history sensor identifiers must be unique")
        if len(set(pair_ids)) != len(pair_ids):
            raise ValueError("thermal-history pair identifiers must be unique")
        sensors = {row.sensor_id: row for row in self.sensors}
        for row in self.observation_pairs:
            sensor = sensors.get(row.sensor_id)
            if sensor is None:
                raise ValueError("every thermal-history pair must reference a declared sensor")
            if row.observation_clock_id != sensor.clock_id:
                raise ValueError("thermal-history pair and sensor clocks must match")
        for attribute, label in (
            ("sequence_id", "physical sequence"),
            ("physical_specimen_id", "physical specimen"),
            ("source_group_id", "source group"),
            ("independence_group_id", "independence group"),
        ):
            partitions_by_id: dict[str, set[str]] = {}
            for row in self.observation_pairs:
                partitions_by_id.setdefault(getattr(row, attribute), set()).add(row.partition)
            if any(len(partitions) > 1 for partitions in partitions_by_id.values()):
                raise ValueError(f"{label} identifiers cannot cross calibration and holdout")
        grouped_times: dict[tuple[str, str], list[float]] = {}
        for row in self.observation_pairs:
            grouped_times.setdefault((row.sequence_id, row.sensor_id), []).append(row.measured_elapsed_time_s)
        for times in grouped_times.values():
            if any(right <= left for left, right in zip(times, times[1:], strict=False)):
                raise ValueError("measured history times must strictly increase within each sensor sequence")
        return self


def _partition_metrics(rows):
    weight_sum = math.fsum(row.sample_weight for row in rows)
    residuals = [row.measured_temperature_K - row.predicted_temperature_K for row in rows]
    weighted_bias = (
        math.fsum(row.sample_weight * residual for row, residual in zip(rows, residuals, strict=True))
        / weight_sum
    )
    weighted_rmse = math.sqrt(
        math.fsum(row.sample_weight * residual**2 for row, residual in zip(rows, residuals, strict=True))
        / weight_sum
    )
    weighted_mae = (
        math.fsum(row.sample_weight * abs(residual) for row, residual in zip(rows, residuals, strict=True))
        / weight_sum
    )
    return {
        "pair_count": len(rows),
        "weight_sum": weight_sum,
        "weighted_bias_K": weighted_bias,
        "weighted_rmse_K": weighted_rmse,
        "weighted_mae_K": weighted_mae,
    }


def thermal_gradient_observation_comparison(x: ThermalGradientObservationComparison) -> Calculation:
    missing_reviews = [
        name
        for name in (
            "specimen_material_state_and_scope_reviewed",
            "geometry_boundary_solver_and_property_state_reviewed",
            "sensor_position_clock_calibration_and_uncertainty_reviewed",
            "measured_and_predicted_history_units_reviewed",
            "time_and_sensor_alignment_reviewed",
            "calibration_holdout_partition_and_independence_reviewed",
            "provider_support_and_holdout_interpolation_reviewed",
            "source_and_result_digests_reviewed",
            "missing_and_invalid_records_reviewed",
        )
        if not getattr(x, name)
    ]
    sensors = {row.sensor_id: row for row in x.sensors}
    invalid_sensor_ids = [row.sensor_id for row in x.sensors if not row.calibration_valid]
    invalid_pair_ids = [
        row.pair_id for row in x.observation_pairs if not row.record_available or not row.record_valid
    ]
    time_misaligned_pair_ids = [
        row.pair_id
        for row in x.observation_pairs
        if abs(row.measured_elapsed_time_s - row.predicted_elapsed_time_s) > x.maximum_time_alignment_error_s
    ]
    position_misaligned_pair_ids = [
        row.pair_id
        for row in x.observation_pairs
        if abs(sensors[row.sensor_id].position_m - row.predicted_sensor_position_m)
        > x.maximum_position_alignment_error_m
    ]
    calibration = [row for row in x.observation_pairs if row.partition == "calibration"]
    holdout = [row for row in x.observation_pairs if row.partition == "holdout"]
    minimum_counts_met = (
        len(calibration) >= x.minimum_calibration_pair_count
        and len(holdout) >= x.minimum_holdout_pair_count
        and len({row.sequence_id for row in calibration}) >= x.minimum_calibration_sequence_count
        and len({row.sequence_id for row in holdout}) >= x.minimum_holdout_sequence_count
        and len({row.independence_group_id for row in holdout}) >= x.minimum_holdout_independence_group_count
    )
    if (
        missing_reviews
        or invalid_sensor_ids
        or invalid_pair_ids
        or time_misaligned_pair_ids
        or position_misaligned_pair_ids
        or not minimum_counts_met
    ):
        return Calculation(
            status="needs_data",
            values={
                "comparison_id": x.comparison_id,
                "missing_reviews": missing_reviews,
                "invalid_sensor_ids": invalid_sensor_ids,
                "invalid_pair_ids": invalid_pair_ids,
                "time_misaligned_pair_ids": time_misaligned_pair_ids,
                "position_misaligned_pair_ids": position_misaligned_pair_ids,
                "minimum_counts_met": minimum_counts_met,
            },
            notes=("Reviewed, valid and aligned measured/predicted temperature pairs are required.",),
        )

    provider = x.provider
    outside_provider_support_ids = [
        row.pair_id
        for row in x.observation_pairs
        if not provider.minimum_supported_time_s
        <= row.predicted_elapsed_time_s
        <= provider.maximum_supported_time_s
        or not provider.minimum_supported_position_m
        <= row.predicted_sensor_position_m
        <= provider.maximum_supported_position_m
    ]
    calibration_time_support = [
        min(row.measured_elapsed_time_s for row in calibration),
        max(row.measured_elapsed_time_s for row in calibration),
    ]
    calibration_position_support = [
        min(sensors[row.sensor_id].position_m for row in calibration),
        max(sensors[row.sensor_id].position_m for row in calibration),
    ]
    holdout_outside_calibration_support_ids = [
        row.pair_id
        for row in holdout
        if not calibration_time_support[0] <= row.measured_elapsed_time_s <= calibration_time_support[1]
        or not calibration_position_support[0]
        <= sensors[row.sensor_id].position_m
        <= calibration_position_support[1]
    ]
    if outside_provider_support_ids or holdout_outside_calibration_support_ids:
        return Calculation(
            status="out_of_scope",
            values={
                "comparison_id": x.comparison_id,
                "outside_provider_support_pair_ids": outside_provider_support_ids,
                "holdout_outside_calibration_support_pair_ids": (holdout_outside_calibration_support_ids),
                "calibration_time_support_s": calibration_time_support,
                "calibration_sensor_position_support_m": calibration_position_support,
                "residual_rows": [],
                "calibration_metrics": None,
                "holdout_metrics": None,
            },
            notes=(
                "No residual metric is emitted when a pair is outside provider support or a holdout pair requires extrapolation beyond calibration observations.",
            ),
        )

    residual_rows = [
        {
            "pair_id": row.pair_id,
            "partition": row.partition,
            "sequence_id": row.sequence_id,
            "sensor_id": row.sensor_id,
            "elapsed_time_s": row.measured_elapsed_time_s,
            "sensor_position_m": sensors[row.sensor_id].position_m,
            "measured_temperature_K": row.measured_temperature_K,
            "predicted_temperature_K": row.predicted_temperature_K,
            "weighted_residual_K": row.sample_weight
            * (row.measured_temperature_K - row.predicted_temperature_K),
            "residual_K": row.measured_temperature_K - row.predicted_temperature_K,
            "sample_weight": row.sample_weight,
            "expanded_measured_temperature_uncertainty_K": (row.expanded_measured_temperature_uncertainty_K),
            "expanded_predicted_temperature_uncertainty_K": (
                row.expanded_predicted_temperature_uncertainty_K
            ),
            "measured_history_digest": row.measured_history_digest,
            "predicted_history_digest": row.predicted_history_digest,
            "pair_record_digest": row.pair_record_digest,
        }
        for row in x.observation_pairs
    ]
    return Calculation(
        status="computed",
        values={
            "comparison_id": x.comparison_id,
            "component_id": x.component_id,
            "material_id": x.material_id,
            "material_state_id": x.material_state_id,
            "provider_id": provider.provider_id,
            "solver_id": provider.solver_id,
            "calibration_metrics": _partition_metrics(calibration),
            "holdout_metrics": _partition_metrics(holdout),
            "residual_rows": residual_rows,
            "calibration_time_support_s": calibration_time_support,
            "calibration_sensor_position_support_m": calibration_position_support,
            "outside_provider_support_pair_ids": [],
            "holdout_outside_calibration_support_pair_ids": [],
            "missing_reviews": [],
        },
        notes=(
            "Residuals compare aligned caller measurements with already-computed external solver histories.",
            "Calibration and holdout metrics are descriptive weighted diagnostics and do not fit or alter the solver.",
            "No PDE, thermal stress, acceptance, life or probability is calculated.",
        ),
    )


def specifications():
    def same_identity(x, context):
        if (x.asset_id, x.location_id, x.time_basis) != (
            context.asset_id,
            context.location_id,
            context.time_basis,
        ):
            raise ValueError("thermal-history comparison identity and clock must match run context")

    return [
        ModelSpec(
            "structural.thermal_gradient_observation_comparison",
            ThermalGradientObservationComparison,
            thermal_gradient_observation_comparison,
            {
                "comparison_id": "1",
                "component_id": "1",
                "material_id": "1",
                "material_state_id": "1",
                "provider_id": "1",
                "solver_id": "1",
                "calibration_metrics": "mixed",
                "holdout_metrics": "mixed",
                "residual_rows": "mixed",
                "calibration_time_support_s": "s",
                "calibration_sensor_position_support_m": "m",
                "outside_provider_support_pair_ids": "1",
                "holdout_outside_calibration_support_pair_ids": "1",
                "missing_reviews": "1",
            },
            (
                "Measured and predicted histories are paired by reviewed clock and sensor identities.",
                "Calibration and holdout physical sequence, specimen, source and independence groups are disjoint.",
                "Residuals are limited to provider and calibration-observation support.",
            ),
            ("authored_transient_temperature_observation_comparison",),
            context_validator=same_identity,
        )
    ]
