"""Trial-state phase rates for the forthcoming component/solid BDF coupling.

This internal kernel performs no integration and is not a public solver. The
caller must obtain saturation from the same trial chemistry, project phase
extents conservatively, and locate seed/depletion events in the integrator.
"""

from __future__ import annotations

import math
from fractions import Fraction

from .crevice_aqueous_component_ledger import ConservedAqueousComponent
from .crevice_competing_solid_equilibrium import CreviceCompetingSolidPhase
from .crevice_nucleation_kinetic_history import CreviceMolarNucleationLaw
from .multiphase_kinetic_ledger import SolidSaturationRateLaw, _derive_solid_saturation_rate


def trial_phase_rate_mol_s(
    *,
    solid_inventory_mol: float,
    solution_volume_m3: float,
    saturation_ratio: float,
    temperature_K: float,
    nucleation_law: CreviceMolarNucleationLaw,
    growth_law: SolidSaturationRateLaw,
    seeded_override: bool | None = None,
) -> tuple[float, str]:
    """Evaluate a signed extent rate without mutating seed history or clipping.

    Below the seed inventory threshold, supersaturated material uses the caller
    molar nucleation source. Undersaturated existing solid may dissolve even if
    below that threshold. At zero solid its dissolution rate is exactly zero.
    The rate does not limit consumption over a finite step: depletion and seed
    crossings must be treated as solver events by the integrating caller.
    """
    if nucleation_law.solid_species_id != growth_law.solid_species_id:
        raise ValueError("nucleation and growth phase identities must match")
    if not math.isfinite(solid_inventory_mol) or solid_inventory_mol < 0:
        raise ValueError("trial solid inventory must be finite and nonnegative")
    if not math.isfinite(solution_volume_m3) or solution_volume_m3 <= 0:
        raise ValueError("trial solution volume must be finite and positive")
    # This also checks saturation, temperature, declared thermal support and
    # Arrhenius representability, including in an unseeded trial state.
    derived = _derive_solid_saturation_rate(growth_law, saturation_ratio, temperature_K=temperature_K)
    threshold = float(nucleation_law.nucleated_inventory_threshold_mol_m3)
    # Division avoids underflow of volume * threshold for small cells.
    concentration = solid_inventory_mol / solution_volume_m3
    if seeded_override is not None and not isinstance(seeded_override, bool):
        raise ValueError("seed mode must be an explicit boolean or absent")
    seeded = concentration >= threshold if seeded_override is None else seeded_override
    if saturation_ratio < 1.0:
        volumetric_rate = float(derived["signed_extent_rate_mol_m3_s"]) if solid_inventory_mol else 0.0
        mode = "dissolution" if solid_inventory_mol else "no_solid_to_dissolve"
    elif seeded:
        volumetric_rate = float(derived["signed_extent_rate_mol_m3_s"])
        mode = "seeded_growth"
    else:
        driving = max(0.0, saturation_ratio / float(nucleation_law.critical_saturation_ratio) - 1.0)
        try:
            volumetric_rate = float(nucleation_law.source_rate_constant_mol_m3_s) * driving ** float(
                nucleation_law.supersaturation_order
            )
        except OverflowError as error:
            raise ArithmeticError("trial nucleation rate exceeds numeric support") from error
        if not math.isfinite(volumetric_rate) or volumetric_rate > float(
            nucleation_law.maximum_rate_mol_m3_s
        ):
            raise ArithmeticError("trial nucleation rate exceeds its declared bound")
        mode = "nucleation_source"
    rate = volumetric_rate * solution_volume_m3
    if not math.isfinite(rate) or (volumetric_rate != 0.0 and rate == 0.0):
        raise ArithmeticError("trial phase molar rate is not representable")
    return rate, mode


def trial_saturation_ratio(
    phase: CreviceCompetingSolidPhase, dimensionless_activity_by_species: dict[str, float]
) -> float:
    """Evaluate IAP/Ksp from the same trial's explicit dimensionless activities."""
    terms = []
    zero_activity = False
    for species, coefficient in phase.aqueous_reactant_stoichiometry.items():
        value = dimensionless_activity_by_species[species]
        if not math.isfinite(value) or value < 0:
            raise ValueError("trial activities must be finite and nonnegative")
        zero_activity |= value == 0
        if value:
            terms.append(float(coefficient) * math.log(value))
    if zero_activity:
        return 0.0
    log_ratio = math.fsum(terms + [-math.log(float(phase.dimensionless_solubility_product))])
    try:
        ratio = math.exp(log_ratio)
    except OverflowError as error:
        raise ArithmeticError("trial saturation exceeds numeric support") from error
    if not math.isfinite(ratio) or ratio == 0:
        raise ArithmeticError("nonzero trial saturation is not representable")
    return ratio


def phase_component_exchange_mol_s(
    phases: tuple[CreviceCompetingSolidPhase, ...],
    components: tuple[ConservedAqueousComponent, ...],
    phase_rate_mol_s: dict[str, float],
    charge_number_by_species: dict[str, int],
) -> tuple[dict[str, float], dict[str, dict[str, float]]]:
    """Project phase rates onto equal/opposite dissolved and solid component rates.

    Exact binary-input arithmetic combines competing phase contributions before
    rounding. Solid maps are component-equivalent rates, not phase mole rates.
    Elemental reaction validation is additionally required by the outer solver.
    """
    phase_ids = [phase.solid_species_id for phase in phases]
    component_ids = [component.component_id for component in components]
    if len(set(phase_ids)) != len(phase_ids) or len(set(component_ids)) != len(component_ids):
        raise ValueError("phase and component identities must be unique")
    if set(phase_ids) != set(phase_rate_mol_s):
        raise ValueError("phase rates must cover exactly the declared phases")
    totals = {key: Fraction(0) for key in component_ids}
    solid_rates = {}

    def represent(value):
        try:
            result = float(value)
        except OverflowError as error:
            raise ArithmeticError("component exchange exceeds numeric support") from error
        if not math.isfinite(result) or (value and result == 0):
            raise ArithmeticError("component exchange is not representable")
        return result

    for phase in phases:
        rate = phase_rate_mol_s[phase.solid_species_id]
        if not math.isfinite(rate):
            raise ValueError("phase rates must be finite")
        stoich = phase.aqueous_reactant_stoichiometry
        charge = sum(
            (
                Fraction(float(coefficient)) * charge_number_by_species[species]
                for species, coefficient in stoich.items()
            ),
            Fraction(0),
        )
        if charge:
            raise ValueError("neutral solid formation must conserve charge")
        projected = {}
        for component in components:
            extent = sum(
                (
                    Fraction(float(term.coefficient)) * Fraction(float(stoich.get(term.species_id, 0)))
                    for term in component.species_coefficients
                ),
                Fraction(0),
            )
            value = extent * Fraction(rate)
            totals[component.component_id] += value
            projected[component.component_id] = represent(value)
        solid_rates[phase.solid_species_id] = projected
    return {key: represent(-value) for key, value in totals.items()}, solid_rates
