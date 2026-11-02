"""Under-insulation exposure accounting using caller-owned state definitions."""

from __future__ import annotations

from pydantic import Field, model_validator

from ..contracts import Calculation, Contract, Evidence, Nonnegative, Positive
from ..registry import ModelSpec


class InsulationExposureInterval(Contract):
    interval_id: str = Field(min_length=1)
    start_time_s: Nonnegative
    end_time_s: Positive
    record_valid: bool
    surface_temperature_K: Positive | None = None
    wetness_state_id: str | None = None
    insulation_condition_id: str | None = None
    missing_basis: str | None = None
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def complete_valid_record(self):
        if self.end_time_s <= self.start_time_s:
            raise ValueError("insulation exposure intervals must have positive duration")
        states = (
            self.surface_temperature_K,
            self.wetness_state_id,
            self.insulation_condition_id,
        )
        if self.record_valid and any(value is None for value in states):
            raise ValueError("a valid interval requires temperature, wetness and insulation condition")
        if not self.record_valid and not self.missing_basis:
            raise ValueError("an invalid interval requires a missing-data basis")
        return self


class DeclaredUnderInsulationExposure(Contract):
    definition_id: str = Field(min_length=1)
    minimum_surface_temperature_K: Positive
    maximum_surface_temperature_K: Positive
    included_wetness_state_ids: tuple[str, ...] = Field(min_length=1)
    included_insulation_condition_ids: tuple[str, ...] = Field(min_length=1)
    definition_basis: str = Field(min_length=1)
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def ordered_and_unique(self):
        if self.maximum_surface_temperature_K < self.minimum_surface_temperature_K:
            raise ValueError("under-insulation temperature bounds must be ordered")
        for name, values in (
            ("wetness", self.included_wetness_state_ids),
            ("insulation condition", self.included_insulation_condition_ids),
        ):
            if any(not value.strip() for value in values) or len(values) != len(set(values)):
                raise ValueError(f"included {name} state identifiers must be nonblank and unique")
        return self


class UnderInsulationExposureHistory(Contract):
    record_id: str = Field(min_length=1)
    source_model_id: str | None = None
    source_result_digest: str | None = Field(default=None, pattern=r"^[a-f0-9]{64}$")
    wetness_state_semantics: str | None = None
    asset_id: str = Field(min_length=1)
    location_id: str = Field(min_length=1)
    clock_id: str = Field(min_length=1)
    horizon_start_s: Nonnegative
    horizon_end_s: Positive
    intervals: tuple[InsulationExposureInterval, ...] = Field(min_length=1)
    exposure_definition: DeclaredUnderInsulationExposure
    clock_and_coverage_reviewed: bool
    temperature_measurement_reviewed: bool
    wetness_state_mapping_reviewed: bool
    insulation_condition_mapping_reviewed: bool
    exposure_definition_reviewed: bool

    @model_validator(mode="after")
    def ordered_history(self):
        if self.horizon_end_s <= self.horizon_start_s:
            raise ValueError("under-insulation history must have positive duration")
        identifiers = [interval.interval_id for interval in self.intervals]
        if len(identifiers) != len(set(identifiers)):
            raise ValueError("insulation interval identifiers must be unique")
        previous_end = self.horizon_start_s
        for interval in self.intervals:
            if interval.start_time_s < self.horizon_start_s or interval.end_time_s > self.horizon_end_s:
                raise ValueError("insulation intervals must remain inside the declared horizon")
            if interval.start_time_s < previous_end:
                raise ValueError("insulation intervals must be ordered and cannot overlap")
            previous_end = interval.end_time_s
        return self


