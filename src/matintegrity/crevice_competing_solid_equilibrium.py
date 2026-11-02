"""Bounded multi-solid equilibrium for a caller-defined crevice liquid."""

from __future__ import annotations

import math

from pydantic import Field, StrictInt, model_validator

from .contracts import Calculation, Contract, Evidence, Nonnegative, Positive, canonical_digest
from .registry import ModelSpec

MODEL_ID = "chemistry.crevice_competing_solid_equilibrium"
SPECIES_SOURCE_ID = "caller_competing_solid_aqueous_state"
PHASE_SOURCE_ID = "caller_competing_solid_equilibrium_constants"
METHOD_SOURCE_ID = "bounded_sequential_active_set_multi_solid_equilibrium"


class CreviceEquilibriumAqueousSpecies(Contract):
    species_id: str = Field(min_length=1)
    initial_concentration_mol_m3: Nonnegative
    activity_reference_concentration_mol_m3: Positive
    activity_coefficient: Positive
    charge_number: int
    elemental_composition: dict[str, int] = Field(min_length=1)
    record_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    evidence: tuple[Evidence, ...] = Field(min_length=1, max_length=64)

    @model_validator(mode="after")
    def bind_record(self):
        if any(not element or amount < 0 for element, amount in self.elemental_composition.items()):
            raise ValueError("aqueous species requires nonnegative elemental composition")
        if not any(self.elemental_composition.values()):
            raise ValueError("aqueous species elemental composition cannot be all zero")
        payload = {
            "species_id": self.species_id,
            "initial_concentration_mol_m3": self.initial_concentration_mol_m3,
            "activity_reference_concentration_mol_m3": self.activity_reference_concentration_mol_m3,
            "activity_coefficient": self.activity_coefficient,
            "charge_number": self.charge_number,
            "elemental_composition": self.elemental_composition,
        }
        if canonical_digest(payload) != self.record_sha256:
            raise ValueError("aqueous species digest must bind concentration, activity state and composition")
        if not any(row.sha256 == self.record_sha256 for row in self.evidence):
            raise ValueError("species Evidence must pin its record digest")
        return self


class CreviceCompetingSolidPhase(Contract):
    solid_species_id: str = Field(min_length=1)
    solid_elemental_composition: dict[str, int] = Field(min_length=1)
    aqueous_reactant_stoichiometry: dict[str, Positive] = Field(min_length=1)
    initial_solid_moles_per_solution_volume_mol_m3: Nonnegative
    dimensionless_solubility_product: Positive
    equilibrium_constant_record_id: str = Field(min_length=1)
    equilibrium_constant_record_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    record_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    evidence: tuple[Evidence, ...] = Field(min_length=1, max_length=64)

    @model_validator(mode="after")
    def bind_phase_record(self):
        if any(not element or amount < 0 for element, amount in self.solid_elemental_composition.items()):
            raise ValueError("solid phase requires nonnegative elemental composition")
        if not any(self.solid_elemental_composition.values()):
            raise ValueError("solid elemental composition cannot be all zero")
        payload = {
            "solid_species_id": self.solid_species_id,
            "solid_elemental_composition": self.solid_elemental_composition,
            "aqueous_reactant_stoichiometry": self.aqueous_reactant_stoichiometry,
            "initial_solid_moles_per_solution_volume_mol_m3": self.initial_solid_moles_per_solution_volume_mol_m3,
            "dimensionless_solubility_product": self.dimensionless_solubility_product,
            "equilibrium_constant_record_id": self.equilibrium_constant_record_id,
            "equilibrium_constant_record_sha256": self.equilibrium_constant_record_sha256,
        }
        if canonical_digest(payload) != self.record_sha256:
            raise ValueError("solid phase digest must bind stoichiometry, inventory, Ksp and Ksp record identity")
        if not any(row.sha256 == self.record_sha256 for row in self.evidence):
            raise ValueError("phase Evidence must pin its complete phase record")
        if not any(row.source_id == self.equilibrium_constant_record_id
                   and row.sha256 == self.equilibrium_constant_record_sha256 for row in self.evidence):
            raise ValueError("phase Evidence must pin the declared equilibrium-constant record")
        return self


