"""Explicitly calibrated stress-strain and strain-life relations."""

from __future__ import annotations

import math
from typing import Literal

from pydantic import Field, model_validator

from ..contracts import Calculation, Contract, Nonnegative, Positive
from ..registry import ModelSpec


class RambergOsgood(Contract):
    stress_amplitude_Pa: Nonnegative
    elastic_modulus_Pa: Positive
    cyclic_strength_coefficient_Pa: Positive
    cyclic_strain_hardening_exponent: Positive


def ramberg_osgood(x: RambergOsgood) -> Calculation:
    try:
        elastic = x.stress_amplitude_Pa / x.elastic_modulus_Pa
        plastic = (x.stress_amplitude_Pa / x.cyclic_strength_coefficient_Pa) ** (
            1 / x.cyclic_strain_hardening_exponent
        )
        values = dict(
            elastic_strain_amplitude=elastic,
            plastic_strain_amplitude=plastic,
            total_strain_amplitude=elastic + plastic,
        )
        if not all(math.isfinite(value) for value in values.values()):
            raise ArithmeticError("strain result exceeds finite numeric support")
    except (ArithmeticError, OverflowError, ZeroDivisionError):
        return Calculation(status="out_of_scope", values={}, notes=("Required Ramberg-Osgood outputs exceed finite numeric support.",))
    return Calculation(
        values=values
    )


class StrainLife(Contract):
    strain_amplitude: Positive
    elastic_modulus_Pa: Positive
    fatigue_strength_coefficient_Pa: Positive
    fatigue_strength_exponent: float = Field(lt=0)
    fatigue_ductility_coefficient: Positive
    fatigue_ductility_exponent: float = Field(lt=0)
    minimum_valid_cycles: Positive
    maximum_valid_cycles: Positive

    @model_validator(mode="after")
    def interval(self):
        if self.maximum_valid_cycles <= self.minimum_valid_cycles:
            raise ValueError("a nonempty calibrated cycle interval is required")
        return self


def strain_life(x: StrainLife) -> Calculation:
    from scipy.optimize import brentq

    def residual(log_cycles):
        log_reversals = math.log(2) + log_cycles
        return (
            x.fatigue_strength_coefficient_Pa
            / x.elastic_modulus_Pa
            * math.exp(x.fatigue_strength_exponent * log_reversals)
            + x.fatigue_ductility_coefficient * math.exp(x.fatigue_ductility_exponent * log_reversals)
            - x.strain_amplitude
        )

    low, high = math.log(x.minimum_valid_cycles), math.log(x.maximum_valid_cycles)
    low_residual, high_residual = residual(low), residual(high)
    # A mathematically exact root at a declared endpoint can round one ULP
    # outside the bracket. Treat only machine-scale endpoint residuals as the
    # endpoint itself; materially unsupported lives remain out of scope.
    low_amplitude = x.fatigue_strength_coefficient_Pa / x.elastic_modulus_Pa * math.exp(
        x.fatigue_strength_exponent * (math.log(2.0) + low)
    ) + x.fatigue_ductility_coefficient * math.exp(
        x.fatigue_ductility_exponent * (math.log(2.0) + low)
    )
    high_amplitude = x.fatigue_strength_coefficient_Pa / x.elastic_modulus_Pa * math.exp(
        x.fatigue_strength_exponent * (math.log(2.0) + high)
    ) + x.fatigue_ductility_coefficient * math.exp(
        x.fatigue_ductility_exponent * (math.log(2.0) + high)
    )
    low_tolerance = 16.0 * math.ulp(max(x.strain_amplitude, low_amplitude))
    high_tolerance = 16.0 * math.ulp(max(x.strain_amplitude, high_amplitude))
    if abs(low_residual) <= low_tolerance:
        cycles = x.minimum_valid_cycles
    elif abs(high_residual) <= high_tolerance:
        cycles = x.maximum_valid_cycles
    elif low_residual < 0 or high_residual > 0:
        return Calculation(
            status="out_of_scope",
            values={},
            notes=("The requested amplitude has no root inside the declared calibrated cycle interval.",),
        )
    else:
        cycles = math.exp(brentq(residual, low, high, xtol=1e-12))
    return Calculation(
        values=dict(cycles_to_failure=cycles, reversals_to_failure=2 * cycles),
        notes=(
            "Fully reversed constant-amplitude strain life; no automatic mean-stress, notch or environment correction.",
        ),
    )


class MorrowStrainLife(Contract):
    """Caller-calibrated Morrow mean-stress correction in uniaxial strain-life form."""

    strain_amplitude: Positive
    mean_stress_Pa: float
    elastic_modulus_Pa: Positive
    fatigue_strength_coefficient_Pa: Positive
    fatigue_strength_exponent: float = Field(lt=0)
    fatigue_ductility_coefficient: Positive
    fatigue_ductility_exponent: float = Field(lt=0)
    minimum_valid_cycles: Positive
    maximum_valid_cycles: Positive
    mean_stress_sign_convention: Literal["tension_positive"]
    coefficients_and_mean_stress_basis_reviewed: bool
    material_applicability_reviewed: bool

    @model_validator(mode="after")
    def interval(self):
        if self.maximum_valid_cycles <= self.minimum_valid_cycles:
            raise ValueError("a nonempty calibrated cycle interval is required")
        if not math.isfinite(self.mean_stress_Pa):
            raise ValueError("mean stress must be finite")
        return self


