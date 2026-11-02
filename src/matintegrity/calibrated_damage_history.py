"""Integrate explicit calibrated microbial/cavitation loss rates without inferring them from indicators."""

import math
from typing import Literal

from pydantic import Field, model_validator

from .contracts import Contract, Nonnegative, Positive, canonical_digest


class CalibratedDamageInterval(Contract):
    interval_id: str = Field(min_length=1)
    start_s: Nonnegative
    end_s: Positive
    loss_rate_m_s: Nonnegative
    provider_id: str = Field(min_length=1)
    provider_revision: str = Field(min_length=1)
    calibration_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    condition_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    condition_within_calibration_support_reviewed: bool

    @model_validator(mode="after")
    def duration(self):
        if self.end_s <= self.start_s:
            raise ValueError("damage interval requires positive duration")
        return self


class CalibratedDamageHistory(Contract):
    history_id: str = Field(min_length=1)
    mechanism: Literal["microbial", "cavitation"]
    material_condition_id: str = Field(min_length=1)
    physical_location_id: str = Field(min_length=1)
    intervals: tuple[CalibratedDamageInterval, ...] = Field(min_length=1)
    calibrated_rate_and_mechanism_reviewed: bool

    @model_validator(mode="after")
    def ordered(self):
        if len({row.interval_id for row in self.intervals}) != len(self.intervals):
            raise ValueError("damage interval identifiers must be unique")
        if any(b.start_s != a.end_s for a, b in zip(self.intervals[:-1], self.intervals[1:], strict=True)):
            raise ValueError("damage history requires contiguous ordered intervals")
        return self


def integrate_calibrated_damage(request: CalibratedDamageHistory) -> dict:
    base = dict(
        history_id=request.history_id,
        mechanism=request.mechanism,
        input_sha256=canonical_digest(request.model_dump(mode="json")),
        status="needs_data",
        cumulative_loss_m=None,
        interval_loss_m=None,
    )
    if not request.calibrated_rate_and_mechanism_reviewed:
        return base
    unsupported = [
        row.interval_id for row in request.intervals if not row.condition_within_calibration_support_reviewed
    ]
    if unsupported:
        return base | dict(status="out_of_scope", unsupported_interval_ids=unsupported)
    increments = [(row.end_s - row.start_s) * row.loss_rate_m_s for row in request.intervals]
    if any(not math.isfinite(value) for value in increments):
        return base | dict(status="out_of_scope", numeric_range_exceeded=True)
    try:
        total_loss = math.fsum(increments)
    except OverflowError:
        return base | dict(status="out_of_scope", numeric_range_exceeded=True)
    if not math.isfinite(total_loss):
        return base | dict(status="out_of_scope", numeric_range_exceeded=True)
    return base | dict(
        status="computed",
        cumulative_loss_m=total_loss,
        interval_loss_m=increments,
        interpretation="Calibrated local loss integration only; no rate inference from microbial counts or cavitation margin.",
    )
