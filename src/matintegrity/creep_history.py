"""Caller-calibrated Norton history integration and declared rupture-time fractions."""

from __future__ import annotations

import math
from typing import Literal

from pydantic import Field, model_validator

from .contracts import Contract, Nonnegative, Positive, canonical_digest


class CreepHistoryInterval(Contract):
    interval_id: str = Field(min_length=1)
    start_s: Nonnegative
    end_s: Positive
    temperature_K: Positive
    stress_Pa: Nonnegative
    reference_stress_Pa: Positive
    strain_rate_at_reference_per_s: Nonnegative
    stress_exponent: Positive
    parameter_set_id: str = Field(min_length=1)
    parameter_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    stress_support_Pa: tuple[Nonnegative, Nonnegative]
    temperature_support_K: tuple[Positive, Positive]
    rupture_time_s: Positive | None = None
    rupture_provider_sha256: str | None = Field(default=None, pattern=r"^[a-f0-9]{64}$")

    @model_validator(mode="after")
    def coherent(self):
        if self.end_s <= self.start_s:
            raise ValueError("creep interval must have positive duration")
        if (
            self.stress_support_Pa[1] < self.stress_support_Pa[0]
            or self.temperature_support_K[1] < self.temperature_support_K[0]
        ):
            raise ValueError("creep support bounds must be ordered")
        if (self.rupture_time_s is None) != (self.rupture_provider_sha256 is None):
            raise ValueError("rupture time and provider digest must be supplied together")
        return self


class CreepHistoryRequest(Contract):
    history_id: str = Field(min_length=1)
    material_condition_id: str = Field(min_length=1)
    exposure_history_sha256: str | None = Field(default=None, pattern=r"^[a-f0-9]{64}$")
    intervals: tuple[CreepHistoryInterval, ...] = Field(min_length=1)
    piecewise_constant_stress_temperature_and_parameters_reviewed: bool
    secondary_creep_applicability_reviewed: bool
    linear_rupture_time_fraction_reviewed: bool

    @model_validator(mode="after")
    def contiguous(self):
        if len({row.interval_id for row in self.intervals}) != len(self.intervals):
            raise ValueError("creep interval identifiers must be unique")
        for first, second in zip(self.intervals[:-1], self.intervals[1:], strict=True):
            if second.start_s != first.end_s:
                raise ValueError("creep history must be ordered and contiguous")
        return self


class CreepHistoryResult(Contract):
    schema_version: Literal["matintegrity.creep_history.v1"] = "matintegrity.creep_history.v1"
    history_id: str
    input_sha256: str
    status: Literal["computed", "needs_data", "out_of_scope"]
    interval_strain_increments: tuple[float, ...]
    cumulative_strain_at_boundaries: tuple[float, ...]
    secondary_creep_strain: float | None
    linear_rupture_time_fraction: float | None
    unsupported_interval_ids: tuple[str, ...]
    notes: tuple[str, ...]


def integrate_creep_history(request: CreepHistoryRequest) -> CreepHistoryResult:
    """Integrate constant-condition secondary strain; rupture fractions require a separate declaration."""
    base = dict(
        history_id=request.history_id,
        input_sha256=canonical_digest(request.model_dump(mode="json")),
        interval_strain_increments=(),
        cumulative_strain_at_boundaries=(),
        secondary_creep_strain=None,
        linear_rupture_time_fraction=None,
        unsupported_interval_ids=(),
    )
    if (
        not request.piecewise_constant_stress_temperature_and_parameters_reviewed
        or not request.secondary_creep_applicability_reviewed
    ):
        return CreepHistoryResult(
            **base,
            status="needs_data",
            notes=("History and secondary-creep applicability reviews are required.",),
        )
    unsupported = tuple(
        row.interval_id
        for row in request.intervals
        if not (
            row.stress_support_Pa[0] <= row.stress_Pa <= row.stress_support_Pa[1]
            and row.temperature_support_K[0] <= row.temperature_K <= row.temperature_support_K[1]
        )
    )
    if unsupported:
        base["unsupported_interval_ids"] = unsupported
        return CreepHistoryResult(
            **base, status="out_of_scope", notes=("Intervals exceed caller parameter support.",)
        )
    increments = []
    for row in request.intervals:
        if row.stress_Pa == 0 or row.strain_rate_at_reference_per_s == 0:
            increments.append(0.0)
            continue
        log_increment = (
            math.log(row.end_s - row.start_s)
            + math.log(row.strain_rate_at_reference_per_s)
            + row.stress_exponent * (math.log(row.stress_Pa) - math.log(row.reference_stress_Pa))
        )
        try:
            increment = math.exp(log_increment)
            if not math.isfinite(increment):
                raise OverflowError("nonfinite creep increment")
            increments.append(increment)
        except OverflowError:
            return CreepHistoryResult(
                **base, status="out_of_scope", notes=("A strain increment exceeds numeric range.",)
            )
    cumulative = [0.0]
    for increment in increments:
        try:
            cumulative.append(math.fsum((cumulative[-1], increment)))
        except OverflowError:
            return CreepHistoryResult(
                **base, status="out_of_scope", notes=("Cumulative creep strain exceeds numeric range.",)
            )
    rupture = None
    if request.linear_rupture_time_fraction_reviewed and all(
        row.rupture_time_s is not None for row in request.intervals
    ):
        try:
            rupture = math.fsum((row.end_s - row.start_s) / row.rupture_time_s for row in request.intervals)
            if not math.isfinite(rupture):
                raise OverflowError("nonfinite rupture fraction")
        except OverflowError:
            return CreepHistoryResult(
                **base, status="out_of_scope", notes=("Rupture time fractions exceed numeric range.",)
            )
    base.update(
        interval_strain_increments=tuple(increments),
        cumulative_strain_at_boundaries=tuple(cumulative),
        secondary_creep_strain=cumulative[-1],
        linear_rupture_time_fraction=rupture,
    )
    return CreepHistoryResult(
        **base,
        status="computed",
        notes=(
            "Secondary strain and declared rupture fractions are separate empirical quantities; stress redistribution, primary/tertiary creep and creep-fatigue interaction require other models.",
        ),
    )