def morrow_strain_life(x: MorrowStrainLife) -> Calculation:
    """Solve the caller-calibrated Morrow strain-life equation within its cycle support."""
    from scipy.optimize import brentq

    if not x.coefficients_and_mean_stress_basis_reviewed or not x.material_applicability_reviewed:
        return Calculation(
            status="needs_data",
            values={"mean_stress_sign_convention": x.mean_stress_sign_convention},
            notes=("Coefficient, sign convention and material applicability review are required.",),
        )
    effective_strength = x.fatigue_strength_coefficient_Pa - x.mean_stress_Pa
    if not math.isfinite(effective_strength) or effective_strength <= 0:
        return Calculation(
            status="out_of_scope",
            values={"effective_fatigue_strength_coefficient_Pa": effective_strength},
            notes=(
                "The selected mean stress leaves no positive elastic fatigue-strength term in this formulation.",
            ),
        )

    log_elastic_coefficient = math.log(effective_strength) - math.log(x.elastic_modulus_Pa)
    log_ductility_coefficient = math.log(x.fatigue_ductility_coefficient)
    log_target = math.log(x.strain_amplitude)

    def log_strain_residual(log_cycles: float) -> float:
        log_reversals = math.log(2.0) + log_cycles
        elastic_term = log_elastic_coefficient + x.fatigue_strength_exponent * log_reversals
        plastic_term = log_ductility_coefficient + x.fatigue_ductility_exponent * log_reversals
        maximum = max(elastic_term, plastic_term)
        if maximum == math.inf:
            return math.inf
        if maximum == -math.inf:
            return -math.inf
        log_total = maximum + math.log(math.exp(elastic_term - maximum) + math.exp(plastic_term - maximum))
        return log_total - log_target

    low, high = math.log(x.minimum_valid_cycles), math.log(x.maximum_valid_cycles)
    if log_strain_residual(low) < 0 or log_strain_residual(high) > 0:
        return Calculation(
            status="out_of_scope",
            values={"effective_fatigue_strength_coefficient_Pa": effective_strength},
            notes=("The requested amplitude has no root inside the declared calibrated cycle interval.",),
        )
    cycles = math.exp(brentq(log_strain_residual, low, high, xtol=1e-12))
    return Calculation(
        values={
            "cycles_to_failure": cycles,
            "reversals_to_failure": 2.0 * cycles,
            "effective_fatigue_strength_coefficient_Pa": effective_strength,
            "mean_stress_Pa": x.mean_stress_Pa,
        },
        notes=(
            "Uses only the declared uniaxial Morrow mean-stress form and caller-supplied coefficients.",
            "The root is restricted to the declared calibration cycle interval; load history, multiaxiality, environment, notch gradients and acceptance are excluded.",
        ),
    )


class SWTStrainLife(Contract):
    """Caller-calibrated uniaxial Smith-Watson-Topper strain-life relation."""

    strain_amplitude: Positive
    maximum_stress_Pa: float
    elastic_modulus_Pa: Positive
    fatigue_strength_coefficient_Pa: Positive
    fatigue_strength_exponent: float = Field(lt=0)
    fatigue_ductility_coefficient: Positive
    fatigue_ductility_exponent: float = Field(lt=0)
    minimum_valid_cycles: Positive
    maximum_valid_cycles: Positive
    stress_and_strain_measurement_basis_reviewed: bool
    material_applicability_reviewed: bool

    @model_validator(mode="after")
    def interval(self):
        if self.maximum_valid_cycles <= self.minimum_valid_cycles:
            raise ValueError("a nonempty calibrated cycle interval is required")
        if not math.isfinite(self.maximum_stress_Pa):
            raise ValueError("maximum stress must be finite")
        return self