def under_insulation_exposure_history(x: UnderInsulationExposureHistory) -> Calculation:
    missing_reviews = [
        name
        for name in (
            "clock_and_coverage_reviewed",
            "temperature_measurement_reviewed",
            "wetness_state_mapping_reviewed",
            "insulation_condition_mapping_reviewed",
            "exposure_definition_reviewed",
        )
        if not getattr(x, name)
    ]
    represented = sum(interval.end_time_s - interval.start_time_s for interval in x.intervals)
    invalid = sum(
        interval.end_time_s - interval.start_time_s for interval in x.intervals if not interval.record_valid
    )
    uncovered = x.horizon_end_s - x.horizon_start_s - represented
    definition = x.exposure_definition
    wetness_states = set(definition.included_wetness_state_ids)
    condition_states = set(definition.included_insulation_condition_ids)

    def classified(interval):
        return (
            interval.record_valid
            and definition.minimum_surface_temperature_K
            <= interval.surface_temperature_K
            <= definition.maximum_surface_temperature_K
            and interval.wetness_state_id in wetness_states
            and interval.insulation_condition_id in condition_states
        )

    classified_ids = []
    classified_duration = 0.0
    maximum_continuous = 0.0
    current_continuous = 0.0
    previous_classified_end = None
    rows = []
    for interval in x.intervals:
        duration = interval.end_time_s - interval.start_time_s
        is_classified = classified(interval)
        rows.append(
            {
                "interval_id": interval.interval_id,
                "duration_s": duration,
                "record_valid": interval.record_valid,
                "within_declared_exposure_definition": is_classified if interval.record_valid else None,
            }
        )
        if is_classified:
            classified_ids.append(interval.interval_id)
            classified_duration += duration
            if previous_classified_end != interval.start_time_s:
                current_continuous = 0.0
            current_continuous += duration
            maximum_continuous = max(maximum_continuous, current_continuous)
            previous_classified_end = interval.end_time_s
        else:
            current_continuous = 0.0
            previous_classified_end = None

    missing_duration = invalid + uncovered
    return Calculation(
        status="needs_data" if missing_reviews or missing_duration > 0 else "computed",
        values={
            "record_id": x.record_id,
            "source_model_id": x.source_model_id,
            "source_result_digest": x.source_result_digest,
            "wetness_state_semantics": x.wetness_state_semantics,
            "definition_id": definition.definition_id,
            "horizon_duration_s": x.horizon_end_s - x.horizon_start_s,
            "represented_interval_duration_s": represented,
            "invalid_interval_duration_s": invalid,
            "uncovered_interval_duration_s": uncovered,
            "missing_interval_duration_s": missing_duration,
            "classified_exposure_duration_s": classified_duration,
            "maximum_continuous_classified_exposure_s": maximum_continuous,
            "classified_exposure_interval_ids": classified_ids,
            "interval_rows": rows,
            "missing_reviews": missing_reviews,
        },
        notes=(
            "Exposure classification follows only the caller-owned temperature and state definition; it is not an embedded corrosion rule.",
            "Classified time does not predict corrosion rate, metal loss, crack initiation, remaining life or failure probability.",
            "Invalid and uncovered intervals are retained as missing time and are never interpolated or classified.",
        ),
    )


def specifications():
    def same_identity(x, context):
        if (x.asset_id, x.location_id) != (context.asset_id, context.location_id):
            raise ValueError("under-insulation asset and location must match the run context")

    return [
        ModelSpec(
            "degradation.under_insulation_exposure_history",
            UnderInsulationExposureHistory,
            under_insulation_exposure_history,
            {
                "record_id": "1",
                "definition_id": "1",
                "horizon_duration_s": "s",
                "represented_interval_duration_s": "s",
                "invalid_interval_duration_s": "s",
                "uncovered_interval_duration_s": "s",
                "missing_interval_duration_s": "s",
                "classified_exposure_duration_s": "s",
                "maximum_continuous_classified_exposure_s": "s",
                "classified_exposure_interval_ids": "1",
                "interval_rows": "mixed",
                "missing_reviews": "1",
            },
            (
                "Surface temperature, wetness and insulation condition are piecewise-constant reviewed observations over explicit intervals.",
                "The exposure definition and every included state identifier are supplied by the caller.",
            ),
            ("declared_under_insulation_exposure_accounting",),
            context_validator=same_identity,
        )
    ]
