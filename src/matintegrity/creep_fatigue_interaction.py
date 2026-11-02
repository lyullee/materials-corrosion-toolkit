"""Caller-owned piecewise-linear creep-fatigue interaction envelopes."""

from __future__ import annotations

from bisect import bisect_right
from typing import Literal

from pydantic import Field, model_validator

from .contracts import Contract, Evidence, Nonnegative, canonical_digest


class CreepFatigueInteractionEnvelope(Contract):
    envelope_id: str = Field(min_length=1)
    revision: str = Field(min_length=1)
    material_condition_id: str = Field(min_length=1)
    creep_damage_definition: str = Field(min_length=1)
    fatigue_damage_definition: str = Field(min_length=1)
    creep_coordinates: tuple[Nonnegative, ...] = Field(min_length=2)
    fatigue_limits: tuple[Nonnegative, ...] = Field(min_length=2)
    applicable_temperature_min_K: float = Field(gt=0)
    applicable_temperature_max_K: float = Field(gt=0)
    calibration_basis: str = Field(min_length=1)
    evidence: tuple[Evidence, ...] = Field(min_length=1)
    curve_and_applicability_reviewed: bool

    @model_validator(mode="after")
    def ordered_curve(self):
        if len(self.creep_coordinates) != len(self.fatigue_limits):
            raise ValueError("interaction coordinates must align")
        if any(b <= a for a, b in zip(self.creep_coordinates[:-1], self.creep_coordinates[1:], strict=True)):
            raise ValueError("creep coordinates must increase strictly")
        if any(b > a for a, b in zip(self.fatigue_limits[:-1], self.fatigue_limits[1:], strict=True)):
            raise ValueError("fatigue limits must be nonincreasing")
        if self.applicable_temperature_max_K < self.applicable_temperature_min_K:
            raise ValueError("temperature support must be ordered")
        return self


class CreepFatigueInteractionPoint(Contract):
    point_id: str = Field(min_length=1)
    material_condition_id: str = Field(min_length=1)
    creep_damage_definition: str = Field(min_length=1)
    fatigue_damage_definition: str = Field(min_length=1)
    creep_damage: Nonnegative
    fatigue_damage: Nonnegative
    temperature_K: float = Field(gt=0)
    exposure_history_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    damage_inputs_reviewed: bool


class CreepFatigueInteractionResult(Contract):
    schema_version: Literal["matintegrity.creep_fatigue_interaction.v1"] = (
        "matintegrity.creep_fatigue_interaction.v1"
    )
    point_id: str
    envelope_id: str
    envelope_revision: str
    envelope_sha256: str
    point_sha256: str
    status: Literal["computed", "needs_data", "out_of_scope"]
    fatigue_limit_at_creep_damage: float | None
    fatigue_margin: float | None
    fatigue_utilization: float | None
    within_caller_envelope: bool | None
    segment_index: int | None
    notes: tuple[str, ...]


def evaluate_creep_fatigue_interaction(
    point: CreepFatigueInteractionPoint, envelope: CreepFatigueInteractionEnvelope
) -> CreepFatigueInteractionResult:
    """Interpolate only the caller envelope; damage measures retain their declared definitions."""
    payload = dict(
        point_id=point.point_id,
        envelope_id=envelope.envelope_id,
        envelope_revision=envelope.revision,
        envelope_sha256=canonical_digest(envelope.model_dump(mode="json")),
        point_sha256=canonical_digest(point.model_dump(mode="json")),
        fatigue_limit_at_creep_damage=None,
        fatigue_margin=None,
        fatigue_utilization=None,
        within_caller_envelope=None,
        segment_index=None,
    )
    if not point.damage_inputs_reviewed or not envelope.curve_and_applicability_reviewed:
        return CreepFatigueInteractionResult(
            **payload,
            status="needs_data",
            notes=("Damage definitions and envelope applicability require review.",),
        )
    identities_match = (
        point.material_condition_id == envelope.material_condition_id
        and point.creep_damage_definition == envelope.creep_damage_definition
        and point.fatigue_damage_definition == envelope.fatigue_damage_definition
    )
    xs, ys = envelope.creep_coordinates, envelope.fatigue_limits
    if not identities_match or not (
        xs[0] <= point.creep_damage <= xs[-1]
        and envelope.applicable_temperature_min_K
        <= point.temperature_K
        <= envelope.applicable_temperature_max_K
    ):
        return CreepFatigueInteractionResult(
            **payload,
            status="out_of_scope",
            notes=(
                "Identity, damage definition or declared envelope support differs; no extrapolation performed.",
            ),
        )
    index = min(bisect_right(xs, point.creep_damage) - 1, len(xs) - 2)
    fraction = (point.creep_damage - xs[index]) / (xs[index + 1] - xs[index])
    limit = (1.0 - fraction) * ys[index] + fraction * ys[index + 1]
    payload.update(
        fatigue_limit_at_creep_damage=limit,
        fatigue_margin=limit - point.fatigue_damage,
        fatigue_utilization=point.fatigue_damage / limit if limit > 0 else None,
        within_caller_envelope=point.fatigue_damage <= limit,
        segment_index=index,
    )
    return CreepFatigueInteractionResult(
        **payload,
        status="computed",
        notes=(
            "Comparison uses only the caller-owned interaction curve; no damage calibration, remaining life or standard acceptance is inferred.",
        ),
    )
