"""One-parameter calibration of reviewed transient-temperature response rows."""

from __future__ import annotations

import math
from typing import Literal

from pydantic import Field, model_validator

from ..contracts import Calculation, Contract, Evidence, Nonnegative, Positive
from ..registry import ModelSpec

Partition = Literal["calibration", "holdout"]


class ThermalCalibrationParameter(Contract):
    parameter_id: str = Field(min_length=1)
    parameter_kind: Literal["thermal_property_multiplier", "thermal_diffusivity"]
    parameter_definition: str = Field(min_length=1)
    unit_token: Literal["1", "m^2/s"]
    reference_value: Positive
    minimum_supported_value: Positive
    maximum_supported_value: Positive
    support_basis: str = Field(min_length=1)
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def coherent_kind_and_support(self):
        expected_unit = "1" if self.parameter_kind == "thermal_property_multiplier" else "m^2/s"
        if self.unit_token != expected_unit:
            raise ValueError("thermal calibration parameter kind and unit must agree")
        if self.maximum_supported_value <= self.minimum_supported_value:
            raise ValueError("thermal parameter support bounds must be ordered")
        if not self.minimum_supported_value <= self.reference_value <= self.maximum_supported_value:
            raise ValueError("thermal parameter reference value must lie within support")
        return self


class ThermalSensorIdentity(Contract):
    sensor_id: str = Field(min_length=1)
    position_m: Nonnegative
    expanded_position_uncertainty_m: Nonnegative
    clock_id: str = Field(min_length=1)
    sensor_calibration_id: str = Field(min_length=1)
    sensor_calibration_provider_id: str = Field(min_length=1)
    sensor_calibration_provider_revision: str = Field(min_length=1)
    sensor_calibration_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    calibration_valid: bool
    invalid_or_missing_basis: str | None = None
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def invalid_calibration_has_basis(self):
        if not self.calibration_valid and not self.invalid_or_missing_basis:
            raise ValueError("invalid thermal-sensor calibrations require a basis")
        return self


class ThermalResponseProviderIdentity(Contract):
    response_basis: Literal["external_provider_sensitivity", "declared_analytical_sensitivity"]
    provider_id: str = Field(min_length=1)
    solver_or_response_id: str = Field(min_length=1)
    provider_revision: str = Field(min_length=1)
    geometry_id: str = Field(min_length=1)
    geometry_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    boundary_condition_id: str = Field(min_length=1)
    boundary_condition_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    provider_configuration_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    provider_state_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    analytical_response_definition: str | None = None
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def analytical_basis_is_explicit(self):
        if self.response_basis == "declared_analytical_sensitivity":
            if not self.analytical_response_definition:
                raise ValueError("analytical thermal responses require an exact response definition")
        elif self.analytical_response_definition is not None:
            raise ValueError("external provider responses cannot declare an analytical response definition")
        return self


class TransientTemperatureResponse(Contract):
    observation_id: str = Field(min_length=1)
    partition: Partition
    sequence_id: str = Field(min_length=1)
    physical_specimen_id: str = Field(min_length=1)
    source_group_id: str = Field(min_length=1)
    independence_group_id: str = Field(min_length=1)
    sensor_id: str = Field(min_length=1)
    observation_clock_id: str = Field(min_length=1)
    observed_elapsed_time_s: Nonnegative
    provider_elapsed_time_s: Nonnegative
    provider_sensor_position_m: Nonnegative
    observed_temperature_K: Positive
    expanded_observed_temperature_uncertainty_K: Nonnegative
    baseline_predicted_temperature_K: Positive
    expanded_baseline_prediction_uncertainty_K: Nonnegative
    predicted_temperature_sensitivity_K_per_parameter_unit: float
    sample_weight: Positive
    sequence_record_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    provider_response_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    observation_record_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    record_available: bool
    record_valid: bool
    invalid_or_missing_basis: str | None = None
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def missing_or_invalid_has_basis(self):
        if (not self.record_available or not self.record_valid) and not self.invalid_or_missing_basis:
            raise ValueError("missing or invalid temperature-response rows require a basis")
        return self