class CreviceCompetingSolidEquilibriumRequest(Contract):
    assessment_id: str = Field(min_length=1)
    asset_id: str = Field(min_length=1)
    physical_scope_id: str = Field(min_length=1)
    temperature_K: Positive
    standard_state_id: str = Field(min_length=1)
    aqueous_species: tuple[CreviceEquilibriumAqueousSpecies, ...] = Field(min_length=1, max_length=64)
    solid_phases: tuple[CreviceCompetingSolidPhase, ...] = Field(min_length=1, max_length=12)
    absolute_charge_balance_tolerance_mol_charge_m3: Positive = 1e-10
    absolute_inventory_balance_tolerance_mol_m3: Positive = 1e-10
    relative_inventory_balance_tolerance: float = Field(default=1e-10, gt=0.0, le=1e-4)
    maximum_log_saturation_residual: Positive = 1e-8
    relative_state_convergence_tolerance: float = Field(default=1e-10, gt=0.0, le=1e-4)
    solid_presence_tolerance_mol_m3: Nonnegative = 1e-12
    maximum_active_set_sweeps: StrictInt = Field(default=100, ge=1, le=10000)
    fixed_gamma_standard_states_and_temperature_reviewed: bool
    equilibrium_constants_applicable_to_declared_state_reviewed: bool
    instantaneous_equilibrium_no_kinetic_barrier_reviewed: bool
    shared_solution_volume_and_complete_candidate_set_reviewed: bool
    computational_use_authorized: bool
    evidence: tuple[Evidence, ...] = Field(min_length=1, max_length=128)

    @model_validator(mode="after")
    def validate_reaction_set(self):
        species_by_id = {row.species_id: row for row in self.aqueous_species}
        if len(species_by_id) != len(self.aqueous_species):
            raise ValueError("aqueous species IDs must be unique")
        phase_ids = [row.solid_species_id for row in self.solid_phases]
        if len(set(phase_ids)) != len(phase_ids):
            raise ValueError("solid phase IDs must be unique")
        if set(species_by_id).intersection(phase_ids):
            raise ValueError("aqueous and solid species IDs must be distinct")
        for phase in self.solid_phases:
            if not set(phase.aqueous_reactant_stoichiometry) <= set(species_by_id):
                raise ValueError("each solid reaction must use declared aqueous species only")
            element_ids = set(phase.solid_elemental_composition)
            charge = 0.0
            for species_id, coefficient in phase.aqueous_reactant_stoichiometry.items():
                species = species_by_id[species_id]
                charge += species.charge_number * coefficient
                element_ids.update(species.elemental_composition)
            if not math.isclose(charge, 0.0, rel_tol=0.0, abs_tol=1e-12):
                raise ValueError("each precipitation reaction must conserve charge for a neutral solid")
            for element in element_ids:
                aqueous = math.fsum(
                    species_by_id[species_id].elemental_composition.get(element, 0) * coefficient
                    for species_id, coefficient in phase.aqueous_reactant_stoichiometry.items()
                )
                solid = phase.solid_elemental_composition.get(element, 0)
                if not math.isclose(aqueous, solid, rel_tol=1e-12, abs_tol=1e-12):
                    raise ValueError("each phase reaction must conserve every declared element")
        if not all((self.fixed_gamma_standard_states_and_temperature_reviewed,
                    self.equilibrium_constants_applicable_to_declared_state_reviewed,
                    self.instantaneous_equilibrium_no_kinetic_barrier_reviewed,
                    self.shared_solution_volume_and_complete_candidate_set_reviewed,
                    self.computational_use_authorized)):
            raise ValueError("all state, phase-set and equilibrium-use reviews are required")
        initial_charge = math.fsum(row.charge_number * row.initial_concentration_mol_m3
                                   for row in self.aqueous_species)
        if abs(initial_charge) > self.absolute_charge_balance_tolerance_mol_charge_m3:
            raise ValueError("initial aqueous state exceeds declared electroneutrality tolerance")
        return self


def _log_ion_activity_product(concentrations, species_by_id, stoichiometry):
    terms = []
    for species_id, coefficient in stoichiometry.items():
        concentration = concentrations[species_id]
        if concentration <= 0.0:
            return -math.inf
        species = species_by_id[species_id]
        terms.append(coefficient * (
            math.log(species.activity_coefficient)
            + math.log(concentration)
            - math.log(species.activity_reference_concentration_mol_m3)
        ))
    return math.fsum(terms)