def swt_strain_life(x: SWTStrainLife) -> Calculation:
    """Solve the caller-calibrated SWT parameter relation within the cycle support."""
    from scipy.optimize import brentq

    if not x.stress_and_strain_measurement_basis_reviewed or not x.material_applicability_reviewed:
        return Calculation(
            status="needs_data",
            values={},
            notes=("Stress/strain basis and material applicability review are required.",),
        )
    if x.maximum_stress_Pa <= 0:
        return Calculation(
            status="out_of_scope",
            values={"maximum_stress_Pa": x.maximum_stress_Pa},
            notes=("The selected SWT formulation requires positive maximum normal stress.",),
        )

    log_strength = math.log(x.fatigue_strength_coefficient_Pa)
    log_elastic = 2.0 * log_strength - math.log(x.elastic_modulus_Pa)
    log_plastic = log_strength + math.log(x.fatigue_ductility_coefficient)
    log_target = math.log(x.maximum_stress_Pa) + math.log(x.strain_amplitude)

    def log_parameter_residual(log_cycles: float) -> float:
        log_reversals = math.log(2.0) + log_cycles
        elastic_term = log_elastic + 2.0 * x.fatigue_strength_exponent * log_reversals
        plastic_term = (
            log_plastic + (x.fatigue_strength_exponent + x.fatigue_ductility_exponent) * log_reversals
        )
        maximum = max(elastic_term, plastic_term)
        if maximum == math.inf:
            return math.inf
        if maximum == -math.inf:
            return -math.inf
        log_total = maximum + math.log(math.exp(elastic_term - maximum) + math.exp(plastic_term - maximum))
        return log_total - log_target

    low, high = math.log(x.minimum_valid_cycles), math.log(x.maximum_valid_cycles)
    if log_parameter_residual(low) < 0 or log_parameter_residual(high) > 0:
        return Calculation(
            status="out_of_scope",
            values={},
            notes=("The requested SWT parameter has no root inside the declared calibrated cycle interval.",),
        )
    cycles = math.exp(brentq(log_parameter_residual, low, high, xtol=1e-12))
    return Calculation(
        values={
            "cycles_to_failure": cycles,
            "reversals_to_failure": 2.0 * cycles,
            "swt_parameter_Pa": x.maximum_stress_Pa * x.strain_amplitude,
        },
        notes=(
            "Uses the caller-calibrated uniaxial SWT parameter and cycle support.",
            "The result does not infer maximum stress, multiaxial critical planes, variable-amplitude damage, environmental effects or acceptance.",
        ),
    )


class NortonCreep(Contract):
    stress_Pa: Nonnegative
    reference_stress_Pa: Positive
    rate_at_reference_stress_per_s: Nonnegative
    stress_exponent: Positive
    exposure_s: Nonnegative


def norton_creep(x: NortonCreep) -> Calculation:
    try:
        rate = x.rate_at_reference_stress_per_s * (x.stress_Pa / x.reference_stress_Pa) ** x.stress_exponent
        strain = rate * x.exposure_s
        if not math.isfinite(rate) or not math.isfinite(strain):
            raise ArithmeticError("creep result exceeds finite numeric support")
    except (ArithmeticError, OverflowError, ZeroDivisionError):
        return Calculation(status="out_of_scope", values={}, notes=("Required Norton creep outputs exceed finite numeric support.",))
    return Calculation(
        values=dict(steady_creep_strain_rate_per_s=rate, steady_creep_strain=strain),
        notes=(
            "Fixed-temperature secondary creep only; primary and tertiary stages, stress redistribution and rupture are excluded.",
        ),
    )


def specifications():
    return [
        ModelSpec(
            "materials.ramberg_osgood",
            RambergOsgood,
            ramberg_osgood,
            {"elastic_strain_amplitude": "1", "plastic_strain_amplitude": "1", "total_strain_amplitude": "1"},
            ("Stabilized uniaxial cyclic amplitude relation with caller-calibrated K-prime and n-prime.",),
            ("cyclic_ramberg_osgood",),
        ),
        ModelSpec(
            "fatigue.strain_life",
            StrainLife,
            strain_life,
            {"cycles_to_failure": "cycle", "reversals_to_failure": "reversal"},
            (
                "Combined Basquin and Coffin-Manson relation; two reversals per cycle and an explicit calibration interval.",
            ),
            ("comsol_strain_life",),
        ),
        ModelSpec(
            "fatigue.morrow_strain_life",
            MorrowStrainLife,
            morrow_strain_life,
            {
                "cycles_to_failure": "cycle",
                "reversals_to_failure": "reversal",
                "effective_fatigue_strength_coefficient_Pa": "Pa",
                "mean_stress_Pa": "Pa",
            },
            (
                "Caller-calibrated uniaxial Morrow mean-stress correction to the elastic Basquin term of a strain-life relation.",
                "Tension-positive mean stress, material applicability and cycle-support reviews are explicit caller inputs.",
                "No variable-amplitude counting, multiaxial correction, notch solution, environment correction or code acceptance is inferred.",
            ),
            ("morrow_mean_stress_strain_life",),
        ),
        ModelSpec(
            "fatigue.swt_strain_life",
            SWTStrainLife,
            swt_strain_life,
            {
                "cycles_to_failure": "cycle",
                "reversals_to_failure": "reversal",
                "swt_parameter_Pa": "Pa",
            },
            (
                "Caller-calibrated uniaxial Smith-Watson-Topper stress-strain parameter for a declared cycle-life interval.",
                "Positive maximum normal stress, strain amplitude, material applicability and measurement basis are explicit inputs.",
                "No multiaxial critical-plane search, load-history counting, environmental correction or code acceptance is inferred.",
            ),
            ("smith_watson_topper_1970",),
        ),
        ModelSpec(
            "creep.norton",
            NortonCreep,
            norton_creep,
            {"steady_creep_strain_rate_per_s": "1/s", "steady_creep_strain": "1"},
            (
                "Isothermal, constant-load empirical steady-creep power law with a dimensionless stress ratio.",
            ),
            ("norton_power_law",),
        ),
    ]