class ThermalGradientParameterCalibration(Contract):
    calibration_id: str = Field(min_length=1)
    asset_id: str = Field(min_length=1)
    location_id: str = Field(min_length=1)
    component_id: str = Field(min_length=1)
    experiment_or_campaign_id: str = Field(min_length=1)
    specimen_material_id: str = Field(min_length=1)
    specimen_material_state_id: str = Field(min_length=1)
    physical_scope_definition: str = Field(min_length=1)
    time_basis: str = Field(min_length=1)
    provider: ThermalResponseProviderIdentity
    parameter: ThermalCalibrationParameter
    sensors: tuple[ThermalSensorIdentity, ...] = Field(min_length=1)
    observations: tuple[TransientTemperatureResponse, ...] = Field(min_length=3)
    maximum_time_alignment_error_s: Nonnegative
    maximum_sensor_position_alignment_error_m: Nonnegative
    minimum_calibration_observation_count: int = Field(ge=1)
    minimum_holdout_observation_count: int = Field(ge=1)
    minimum_calibration_sequence_count: int = Field(ge=1)
    minimum_holdout_sequence_count: int = Field(ge=1)
    minimum_holdout_independence_group_count: int = Field(ge=1)
    minimum_weighted_sensitivity_information: Positive
    specimen_material_state_and_scope_reviewed: bool
    geometry_boundary_and_provider_identity_reviewed: bool
    sensor_positions_clocks_calibrations_and_uncertainty_reviewed: bool
    parameter_definition_units_and_support_reviewed: bool
    source_specimen_independence_partitions_reviewed: bool
    observation_provider_alignment_reviewed: bool
    provider_response_and_record_digests_reviewed: bool
    missing_invalid_and_support_gates_reviewed: bool
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def identities_partitions_and_histories_are_aligned(self):
        sensor_ids = [row.sensor_id for row in self.sensors]
        if len(set(sensor_ids)) != len(sensor_ids):
            raise ValueError("thermal sensor identifiers must be unique")
        observation_ids = [row.observation_id for row in self.observations]
        if len(set(observation_ids)) != len(observation_ids):
            raise ValueError("temperature-response observation identifiers must be unique")
        sensors = {row.sensor_id: row for row in self.sensors}
        for row in self.observations:
            sensor = sensors.get(row.sensor_id)
            if sensor is None:
                raise ValueError("every temperature-response row must reference a declared sensor")
            if row.observation_clock_id != sensor.clock_id:
                raise ValueError("temperature-response and sensor clock identities must match")
        sequence_partitions: dict[str, set[str]] = {}
        for row in self.observations:
            sequence_partitions.setdefault(row.sequence_id, set()).add(row.partition)
        if any(len(partitions) > 1 for partitions in sequence_partitions.values()):
            raise ValueError("physical temperature sequences cannot cross calibration and holdout")
        for attribute, label in (
            ("physical_specimen_id", "physical specimen"),
            ("source_group_id", "source group"),
            ("independence_group_id", "independence group"),
        ):
            partitions_by_id: dict[str, set[str]] = {}
            for row in self.observations:
                partitions_by_id.setdefault(getattr(row, attribute), set()).add(row.partition)
            if any(len(partitions) > 1 for partitions in partitions_by_id.values()):
                raise ValueError(f"{label} identifiers cannot cross calibration and holdout")
        grouped_times: dict[tuple[str, str], list[float]] = {}
        for row in self.observations:
            grouped_times.setdefault((row.sequence_id, row.sensor_id), []).append(row.observed_elapsed_time_s)
        for times in grouped_times.values():
            if any(right <= left for left, right in zip(times, times[1:], strict=False)):
                raise ValueError(
                    "temperature history times must strictly increase within each sensor sequence"
                )
        return self