def _equilibrate_phase_once(phase, concentrations, solid_inventory, species_by_id):
    """Apply one scalar phase update against the current shared aqueous state."""
    stoich = phase.aqueous_reactant_stoichiometry
    log_k = math.log(phase.dimensionless_solubility_product)
    log_q0 = _log_ion_activity_product(concentrations, species_by_id, stoich)
    extent = 0.0
    if log_q0 > log_k:
        upper = min(concentrations[key] / coefficient for key, coefficient in stoich.items())
        if upper <= 0.0 or not math.isfinite(upper):
            raise ArithmeticError("supersaturated phase has no finite precipitation extent bracket")

        def residual(fraction):
            trial = {key: concentrations[key] - stoich.get(key, 0.0) * upper * fraction
                     for key in concentrations}
            log_q = _log_ion_activity_product(trial, species_by_id, stoich)
            if fraction == 1.0 and log_q == -math.inf:
                return -1.0
            return math.tanh(0.5 * (log_q - log_k))

        from scipy.optimize import brentq

        extent = upper * brentq(residual, 0.0, 1.0, xtol=1e-14, rtol=1e-12, maxiter=200)
    elif log_q0 < log_k and solid_inventory > 0.0:
        max_dissolution = solid_inventory
        trial = {key: concentrations[key] + stoich.get(key, 0.0) * max_dissolution
                 for key in concentrations}
        log_q_depleted = _log_ion_activity_product(trial, species_by_id, stoich)
        if log_q_depleted <= log_k:
            extent = -max_dissolution
        else:
            def residual(fraction):
                trial_state = {key: concentrations[key] + stoich.get(key, 0.0) * max_dissolution * fraction
                               for key in concentrations}
                return math.tanh(0.5 * (_log_ion_activity_product(trial_state, species_by_id, stoich) - log_k))

            from scipy.optimize import brentq

            extent = -max_dissolution * brentq(residual, 0.0, 1.0, xtol=1e-14, rtol=1e-12, maxiter=200)
    next_concentrations = {
        key: concentrations[key] - stoich.get(key, 0.0) * extent for key in concentrations
    }
    next_solid = solid_inventory + extent
    if next_solid < 0.0 or any(value < 0.0 or not math.isfinite(value)
                               for value in next_concentrations.values()):
        raise ArithmeticError("phase update produced negative or nonfinite inventory; no clipping is applied")
    return next_concentrations, next_solid, extent


