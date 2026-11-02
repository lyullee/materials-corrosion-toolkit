"""Caller-calibrated signed Butler-Volmer reaction rate and stoichiometric flux mapping."""

import math

from pydantic import Field

from .contracts import Contract, Nonnegative, Positive


class ButlerVolmerReaction(Contract):
    reaction_id: str = Field(min_length=1)
    calibration_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    exchange_current_density_A_m2: Nonnegative
    electron_count: int = Field(gt=0)
    anodic_transfer_coefficient: float = Field(gt=0, le=1)
    cathodic_transfer_coefficient: float = Field(gt=0, le=1)
    equilibrium_potential_V: float
    temperature_K: Positive
    minimum_overpotential_V: float
    maximum_overpotential_V: float
    stoichiometric_species_coefficients: dict[str, float]
    calibration_and_reaction_direction_reviewed: bool


def electrode_reaction_flux(request: ButlerVolmerReaction, metal_minus_solution_potential_V: float) -> dict:
    if isinstance(metal_minus_solution_potential_V, bool) or not math.isfinite(
        metal_minus_solution_potential_V
    ):
        raise ValueError("electrode potential difference must be finite")
    if request.maximum_overpotential_V < request.minimum_overpotential_V:
        raise ValueError("overpotential support must be ordered")
    if not request.calibration_and_reaction_direction_reviewed:
        return dict(status="needs_data")
    eta = metal_minus_solution_potential_V - request.equilibrium_potential_V
    if not request.minimum_overpotential_V <= eta <= request.maximum_overpotential_V:
        return dict(status="out_of_scope")
    scale = request.electron_count * 96485.33212 / (8.31446261815324 * request.temperature_K)
    try:
        if request.exchange_current_density_A_m2 == 0:
            anodic = cathodic = current = 0.0
        else:
            log_exchange = math.log(request.exchange_current_density_A_m2)
            anodic = math.exp(log_exchange + request.anodic_transfer_coefficient * scale * eta)
            cathodic = math.exp(log_exchange - request.cathodic_transfer_coefficient * scale * eta)
            difference = (
                (request.anodic_transfer_coefficient + request.cathodic_transfer_coefficient) * scale * eta
            )
            current = (
                anodic * (-math.expm1(-difference)) if difference >= 0 else cathodic * math.expm1(difference)
            )
    except OverflowError:
        return dict(status="out_of_scope", reason="Current exceeds numeric range")
    rate = current / (request.electron_count * 96485.33212)
    fluxes = {
        species: coefficient * rate
        for species, coefficient in request.stoichiometric_species_coefficients.items()
    }
    if not all(math.isfinite(value) for value in (anodic, cathodic, current, rate, *fluxes.values())):
        return dict(status="out_of_scope", reason="Current or species flux exceeds numeric range")
    return dict(
        status="computed",
        reaction_id=request.reaction_id,
        equilibrium_potential_V=request.equilibrium_potential_V,
        overpotential_V=eta,
        temperature_K=request.temperature_K,
        signed_current_density_A_m2=current,
        gross_anodic_current_density_A_m2=anodic,
        gross_cathodic_current_density_A_m2=cathodic,
        signed_reaction_extent_mol_m2_s=rate,
        inward_species_flux_mol_m2_s=fluxes,
        basis="Positive current follows the caller anodic reaction direction; no exchange current or equilibrium potential is inferred from CO2 pressure.",
    )


def solve_electrode_mixed_potential(reactions: tuple[ButlerVolmerReaction, ...]) -> dict:
    """Find zero net signed current only within the common calibrated potential interval."""
    if not reactions or len({row.reaction_id for row in reactions}) != len(reactions):
        raise ValueError("mixed-potential reactions must have unique IDs")
    if any(not row.calibration_and_reaction_direction_reviewed for row in reactions):
        return dict(status="needs_data")
    low = max(row.equilibrium_potential_V + row.minimum_overpotential_V for row in reactions)
    high = min(row.equilibrium_potential_V + row.maximum_overpotential_V for row in reactions)
    if low >= high:
        return dict(status="out_of_scope", reason="No common calibrated potential interval")
    def net(potential):
        values = [electrode_reaction_flux(row, potential) for row in reactions]
        if any(value["status"] != "computed" for value in values):
            raise ValueError("reaction left its calibrated potential support")
        return math.fsum(value["signed_current_density_A_m2"] for value in values)

    left, right = net(low), net(high)
    if left > 0 or right < 0:
        return dict(status="out_of_scope", reason="Zero net current is not bracketed")
    if left == 0:
        potential = low
    elif right == 0:
        potential = high
    else:
        # Monotone Butler-Volmer branches permit a bounded deterministic bisection.
        # This avoids making SciPy a runtime requirement for this base electrochemical API.
        lo, hi = low, high
        potential = (lo + hi) / 2.0
        for _ in range(200):
            potential = lo + (hi - lo) / 2.0
            residual = net(potential)
            if residual == 0.0 or hi - lo <= 1e-12:
                break
            if residual < 0.0:
                lo = potential
            else:
                hi = potential
    partial = [electrode_reaction_flux(row, potential) for row in reactions]
    if all(row.exchange_current_density_A_m2 == 0 for row in reactions):
        return dict(status="needs_data", reason="All currents vanish; mixed potential is unidentifiable")
    return dict(
        status="computed",
        metal_minus_solution_potential_V=potential,
        net_current_density_A_m2=net(potential),
        partial_reactions=partial,
    )