def thermal_gradient_parameter_calibration(x: ThermalGradientParameterCalibration) -> Calculation:
    missing_reviews = [
        name
        for name in (
            "specimen_material_state_and_scope_reviewed",
            "geometry_boundary_and_provider_identity_reviewed",
            "sensor_positions_clocks_calibrations_and_uncertainty_reviewed",
            "parameter_definition_units_and_support_reviewed",
            "source_specimen_independence_partitions_reviewed",
            "observation_provider_alignment_reviewed",
            "provider_response_and_record_digests_reviewed",
            "missing_invalid_and_support_gates_reviewed",
        )
        if not getattr(x, name)
    ]
    sensors = {row.sensor_id: row for row in x.sensors}
    invalid_sensor_ids = [row.sensor_id for row in x.sensors if not row.calibration_valid]
    invalid_observation_ids = [
        row.observation_id for row in x.observations if not row.record_available or not row.record_valid
    ]
    time_misaligned_ids = [
        row.observation_id
        for row in x.observations
        if abs(row.observed_elapsed_time_s - row.provider_elapsed_time_s) > x.maximum_time_alignment_error_s
    ]
    sensor_misaligned_ids = [
        row.observation_id
        for row in x.observations
        if abs(sensors[row.sensor_id].position_m - row.provider_sensor_position_m)
        > x.maximum_sensor_position_alignment_error_m
    ]
    calibration_rows = [row for row in x.observations if row.partition == "calibration"]
    holdout_rows = [row for row in x.observations if row.partition == "holdout"]
    minimum_counts_met = (
        len(calibration_rows) >= x.minimum_calibration_observation_count
        and len(holdout_rows) >= x.minimum_holdout_observation_count
        and len({row.sequence_id for row in calibration_rows}) >= x.minimum_calibration_sequence_count
        and len({row.sequence_id for row in holdout_rows}) >= x.minimum_holdout_sequence_count
        and len({row.independence_group_id for row in holdout_rows})
        >= x.minimum_holdout_independence_group_count
    )
    if (
        missing_reviews
        or invalid_sensor_ids
        or invalid_observation_ids
        or time_misaligned_ids
        or sensor_misaligned_ids
        or not minimum_counts_met
    ):
        return Calculation(
            status="needs_data",
            values={
                "calibration_id": x.calibration_id,
                "missing_reviews": missing_reviews,
                "invalid_sensor_ids": invalid_sensor_ids,
                "invalid_observation_ids": invalid_observation_ids,
                "time_misaligned_observation_ids": time_misaligned_ids,
                "sensor_misaligned_observation_ids": sensor_misaligned_ids,
                "minimum_counts_met": minimum_counts_met,
            },
            notes=("Only reviewed, valid and aligned measured/provider response pairs enter calibration.",),
        )

    information = math.fsum(
        row.sample_weight * row.predicted_temperature_sensitivity_K_per_parameter_unit**2
        for row in calibration_rows
    )
    if information < x.minimum_weighted_sensitivity_information:
        return Calculation(
            status="needs_data",
            values={
                "calibration_id": x.calibration_id,
                "weighted_sensitivity_information": information,
                "minimum_weighted_sensitivity_information": x.minimum_weighted_sensitivity_information,
                "identifiable_parameter_response": False,
            },
            notes=("The supplied calibration sensitivities do not identify the declared parameter.",),
        )
    parameter_increment = (
        math.fsum(
            row.sample_weight
            * row.predicted_temperature_sensitivity_K_per_parameter_unit
            * (row.observed_temperature_K - row.baseline_predicted_temperature_K)
            for row in calibration_rows
        )
        / information
    )
    fitted_value = x.parameter.reference_value + parameter_increment
    if not x.parameter.minimum_supported_value <= fitted_value <= x.parameter.maximum_supported_value:
        return Calculation(
            status="out_of_scope",
            values={
                "calibration_id": x.calibration_id,
                "fitted_parameter_value": fitted_value,
                "parameter_unit": x.parameter.unit_token,
                "minimum_supported_parameter_value": x.parameter.minimum_supported_value,
                "maximum_supported_parameter_value": x.parameter.maximum_supported_value,
                "holdout_residuals": [],
            },
            notes=(
                "The fitted parameter is outside caller-reviewed support; no holdout residual is emitted.",
            ),
        )

    calibration_time_min = min(row.observed_elapsed_time_s for row in calibration_rows)
    calibration_time_max = max(row.observed_elapsed_time_s for row in calibration_rows)
    calibration_position_min = min(sensors[row.sensor_id].position_m for row in calibration_rows)
    calibration_position_max = max(sensors[row.sensor_id].position_m for row in calibration_rows)
    out_of_support_holdout_ids = [
        row.observation_id
        for row in holdout_rows
        if not calibration_time_min <= row.observed_elapsed_time_s <= calibration_time_max
        or not calibration_position_min <= sensors[row.sensor_id].position_m <= calibration_position_max
    ]
    if out_of_support_holdout_ids:
        return Calculation(
            status="out_of_scope",
            values={
                "calibration_id": x.calibration_id,
                "fitted_parameter_value": fitted_value,
                "parameter_unit": x.parameter.unit_token,
                "calibration_time_support_s": [calibration_time_min, calibration_time_max],
                "calibration_sensor_position_support_m": [
                    calibration_position_min,
                    calibration_position_max,
                ],
                "out_of_support_holdout_observation_ids": out_of_support_holdout_ids,
                "holdout_residuals": [],
            },
            notes=("Holdout rows outside calibration time or sensor-position support are not scored.",),
        )

    def prediction(row):
        return row.baseline_predicted_temperature_K + (
            row.predicted_temperature_sensitivity_K_per_parameter_unit * parameter_increment
        )

    calibration_residuals = [row.observed_temperature_K - prediction(row) for row in calibration_rows]
    holdout_residual_rows = [
        {
            "observation_id": row.observation_id,
            "sequence_id": row.sequence_id,
            "sensor_id": row.sensor_id,
            "elapsed_time_s": row.observed_elapsed_time_s,
            "sensor_position_m": sensors[row.sensor_id].position_m,
            "observed_temperature_K": row.observed_temperature_K,
            "predicted_temperature_K": prediction(row),
            "residual_K": row.observed_temperature_K - prediction(row),
            "expanded_observed_temperature_uncertainty_K": (row.expanded_observed_temperature_uncertainty_K),
            "expanded_baseline_prediction_uncertainty_K": (row.expanded_baseline_prediction_uncertainty_K),
            "provider_response_digest": row.provider_response_digest,
            "observation_record_digest": row.observation_record_digest,
        }
        for row in holdout_rows
    ]
    holdout_weight_sum = math.fsum(row.sample_weight for row in holdout_rows)
    holdout_bias = (
        math.fsum(row.sample_weight * (row.observed_temperature_K - prediction(row)) for row in holdout_rows)
        / holdout_weight_sum
    )
    holdout_rmse = math.sqrt(
        math.fsum(
            row.sample_weight * (row.observed_temperature_K - prediction(row)) ** 2 for row in holdout_rows
        )
        / holdout_weight_sum
    )
    return Calculation(
        status="computed",
        values={
            "calibration_id": x.calibration_id,
            "parameter_id": x.parameter.parameter_id,
            "parameter_kind": x.parameter.parameter_kind,
            "fitted_parameter_value": fitted_value,
            "parameter_unit": x.parameter.unit_token,
            "weighted_sensitivity_information": information,
            "calibration_observation_ids": [row.observation_id for row in calibration_rows],
            "holdout_observation_ids": [row.observation_id for row in holdout_rows],
            "calibration_weighted_rmse_K": math.sqrt(
                math.fsum(
                    row.sample_weight * residual**2
                    for row, residual in zip(calibration_rows, calibration_residuals, strict=True)
                )
                / math.fsum(row.sample_weight for row in calibration_rows)
            ),
            "holdout_weighted_bias_K": holdout_bias,
            "holdout_weighted_rmse_K": holdout_rmse,
            "holdout_residuals": holdout_residual_rows,
            "calibration_time_support_s": [calibration_time_min, calibration_time_max],
            "calibration_sensor_position_support_m": [
                calibration_position_min,
                calibration_position_max,
            ],
            "missing_reviews": [],
        },
        notes=(
            "The fit uses caller/provider baseline temperatures and local parameter sensitivities; it does not solve a heat equation.",
            "Holdout residuals are emitted only inside calibration time and sensor-position support.",
            "No phase mechanism, thermal stress, acceptance, life or probability is inferred.",
        ),
    )