def evaluate_crevice_competing_solid_equilibrium(
    request: CreviceCompetingSolidEquilibriumRequest,
) -> Calculation:
    """Sequentially solve a finite caller-defined set of neutral solid equilibria."""
    digest = canonical_digest(request.model_dump(mode="json"))
    species_by_id = {row.species_id: row for row in request.aqueous_species}
    concentrations = {row.species_id: row.initial_concentration_mol_m3 for row in request.aqueous_species}
    initial_concentrations = dict(concentrations)
    solids = {row.solid_species_id: row.initial_solid_moles_per_solution_volume_mol_m3
              for row in request.solid_phases}
    initial_solids = dict(solids)
    cumulative_extents = {key: 0.0 for key in solids}
    converged = False
    sweeps = 0
    try:
        for sweeps in range(1, request.maximum_active_set_sweeps + 1):
            before_c = dict(concentrations)
            before_s = dict(solids)
            for phase in request.solid_phases:
                concentrations, solids[phase.solid_species_id], extent = _equilibrate_phase_once(
                    phase, concentrations, solids[phase.solid_species_id], species_by_id
                )
                cumulative_extents[phase.solid_species_id] += extent
            scales = [1e-30, *(abs(value) for value in before_c.values()),
                      *(abs(value) for value in before_s.values())]
            scale = max(scales)
            change = max(
                [abs(concentrations[key] - before_c[key]) for key in concentrations]
                + [abs(solids[key] - before_s[key]) for key in solids]
                + [0.0]
            ) / scale
            if change <= request.relative_state_convergence_tolerance:
                converged = True
                break
    except (ArithmeticError, OverflowError, ValueError, RuntimeError) as error:
        return Calculation(status="out_of_scope", values={
            "model_id": MODEL_ID, "assessment_id": request.assessment_id,
            "asset_id": request.asset_id, "physical_scope_id": request.physical_scope_id,
            "input_sha256": digest, "status_reason": str(error), "committed": False,
        })
    if not converged:
        return Calculation(status="out_of_scope", values={
            "model_id": MODEL_ID, "assessment_id": request.assessment_id,
            "asset_id": request.asset_id, "physical_scope_id": request.physical_scope_id,
            "input_sha256": digest, "status_reason": "active-set sweeps did not meet the declared state convergence tolerance",
            "active_set_sweeps": sweeps, "committed": False,
        })
    phase_results = []
    for phase in request.solid_phases:
        log_q = _log_ion_activity_product(concentrations, species_by_id,
                                          phase.aqueous_reactant_stoichiometry)
        log_k = math.log(phase.dimensionless_solubility_product)
        residual = log_q - log_k
        present = solids[phase.solid_species_id] > request.solid_presence_tolerance_mol_m3
        if (present and (not math.isfinite(residual)
                         or abs(residual) > request.maximum_log_saturation_residual)):
            return Calculation(status="out_of_scope", values={
                "model_id": MODEL_ID, "assessment_id": request.assessment_id,
                "asset_id": request.asset_id, "physical_scope_id": request.physical_scope_id,
                "input_sha256": digest, "status_reason": "present phase failed saturation complementarity residual",
                "solid_species_id": phase.solid_species_id, "log_saturation_residual": residual,
                "active_set_sweeps": sweeps, "committed": False,
            })
        if not present and residual > request.maximum_log_saturation_residual:
            return Calculation(status="out_of_scope", values={
                "model_id": MODEL_ID, "assessment_id": request.assessment_id,
                "asset_id": request.asset_id, "physical_scope_id": request.physical_scope_id,
                "input_sha256": digest, "status_reason": "absent phase remains supersaturated beyond tolerance",
                "solid_species_id": phase.solid_species_id, "log_saturation_residual": residual,
                "active_set_sweeps": sweeps, "committed": False,
            })
        phase_results.append({
            "solid_species_id": phase.solid_species_id,
            "initial_solid_moles_per_solution_volume_mol_m3": initial_solids[phase.solid_species_id],
            "final_solid_moles_per_solution_volume_mol_m3": solids[phase.solid_species_id],
            "net_extent_mol_m3": cumulative_extents[phase.solid_species_id],
            "phase_present": present,
            "final_log_ion_activity_product": log_q if math.isfinite(log_q) else None,
            "log_solubility_product": log_k,
            "log_saturation_residual": residual if math.isfinite(residual) else None,
            "equilibrium_constant_record_id": phase.equilibrium_constant_record_id,
            "equilibrium_constant_record_sha256": phase.equilibrium_constant_record_sha256,
            "phase_record_sha256": phase.record_sha256,
        })
    charge_residual = math.fsum(row.charge_number * concentrations[row.species_id]
                                for row in request.aqueous_species)
    if abs(charge_residual) > request.absolute_charge_balance_tolerance_mol_charge_m3:
        return Calculation(status="out_of_scope", values={
            "model_id": MODEL_ID, "assessment_id": request.assessment_id,
            "asset_id": request.asset_id, "physical_scope_id": request.physical_scope_id,
            "input_sha256": digest, "status_reason": "final aqueous charge balance exceeds tolerance",
            "charge_balance_residual_mol_charge_m3": charge_residual,
            "active_set_sweeps": sweeps, "committed": False,
        })
    species_results = {}
    inventory_balance_failures = []
    for species in request.aqueous_species:
        reconstructed = initial_concentrations[species.species_id] - math.fsum(
            phase.aqueous_reactant_stoichiometry.get(species.species_id, 0.0)
            * cumulative_extents[phase.solid_species_id] for phase in request.solid_phases
        )
        residual = concentrations[species.species_id] - reconstructed
        limit = (request.absolute_inventory_balance_tolerance_mol_m3
                 + request.relative_inventory_balance_tolerance
                 * max(abs(concentrations[species.species_id]), abs(reconstructed),
                       initial_concentrations[species.species_id]))
        if not math.isfinite(residual) or abs(residual) > limit:
            inventory_balance_failures.append(species.species_id)
        species_results[species.species_id] = {
            "initial_concentration_mol_m3": initial_concentrations[species.species_id],
            "final_concentration_mol_m3": concentrations[species.species_id],
            "extent_balance_residual_mol_m3": residual,
            "extent_balance_limit_mol_m3": limit,
        }
    solid_balance_results = {}
    for phase in request.solid_phases:
        phase_id = phase.solid_species_id
        residual = solids[phase_id] - initial_solids[phase_id] - cumulative_extents[phase_id]
        limit = (request.absolute_inventory_balance_tolerance_mol_m3
                 + request.relative_inventory_balance_tolerance
                 * max(solids[phase_id], initial_solids[phase_id], abs(cumulative_extents[phase_id])))
        if not math.isfinite(residual) or abs(residual) > limit:
            inventory_balance_failures.append(phase_id)
        solid_balance_results[phase_id] = {
            "extent_balance_residual_mol_m3": residual,
            "extent_balance_limit_mol_m3": limit,
        }
    if inventory_balance_failures:
        return Calculation(status="out_of_scope", values={
            "model_id": MODEL_ID, "assessment_id": request.assessment_id,
            "asset_id": request.asset_id, "physical_scope_id": request.physical_scope_id,
            "input_sha256": digest,
            "status_reason": "aqueous or solid extent inventory closure exceeds declared tolerance",
            "failed_inventory_ids": inventory_balance_failures,
            "active_set_sweeps": sweeps, "committed": False,
        })
    return Calculation(status="computed", values={
        "model_id": MODEL_ID,
        "assessment_id": request.assessment_id,
        "asset_id": request.asset_id,
        "physical_scope_id": request.physical_scope_id,
        "input_sha256": digest,
        "temperature_K": request.temperature_K,
        "standard_state_id": request.standard_state_id,
        "active_set_sweeps": sweeps,
        "aqueous_species": species_results,
        "solid_phases": phase_results,
        "solid_inventory_balance": solid_balance_results,
        "aqueous_charge_balance_residual_mol_charge_m3": charge_residual,
        "phase_complementarity_verified": True,
        "interpretation": "caller_defined_competing_pure_solid_equilibrium_at_fixed_temperature_and_volume",
        "limitations": [
            "Only the caller's finite candidate set of neutral pure solids and aqueous reactants is considered.",
            "Activity coefficients, reference concentrations, equilibrium constants, standard states and temperature applicability are caller supplied and fixed.",
            "Sequential active-set iteration is fail-closed on nonconvergence or saturation complementarity failure; it is not a global Gibbs-energy phase-stability proof.",
            "Instantaneous equilibrium is assumed; nucleation barriers, metastability, finite kinetics, gas phases, complexes, pH/speciation discovery and transport are not modeled.",
            "No wall precipitation location, deposit morphology, corrosion rate, moving aperture or engineering acceptance is inferred.",
        ],
    })


