"""Integrate caller-qualified tangent expansion tables without secant/tangent substitution."""

from __future__ import annotations

import math
from bisect import bisect_right
from fractions import Fraction
from typing import Literal

from pydantic import Field, model_validator

from .contracts import Contract, Evidence, Positive, canonical_digest


class TangentExpansionTable(Contract):
    table_id: str = Field(min_length=1)
    material_condition_id: str = Field(min_length=1)
    direction_id: str = Field(min_length=1)
    temperature_K: tuple[Positive, ...] = Field(min_length=2)
    tangent_alpha_1_K: tuple[float, ...] = Field(min_length=2)
    evidence: tuple[Evidence, ...] = Field(min_length=1)
    coefficient_definition: Literal["d_log_length_d_temperature"]
    applicability_reviewed: bool

    @model_validator(mode="after")
    def ordered(self):
        if len(self.temperature_K) != len(self.tangent_alpha_1_K):
            raise ValueError("temperature and tangent expansion arrays must align")
        if any(b <= a for a, b in zip(self.temperature_K[:-1], self.temperature_K[1:], strict=True)):
            raise ValueError("expansion temperatures must increase strictly")
        return self


class ThermalExpansionResult(Contract):
    schema_version: Literal["matintegrity.thermal_expansion.v1"] = "matintegrity.thermal_expansion.v1"
    table_id: str
    table_sha256: str
    start_temperature_K: Positive
    end_temperature_K: Positive
    status: Literal["computed", "needs_data", "out_of_scope"]
    logarithmic_length_change: float | None
    engineering_length_change: float | None
    notes: tuple[str, ...]


def integrate_tangent_expansion(
    table: TangentExpansionTable, start_temperature_K: float, end_temperature_K: float
) -> ThermalExpansionResult:
    """Integrate piecewise-linear d(log L)/dT and map the result with expm1."""
    if any(
        isinstance(value, bool) or not math.isfinite(value) or value <= 0
        for value in (start_temperature_K, end_temperature_K)
    ):
        raise ValueError("expansion endpoints must be finite positive kelvin")
    base = dict(
        table_id=table.table_id,
        table_sha256=canonical_digest(table.model_dump(mode="json")),
        start_temperature_K=start_temperature_K,
        end_temperature_K=end_temperature_K,
        logarithmic_length_change=None,
        engineering_length_change=None,
    )
    if not table.applicability_reviewed:
        return ThermalExpansionResult(
            **base,
            status="needs_data",
            notes=("Material, direction and coefficient definition require review.",),
        )
    low, high = sorted((start_temperature_K, end_temperature_K))
    xs, ys = table.temperature_K, table.tangent_alpha_1_K
    if low < xs[0] or high > xs[-1]:
        return ThermalExpansionResult(
            **base, status="out_of_scope", notes=("Endpoint temperature exceeds table support.",)
        )
    knots = [low, *(value for value in xs if low < value < high), high]

    def alpha(value):
        index = min(bisect_right(xs, value) - 1, len(xs) - 2)
        fraction = (Fraction(value) - Fraction(xs[index])) / (Fraction(xs[index + 1]) - Fraction(xs[index]))
        return (1 - fraction) * Fraction(ys[index]) + fraction * Fraction(ys[index + 1])

    exact_change = sum(
        (
            (Fraction(b) - Fraction(a)) * (alpha(a) + alpha(b)) / 2
            for a, b in zip(knots[:-1], knots[1:], strict=True)
        ),
        Fraction(0),
    )
    if end_temperature_K < start_temperature_K:
        exact_change = -exact_change
    try:
        change = float(exact_change)
        if exact_change and change == 0:
            raise OverflowError("Nonzero integrated strain underflows.")
        engineering = math.expm1(change)
        if engineering == -1:
            raise OverflowError("Positive final length is not representable relative to its reference.")
    except OverflowError:
        return ThermalExpansionResult(
            **base, status="out_of_scope", notes=("Integrated length change exceeds numeric range.",)
        )
    base.update(logarithmic_length_change=change, engineering_length_change=engineering)
    return ThermalExpansionResult(
        **base,
        status="computed",
        notes=(
            "Free directional expansion only; restraint stress and phase-change discontinuities require separate models.",
        ),
    )


def differential_thermal_expansion(
    first: TangentExpansionTable,
    second: TangentExpansionTable,
    start_temperature_K: float,
    end_temperature_K: float,
) -> tuple[ThermalExpansionResult, ThermalExpansionResult, float | None]:
    """Return both supported free-expansion results and their engineering-strain difference."""
    a = integrate_tangent_expansion(first, start_temperature_K, end_temperature_K)
    b = integrate_tangent_expansion(second, start_temperature_K, end_temperature_K)
    difference = (
        a.engineering_length_change - b.engineering_length_change
        if a.status == b.status == "computed"
        else None
    )
    return a, b, difference
