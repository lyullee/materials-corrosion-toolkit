"""Single neutral-solid equilibrium with explicit fixed activity coefficients.

The independent extent consumes nu_i aqueous moles for one mole of solid.
Only this declared reaction changes composition; no speciation is inferred.
"""

import math

from pydantic import Field, model_validator

from .contracts import Contract, Nonnegative, Positive, canonical_digest


class PrecipitatingAqueousSpecies(Contract):
    species_id: str = Field(min_length=1)
    stoichiometric_moles_per_solid_mole: Positive
    initial_concentration_mol_m3: Nonnegative
    activity_reference_concentration_mol_m3: Positive
    activity_coefficient: Positive
    charge_number: int
    elemental_composition: dict[str, int]

    @model_validator(mode="after")
    def composition(self):
        if not self.elemental_composition or any(value < 0 for value in self.elemental_composition.values()):
            raise ValueError("species requires explicit nonnegative elemental composition")
        if not any(self.elemental_composition.values()):
            raise ValueError("species elemental composition cannot be all zero")
        return self


class SingleSolidEquilibrium(Contract):
    equilibrium_id: str = Field(min_length=1)
    solid_species_id: str = Field(min_length=1)
    solid_elemental_composition: dict[str, int]
    aqueous_species: tuple[PrecipitatingAqueousSpecies, ...] = Field(min_length=1)
    initial_solid_moles_per_solution_volume_mol_m3: Nonnegative
    dimensionless_solubility_product: Positive
    temperature_K: Positive
    standard_state_id: str = Field(min_length=1)
    equilibrium_constant_source_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    maximum_absolute_log_saturation_residual: float = Field(default=1e-8, gt=0, le=0.01)
    absolute_extent_balance_tolerance_mol_m3: Positive = 1e-10
    relative_extent_balance_tolerance: float = Field(default=1e-10, gt=0, le=0.01)
    single_neutral_pure_solid_and_fixed_volume_reviewed: bool
    fixed_activity_coefficients_and_standard_states_reviewed: bool
    equilibrium_constant_temperature_and_computational_use_reviewed: bool

    @model_validator(mode="after")
    def conservation(self):
        if len({row.species_id for row in self.aqueous_species}) != len(self.aqueous_species):
            raise ValueError("precipitating aqueous species IDs must be unique")
        if self.solid_species_id in {row.species_id for row in self.aqueous_species}:
            raise ValueError("solid and aqueous species identities must differ")
        if not self.solid_elemental_composition or any(
            value < 0 for value in self.solid_elemental_composition.values()
        ):
            raise ValueError("solid requires nonnegative explicit elemental composition")
        charge = math.fsum(
            row.charge_number * row.stoichiometric_moles_per_solid_mole for row in self.aqueous_species
        )
        if not math.isfinite(charge) or not math.isclose(charge, 0.0, abs_tol=1e-12):
            raise ValueError("declared solid reaction must conserve charge for a neutral solid")
        elements = set(self.solid_elemental_composition)
        for row in self.aqueous_species:
            elements.update(row.elemental_composition)
        for element in elements:
            aqueous = math.fsum(
                row.elemental_composition.get(element, 0) * row.stoichiometric_moles_per_solid_mole
                for row in self.aqueous_species
            )
            solid = self.solid_elemental_composition.get(element, 0)
            if not math.isfinite(aqueous) or not math.isclose(aqueous, solid, rel_tol=1e-12, abs_tol=1e-12):
                raise ValueError("solid precipitation stoichiometry must conserve each declared element")
        if not any(self.solid_elemental_composition.values()):
            raise ValueError("solid elemental composition cannot be all zero")
        return self