def specifications() -> list[ModelSpec]:
    return [ModelSpec(
        model_id=MODEL_ID,
        input_type=CreviceCompetingSolidEquilibriumRequest,
        evaluator=evaluate_crevice_competing_solid_equilibrium,
        units={
            "aqueous_species[].initial_concentration_mol_m3": "mol/m^3",
            "aqueous_species[].final_concentration_mol_m3": "mol/m^3",
            "solid_phases[].initial_solid_moles_per_solution_volume_mol_m3": "mol/m^3",
            "solid_phases[].final_solid_moles_per_solution_volume_mol_m3": "mol/m^3",
            "solid_phases[].net_extent_mol_m3": "mol/m^3",
            "aqueous_charge_balance_residual_mol_charge_m3": "mol-charge/m^3",
        },
        assumptions=(
            "One fixed, homogeneous solution volume and one temperature are used with fixed caller activity coefficients and standard states.",
            "Each candidate phase is a neutral pure solid with explicit charge and elemental balance in its dissolution/precipitation reaction.",
            "The bounded sequential active-set iteration must converge and satisfy present/absent phase complementarity before values are committed.",
            "The calculation is an equilibrium screen, not a kinetic or global phase-stability solver.",
        ),
        source_ids=(SPECIES_SOURCE_ID, PHASE_SOURCE_ID, METHOD_SOURCE_ID),
    )]
