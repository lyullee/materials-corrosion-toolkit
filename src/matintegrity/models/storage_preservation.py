"""Storage-preservation exposure and inspection records with caller-owned limits."""

from __future__ import annotations

from pydantic import Field, model_validator

from ..contracts import Calculation, Contract, Evidence, Fraction, Nonnegative, Positive
from ..registry import ModelSpec


class PreservationEnvironmentInterval(Contract):
    interval_id: str = Field(min_length=1)
    start_time_s: Nonnegative
    end_time_s: Positive
    record_valid: bool
    temperature_K: Positive | None = None
    relative_humidity_fraction: Fraction | None = None
    preservation_state_id: str | None = None
    missing_basis: str | None = None
    evidence: list[Evidence] = Field(min_length=1)

    @model_validator(mode="after")
    def valid_interval(self):
        if self.end_time_s <= self.start_time_s:
            raise ValueError("environment interval must have positive duration")
        values = (self.temperature_K, self.relative_humidity_fraction, self.preservation_state_id)
        if self.record_valid and any(value is None for value in values):
            raise ValueError(
                "a valid environment interval requires temperature, humidity and preservation state"
            )
        if not self.record_valid and not self.missing_basis:
            raise ValueError("an invalid environment interval requires a missing-data basis")
        return self


class PreservationInspection(Contract):
    inspection_id: str = Field(min_length=1)
    inspection_time_s: Nonnegative
    reported_disposition: str = Field(min_length=1)
    evidence: list[Evidence] = Field(min_length=1)


class StoragePreservationHistory(Contract):
    record_id: str = Field(min_length=1)
    asset_id: str = Field(min_length=1)
    location_id: str = Field(min_length=1)
    clock_id: str = Field(min_length=1)
    horizon_start_s: Nonnegative
    horizon_end_s: Positive
    environment_intervals: list[PreservationEnvironmentInterval] = Field(min_length=1)
    inspections: list[PreservationInspection] = Field(default_factory=list)
    minimum_allowed_temperature_K: Positive
    maximum_allowed_temperature_K: Positive
    minimum_allowed_relative_humidity_fraction: Fraction
    maximum_allowed_relative_humidity_fraction: Fraction
    allowed_preservation_state_ids: list[str] = Field(min_length=1)
    maximum_inspection_interval_s: Positive
    clock_and_coverage_reviewed: bool
    environment_units_reviewed: bool
    preservation_state_mapping_reviewed: bool
    declared_limits_reviewed: bool
    inspection_records_reviewed: bool
    evidence: list[Evidence] = Field(min_length=1)

    @model_validator(mode="after")
    def ordered_history(self):
        if self.horizon_end_s <= self.horizon_start_s:
            raise ValueError("preservation horizon must have positive duration")
        if self.maximum_allowed_temperature_K < self.minimum_allowed_temperature_K:
            raise ValueError("temperature limits must be ordered")
        if self.maximum_allowed_relative_humidity_fraction < self.minimum_allowed_relative_humidity_fraction:
            raise ValueError("humidity limits must be ordered")
        if any(not state.strip() for state in self.allowed_preservation_state_ids):
            raise ValueError("allowed preservation state IDs cannot be blank")
        if len(set(self.allowed_preservation_state_ids)) != len(self.allowed_preservation_state_ids):
            raise ValueError("allowed preservation state IDs must be unique")

        interval_ids = [row.interval_id for row in self.environment_intervals]
        if len(set(interval_ids)) != len(interval_ids):
            raise ValueError("environment interval IDs must be unique")
        previous_end = self.horizon_start_s
        for row in self.environment_intervals:
            if row.start_time_s < self.horizon_start_s or row.end_time_s > self.horizon_end_s:
                raise ValueError("environment intervals must remain inside the preservation horizon")
            if row.start_time_s < previous_end:
                raise ValueError("environment intervals must be ordered and cannot overlap")
            previous_end = row.end_time_s

        inspection_ids = [row.inspection_id for row in self.inspections]
        if len(set(inspection_ids)) != len(inspection_ids):
            raise ValueError("inspection IDs must be unique")
        previous_time = None
        for row in self.inspections:
            if not self.horizon_start_s <= row.inspection_time_s <= self.horizon_end_s:
                raise ValueError("inspection times must remain inside the preservation horizon")
            if previous_time is not None and row.inspection_time_s <= previous_time:
                raise ValueError("inspection times must be strictly increasing")
            previous_time = row.inspection_time_s
        return self


