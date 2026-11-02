"""Invert a caller-authorized rational pressure/thickness relation."""

from __future__ import annotations

import math
from fractions import Fraction as Rational
from typing import Literal

from pydantic import Field, model_validator

from ..contracts import Calculation, Nonnegative, Positive
from ..registry import ModelSpec
from .engineering_correlations import CorrelationRequest


class DeclaredPressureThicknessRelation(CorrelationRequest):
    asset_id: str = Field(min_length=1)
    location_id: str = Field(min_length=1)
    component_id: str = Field(min_length=1)
    geometry_definition_id: str = Field(min_length=1)
    material_condition_id: str = Field(min_length=1)
    temperature_K: Positive
    coefficient_definition_id: str = Field(min_length=1)
    dimension_convention_id: str = Field(min_length=1)
    direction: Literal["pressure_from_thickness", "thickness_from_pressure"]
    allowable_stress_Pa: Positive
    joint_efficiency: float = Field(gt=0, le=1)
    numerator_factor: Positive
    geometry_length_m: Positive
    thickness_coefficient: float
    effective_thickness_m: Positive | None = None
    pressure_difference_Pa: Positive | None = None
    minimum_supported_thickness_m: Positive
    maximum_supported_thickness_m: Positive
    minimum_supported_pressure_Pa: Nonnegative
    maximum_supported_pressure_Pa: Positive
    geometry_material_temperature_and_coefficient_scope_reviewed: bool
    effective_thickness_and_allowances_reviewed: bool
    pressure_difference_and_load_scope_reviewed: bool

    @model_validator(mode="after")
    def domain(self):
        if self.maximum_supported_thickness_m < self.minimum_supported_thickness_m:
            raise ValueError("thickness support must be ordered")
        if self.maximum_supported_pressure_Pa < self.minimum_supported_pressure_Pa:
            raise ValueError("pressure support must be ordered")
        if self.direction == "pressure_from_thickness":
            if self.effective_thickness_m is None or self.pressure_difference_Pa is not None:
                raise ValueError("pressure evaluation requires only effective thickness")
        elif self.pressure_difference_Pa is None or self.effective_thickness_m is not None:
            raise ValueError("thickness evaluation requires only pressure difference")
        return self


def declared_pressure_thickness_relation(x: DeclaredPressureThicknessRelation) -> Calculation:
    if not all(
        (
            x.geometry_material_temperature_and_coefficient_scope_reviewed,
            x.effective_thickness_and_allowances_reviewed,
            x.pressure_difference_and_load_scope_reviewed,
        )
    ):
        return Calculation(status="needs_data", values={})
    strength = Rational(x.numerator_factor) * Rational(x.allowable_stress_Pa) * Rational(x.joint_efficiency)
    length = Rational(x.geometry_length_m)
    coefficient = Rational(x.thickness_coefficient)
    if x.direction == "pressure_from_thickness":
        thickness = Rational(x.effective_thickness_m)
        denominator = length + coefficient * thickness
        if denominator <= 0:
            return Calculation(status="out_of_scope", values={}, notes=("Nonpositive relation denominator.",))
        pressure = strength * thickness / denominator
    else:
        pressure = Rational(x.pressure_difference_Pa)
        denominator = strength - coefficient * pressure
        if denominator <= 0:
            return Calculation(
                status="out_of_scope", values={}, notes=("No positive supported inverse thickness.",)
            )
        thickness = pressure * length / denominator
    if not (
        Rational(x.minimum_supported_thickness_m) <= thickness <= Rational(x.maximum_supported_thickness_m)
        and Rational(x.minimum_supported_pressure_Pa) <= pressure <= Rational(x.maximum_supported_pressure_Pa)
    ):
        return Calculation(
            status="out_of_scope",
            values={},
            notes=("Input or derived value is outside declared relation support.",),
        )
    try:
        t, p = float(thickness), float(pressure)
        if not all(math.isfinite(v) and v > 0 for v in (t, p)):
            raise ArithmeticError
    except ArithmeticError:
        return Calculation(
            status="out_of_scope", values={}, notes=("Pressure or thickness exceeds numeric support.",)
        )
    return Calculation(
        values=dict(
            effective_thickness_m=t,
            pressure_difference_Pa=p,
            component_id=x.component_id,
            geometry_definition_id=x.geometry_definition_id,
            material_condition_id=x.material_condition_id,
            temperature_K=x.temperature_K,
            coefficient_definition_id=x.coefficient_definition_id,
            dimension_convention_id=x.dimension_convention_id,
            record_sha256=x.basis.record_sha256,
        ),
        notes=(
            "Caller relation P = k*S*E*t/(L+c*t) only. No standard formula selection, allowance addition, other-load check, external-pressure stability, certification or acceptance.",
        ),
    )


def specifications():
    def context_check(x, context):
        if (x.asset_id, x.location_id) != (context.asset_id, context.location_id):
            raise ValueError("pressure relation asset/location must match run context")

    return (
        ModelSpec(
            "structural.declared_pressure_thickness_relation",
            DeclaredPressureThicknessRelation,
            declared_pressure_thickness_relation,
            {"effective_thickness_m": "m", "pressure_difference_Pa": "Pa", "temperature_K": "K"},
            (
                "Caller supplies reviewed dimension conventions, signed thickness coefficient, numerator factor, allowable stress, joint efficiency and pressure/thickness support.",
                "Effective thickness and pressure difference are explicit; no code coefficient, geometry default or qualification is inferred.",
            ),
            ("caller_declared_pressure_thickness_relation",),
            context_validator=context_check,
            qualification="user_model",
        ),
    )
