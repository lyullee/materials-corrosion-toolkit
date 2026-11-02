"""Condensation exposure accounting for insulated surfaces and weather barriers."""

from __future__ import annotations

from pydantic import Field, model_validator

from ..contracts import Calculation, Contract, Evidence, Nonnegative, Positive
from ..registry import ModelSpec


class InsulationCondensationInterval(Contract):
    interval_id: str = Field(min_length=1)
    start_time_s: Nonnegative
    end_time_s: Positive
    outer_surface_temperature_K: Positive | None = None
    ambient_dew_point_temperature_K: Positive | None = None
    weather_barrier_state_id: str | None = None
    record_valid: bool
    invalid_basis: str | None = None
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def complete_interval(self):
        if self.end_time_s <= self.start_time_s:
            raise ValueError("condensation interval must have positive duration")
        required = (
            self.outer_surface_temperature_K,
            self.ambient_dew_point_temperature_K,
            self.weather_barrier_state_id,
        )
        if self.record_valid and any(value is None for value in required):
            raise ValueError("valid intervals require surface temperature, dew point and barrier state")
        if not self.record_valid and not self.invalid_basis:
            raise ValueError("invalid intervals require a basis")
        return self


class InsulationCondensationExposure(Contract):
    assessment_id: str = Field(min_length=1)
    asset_id: str = Field(min_length=1)
    location_id: str = Field(min_length=1)
    insulation_system_id: str = Field(min_length=1)
    outer_surface_location_definition: str = Field(min_length=1)
    dew_point_definition: str = Field(min_length=1)
    dew_point_provider_state_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    clock_id: str = Field(min_length=1)
    horizon_start_s: Nonnegative
    horizon_end_s: Positive
    intervals: tuple[InsulationCondensationInterval, ...] = Field(min_length=1)
    barrier_states_allowing_external_moisture: tuple[str, ...] = Field(min_length=1)
    temperature_measurement_uncertainty_K: Nonnegative
    dew_point_uncertainty_K: Nonnegative
    temperature_and_dew_point_units_reviewed: bool
    surface_location_reviewed: bool
    clock_and_coverage_reviewed: bool
    weather_barrier_mapping_reviewed: bool
    uncertainty_basis_reviewed: bool
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def ordered_history(self):
        if self.horizon_end_s <= self.horizon_start_s:
            raise ValueError("assessment horizon must have positive duration")
        if len(set(self.barrier_states_allowing_external_moisture)) != len(
            self.barrier_states_allowing_external_moisture
        ):
            raise ValueError("barrier state IDs must be unique")
        if any(not value.strip() for value in self.barrier_states_allowing_external_moisture):
            raise ValueError("barrier state IDs cannot be blank")
        ids = [row.interval_id for row in self.intervals]
        if len(set(ids)) != len(ids):
            raise ValueError("interval IDs must be unique")
        previous_end = self.horizon_start_s
        for row in self.intervals:
            if row.start_time_s < self.horizon_start_s or row.end_time_s > self.horizon_end_s:
                raise ValueError("intervals must remain inside the assessment horizon")
            if row.start_time_s < previous_end:
                raise ValueError("intervals must be ordered and non-overlapping")
            previous_end = row.end_time_s
        return self


