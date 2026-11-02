"""Authored regression checks for the caller-calibrated Morrow relation; not run locally."""

import math

import pytest

from matintegrity.models.constitutive import (
    MorrowStrainLife,
    SWTStrainLife,
    morrow_strain_life,
    swt_strain_life,
)


def _case(**updates):
    values = {
        "strain_amplitude": 0.004,
        "mean_stress_Pa": 0.0,
        "elastic_modulus_Pa": 200e9,
        "fatigue_strength_coefficient_Pa": 1000e6,
        "fatigue_strength_exponent": -0.1,
        "fatigue_ductility_coefficient": 0.5,
        "fatigue_ductility_exponent": -0.5,
        "minimum_valid_cycles": 1.0,
        "maximum_valid_cycles": 1e9,
        "mean_stress_sign_convention": "tension_positive",
        "coefficients_and_mean_stress_basis_reviewed": True,
        "material_applicability_reviewed": True,
    }
    values.update(updates)
    return MorrowStrainLife(**values)


def test_zero_mean_stress_recovers_unmodified_strain_life_equation():
    result = morrow_strain_life(_case())
    assert result.status == "computed"
    cycles = result.values["cycles_to_failure"]
    reversals = 2.0 * cycles
    predicted = 1000e6 / 200e9 * reversals**-0.1 + 0.5 * reversals**-0.5
    assert predicted == pytest.approx(0.004, rel=1e-10)


def test_tensile_and_compressive_mean_stress_shift_life_in_expected_direction():
    zero = morrow_strain_life(_case()).values["cycles_to_failure"]
    tension = morrow_strain_life(_case(mean_stress_Pa=100e6)).values["cycles_to_failure"]
    compression = morrow_strain_life(_case(mean_stress_Pa=-100e6)).values["cycles_to_failure"]
    assert tension < zero < compression


def test_review_gate_and_cycle_support_are_enforced():
    withheld = morrow_strain_life(_case(material_applicability_reviewed=False))
    outside = morrow_strain_life(_case(minimum_valid_cycles=1e8, maximum_valid_cycles=1e9))
    invalid_elastic_term = morrow_strain_life(_case(mean_stress_Pa=1100e6))
    assert withheld.status == "needs_data"
    assert outside.status == "out_of_scope"
    assert invalid_elastic_term.status == "out_of_scope"


def test_logarithmic_root_remains_finite_for_very_small_positive_strain():
    result = morrow_strain_life(_case(strain_amplitude=6e-4))
    assert result.status == "computed"
    assert math.isfinite(result.values["cycles_to_failure"])


def test_swt_solution_closes_its_stress_strain_life_parameter():
    request = SWTStrainLife(
        strain_amplitude=0.004,
        maximum_stress_Pa=350e6,
        elastic_modulus_Pa=200e9,
        fatigue_strength_coefficient_Pa=1000e6,
        fatigue_strength_exponent=-0.1,
        fatigue_ductility_coefficient=0.5,
        fatigue_ductility_exponent=-0.5,
        minimum_valid_cycles=1.0,
        maximum_valid_cycles=1e9,
        stress_and_strain_measurement_basis_reviewed=True,
        material_applicability_reviewed=True,
    )
    result = swt_strain_life(request)
    reversals = 2.0 * result.values["cycles_to_failure"]
    predicted = request.fatigue_strength_coefficient_Pa**2 / request.elastic_modulus_Pa * reversals ** (
        2 * request.fatigue_strength_exponent
    ) + request.fatigue_strength_coefficient_Pa * request.fatigue_ductility_coefficient * reversals ** (
        request.fatigue_strength_exponent + request.fatigue_ductility_exponent
    )
    assert result.status == "computed"
    assert predicted == pytest.approx(request.maximum_stress_Pa * request.strain_amplitude, rel=1e-10)


def test_swt_requires_positive_peak_stress_and_review():
    base = {
        "strain_amplitude": 0.004,
        "maximum_stress_Pa": 300e6,
        "elastic_modulus_Pa": 200e9,
        "fatigue_strength_coefficient_Pa": 1000e6,
        "fatigue_strength_exponent": -0.1,
        "fatigue_ductility_coefficient": 0.5,
        "fatigue_ductility_exponent": -0.5,
        "minimum_valid_cycles": 1.0,
        "maximum_valid_cycles": 1e9,
        "stress_and_strain_measurement_basis_reviewed": True,
        "material_applicability_reviewed": True,
    }
    negative_peak = SWTStrainLife(**(base | {"maximum_stress_Pa": -100e6}))
    missing_review = SWTStrainLife(**(base | {"material_applicability_reviewed": False}))
    assert swt_strain_life(negative_peak).status == "out_of_scope"
    assert swt_strain_life(missing_review).status == "needs_data"