def evaluate_single_solid_equilibrium(request: SingleSolidEquilibrium) -> dict:
    base = dict(
        equilibrium_id=request.equilibrium_id,
        solid_species_id=request.solid_species_id,
        status="needs_data",
        input_sha256=canonical_digest(request.model_dump(mode="json")),
        equilibrium_constant_source_sha256=request.equilibrium_constant_source_sha256,
        temperature_K=request.temperature_K,
        standard_state_id=request.standard_state_id,
    )
    if not (
        request.single_neutral_pure_solid_and_fixed_volume_reviewed
        and request.fixed_activity_coefficients_and_standard_states_reviewed
        and request.equilibrium_constant_temperature_and_computational_use_reviewed
    ):
        return base
    species = request.aqueous_species
    log_k = math.log(request.dimensionless_solubility_product)

    def log_product(extent):
        terms = []
        for row in species:
            concentration = (
                row.initial_concentration_mol_m3 - row.stoichiometric_moles_per_solid_mole * extent
            )
            if concentration <= 0:
                return -math.inf
            if not math.isfinite(concentration):
                raise ArithmeticError("Aqueous concentration exceeds numeric range")
            terms.append(
                row.stoichiometric_moles_per_solid_mole
                * (
                    math.log(row.activity_coefficient)
                    + math.log(concentration)
                    - math.log(row.activity_reference_concentration_mol_m3)
                )
            )
        value = math.fsum(terms)
        if not math.isfinite(value):
            raise ArithmeticError("Ion activity product exceeds numeric range")
        return value

    solid0 = request.initial_solid_moles_per_solution_volume_mol_m3
    extent = 0.0
    bound = 0.0
    direction = 0.0
    saturated = False
    try:
        initial_log_q = log_product(0.0)
        if initial_log_q > log_k:
            direction = 1.0
            bound = min(
                row.initial_concentration_mol_m3 / row.stoichiometric_moles_per_solid_mole for row in species
            )
            saturated = True
        elif initial_log_q < log_k and solid0 > 0:
            exhausted_log_q = log_product(-solid0)
            if exhausted_log_q <= log_k:
                extent = -solid0
                saturated = exhausted_log_q == log_k
            else:
                direction, bound, saturated = -1.0, solid0, True
        elif initial_log_q == log_k:
            saturated = True
        if direction:
            if not math.isfinite(bound) or bound <= 0:
                return base | dict(
                    status="out_of_scope", reason="Reaction-extent bracket cannot be represented"
                )
            from scipy.optimize import brentq

            def residual(fraction):
                # At complete precipitation at least one reactant is exhausted exactly.
                log_q = (
                    -math.inf
                    if direction > 0 and fraction == 1
                    else log_product(direction * bound * fraction)
                )
                return math.tanh(0.5 * (log_q - log_k))

            fraction = brentq(residual, 0.0, 1.0, xtol=math.ulp(0.0), rtol=1e-12, maxiter=1000)
            extent = direction * bound * fraction
        final = {
            row.species_id: row.initial_concentration_mol_m3
            - row.stoichiometric_moles_per_solid_mole * extent
            for row in species
        }
        solid = solid0 + extent
        if (
            solid < 0
            or any(value < 0 or not math.isfinite(value) for value in final.values())
            or not math.isfinite(solid)
        ):
            return base | dict(
                status="out_of_scope", reason="Nonphysical or nonfinite equilibrium; values were not clipped"
            )
        final_log_q = log_product(extent)
    except (ArithmeticError, OverflowError, ValueError, RuntimeError) as error:
        return base | dict(status="out_of_scope", reason=str(error))
    log_residual = final_log_q - log_k
    if saturated and (
        not math.isfinite(log_residual)
        or abs(log_residual) > request.maximum_absolute_log_saturation_residual
    ):
        return base | dict(
            status="out_of_scope",
            reason="Saturation root cannot meet the declared log residual",
            log_saturation_residual=log_residual if math.isfinite(log_residual) else None,
        )
    balances = {
        row.species_id: final[row.species_id]
        - row.initial_concentration_mol_m3
        + row.stoichiometric_moles_per_solid_mole * extent
        for row in species
    }
    solid_residual = solid - solid0 - extent
    limits = {
        row.species_id: request.absolute_extent_balance_tolerance_mol_m3
        + request.relative_extent_balance_tolerance
        * max(
            abs(final[row.species_id]),
            row.initial_concentration_mol_m3,
            abs(row.stoichiometric_moles_per_solid_mole * extent),
        )
        for row in species
    }
    solid_limit = (
        request.absolute_extent_balance_tolerance_mol_m3
        + request.relative_extent_balance_tolerance * max(solid, solid0, abs(extent))
    )
    finite = all(
        math.isfinite(value)
        for value in list(balances.values()) + list(limits.values()) + [solid_residual, solid_limit]
    )
    if not finite:
        return base | dict(status="out_of_scope", reason="Extent balance arithmetic exceeds numeric range")
    within = (
        finite
        and abs(solid_residual) <= solid_limit
        and all(abs(balances[key]) <= limits[key] for key in balances)
    )
    return base | dict(
        status="computed" if within else "out_of_scope",
        reaction_extent_mol_m3=extent,
        final_aqueous_concentration_mol_m3=final,
        final_solid_moles_per_solution_volume_mol_m3=solid,
        solid_present=solid > 0,
        equilibrium_state="saturated" if saturated else "undersaturated_without_solid",
        log_ion_activity_product=final_log_q if math.isfinite(final_log_q) else None,
        ion_activity_product_exactly_zero=final_log_q == -math.inf,
        log_solubility_product=log_k,
        log_saturation_residual=log_residual if math.isfinite(log_residual) else None,
        species_extent_balance_residual_mol_m3=balances,
        solid_extent_balance_residual_mol_m3=solid_residual,
        extent_balance_within_declared_tolerance=within,
        basis="Single declared neutral pure-solid equilibrium with fixed solution volume and fixed caller activity coefficients. No other speciation, competing phases, kinetics, nucleation time, porosity, transport coupling or surface protection is inferred.",
    )