def insulation_condensation_exposure(x: InsulationCondensationExposure) -> Calculation:
    missing_reviews = [
        field
        for field in (
            "temperature_and_dew_point_units_reviewed",
            "surface_location_reviewed",
            "clock_and_coverage_reviewed",
            "weather_barrier_mapping_reviewed",
            "uncertainty_basis_reviewed",
        )
        if not getattr(x, field)
    ]
    represented = sum(row.end_time_s - row.start_time_s for row in x.intervals)
    invalid = sum(row.end_time_s - row.start_time_s for row in x.intervals if not row.record_valid)
    uncovered = x.horizon_end_s - x.horizon_start_s - represented
    allowed = set(x.barrier_states_allowing_external_moisture)

    possible_ids: list[str] = []
    conservative_ids: list[str] = []
    possible_duration = 0.0
    conservative_duration = 0.0
    maximum_continuous = 0.0
    current_continuous = 0.0
    previous_end = None
    margins: dict[str, float] = {}
    conservative_margins: dict[str, float] = {}

    for row in x.intervals:
        if not row.record_valid:
            current_continuous = 0.0
            previous_end = None
            continue
        duration = row.end_time_s - row.start_time_s
        margin = row.outer_surface_temperature_K - row.ambient_dew_point_temperature_K
        conservative_margin = (
            row.outer_surface_temperature_K
            - x.temperature_measurement_uncertainty_K
            - row.ambient_dew_point_temperature_K
            - x.dew_point_uncertainty_K
        )
        margins[row.interval_id] = margin
        conservative_margins[row.interval_id] = conservative_margin
        barrier_allows = row.weather_barrier_state_id in allowed
        possible = barrier_allows and margin <= 0
        conservative = barrier_allows and conservative_margin <= 0
        if possible:
            possible_ids.append(row.interval_id)
            possible_duration += duration
        if conservative:
            conservative_ids.append(row.interval_id)
            conservative_duration += duration
            if previous_end != row.start_time_s:
                current_continuous = 0.0
            current_continuous += duration
            maximum_continuous = max(maximum_continuous, current_continuous)
            previous_end = row.end_time_s
        else:
            current_continuous = 0.0
            previous_end = None

    status = "needs_data" if missing_reviews or invalid > 0 or uncovered > 0 else "computed"
    return Calculation(
        status=status,
        values={
            "assessment_id": x.assessment_id,
            "horizon_duration_s": x.horizon_end_s - x.horizon_start_s,
            "represented_duration_s": represented,
            "invalid_duration_s": invalid,
            "uncovered_duration_s": uncovered,
            "nominal_condensation_possible_duration_s": possible_duration,
            "conservative_condensation_possible_duration_s": conservative_duration,
            "maximum_continuous_conservative_condensation_possible_s": maximum_continuous,
            "nominal_condensation_possible_interval_ids": possible_ids,
            "conservative_condensation_possible_interval_ids": conservative_ids,
            "temperature_margin_K_by_interval": margins,
            "conservative_temperature_margin_K_by_interval": conservative_margins,
            "invalid_interval_ids": [row.interval_id for row in x.intervals if not row.record_valid],
            "missing_reviews": missing_reviews,
        },
        notes=(
            "A nonpositive surface-to-dew-point margin identifies thermodynamic condensation potential only when the caller-declared barrier state permits external moisture.",
            "Temperature and dew-point uncertainties are combined as a one-sided arithmetic screen, not a statistical confidence bound.",
            "The result does not model water ingress, wet insulation, dry-out, corrosion rate, coating failure, acceptance, remaining life or failure probability.",
        ),
    )


def specifications():
    def same_scope(x, context):
        if (x.asset_id, x.location_id) != (context.asset_id, context.location_id):
            raise ValueError("insulation assessment scope must match the run context")

    return [
        ModelSpec(
            "fabrication.insulation_condensation_exposure",
            InsulationCondensationExposure,
            insulation_condensation_exposure,
            {
                "horizon_duration_s": "s",
                "represented_duration_s": "s",
                "invalid_duration_s": "s",
                "uncovered_duration_s": "s",
                "nominal_condensation_possible_duration_s": "s",
                "conservative_condensation_possible_duration_s": "s",
                "maximum_continuous_conservative_condensation_possible_s": "s",
                "temperature_margin_K_by_interval": "K",
                "conservative_temperature_margin_K_by_interval": "K",
            },
            (
                "Piecewise-constant, non-overlapping surface and ambient dew-point observations on one reviewed clock.",
                "Weather-barrier state mappings and uncertainty magnitudes are caller-owned and reviewed.",
            ),
            ("reviewed_insulation_condensation_exposure_accounting",),
            context_validator=same_scope,
        )
    ]