def _maximum_continuous_duration(rows: list[PreservationEnvironmentInterval], predicate) -> float:
    maximum = 0.0
    current = 0.0
    previous_end = None
    for row in rows:
        violating = row.record_valid and predicate(row)
        if violating:
            if previous_end != row.start_time_s:
                current = 0.0
            current += row.end_time_s - row.start_time_s
            maximum = max(maximum, current)
            previous_end = row.end_time_s
        else:
            current = 0.0
            previous_end = None
    return maximum


def storage_preservation_history(x: StoragePreservationHistory) -> Calculation:
    missing_reviews = [
        name
        for name in (
            "clock_and_coverage_reviewed",
            "environment_units_reviewed",
            "preservation_state_mapping_reviewed",
            "declared_limits_reviewed",
            "inspection_records_reviewed",
        )
        if not getattr(x, name)
    ]

    invalid_duration = sum(
        row.end_time_s - row.start_time_s for row in x.environment_intervals if not row.record_valid
    )
    represented_duration = sum(row.end_time_s - row.start_time_s for row in x.environment_intervals)
    uncovered_duration = x.horizon_end_s - x.horizon_start_s - represented_duration
    missing_duration = invalid_duration + uncovered_duration
    valid_rows = [row for row in x.environment_intervals if row.record_valid]

    def temperature_outside(row):
        return not x.minimum_allowed_temperature_K <= row.temperature_K <= x.maximum_allowed_temperature_K

    def humidity_outside(row):
        return not (
            x.minimum_allowed_relative_humidity_fraction
            <= row.relative_humidity_fraction
            <= x.maximum_allowed_relative_humidity_fraction
        )

    allowed_states = set(x.allowed_preservation_state_ids)

    def state_outside(row):
        return row.preservation_state_id not in allowed_states

    def any_outside(row):
        return temperature_outside(row) or humidity_outside(row) or state_outside(row)

    def duration(predicate):
        return sum(row.end_time_s - row.start_time_s for row in valid_rows if predicate(row))

    inspection_times = [x.horizon_start_s]
    inspection_times.extend(row.inspection_time_s for row in x.inspections)
    inspection_times.append(x.horizon_end_s)
    inspection_gaps = [
        end - start for start, end in zip(inspection_times, inspection_times[1:], strict=False)
    ]
    overdue_durations = [max(0.0, gap - x.maximum_inspection_interval_s) for gap in inspection_gaps]
    # Partition the horizon at evidence and inspection boundaries; gaps stay explicit.
    boundaries = {x.horizon_start_s, x.horizon_end_s, *inspection_times}
    for row in x.environment_intervals:
        boundaries.update((row.start_time_s, row.end_time_s))
    ordered_boundaries = sorted(boundaries)
    inspection_id_at_time = {row.inspection_time_s: row.inspection_id for row in x.inspections}
    environment_timeline = []
    interval_index = 0
    for start, end in zip(ordered_boundaries, ordered_boundaries[1:], strict=False):
        while (
            interval_index < len(x.environment_intervals)
            and x.environment_intervals[interval_index].end_time_s <= start
        ):
            interval_index += 1
        row = None
        if interval_index < len(x.environment_intervals):
            candidate = x.environment_intervals[interval_index]
            if candidate.start_time_s <= start and candidate.end_time_s >= end:
                row = candidate
        if row is None:
            environment_timeline.append(
                {
                    "start_time_s": start,
                    "end_time_s": end,
                    "duration_s": end - start,
                    "start_inspection_id": inspection_id_at_time.get(start),
                    "end_inspection_id": inspection_id_at_time.get(end),
                    "coverage_status": "uncovered",
                    "source_interval_id": None,
                    "missing_basis": "no environment interval supplied",
                    "outside_limit_dimensions": [],
                }
            )
            continue
        outside = []
        if row.record_valid:
            if temperature_outside(row):
                outside.append("temperature")
            if humidity_outside(row):
                outside.append("relative_humidity")
            if state_outside(row):
                outside.append("preservation_state")
        environment_timeline.append(
            {
                "start_time_s": start,
                "end_time_s": end,
                "duration_s": end - start,
                "start_inspection_id": inspection_id_at_time.get(start),
                "end_inspection_id": inspection_id_at_time.get(end),
                "coverage_status": "observed" if row.record_valid else "invalid_record",
                "source_interval_id": row.interval_id,
                "missing_basis": row.missing_basis if not row.record_valid else None,
                "temperature_K": row.temperature_K if row.record_valid else None,
                "relative_humidity_fraction": row.relative_humidity_fraction if row.record_valid else None,
                "preservation_state_id": row.preservation_state_id if row.record_valid else None,
                "outside_limit_dimensions": outside,
            }
        )
    inspection_schedule = [
        {
            "start_time_s": start,
            "end_time_s": end,
            "gap_s": gap,
            "start_inspection_id": inspection_id_at_time.get(start),
            "end_inspection_id": inspection_id_at_time.get(end),
            "overdue_duration_s": overdue,
            "exceeded_declared_interval": overdue > 0.0,
        }
        for start, end, gap, overdue in zip(
            inspection_times[:-1], inspection_times[1:], inspection_gaps, overdue_durations, strict=True
        )
    ]

    status = "needs_data" if missing_reviews or missing_duration > 0 else "computed"
    return Calculation(
        status=status,
        values={
            "record_id": x.record_id,
            "asset_id": x.asset_id,
            "location_id": x.location_id,
            "clock_id": x.clock_id,
            "horizon_duration_s": x.horizon_end_s - x.horizon_start_s,
            "represented_environment_duration_s": represented_duration,
            "valid_environment_duration_s": sum(row.end_time_s - row.start_time_s for row in valid_rows),
            "invalid_environment_duration_s": invalid_duration,
            "uncovered_environment_duration_s": uncovered_duration,
            "missing_environment_duration_s": missing_duration,
            "invalid_interval_ids": [
                row.interval_id for row in x.environment_intervals if not row.record_valid
            ],
            "temperature_outside_duration_s": duration(temperature_outside),
            "humidity_outside_duration_s": duration(humidity_outside),
            "preservation_state_outside_duration_s": duration(state_outside),
            "any_declared_limit_outside_duration_s": duration(any_outside),
            "maximum_continuous_temperature_outside_s": _maximum_continuous_duration(
                x.environment_intervals, temperature_outside
            ),
            "maximum_continuous_humidity_outside_s": _maximum_continuous_duration(
                x.environment_intervals, humidity_outside
            ),
            "maximum_continuous_preservation_state_outside_s": _maximum_continuous_duration(
                x.environment_intervals, state_outside
            ),
            "maximum_continuous_any_declared_limit_outside_s": _maximum_continuous_duration(
                x.environment_intervals, any_outside
            ),
            "outside_limit_interval_ids": [row.interval_id for row in valid_rows if any_outside(row)],
            "inspection_count": len(x.inspections),
            "inspection_gap_s": inspection_gaps,
            "inspection_overdue_duration_s": overdue_durations,
            "total_inspection_overdue_duration_s": sum(overdue_durations),
            "maximum_inspection_overdue_duration_s": max(overdue_durations, default=0.0),
            "inspection_interval_exceeded": any(value > 0 for value in overdue_durations),
            "environment_timeline": environment_timeline,
            "inspection_schedule": inspection_schedule,
            "missing_reviews": missing_reviews,
        },
        notes=(
            "Environment values are treated as constant only over their explicitly recorded intervals; gaps and invalid records are never bridged.",
            "Limits and inspection spacing are caller declarations, not bundled standard, material, preservation or acceptance requirements.",
            "Reported exposure duration does not predict corrosion, degradation, remaining life or failure probability.",
        ),
    )


