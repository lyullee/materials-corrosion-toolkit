"""Caller-calibrated composition/temperature correlation with explicit support."""

import math
from fractions import Fraction as Rational
from typing import Literal

from pydantic import Field, model_validator

from ..contracts import Calculation, Contract, Nonnegative
from ..registry import ModelSpec
from .engineering_correlations import SOURCE_ID, CompositionIndexRecipe, _composition_recipe_exact_arithmetic


class CompositionSupportRange(Contract):
    support_id: str = Field(min_length=1)
    element_ids: tuple[str, ...] = Field(min_length=1, max_length=60)
    minimum_sum: Nonnegative
    maximum_sum: Nonnegative

    @model_validator(mode="after")
    def ordered_unique(self):
        if len(set(self.element_ids)) != len(self.element_ids) or any(
            not x.strip() for x in self.element_ids
        ):
            raise ValueError("support group elements must be unique and nonblank")
        if self.minimum_sum > self.maximum_sum:
            raise ValueError("composition support sums must be ordered")
        return self


class CompositionTemperatureCorrelation(CompositionIndexRecipe):
    output_unit: Literal["K", "degC", "degF"]
    material_condition_id: str = Field(min_length=1)
    temperature_quantity_id: str = Field(min_length=1)
    calibration_population_id: str = Field(min_length=1)
    correlation_revision_id: str = Field(min_length=1)
    composition_support: tuple[CompositionSupportRange, ...] = Field(min_length=1, max_length=100)
    correlation_and_composition_support_reviewed: bool

    @model_validator(mode="after")
    def support_members(self):
        if len({x.support_id for x in self.composition_support}) != len(self.composition_support):
            raise ValueError("composition support identities must be unique")
        supported = {key for row in self.composition_support for key in row.element_ids}
        required = {factor.element_id for term in self.terms for factor in term.factors}
        if not supported <= set(self.chemistry) or not required <= supported:
            raise ValueError("support groups require measured chemistry and must cover every recipe element")
        return self


def composition_temperature_correlation(x: CompositionTemperatureCorrelation) -> Calculation:
    base = dict(
        index_id=x.index_id,
        material_condition_id=x.material_condition_id,
        temperature_quantity_id=x.temperature_quantity_id,
        calibration_population_id=x.calibration_population_id,
        correlation_revision_id=x.correlation_revision_id,
        record_sha256=x.basis.record_sha256,
    )
    if not x.correlation_and_composition_support_reviewed:
        return Calculation(
            status="needs_data",
            values=base,
            notes=("Correlation and composition support require explicit review.",),
        )
    scales = {"mass_fraction": 1, "mass_percent": 100, "mass_ppm": 1_000_000}
    multiplier = Rational(scales[x.recipe_mass_basis], scales[x.input_mass_basis])
    assay = {key: Rational(value) * multiplier for key, value in x.chemistry.items()}
    outside = []
    for support in x.composition_support:
        total = sum((assay[key] for key in support.element_ids), Rational(0))
        if not Rational(support.minimum_sum) <= total <= Rational(support.maximum_sum):
            outside.append(support.support_id)
    if outside:
        return Calculation(
            status="out_of_scope",
            values=base | {"outside_support_ids": outside},
            notes=("No composition extrapolation or default missing constituent is applied.",),
        )
    try:
        converted, _, contributions, value, exact = _composition_recipe_exact_arithmetic(
            x, {}, return_exact=True
        )
        # Celsius and Fahrenheit origins are exact decimal unit definitions.
        kelvin = (
            exact
            if x.output_unit == "K"
            else exact + Rational(27315, 100)
            if x.output_unit == "degC"
            else (exact + Rational(45967, 100)) * Rational(5, 9)
        )
        temperature = float(kelvin)
        if kelvin <= 0 or not math.isfinite(temperature) or temperature <= 0:
            raise ArithmeticError
    except (ArithmeticError, ValueError):
        return Calculation(
            status="out_of_scope",
            values=base | {"reason": "temperature correlation exceeds positive finite support"},
        )
    return Calculation(
        values=base
        | dict(
            predicted_temperature_K=temperature,
            recipe_temperature_value=value,
            recipe_temperature_unit=x.output_unit,
            recipe_mass_basis=x.recipe_mass_basis,
            converted_assay=converted,
            term_contributions=contributions,
        ),
        notes=(
            "Caller coefficients, thermal endpoint and calibration population only; support applies to single constituents or explicit sums in the recipe mass basis.",
            "A correlation prediction is not an observed transformation temperature, transformed phase fraction, heat-treatment outcome, uncertainty interval or material acceptance.",
        ),
    )


def specifications():
    return [
        ModelSpec(
            "materials.composition_temperature_correlation",
            CompositionTemperatureCorrelation,
            composition_temperature_correlation,
            {"predicted_temperature_K": "K", "recipe_temperature_value": "caller_declared_temperature_unit"},
            (
                "Caller composition support, coefficients, temperature units, material condition and calibration population are explicit.",
            ),
            (SOURCE_ID,),
            version="1.0.1",
            qualification="user_model",
        )
    ]
