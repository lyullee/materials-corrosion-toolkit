"""Common-datum aggregation of declared component pressure limits."""

from __future__ import annotations

import math
from fractions import Fraction as Rational
from typing import Literal

from pydantic import Field, model_validator

from ..contracts import Calculation, Contract, Evidence, Nonnegative, Positive
from ..registry import ModelSpec


class ComponentPressureLimit(Contract):
    component_id: str = Field(min_length=1)
    pressure_limit_Pa: Positive
    elevation_m: float
    condition_id: str = Field(min_length=1)
    temperature_K: Positive
    capacity_input_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    capacity_result_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    evidence: tuple[Evidence, ...] = Field(min_length=1)


class ComponentPressureReference(Contract):
    asset_id: str = Field(min_length=1)
    location_id: str = Field(min_length=1)
    physical_scope_id: str = Field(min_length=1)
    condition_id: str = Field(min_length=1)
    coordinate_frame_id: str = Field(min_length=1)
    pressure_basis: Literal["absolute", "gauge_common_reference"]
    common_pressure_reference_id: str = Field(min_length=1)
    reference_elevation_m: float
    uniform_density_kg_m3: Nonnegative
    gravity_m_s2: Nonnegative
    components: tuple[ComponentPressureLimit, ...] = Field(min_length=1)
    static_connected_uniform_fluid_reviewed: bool
    component_scope_complete_reviewed: bool
    common_pressure_and_elevation_reference_reviewed: bool
    component_capacity_and_condition_reviewed: bool

    @model_validator(mode="after")
    def identities(self):
        ids = [row.component_id for row in self.components]
        if len(ids) != len(set(ids)):
            raise ValueError("component identities must be unique")
        if any(row.condition_id != self.condition_id for row in self.components):
            raise ValueError("component conditions must match the requested scenario")
        return self


def component_pressure_reference(x: ComponentPressureReference) -> Calculation:
    if not all(
        (
            x.static_connected_uniform_fluid_reviewed,
            x.component_scope_complete_reviewed,
            x.common_pressure_and_elevation_reference_reviewed,
            x.component_capacity_and_condition_reviewed,
        )
    ):
        return Calculation(status="needs_data", values={})
    # Upward elevation decreases static pressure. Transport each local upper
    # limit to the same datum before taking the minimum; keep exact ties.
    offsets = [
        Rational(x.uniform_density_kg_m3)
        * Rational(x.gravity_m_s2)
        * (Rational(row.elevation_m) - Rational(x.reference_elevation_m))
        for row in x.components
    ]
    limits = [
        Rational(row.pressure_limit_Pa) + offset for row, offset in zip(x.components, offsets, strict=True)
    ]
    governing = min(limits)
    try:
        all_exact = offsets + limits
        converted = [float(value) for value in all_exact]
        if any(
            not math.isfinite(value) or (value == 0 and exact != 0)
            for exact, value in zip(all_exact, converted, strict=True)
        ):
            raise ArithmeticError
    except ArithmeticError:
        return Calculation(
            status="out_of_scope", values={}, notes=("Datum quantities exceed numeric support.",)
        )
    if x.pressure_basis == "absolute" and governing <= 0:
        return Calculation(
            status="out_of_scope",
            values={},
            notes=("No positive absolute reference pressure satisfies all supplied limits.",),
        )
    n = len(offsets)
    return Calculation(
        values=dict(
            component_ids=[row.component_id for row in x.components],
            hydrostatic_reference_offsets_Pa=converted[:n],
            reference_pressure_limits_Pa=converted[n:],
            governing_reference_pressure_limit_Pa=float(governing),
            governing_component_ids=[
                row.component_id
                for row, value in zip(x.components, limits, strict=True)
                if value == governing
            ],
            pressure_basis=x.pressure_basis,
            common_pressure_reference_id=x.common_pressure_reference_id,
            coordinate_frame_id=x.coordinate_frame_id,
            physical_scope_id=x.physical_scope_id,
            condition_id=x.condition_id,
            capacity_result_digests=[row.capacity_result_digest for row in x.components],
        ),
        notes=(
            "Declared upper limits only; no component capacity calculation, lower-pressure/cavitation check, code acceptance or failure probability.",
        ),
    )


def specifications():
    def context_check(x, context):
        if (x.asset_id, x.location_id) != (context.asset_id, context.location_id):
            raise ValueError("pressure aggregation asset/location must match run context")

    return (
        ModelSpec(
            "structural.component_pressure_reference",
            ComponentPressureReference,
            component_pressure_reference,
            {
                "hydrostatic_reference_offsets_Pa": "Pa",
                "reference_pressure_limits_Pa": "Pa",
                "governing_reference_pressure_limit_Pa": "Pa",
            },
            (
                "Static connected fluid, uniform caller density and gravity; upward-positive elevations in a reviewed common frame.",
                "All component upper limits and condition-specific capacity evidence are caller supplied; no code limits or capacity formulas are bundled.",
            ),
            ("hydrostatic_pressure_balance",),
            context_validator=context_check,
        ),
    )