def specifications():
    def same_identity(x, context):
        if (x.asset_id, x.location_id) != (context.asset_id, context.location_id):
            raise ValueError("preservation-history asset and location must match the assessment context")

    return [
        ModelSpec(
            "fabrication.storage_preservation_history",
            StoragePreservationHistory,
            storage_preservation_history,
            {
                "horizon_duration_s": "s",
                "represented_environment_duration_s": "s",
                "valid_environment_duration_s": "s",
                "invalid_environment_duration_s": "s",
                "uncovered_environment_duration_s": "s",
                "missing_environment_duration_s": "s",
                "temperature_outside_duration_s": "s",
                "humidity_outside_duration_s": "s",
                "preservation_state_outside_duration_s": "s",
                "any_declared_limit_outside_duration_s": "s",
                "maximum_continuous_temperature_outside_s": "s",
                "maximum_continuous_humidity_outside_s": "s",
                "maximum_continuous_preservation_state_outside_s": "s",
                "maximum_continuous_any_declared_limit_outside_s": "s",
                "inspection_gap_s": "s",
                "inspection_overdue_duration_s": "s",
                "total_inspection_overdue_duration_s": "s",
                "maximum_inspection_overdue_duration_s": "s",
                "inspection_interval_exceeded": "1",
                "environment_timeline": "structured_record",
                "inspection_schedule": "structured_record",
            },
            (
                "Piecewise-constant environment observations remain separate from caller-declared temperature, humidity, preservation-state and inspection-spacing limits.",
                "Uncovered or invalid intervals stop a complete-history result and are not replaced, interpolated or classified as acceptable exposure.",
                "Timeline rows partition the declared horizon; uncovered spans remain explicit and are not imputed.",
            ),
            ("storage_preservation_interval_accounting",),
            context_validator=same_identity,
        )
    ]