def specifications():
    def same_identity(x, context):
        if (x.asset_id, x.location_id, x.time_basis) != (
            context.asset_id,
            context.location_id,
            context.time_basis,
        ):
            raise ValueError("thermal-gradient calibration identity and clock must match run context")

    return [
        ModelSpec(
            "structural.thermal_gradient_parameter_calibration",
            ThermalGradientParameterCalibration,
            thermal_gradient_parameter_calibration,
            {
                "calibration_id": "1",
                "parameter_id": "1",
                "parameter_kind": "1",
                "fitted_parameter_value": "caller_parameter_unit",
                "parameter_unit": "1",
                "weighted_sensitivity_information": "mixed",
                "calibration_observation_ids": "1",
                "holdout_observation_ids": "1",
                "calibration_weighted_rmse_K": "K",
                "holdout_weighted_bias_K": "K",
                "holdout_weighted_rmse_K": "K",
                "holdout_residuals": "mixed",
                "calibration_time_support_s": "s",
                "calibration_sensor_position_support_m": "m",
                "missing_reviews": "1",
            },
            (
                "Caller-reviewed transient measurements align to supplied baseline and sensitivity responses.",
                "Calibration and holdout physical specimens, source groups and independence groups are disjoint.",
                "The fitted value and all scored holdout rows remain inside declared support.",
            ),
            ("authored_weighted_transient_temperature_sensitivity_calibration",),
            context_validator=same_identity,
        )
    ]
