"""Self-consistent single-liquid activity/speciation with caller-supplied Davies A."""

from __future__ import annotations

import math
from typing import Literal

import numpy as np
from pydantic import Field, model_validator

from ..contracts import Calculation, Contract, Evidence, Positive, canonical_digest
from ..registry import ModelSpec
from .aqueous_mass_action import AqueousMassActionSystem, aqueous_mass_action_speciation
from .aqueous_saturation_screening import AqueousSaturationScreen, build_transport_saturation_callback_from_activity_provider
from .sit_activity import SITActivityCoefficientInput, SITInteraction, SITSpecies, sit_activity_coefficients


class AqueousDaviesIteration(Contract):
    schema_version: Literal["matintegrity.aqueous_davies_iteration.v1"] = (
        "matintegrity.aqueous_davies_iteration.v1"
    )
    system: AqueousMassActionSystem
    water_mass_per_solution_volume_kg_L: Positive
    davies_A_at_temperature: Positive
    davies_A_provider_id: str = Field(min_length=1)
    davies_A_provider_revision: str = Field(min_length=1)
    davies_A_configuration_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    davies_A_record_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    ionic_strength_limit_mol_kg: Positive = Field(le=0.5)
    charge_balance_tolerance_mol_kg: Positive
    maximum_outer_iterations: int = Field(default=100, ge=1, le=1000)
    log_gamma_tolerance: Positive = Field(default=1e-9, le=1e-3)
    damping_fraction: Positive = Field(default=0.5, le=1.0)
    water_mass_conversion_reviewed: bool
    Davies_A_temperature_solvent_basis_reviewed: bool
    molarity_to_molality_standard_state_mapping_reviewed: bool
    complete_inventory_and_charge_scope_reviewed: bool
    fixed_point_solver_settings_reviewed: bool
    single_liquid_no_precipitation_scope_reviewed: bool
    evidence: tuple[Evidence, ...] = Field(min_length=1)


class BdotSpeciesParameter(Contract):
    """Caller-owned species parameters for the extended Debye-Huckel B-dot form."""

    species_id: str = Field(min_length=1)
    ion_size_angstrom: float = Field(ge=0.0, le=100.0)
    bdot_kg_per_mol: float
    source_id: str = Field(min_length=1)
    source_record_id: str = Field(min_length=1)
    source_record_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")


class AqueousBdotIteration(Contract):
    """Self-consistent single-liquid speciation with caller-owned B-dot parameters."""

    schema_version: Literal["matintegrity.aqueous_bdot_iteration.v1"] = (
        "matintegrity.aqueous_bdot_iteration.v1"
    )
    system: AqueousMassActionSystem
    water_mass_per_solution_volume_kg_L: Positive
    debye_huckel_A_at_temperature: Positive
    debye_huckel_B_at_temperature_sqrt_kg_mol_per_angstrom: Positive
    parameter_temperature_K: Positive
    temperature_match_tolerance_K: float = Field(default=0.01, ge=0.0, le=5.0)
    parameter_provider_id: str = Field(min_length=1)
    parameter_provider_revision: str = Field(min_length=1)
    parameter_configuration_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    parameter_record_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    maximum_supported_ionic_strength_mol_kg: Positive
    charge_balance_tolerance_mol_kg: Positive
    species_parameters: tuple[BdotSpeciesParameter, ...] = Field(min_length=1, max_length=100)
    maximum_outer_iterations: int = Field(default=100, ge=1, le=1000)
    log_gamma_tolerance: Positive = Field(default=1e-9, le=1e-3)
    damping_fraction: Positive = Field(default=0.5, le=1.0)
    water_mass_conversion_reviewed: bool
    molarity_to_molality_standard_state_mapping_reviewed: bool
    temperature_solvent_and_parameter_basis_reviewed: bool
    complete_inventory_and_charge_scope_reviewed: bool
    species_parameter_completeness_and_applicability_reviewed: bool
    fixed_point_solver_settings_reviewed: bool
    single_liquid_no_precipitation_scope_reviewed: bool
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def coherent_bdot_parameterization(self):
        if self.system.activity_standard_state != "molarity_1_mol_L":
            raise ValueError("B-dot coupling requires the molarity 1 mol/L activity standard state")
        if abs(self.system.temperature_K - self.parameter_temperature_K) > self.temperature_match_tolerance_K:
            raise ValueError("B-dot parameters are used only within the declared temperature match tolerance")
        expected_ids = tuple(row.species_id for row in self.system.species)
        parameter_ids = tuple(row.species_id for row in self.species_parameters)
        if parameter_ids != expected_ids:
            raise ValueError("B-dot parameter rows must exactly match the mass-action species order")
        charges = {row.species_id: row.charge_number for row in self.system.species}
        if any(charges[row.species_id] != 0 and row.ion_size_angstrom <= 0.0 for row in self.species_parameters):
            raise ValueError("charged species require a positive ion-size parameter")
        evidence = {(row.source_id, row.sha256) for row in self.evidence}
        if (self.parameter_provider_id, self.parameter_record_sha256) not in evidence:
            raise ValueError("provider parameter record must match a declared Evidence source and SHA-256")
        for row in self.species_parameters:
            if (row.source_id, row.source_record_sha256) not in evidence:
                raise ValueError("each species B-dot record must match declared Evidence source and SHA-256")
        return self


class AqueousSITIteration(Contract):
    """Self-consistent mass-action speciation with a caller-owned SIT parameter set."""

    schema_version: Literal["matintegrity.aqueous_sit_iteration.v2"] = "matintegrity.aqueous_sit_iteration.v2"
    system: AqueousMassActionSystem
    water_mass_per_solution_volume_kg_L: Positive
    debye_huckel_A_at_temperature: Positive
    A_evidence_source_id: str = Field(min_length=1)
    sit_provider_id: str = Field(min_length=1)
    sit_provider_revision: str = Field(min_length=1)
    sit_configuration_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    sit_record_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    ionic_strength_limit_mol_kg: Positive = Field(le=6.0)
    charge_balance_tolerance_mol_kg: Positive
    interactions: tuple[SITInteraction, ...] = Field(default=(), max_length=100_000)
    maximum_outer_iterations: int = Field(default=100, ge=1, le=1000)
    log_gamma_tolerance: Positive = Field(default=1e-9, le=1e-3)
    damping_fraction: Positive = Field(default=0.5, le=1.0)
    water_mass_conversion_reviewed: bool
    temperature_solvent_and_A_basis_reviewed: bool
    molarity_to_molality_standard_state_mapping_reviewed: bool
    complete_inventory_and_charge_scope_reviewed: bool
    interaction_parameter_set_completeness_and_applicability_reviewed: bool
    fixed_point_solver_settings_reviewed: bool
    single_liquid_no_precipitation_scope_reviewed: bool
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def coherent_SIT_system(self):
        if self.system.activity_standard_state != "molarity_1_mol_L":
            raise ValueError("SIT coupling currently maps the molarity 1 mol/L activity standard state to molality")
        species_ids = {row.species_id for row in self.system.species}
        pair_ids = [(row.target_species_id, row.counter_species_id) for row in self.interactions]
        if len(pair_ids) != len(set(pair_ids)):
            raise ValueError("SIT interaction pairs must be unique and directional")
        if any(a not in species_ids or b not in species_ids for a, b in pair_ids):
            raise ValueError("SIT interaction pairs must use species declared in the mass-action system")
        evidence_ids = [row.source_id for row in self.evidence]
        if len(evidence_ids) != len(set(evidence_ids)):
            raise ValueError("SIT evidence source IDs must be unique")
        if self.A_evidence_source_id not in evidence_ids:
            raise ValueError("the Debye-Huckel A parameter must reference one declared Evidence source")
        if any(row.evidence_source_id not in evidence_ids for row in self.interactions):
            raise ValueError("every SIT interaction must reference a declared Evidence source")
        if any(
            not any(
                evidence.source_id == row.evidence_source_id
                and evidence.sha256 == row.evidence_sha256
                for evidence in self.evidence
            )
            for row in self.interactions
        ):
            raise ValueError("every SIT interaction record digest must match its declared Evidence")
        finite = (
            self.system.temperature_K,
            self.water_mass_per_solution_volume_kg_L,
            self.debye_huckel_A_at_temperature,
            self.ionic_strength_limit_mol_kg,
            self.charge_balance_tolerance_mol_kg,
            self.log_gamma_tolerance,
            self.damping_fraction,
        )
        if any(not math.isfinite(value) for value in finite):
            raise ValueError("SIT conditions and fixed-point controls must be finite")
        return self


def _davies_gamma(charges: np.ndarray, ionic_strength: float, A: float) -> np.ndarray:
    root_strength = math.sqrt(ionic_strength)
    term = root_strength / (1.0 + root_strength) - 0.3 * ionic_strength
    exponents = -A * (charges**2) * term * math.log(10.0)
    gamma = np.exp(exponents)
    if np.any(~np.isfinite(gamma)) or np.any(gamma <= 0.0):
        raise ArithmeticError("Davies activity coefficient is not finite and positive")
    return gamma


def molality_gamma_to_molarity_standard_state(
    gamma_molality: np.ndarray, water_mass_per_solution_volume_kg_L: float
) -> np.ndarray:
    """Map gamma_m*m to gamma_c*c for a 1 mol/kg-water to 1 mol/L standard state."""
    values = np.asarray(gamma_molality, dtype=float)
    log_gamma_molarity = np.log(values) - math.log(water_mass_per_solution_volume_kg_L)
    if (not np.isfinite(log_gamma_molarity).all()
            or np.any(log_gamma_molarity > math.log(np.finfo(float).max))
            or np.any(log_gamma_molarity < math.log(np.nextafter(0.0, 1.0)))):
        raise ArithmeticError("molality-to-molarity activity standard-state conversion exceeds binary64 support")
    converted = np.exp(log_gamma_molarity)
    if not np.isfinite(converted).all() or np.any(converted <= 0.0):
        raise ArithmeticError("converted molarity-standard-state activity coefficients are invalid")
    return converted


def aqueous_davies_self_consistent_speciation(x: AqueousDaviesIteration) -> Calculation:
    """Iterate aqueous activities and molal Davies coefficients to a fixed point.

    The mass-action core remains a caller-specified square equilibrium/constraint
    system. This wrapper only closes gamma against ionic strength; it does not
    add species, infer constraints, or handle other phases.
    """
    system = x.system
    digest = canonical_digest(x.model_dump(mode="json"))
    base = {
        "assessment_id": system.assessment_id,
        "solution_id": system.solution_id,
        "temperature_K": system.temperature_K,
        "input_digest": digest,
        "water_mass_per_solution_volume_kg_L": x.water_mass_per_solution_volume_kg_L,
        "activity_standard_state": "dimensionless_molarity_1_mol_L",
        "activity_coefficient_mapping": "gamma_c=gamma_m/w; w=kg_water_per_L_solution",
        "davies_A_at_temperature": x.davies_A_at_temperature,
        "davies_A_provider_id": x.davies_A_provider_id,
        "davies_A_provider_revision": x.davies_A_provider_revision,
        "davies_A_configuration_digest": x.davies_A_configuration_digest,
        "davies_A_record_digest": x.davies_A_record_digest,
        "ionic_strength_limit_mol_kg": x.ionic_strength_limit_mol_kg,
    }
    reviews = {
        "water_mass_conversion_reviewed": x.water_mass_conversion_reviewed,
        "Davies_A_temperature_solvent_basis_reviewed": x.Davies_A_temperature_solvent_basis_reviewed,
        "molarity_to_molality_standard_state_mapping_reviewed": x.molarity_to_molality_standard_state_mapping_reviewed,
        "complete_inventory_and_charge_scope_reviewed": x.complete_inventory_and_charge_scope_reviewed,
        "fixed_point_solver_settings_reviewed": x.fixed_point_solver_settings_reviewed,
        "single_liquid_no_precipitation_scope_reviewed": x.single_liquid_no_precipitation_scope_reviewed,
    }
    missing_reviews = [name for name, reviewed in reviews.items() if not reviewed]
    if missing_reviews:
        return Calculation(
            status="needs_data",
            values=base | {"missing_reviews": missing_reviews, "outer_iterations": 0},
            notes=("Review water-mass conversion, temperature-specific Davies parameter, complete inventory, charge scope and one-liquid applicability before iteration.",),
        )
    if system.activity_standard_state != "molarity_1_mol_L":
        return Calculation(
            status="out_of_scope",
            values=base | {"out_of_scope_reason": "unsupported_mass_action_activity_standard_state", "outer_iterations": 0},
            notes=("This coupling requires dimensionless activities referenced to 1 mol/L and an explicit mol/L-to-molality water-mass conversion.",),
        )

    species = system.species
    charges = np.asarray([row.charge_number for row in species], dtype=float)
    gamma = np.asarray([row.activity_coefficient for row in species], dtype=float)
    history: list[dict] = []
    last_solution = None
    try:
        for iteration in range(1, x.maximum_outer_iterations + 1):
            iteration_system = system.model_copy(update={
                "species": tuple(
                    row.model_copy(update={"activity_coefficient": float(gamma[i])})
                    for i, row in enumerate(species)
                ),
                "activity_provider_id": x.davies_A_provider_id,
                "activity_provider_revision": x.davies_A_provider_revision,
                "activity_configuration_digest": x.davies_A_configuration_digest,
                "activity_record_digest": x.davies_A_record_digest,
            })
            solved = aqueous_mass_action_speciation(iteration_system)
            last_solution = solved
            if solved.status != "computed":
                return Calculation(
                    status=solved.status,
                    values=base | {
                        "outer_iterations": iteration,
                        "fixed_point_history": history,
                        "inner_solver_status": solved.status,
                        "inner_solver_values": solved.values,
                    },
                    notes=("The fixed-activity mass-action subproblem did not produce a computed equilibrium; no outer fixed-point result is reported.", *solved.notes),
                )
            concentration = np.asarray([row["concentration_mol_L"] for row in solved.values["species"]], dtype=float)
            molality = concentration / x.water_mass_per_solution_volume_kg_L
            ionic_strength = 0.5 * float(np.dot(molality, np.square(charges)))
            charge_residual = float(np.dot(molality, charges))
            if not math.isfinite(ionic_strength) or ionic_strength > x.ionic_strength_limit_mol_kg:
                return Calculation(
                    status="out_of_scope",
                    values=base | {
                        "outer_iterations": iteration,
                        "ionic_strength_mol_kg": ionic_strength,
                        "charge_balance_residual_mol_kg": charge_residual,
                        "out_of_scope_reason": "ionic_strength_exceeds_declared_davies_limit",
                        "fixed_point_history": history,
                    },
                    notes=("The speciation-derived ionic strength exceeds the caller limit, which cannot exceed 0.5 mol/kg water. No alternative electrolyte model is substituted.",),
                )
            if not math.isfinite(charge_residual) or abs(charge_residual) > x.charge_balance_tolerance_mol_kg:
                return Calculation(
                    status="needs_data",
                    values=base | {
                        "outer_iterations": iteration,
                        "ionic_strength_mol_kg": ionic_strength,
                        "charge_balance_residual_mol_kg": charge_residual,
                        "out_of_scope_reason": "speciation_charge_balance_tolerance_exceeded",
                        "fixed_point_history": history,
                    },
                    notes=("The complete speciation inventory does not satisfy the separately declared molal charge-balance tolerance.",),
                )

            target_gamma_molality = _davies_gamma(charges, ionic_strength, x.davies_A_at_temperature)
            target_gamma = molality_gamma_to_molarity_standard_state(
                target_gamma_molality, x.water_mass_per_solution_volume_kg_L
            )
            log_residual = float(np.max(np.abs(np.log(target_gamma) - np.log(gamma))))
            history.append({
                "iteration": iteration,
                "ionic_strength_mol_kg": ionic_strength,
                "charge_balance_residual_mol_kg": charge_residual,
                "maximum_log_gamma_fixed_point_residual": log_residual,
                "inner_normalized_residual_norm": solved.values["normalized_residual_norm"],
            })
            if not math.isfinite(log_residual):
                raise ArithmeticError("activity-coefficient fixed-point residual is not finite")
            if log_residual <= x.log_gamma_tolerance:
                result_species = []
                for i, row in enumerate(solved.values["species"]):
                    result_species.append({
                        **row,
                        "molality_mol_kg": float(molality[i]),
                        "ionic_strength_contribution_mol_kg": float(0.5 * molality[i] * charges[i] ** 2),
                        "davies_target_molality_activity_coefficient": float(target_gamma_molality[i]),
                        "davies_target_molarity_activity_coefficient": float(target_gamma[i]),
                        "activity_coefficient_fixed_point_residual_ln": float(math.log(target_gamma[i] / gamma[i])),
                    })
                return Calculation(
                    values=base | {
                        "outer_iterations": iteration,
                        "ionic_strength_mol_kg": ionic_strength,
                        "charge_balance_residual_mol_kg": charge_residual,
                        "maximum_log_gamma_fixed_point_residual": log_residual,
                        "fixed_point_history": history,
                        "species": result_species,
                        "constraint_closure": solved.values["constraint_closure"],
                        "reaction_closure": solved.values["reaction_closure"],
                        "inner_normalized_residual_norm": solved.values["normalized_residual_norm"],
                        "converged": True,
                        "activity_standard_state": "dimensionless_molarity_1_mol_L; Davies molality basis via caller water-mass conversion",
                        "aqueous_liquid_only": True,
                    },
                    notes=(
                        "A damped fixed-point iteration couples caller-defined single-liquid mass-action speciation to Davies coefficients computed from the resulting molal ionic strength.",
                        "Davies A, water-mass conversion, complete species inventory, reaction constants and balance equations remain caller-supplied and reviewed. No gas/solid phase, precipitation, kinetic scale, salting model or corrosion rate is inferred.",
                    ),
                )
            log_gamma = np.log(gamma) + x.damping_fraction * (np.log(target_gamma) - np.log(gamma))
            gamma = np.exp(log_gamma)
            if np.any(~np.isfinite(gamma)) or np.any(gamma <= 0.0):
                raise ArithmeticError("damped activity coefficient update is not finite and positive")
    except (ArithmeticError, FloatingPointError, OverflowError, ValueError) as error:
        return Calculation(
            status="out_of_scope",
            values=base | {
                "outer_iterations": len(history),
                "out_of_scope_reason": str(error),
                "fixed_point_history": history,
                "inner_solver_status": last_solution.status if last_solution is not None else None,
            },
            notes=("The Davies/mass-action fixed-point iteration encountered a non-finite or unsupported state; no partial equilibrium is promoted.",),
        )

    return Calculation(
        status="out_of_scope",
        values=base | {
            "outer_iterations": len(history),
            "out_of_scope_reason": "activity_ionic_strength_fixed_point_not_converged",
            "maximum_log_gamma_fixed_point_residual": history[-1]["maximum_log_gamma_fixed_point_residual"] if history else None,
            "fixed_point_history": history,
            "inner_solver_status": last_solution.status if last_solution is not None else None,
        },
        notes=("The caller's outer iteration budget did not reach the declared activity-coefficient tolerance; no last iterate is presented as a converged equilibrium.",),
    )


def _aqueous_bdot_log10_gamma(
    charges: np.ndarray,
    ion_sizes_angstrom: np.ndarray,
    bdot_kg_per_mol: np.ndarray,
    ionic_strength_mol_kg: float,
    A: float,
    B_sqrt_kg_mol_per_angstrom: float,
) -> np.ndarray:
    """Evaluate caller-parameterized extended Debye-Huckel B-dot log10 gamma."""
    if not math.isfinite(ionic_strength_mol_kg) or ionic_strength_mol_kg < 0.0:
        raise ArithmeticError("B-dot ionic strength must be finite and nonnegative")
    root_strength = math.sqrt(ionic_strength_mol_kg)
    denominator = 1.0 + B_sqrt_kg_mol_per_angstrom * ion_sizes_angstrom * root_strength
    if not np.isfinite(denominator).all() or np.any(denominator <= 0.0):
        raise ArithmeticError("B-dot ion-size denominator is not finite and positive")
    log10_gamma = -(A * np.square(charges) * root_strength) / denominator
    log10_gamma += bdot_kg_per_mol * ionic_strength_mol_kg
    if not np.isfinite(log10_gamma).all():
        raise ArithmeticError("B-dot log activity coefficients are not finite")
    return log10_gamma


def aqueous_bdot_self_consistent_speciation(x: AqueousBdotIteration) -> Calculation:
    """Couple caller-defined mass action to an evidence-bound B-dot parameter set."""
    system = x.system
    parameter_rows = [row.model_dump(mode="json") for row in x.species_parameters]
    digest = canonical_digest(x.model_dump(mode="json"))
    base = {
        "assessment_id": system.assessment_id,
        "solution_id": system.solution_id,
        "temperature_K": system.temperature_K,
        "parameter_temperature_K": x.parameter_temperature_K,
        "temperature_match_tolerance_K": x.temperature_match_tolerance_K,
        "water_mass_per_solution_volume_kg_L": x.water_mass_per_solution_volume_kg_L,
        "activity_standard_state": "dimensionless_molarity_1_mol_L",
        "activity_coefficient_mapping": "gamma_c=gamma_m/w; w=kg_water_per_L_solution",
        "debye_huckel_A_at_temperature": x.debye_huckel_A_at_temperature,
        "debye_huckel_B_at_temperature_sqrt_kg_mol_per_angstrom": x.debye_huckel_B_at_temperature_sqrt_kg_mol_per_angstrom,
        "parameter_provider_id": x.parameter_provider_id,
        "parameter_provider_revision": x.parameter_provider_revision,
        "parameter_configuration_sha256": x.parameter_configuration_sha256,
        "parameter_record_sha256": x.parameter_record_sha256,
        "species_parameter_sha256": canonical_digest(parameter_rows),
        "maximum_supported_ionic_strength_mol_kg": x.maximum_supported_ionic_strength_mol_kg,
        "input_sha256": digest,
    }
    reviews = {
        "water_mass_conversion_reviewed": x.water_mass_conversion_reviewed,
        "molarity_to_molality_standard_state_mapping_reviewed": x.molarity_to_molality_standard_state_mapping_reviewed,
        "temperature_solvent_and_parameter_basis_reviewed": x.temperature_solvent_and_parameter_basis_reviewed,
        "complete_inventory_and_charge_scope_reviewed": x.complete_inventory_and_charge_scope_reviewed,
        "species_parameter_completeness_and_applicability_reviewed": x.species_parameter_completeness_and_applicability_reviewed,
        "fixed_point_solver_settings_reviewed": x.fixed_point_solver_settings_reviewed,
        "single_liquid_no_precipitation_scope_reviewed": x.single_liquid_no_precipitation_scope_reviewed,
    }
    missing = [name for name, reviewed in reviews.items() if not reviewed]
    if missing:
        return Calculation(status="needs_data", values=base | {
            "missing_reviews": missing,
            "outer_iterations": 0,
        }, notes=("Review the B-dot parameter sources/support, water-mass and activity-standard-state mapping, complete species inventory, and single-liquid scope before iteration.",))
    if system.activity_standard_state != "molarity_1_mol_L":
        return Calculation(status="out_of_scope", values=base | {
            "out_of_scope_reason": "unsupported_mass_action_activity_standard_state",
            "outer_iterations": 0,
        })

    species = system.species
    charges = np.asarray([row.charge_number for row in species], dtype=float)
    ion_sizes = np.asarray([row.ion_size_angstrom for row in x.species_parameters], dtype=float)
    bdot = np.asarray([row.bdot_kg_per_mol for row in x.species_parameters], dtype=float)
    gamma = np.asarray([row.activity_coefficient for row in species], dtype=float)
    history: list[dict] = []
    last_solution = None
    try:
        for iteration in range(1, x.maximum_outer_iterations + 1):
            iteration_system = system.model_copy(update={
                "species": tuple(
                    row.model_copy(update={"activity_coefficient": float(gamma[i])})
                    for i, row in enumerate(species)
                ),
                "activity_provider_id": x.parameter_provider_id,
                "activity_provider_revision": x.parameter_provider_revision,
                "activity_configuration_digest": x.parameter_configuration_sha256,
                "activity_record_digest": x.parameter_record_sha256,
            })
            solved = aqueous_mass_action_speciation(iteration_system)
            last_solution = solved
            if solved.status != "computed":
                return Calculation(status=solved.status, values=base | {
                    "outer_iterations": iteration,
                    "fixed_point_history": history,
                    "inner_solver_status": solved.status,
                    "inner_solver_values": solved.values,
                }, notes=("The fixed-activity mass-action subproblem did not converge; no outer B-dot equilibrium is reported.", *solved.notes))

            concentration = np.asarray([row["concentration_mol_L"] for row in solved.values["species"]], dtype=float)
            molality = concentration / x.water_mass_per_solution_volume_kg_L
            ionic_strength = 0.5 * float(np.dot(molality, np.square(charges)))
            charge_residual = float(np.dot(molality, charges))
            if not math.isfinite(ionic_strength) or ionic_strength > x.maximum_supported_ionic_strength_mol_kg:
                return Calculation(status="out_of_scope", values=base | {
                    "outer_iterations": iteration,
                    "ionic_strength_mol_kg": ionic_strength,
                    "charge_balance_residual_mol_kg": charge_residual,
                    "out_of_scope_reason": "ionic_strength_exceeds_parameter_support",
                    "fixed_point_history": history,
                }, notes=("The speciation-derived ionic strength is outside caller-declared B-dot parameter support; no alternate activity model is substituted.",))
            if not math.isfinite(charge_residual) or abs(charge_residual) > x.charge_balance_tolerance_mol_kg:
                return Calculation(status="needs_data", values=base | {
                    "outer_iterations": iteration,
                    "ionic_strength_mol_kg": ionic_strength,
                    "charge_balance_residual_mol_kg": charge_residual,
                    "out_of_scope_reason": "speciation_charge_balance_tolerance_exceeded",
                    "fixed_point_history": history,
                }, notes=("The complete speciation inventory does not satisfy its caller-declared molal charge-balance tolerance.",))

            log10_gamma_m = _aqueous_bdot_log10_gamma(
                charges, ion_sizes, bdot, ionic_strength,
                float(x.debye_huckel_A_at_temperature),
                float(x.debye_huckel_B_at_temperature_sqrt_kg_mol_per_angstrom),
            )
            log_gamma_m = log10_gamma_m * math.log(10.0)
            if (np.any(log_gamma_m > math.log(np.finfo(float).max))
                    or np.any(log_gamma_m < math.log(np.nextafter(0.0, 1.0)))):
                raise ArithmeticError("B-dot molality activity coefficient exceeds binary64 support")
            target_gamma_m = np.exp(log_gamma_m)
            target_gamma_c = molality_gamma_to_molarity_standard_state(
                target_gamma_m, x.water_mass_per_solution_volume_kg_L
            )
            log_residual = float(np.max(np.abs(np.log(target_gamma_c) - np.log(gamma))))
            history.append({
                "iteration": iteration,
                "ionic_strength_mol_kg": ionic_strength,
                "charge_balance_residual_mol_kg": charge_residual,
                "maximum_log_gamma_fixed_point_residual": log_residual,
                "inner_normalized_residual_norm": solved.values["normalized_residual_norm"],
            })
            if not math.isfinite(log_residual):
                raise ArithmeticError("B-dot activity fixed-point residual is not finite")
            if log_residual <= x.log_gamma_tolerance:
                result_species = []
                for index, row in enumerate(solved.values["species"]):
                    result_species.append({
                        **row,
                        "molality_mol_kg": float(molality[index]),
                        "ionic_strength_contribution_mol_kg": float(0.5 * molality[index] * charges[index] ** 2),
                        "ion_size_angstrom": float(ion_sizes[index]),
                        "Bdot_kg_per_mol": float(bdot[index]),
                        "Bdot_target_log10_gamma_molality": float(log10_gamma_m[index]),
                        "Bdot_target_gamma_molality": float(target_gamma_m[index]),
                        "Bdot_target_gamma_molarity_standard_state": float(target_gamma_c[index]),
                        "activity_coefficient_fixed_point_residual_ln": float(math.log(target_gamma_c[index] / gamma[index])),
                    })
                return Calculation(values=base | {
                    "outer_iterations": iteration,
                    "ionic_strength_mol_kg": ionic_strength,
                    "charge_balance_residual_mol_kg": charge_residual,
                    "maximum_log_gamma_fixed_point_residual": log_residual,
                    "fixed_point_history": history,
                    "species": result_species,
                    "constraint_closure": solved.values["constraint_closure"],
                    "reaction_closure": solved.values["reaction_closure"],
                    "inner_normalized_residual_norm": solved.values["normalized_residual_norm"],
                    "converged": True,
                    "aqueous_liquid_only": True,
                    "neutral_species_activity_model": "caller-specified B-dot interaction term; not an inferred salting law",
                }, notes=(
                    "A damped fixed-point iteration couples caller-defined single-liquid mass action to species-specific extended Debye-Huckel B-dot activity coefficients.",
                    "Temperature-specific A/B constants, species ion-size and B-dot parameters, their support, standard-state conversion, reaction data and rights evidence remain caller supplied. No alternate phase, species, precipitation law or corrosion rate is inferred.",
                ))
            gamma = np.exp(np.log(gamma) + x.damping_fraction * (np.log(target_gamma_c) - np.log(gamma)))
            if np.any(~np.isfinite(gamma)) or np.any(gamma <= 0.0):
                raise ArithmeticError("damped B-dot activity update is not finite and positive")
    except (ArithmeticError, FloatingPointError, OverflowError, ValueError) as error:
        return Calculation(status="out_of_scope", values=base | {
            "outer_iterations": len(history),
            "out_of_scope_reason": str(error),
            "fixed_point_history": history,
            "inner_solver_status": last_solution.status if last_solution is not None else None,
        }, notes=("The B-dot/mass-action iteration encountered a non-finite or unsupported state; no unconverged partial result is presented as equilibrium.",))
    return Calculation(status="out_of_scope", values=base | {
        "outer_iterations": len(history),
        "out_of_scope_reason": "Bdot_activity_fixed_point_not_converged",
        "maximum_log_gamma_fixed_point_residual": history[-1]["maximum_log_gamma_fixed_point_residual"] if history else None,
        "fixed_point_history": history,
        "inner_solver_status": last_solution.status if last_solution is not None else None,
    }, notes=("The caller outer-iteration budget ended before the declared log-coefficient tolerance; the last iterate is not promoted as a converged equilibrium.",))


def build_bdot_transport_activity_callback(
    request: AqueousBdotIteration,
    *,
    transport_species_ids: tuple[str, ...],
    temperature_K: float,
):
    """Build a provenance-bound B-dot gamma_m callback for restricted transport.

    The callback accepts species-by-mouth-plus-cell concentrations in mol/m3,
    converts them to molality with the request water-mass basis, and evaluates
    the declared B-dot expression independently at each location. It does not
    solve local speciation or impose local electroneutrality.
    """
    expected_species = tuple(row.species_id for row in request.system.species)
    if tuple(transport_species_ids) != expected_species:
        raise ValueError("transport species order must exactly match the B-dot mass-action system")
    if not math.isfinite(float(temperature_K)) or temperature_K != request.system.temperature_K:
        raise ValueError("transport temperature must match the reviewed B-dot system temperature")
    if len(set(transport_species_ids)) != len(transport_species_ids):
        raise ValueError("transport species identifiers must be unique")
    reviews = (
        request.water_mass_conversion_reviewed,
        request.molarity_to_molality_standard_state_mapping_reviewed,
        request.temperature_solvent_and_parameter_basis_reviewed,
        request.complete_inventory_and_charge_scope_reviewed,
        request.species_parameter_completeness_and_applicability_reviewed,
        request.single_liquid_no_precipitation_scope_reviewed,
    )
    if not all(reviews):
        raise ValueError("all B-dot transport applicability, inventory and standard-state reviews are required")

    charges = np.asarray([row.charge_number for row in request.system.species], dtype=float)
    ion_sizes = np.asarray([row.ion_size_angstrom for row in request.species_parameters], dtype=float)
    bdot = np.asarray([row.bdot_kg_per_mol for row in request.species_parameters], dtype=float)
    water_mass = float(request.water_mass_per_solution_volume_kg_L)
    ionic_strength_limit = float(request.maximum_supported_ionic_strength_mol_kg)
    A = float(request.debye_huckel_A_at_temperature)
    B = float(request.debye_huckel_B_at_temperature_sqrt_kg_mol_per_angstrom)

    def activity_coefficients(time_s: float, concentration_mol_m3: np.ndarray) -> np.ndarray:
        if isinstance(time_s, bool) or not math.isfinite(float(time_s)):
            raise ValueError("transport callback time must be finite")
        concentration = np.asarray(concentration_mol_m3, dtype=float)
        if concentration.ndim != 2 or concentration.shape[0] != len(expected_species):
            raise ValueError("B-dot callback expects species-by-mouth-plus-cell concentrations")
        if not np.isfinite(concentration).all() or np.any(concentration < 0.0):
            raise ValueError("transport concentrations must be finite and nonnegative")
        molality = concentration / 1000.0 / water_mass
        ionic_strength = 0.5 * np.sum(np.square(charges)[:, None] * molality, axis=0)
        if not np.isfinite(ionic_strength).all() or np.any(ionic_strength > ionic_strength_limit):
            raise ValueError("transport ionic strength exceeds the declared B-dot support")
        log10_gamma = np.column_stack([
            _aqueous_bdot_log10_gamma(charges, ion_sizes, bdot, float(value), A, B)
            for value in ionic_strength
        ])
        log_gamma = log10_gamma * math.log(10.0)
        if (not np.isfinite(log_gamma).all()
                or np.any(log_gamma > math.log(np.finfo(float).max))
                or np.any(log_gamma < math.log(np.nextafter(0.0, 1.0)))):
            raise ValueError("B-dot transport activity coefficients exceed finite binary64 support")
        gamma = np.exp(log_gamma)
        if not np.isfinite(gamma).all() or np.any(gamma <= 0.0):
            raise ValueError("B-dot transport activity coefficients must be finite and positive")
        return gamma

    request_sha256 = canonical_digest(request.model_dump(mode="json"))
    parameter_rows = [row.model_dump(mode="json") for row in request.species_parameters]
    activity_coefficients.provider_id = request.parameter_provider_id
    activity_coefficients.provider_revision = request.parameter_provider_revision
    activity_coefficients.configuration_sha256 = canonical_digest({
        "adapter": "matintegrity.aqueous_bdot_transport_activity_callback.v1",
        "provider_id": request.parameter_provider_id,
        "provider_revision": request.parameter_provider_revision,
        "configuration_sha256": request.parameter_configuration_sha256,
        "parameter_record_sha256": request.parameter_record_sha256,
        "species_parameter_sha256": canonical_digest(parameter_rows),
        "request_sha256": request_sha256,
        "species_ids": list(expected_species),
        "temperature_K": float(temperature_K),
        "concentration_unit": "mol/m3",
        "returned_coefficient_basis": "molality_relative_to_1_mol_per_kg_water",
    })
    activity_coefficients.record_sha256 = request.parameter_record_sha256
    activity_coefficients.source_request_sha256 = request_sha256
    activity_coefficients.species_ids = expected_species
    activity_coefficients.temperature_K = float(temperature_K)
    activity_coefficients.parameter_sha256 = canonical_digest(parameter_rows)
    activity_coefficients.phase_parameter_configuration_sha256 = request.parameter_configuration_sha256
    activity_coefficients.water_mass_per_solution_volume_kg_L = request.water_mass_per_solution_volume_kg_L
    activity_coefficients.debye_huckel_A_at_temperature = request.debye_huckel_A_at_temperature
    activity_coefficients.debye_huckel_B_at_temperature_sqrt_kg_mol_per_angstrom = request.debye_huckel_B_at_temperature_sqrt_kg_mol_per_angstrom
    activity_coefficients.evidence_sha256 = canonical_digest(
        [row.model_dump(mode="json") for row in request.evidence]
    )
    return activity_coefficients


def build_bdot_transport_saturation_callback(
    request: AqueousBdotIteration,
    *,
    screen_template: AqueousSaturationScreen,
    transport_species_ids: tuple[str, ...],
    saturation_provider_id: str,
    saturation_provider_revision: str,
):
    """Compose the B-dot transport adapter with a caller-reviewed Ksp screen."""
    expected_species = tuple(row.species_id for row in request.system.species)
    if tuple(transport_species_ids) != expected_species:
        raise ValueError("transport species order must exactly match the B-dot system")
    if tuple(row.species_id for row in screen_template.species) != expected_species:
        raise ValueError("saturation screen species order must exactly match the B-dot system")
    if screen_template.temperature_K != request.system.temperature_K:
        raise ValueError("saturation-screen temperature must match the B-dot system")
    if screen_template.activity_standard_state != "molality_relative_to_1_mol_per_kg_water":
        raise ValueError("B-dot saturation activities require the molality 1 mol/kg-water standard state")
    if not saturation_provider_id.strip() or not saturation_provider_revision.strip():
        raise ValueError("saturation provider identity and revision are required")

    gamma_callback = build_bdot_transport_activity_callback(
        request,
        transport_species_ids=transport_species_ids,
        temperature_K=float(screen_template.temperature_K),
    )
    water_mass = float(request.water_mass_per_solution_volume_kg_L)

    def activity_provider(time_s: float, cell_index: int, temperature_K: float, concentration_mol_m3):
        if temperature_K != request.system.temperature_K:
            raise ValueError("cell activity temperature differs from the reviewed B-dot system")
        concentration = np.asarray(concentration_mol_m3, dtype=float)
        if concentration.shape != (len(expected_species),):
            raise ValueError("cell composition must align with the exact B-dot species order")
        gamma_m = gamma_callback(float(time_s), concentration[:, None])[:, 0]
        molality = concentration / 1000.0 / water_mass
        activities = gamma_m * molality
        if not np.isfinite(activities).all() or np.any(activities < 0.0):
            raise ValueError("B-dot dimensionless molality activities must be finite and nonnegative")
        return {
            species_id: float(value)
            for species_id, value in zip(expected_species, activities, strict=True)
        }

    activity_provider.provider_id = request.parameter_provider_id
    activity_provider.provider_revision = request.parameter_provider_revision
    activity_provider.configuration_sha256 = gamma_callback.configuration_sha256
    activity_provider.record_sha256 = request.parameter_record_sha256
    activity_provider.source_request_sha256 = gamma_callback.source_request_sha256
    activity_provider.activity_standard_state = "molality_relative_to_1_mol_per_kg_water"
    activity_provider.species_ids = expected_species
    activity_provider.temperature_K = float(request.system.temperature_K)
    activity_provider.bdot_parameter_sha256 = gamma_callback.parameter_sha256
    activity_provider.bdot_evidence_sha256 = gamma_callback.evidence_sha256

    return build_transport_saturation_callback_from_activity_provider(
        screen_template,
        transport_species_ids=transport_species_ids,
        saturation_provider_id=saturation_provider_id,
        saturation_provider_revision=saturation_provider_revision,
        activity_provider_id=request.parameter_provider_id,
        activity_provider_revision=request.parameter_provider_revision,
        activity_provider_configuration_sha256=gamma_callback.configuration_sha256,
        activity_provider=activity_provider,
    )


def aqueous_sit_self_consistent_speciation(x: AqueousSITIteration) -> Calculation:
    """Couple caller-defined mass action to caller-owned, directional SIT data."""
    system = x.system
    input_digest = canonical_digest(x.model_dump(mode="json"))
    interaction_records = [row.model_dump(mode="json") for row in x.interactions]
    evidence_records = [row.model_dump(mode="json") for row in x.evidence]
    base = {
        "assessment_id": system.assessment_id,
        "solution_id": system.solution_id,
        "temperature_K": system.temperature_K,
        "activity_standard_state": "dimensionless_molarity_1_mol_L; SIT molality basis via caller water-mass conversion",
        "water_mass_per_solution_volume_kg_L": x.water_mass_per_solution_volume_kg_L,
        "activity_coefficient_mapping": "gamma_c=gamma_m/w; w=kg_water_per_L_solution",
        "ionic_strength_limit_mol_kg": x.ionic_strength_limit_mol_kg,
        "debye_huckel_A_at_temperature": x.debye_huckel_A_at_temperature,
        "A_evidence_source_id": x.A_evidence_source_id,
        "SIT_provider_id": x.sit_provider_id,
        "SIT_provider_revision": x.sit_provider_revision,
        "SIT_configuration_sha256": x.sit_configuration_sha256,
        "SIT_record_sha256": x.sit_record_sha256,
        "SIT_interaction_parameter_sha256": canonical_digest(interaction_records),
        "SIT_interaction_source_record_lineage_sha256": canonical_digest([
            {"target_species_id": row.target_species_id,
             "counter_species_id": row.counter_species_id,
             "evidence_source_id": row.evidence_source_id,
             "source_record_id": row.source_record_id,
             "evidence_sha256": row.evidence_sha256}
            for row in x.interactions
        ]),
        "SIT_evidence_bundle_sha256": canonical_digest(evidence_records),
        "input_sha256": input_digest,
    }
    reviews = {
        "water_mass_conversion_reviewed": x.water_mass_conversion_reviewed,
        "temperature_solvent_and_A_basis_reviewed": x.temperature_solvent_and_A_basis_reviewed,
        "molarity_to_molality_standard_state_mapping_reviewed": x.molarity_to_molality_standard_state_mapping_reviewed,
        "complete_inventory_and_charge_scope_reviewed": x.complete_inventory_and_charge_scope_reviewed,
        "interaction_parameter_set_completeness_and_applicability_reviewed": x.interaction_parameter_set_completeness_and_applicability_reviewed,
        "fixed_point_solver_settings_reviewed": x.fixed_point_solver_settings_reviewed,
        "single_liquid_no_precipitation_scope_reviewed": x.single_liquid_no_precipitation_scope_reviewed,
    }
    missing = [name for name, reviewed in reviews.items() if not reviewed]
    if missing:
        return Calculation(status="needs_data", values=base | {"missing_reviews": missing, "outer_iterations": 0}, notes=(
            "Review the water-mass and standard-state mapping, temperature-specific SIT parameter, directional interaction coverage and single-liquid applicability before iteration.",
        ))

    species = system.species
    gamma = np.asarray([row.activity_coefficient for row in species], dtype=float)
    history: list[dict] = []
    last_solution = None
    try:
        for iteration in range(1, x.maximum_outer_iterations + 1):
            iteration_system = system.model_copy(update={
                "species": tuple(
                    row.model_copy(update={"activity_coefficient": float(gamma[i])})
                    for i, row in enumerate(species)
                ),
                "activity_provider_id": x.sit_provider_id,
                "activity_provider_revision": x.sit_provider_revision,
                "activity_configuration_digest": x.sit_configuration_sha256,
                "activity_record_digest": x.sit_record_sha256,
            })
            solved = aqueous_mass_action_speciation(iteration_system)
            last_solution = solved
            if solved.status != "computed":
                return Calculation(status=solved.status, values=base | {
                    "outer_iterations": iteration,
                    "fixed_point_history": history,
                    "inner_solver_status": solved.status,
                    "inner_solver_values": solved.values,
                }, notes=("The fixed-activity mass-action subproblem did not converge; no outer SIT equilibrium is reported.", *solved.notes))
            concentrations = np.asarray([row["concentration_mol_L"] for row in solved.values["species"]], dtype=float)
            molalities = concentrations / x.water_mass_per_solution_volume_kg_L
            sit_input = SITActivityCoefficientInput(
                assessment_id=system.assessment_id,
                solution_id=system.solution_id,
                temperature_K=system.temperature_K,
                ionic_strength_limit_mol_kg=x.ionic_strength_limit_mol_kg,
                debye_huckel_A_at_temperature=x.debye_huckel_A_at_temperature,
                A_evidence_source_id=x.A_evidence_source_id,
                A_provider_id=x.sit_provider_id,
                A_provider_revision=x.sit_provider_revision,
                A_configuration_sha256=x.sit_configuration_sha256,
                A_record_sha256=x.sit_record_sha256,
                species=tuple(SITSpecies(
                    species_id=row.species_id,
                    species_label=row.species_id,
                    charge_number=row.charge_number,
                    molality_mol_kg=float(molalities[i]),
                ) for i, row in enumerate(species)),
                interactions=x.interactions,
                charge_balance_absolute_tolerance_mol_kg=x.charge_balance_tolerance_mol_kg,
                complete_ionic_inventory_reviewed=True,
                charge_balance_reviewed=True,
                ionic_strength_convention_reviewed=True,
                interaction_parameter_set_complete_and_applicable_reviewed=True,
                temperature_solvent_A_lineage_reviewed=True,
                evidence=x.evidence,
            )
            sit = sit_activity_coefficients(sit_input)
            if sit.status != "computed":
                return Calculation(status=sit.status, values=base | {
                    "outer_iterations": iteration,
                    "fixed_point_history": history,
                    "SIT_activity_status": sit.status,
                    "SIT_activity_values": sit.values,
                }, notes=("The speciation-derived SIT calculation did not satisfy declared charge or ionic-strength support.", *sit.notes))
            target_gamma_molality = np.asarray(
                [row["activity_coefficient"] for row in sit.values["species"]], dtype=float
            )
            target_gamma = molality_gamma_to_molarity_standard_state(
                target_gamma_molality, x.water_mass_per_solution_volume_kg_L
            )
            ionic_strength = float(sit.values["ionic_strength_mol_kg"])
            charge_residual = float(sit.values["charge_balance_residual_mol_kg"])
            log_residual = float(np.max(np.abs(np.log(target_gamma) - np.log(gamma))))
            history.append({
                "iteration": iteration,
                "ionic_strength_mol_kg": ionic_strength,
                "charge_balance_residual_mol_kg": charge_residual,
                "maximum_log_gamma_fixed_point_residual": log_residual,
                "inner_normalized_residual_norm": solved.values["normalized_residual_norm"],
            })
            if not math.isfinite(log_residual):
                raise ArithmeticError("SIT activity fixed-point residual is not finite")
            if log_residual <= x.log_gamma_tolerance:
                output_species = []
                for i, row in enumerate(solved.values["species"]):
                    output_species.append({
                        **row,
                        "molality_mol_kg": float(molalities[i]),
                        "ionic_strength_contribution_mol_kg": float(0.5 * molalities[i] * species[i].charge_number**2),
                        "SIT_target_molality_activity_coefficient": float(target_gamma_molality[i]),
                        "SIT_target_molarity_activity_coefficient": float(target_gamma[i]),
                        "activity_coefficient_fixed_point_residual_ln": float(math.log(target_gamma[i] / gamma[i])),
                    })
                return Calculation(values=base | {
                    "outer_iterations": iteration,
                    "ionic_strength_mol_kg": ionic_strength,
                    "charge_balance_residual_mol_kg": charge_residual,
                    "maximum_log_gamma_fixed_point_residual": log_residual,
                    "fixed_point_history": history,
                    "species": output_species,
                    "constraint_closure": solved.values["constraint_closure"],
                    "reaction_closure": solved.values["reaction_closure"],
                    "inner_normalized_residual_norm": solved.values["normalized_residual_norm"],
                    "converged": True,
                    "aqueous_liquid_only": True,
                }, notes=(
                    "A damped fixed-point iteration couples caller-defined single-liquid mass-action speciation to caller-parameterized SIT coefficients calculated from the resulting molal ionic strength and declared directional interactions.",
                    "The interaction set, temperature-specific Debye-Huckel A, water-mass conversion, standard-state mapping, equilibrium constants and balance equations remain caller-supplied. No species, phase, precipitation kinetics or corrosion rate is inferred.",
                ))
            gamma = np.exp(np.log(gamma) + x.damping_fraction * (np.log(target_gamma) - np.log(gamma)))
            if np.any(~np.isfinite(gamma)) or np.any(gamma <= 0.0):
                raise ArithmeticError("damped SIT activity update is not finite and positive")
    except (ArithmeticError, FloatingPointError, OverflowError, ValueError) as error:
        return Calculation(status="out_of_scope", values=base | {
            "outer_iterations": len(history),
            "out_of_scope_reason": str(error),
            "fixed_point_history": history,
            "inner_solver_status": last_solution.status if last_solution is not None else None,
        }, notes=("The coupled SIT/mass-action iteration encountered an unsupported or nonfinite state; no partial last iterate is promoted as an equilibrium.",))
    return Calculation(status="out_of_scope", values=base | {
        "outer_iterations": len(history),
        "out_of_scope_reason": "SIT_activity_fixed_point_not_converged",
        "maximum_log_gamma_fixed_point_residual": history[-1]["maximum_log_gamma_fixed_point_residual"] if history else None,
        "fixed_point_history": history,
        "inner_solver_status": last_solution.status if last_solution is not None else None,
    }, notes=("The caller outer-iteration budget ended before the declared log-coefficient tolerance was met; the unconverged last iterate is not returned as an equilibrium.",))


def build_sit_transport_activity_callback(
    request: AqueousSITIteration,
    *,
    transport_species_ids: tuple[str, ...],
    temperature_K: float,
):
    """Build a provenance-bound SIT activity-coefficient callback for transport.

    Concentrations use mol/m3 in species-by-mouth-plus-cell order. The adapter
    evaluates the caller-declared SIT expression at each transport location;
    it does not solve local speciation or impose a local charge-balance rule.
    """
    expected_species = tuple(row.species_id for row in request.system.species)
    if tuple(transport_species_ids) != expected_species:
        raise ValueError("transport species order must exactly match the SIT system")
    if temperature_K != request.system.temperature_K:
        raise ValueError("transport temperature must match the SIT system temperature")
    if len(set(transport_species_ids)) != len(transport_species_ids):
        raise ValueError("transport species identifiers must be unique")
    reviews = (
        request.water_mass_conversion_reviewed,
        request.temperature_solvent_and_A_basis_reviewed,
        request.molarity_to_molality_standard_state_mapping_reviewed,
        request.complete_inventory_and_charge_scope_reviewed,
        request.interaction_parameter_set_completeness_and_applicability_reviewed,
        request.single_liquid_no_precipitation_scope_reviewed,
    )
    if not all(reviews):
        raise ValueError("all SIT transport applicability and standard-state reviews are required")

    charges = np.asarray([row.charge_number for row in request.system.species], dtype=float)
    interaction_matrix = np.zeros((len(expected_species), len(expected_species)), dtype=float)
    index = {species_id: i for i, species_id in enumerate(expected_species)}
    for row in request.interactions:
        interaction_matrix[index[row.target_species_id], index[row.counter_species_id]] = row.epsilon_kg_mol
    water_mass = float(request.water_mass_per_solution_volume_kg_L)
    ionic_strength_limit = float(request.ionic_strength_limit_mol_kg)
    A = float(request.debye_huckel_A_at_temperature)

    def activity_coefficients(time_s: float, concentration_mol_m3: np.ndarray) -> np.ndarray:
        if not math.isfinite(float(time_s)):
            raise ValueError("transport time must be finite")
        concentration = np.asarray(concentration_mol_m3, dtype=float)
        if concentration.ndim != 2 or concentration.shape[0] != len(expected_species):
            raise ValueError("SIT callback expects species-by-mouth-plus-cell concentration values")
        if not np.isfinite(concentration).all() or np.any(concentration < 0.0):
            raise ValueError("transport concentrations must be finite and nonnegative")
        molality = concentration / 1000.0 / water_mass
        ionic_strength = 0.5 * np.sum(charges[:, None] ** 2 * molality, axis=0)
        if not np.isfinite(ionic_strength).all() or np.any(ionic_strength > ionic_strength_limit):
            raise ValueError("transport ionic strength exceeds the declared SIT limit")
        root_strength = np.sqrt(ionic_strength)
        debye_term = A * root_strength / (1.0 + 1.5 * root_strength)
        log10_gamma = -(charges[:, None] ** 2) * debye_term[None, :]
        log10_gamma += interaction_matrix @ molality
        log_gamma = log10_gamma * math.log(10.0)
        if not np.isfinite(log_gamma).all() or np.any(log_gamma > math.log(np.finfo(float).max)):
            raise ValueError("SIT activity coefficient exceeds finite binary64 support")
        gamma = np.exp(log_gamma)
        if not np.isfinite(gamma).all() or np.any(gamma <= 0.0):
            raise ValueError("SIT activity coefficients must be finite and positive")
        return gamma

    request_sha256 = canonical_digest(request.model_dump(mode="json"))
    activity_coefficients.provider_id = request.sit_provider_id
    activity_coefficients.provider_revision = request.sit_provider_revision
    activity_coefficients.configuration_sha256 = canonical_digest({
        "adapter": "matintegrity.sit_transport_activity_callback.v1",
        "sit_provider_id": request.sit_provider_id,
        "sit_provider_revision": request.sit_provider_revision,
        "sit_provider_configuration_sha256": request.sit_configuration_sha256,
        "sit_record_sha256": request.sit_record_sha256,
        "request_sha256": request_sha256,
        "species_ids": list(expected_species),
        "temperature_K": float(temperature_K),
        "concentration_unit": "mol/m3",
        "activity_standard_state": "molality_relative_to_1_mol_per_kg_water",
    })
    activity_coefficients.record_sha256 = request.sit_record_sha256
    activity_coefficients.source_request_sha256 = request_sha256
    activity_coefficients.species_ids = expected_species
    activity_coefficients.temperature_K = float(temperature_K)
    activity_coefficients.sit_interaction_parameter_sha256 = canonical_digest(
        [row.model_dump(mode="json") for row in request.interactions]
    )
    activity_coefficients.sit_provider_configuration_sha256 = request.sit_configuration_sha256
    activity_coefficients.phase_parameter_configuration_sha256 = request.sit_configuration_sha256
    activity_coefficients.water_mass_per_solution_volume_kg_L = request.water_mass_per_solution_volume_kg_L
    activity_coefficients.debye_huckel_A_at_temperature = request.debye_huckel_A_at_temperature
    activity_coefficients.sit_evidence_sha256 = canonical_digest(
        [row.model_dump(mode="json") for row in request.evidence]
    )
    return activity_coefficients


def build_sit_transport_saturation_callback(
    request: AqueousSITIteration,
    *,
    screen_template: AqueousSaturationScreen,
    transport_species_ids: tuple[str, ...],
    saturation_provider_id: str,
    saturation_provider_revision: str,
):
    """Compose SIT activities with a reviewed Ksp screen for kinetic transport.

    The returned callback maps each post-transport cell composition to
    caller-declared solid saturation ratios. Solid rates and inventory updates
    remain the responsibility of the competing-solid kinetic ledger.
    """
    expected_species = tuple(row.species_id for row in request.system.species)
    if tuple(transport_species_ids) != expected_species:
        raise ValueError("transport species order must exactly match the SIT system")
    if tuple(row.species_id for row in screen_template.species) != expected_species:
        raise ValueError("saturation screen species order must exactly match the SIT system")
    if screen_template.temperature_K != request.system.temperature_K:
        raise ValueError("saturation-screen temperature must match the SIT system")
    if screen_template.activity_standard_state != "molality_relative_to_1_mol_per_kg_water":
        raise ValueError("SIT saturation activities require the molality 1 mol/kg-water standard state")
    if not saturation_provider_id.strip() or not saturation_provider_revision.strip():
        raise ValueError("saturation provider identity and revision are required")

    gamma_callback = build_sit_transport_activity_callback(
        request,
        transport_species_ids=transport_species_ids,
        temperature_K=float(screen_template.temperature_K),
    )
    water_mass = float(request.water_mass_per_solution_volume_kg_L)

    def activity_provider(time_s: float, cell_index: int, temperature_K: float, concentration_mol_m3):
        if temperature_K != request.system.temperature_K:
            raise ValueError("cell activity temperature differs from the reviewed SIT system")
        concentration = np.asarray(concentration_mol_m3, dtype=float)
        if concentration.shape != (len(expected_species),):
            raise ValueError("cell composition must align with the exact SIT species order")
        gamma = gamma_callback(float(time_s), concentration[:, None])[:, 0]
        molality = concentration / 1000.0 / water_mass
        activities = gamma * molality
        if not np.isfinite(activities).all() or np.any(activities < 0.0):
            raise ValueError("SIT dimensionless molality activities must be finite and nonnegative")
        return {species_id: float(value) for species_id, value in zip(expected_species, activities, strict=True)}

    activity_provider.provider_id = request.sit_provider_id
    activity_provider.provider_revision = request.sit_provider_revision
    activity_provider.configuration_sha256 = gamma_callback.configuration_sha256
    activity_provider.record_sha256 = request.sit_record_sha256
    activity_provider.source_request_sha256 = gamma_callback.source_request_sha256
    activity_provider.activity_standard_state = "molality_relative_to_1_mol_per_kg_water"
    activity_provider.species_ids = expected_species
    activity_provider.temperature_K = float(request.system.temperature_K)
    activity_provider.sit_interaction_parameter_sha256 = gamma_callback.sit_interaction_parameter_sha256
    activity_provider.sit_evidence_sha256 = gamma_callback.sit_evidence_sha256

    return build_transport_saturation_callback_from_activity_provider(
        screen_template,
        transport_species_ids=transport_species_ids,
        saturation_provider_id=saturation_provider_id,
        saturation_provider_revision=saturation_provider_revision,
        activity_provider_id=request.sit_provider_id,
        activity_provider_revision=request.sit_provider_revision,
        activity_provider_configuration_sha256=activity_provider.configuration_sha256,
        activity_provider=activity_provider,
    )


def specifications() -> list[ModelSpec]:
    return [
        ModelSpec(
            "chemistry.aqueous_bdot_self_consistent_speciation",
            AqueousBdotIteration,
            aqueous_bdot_self_consistent_speciation,
            {
                "temperature_K": "K",
                "ionic_strength_mol_kg": "mol/kg",
                "charge_balance_residual_mol_kg": "mol/kg",
                "water_mass_per_solution_volume_kg_L": "kg/L",
                "species.activity_coefficient": "1",
                "species.Bdot_target_log10_gamma_molality": "1",
                "species.Bdot_target_gamma_molality": "1",
                "species.Bdot_target_gamma_molarity_standard_state": "1",
                "species.dimensionless_activity": "1",
                "species.concentration_mol_L": "mol/L",
                "species.molality_mol_kg": "mol/kg",
                "species.ionic_strength_contribution_mol_kg": "mol/kg",
                "species.activity_coefficient_fixed_point_residual_ln": "1",
                "maximum_log_gamma_fixed_point_residual": "1",
                "inner_normalized_residual_norm": "1",
                "outer_iterations": "1",
            },
            (
                "Caller-defined aqueous mass-action balances are iterated with species-specific extended Debye-Huckel B-dot coefficients evaluated from the resulting molal ionic strength.",
                "Requires caller-supplied temperature-specific A and B constants, water-mass conversion, ion-size and B-dot parameter records, explicit support limits, evidence, and reviewed molarity-to-molality activity mapping.",
                "The solver retains a molarity 1 mol/L standard state and maps molality coefficients by gamma_c=gamma_m/w, where w is kg water per L solution.",
                "A neutral-species B-dot term is used only when explicitly supplied by the caller; no salting law, missing parameter, phase, precipitation, corrosion rate, or acceptance criterion is inferred.",
            ),
            (
                "caller_general_aqueous_mass_action_speciation",
                "usgs_phreeqc_llnl_bdot_activity",
                "molality_to_molarity_activity_standard_state_bridge",
            ),
            qualification="user_model",
        ),
        ModelSpec(
            "chemistry.aqueous_davies_self_consistent_speciation",
            AqueousDaviesIteration,
            aqueous_davies_self_consistent_speciation,
            {
                "temperature_K": "K",
                "ionic_strength_mol_kg": "mol/kg",
                "charge_balance_residual_mol_kg": "mol/kg",
                "species.activity_coefficient": "1",
                "species.davies_target_molality_activity_coefficient": "1",
                "species.davies_target_molarity_activity_coefficient": "1",
                "species.dimensionless_activity": "1",
                "species.concentration_mol_L": "mol/L",
                "species.molality_mol_kg": "mol/kg",
                "species.ionic_strength_contribution_mol_kg": "mol/kg",
                "species.activity_coefficient_fixed_point_residual_ln": "1",
                "maximum_log_gamma_fixed_point_residual": "1",
                "inner_normalized_residual_norm": "1",
                "outer_iterations": "1",
            },
            (
                "Caller-defined square aqueous equilibrium/constraint system is solved repeatedly while Davies coefficients are recalculated from speciation-derived molal ionic strength.",
                "Requires caller water-mass-per-solution-volume conversion, temperature-specific Davies A, charge tolerance and explicit single-liquid applicability; ionic strength is limited to the declared ceiling no greater than 0.5 mol/kg.",
                "The mass-action solver uses the molarity standard state; Davies molality gamma is mapped by gamma_c=gamma_m/w and both values are reported.",
                "No species, reactions, charge constraints, gas/solid phases, kinetic scale, salting-out, corrosion rate or acceptance are inferred.",
            ),
            ("caller_general_aqueous_mass_action_speciation", "usgs_phreeqc_davies_activity_coefficients", "usgs_davies_ionic_strength_approximation", "molality_to_molarity_activity_standard_state_bridge"),
            qualification="user_model",
        ),
        ModelSpec(
            "chemistry.aqueous_sit_self_consistent_speciation",
            AqueousSITIteration,
            aqueous_sit_self_consistent_speciation,
            {
                "temperature_K": "K",
                "ionic_strength_mol_kg": "mol/kg",
                "charge_balance_residual_mol_kg": "mol/kg",
                "water_mass_per_solution_volume_kg_L": "kg/L",
                "species.activity_coefficient": "1",
                "species.SIT_target_molality_activity_coefficient": "1",
                "species.SIT_target_molarity_activity_coefficient": "1",
                "species.dimensionless_activity": "1",
                "species.concentration_mol_L": "mol/L",
                "species.molality_mol_kg": "mol/kg",
                "species.ionic_strength_contribution_mol_kg": "mol/kg",
                "species.activity_coefficient_fixed_point_residual_ln": "1",
                "maximum_log_gamma_fixed_point_residual": "1",
                "inner_normalized_residual_norm": "1",
                "outer_iterations": "1",
            },
            (
                "Caller-defined square aqueous mass-action equations are iterated with caller-parameterized SIT coefficients evaluated from the resulting molal ionic inventory and directional interaction records.",
                "Requires explicit water-mass conversion, standard-state mapping, temperature-specific Debye-Huckel A, interaction parameter provenance and a complete applicable directional parameter set; ionic strength cannot exceed 6 mol/kg.",
                "The mass-action solver uses the molarity standard state; SIT molality gamma is mapped by gamma_c=gamma_m/w and both values are reported.",
                "The API does not infer reactions, parameter values, phase stability, precipitation kinetics, salting effects outside the declared SIT expression, corrosion rates or model qualification.",
            ),
            (
                "caller_general_aqueous_mass_action_speciation",
                "nea_thermochemical_database_sit_method",
                "usgs_phreeqc_sit_model_documentation",
                "molality_to_molarity_activity_standard_state_bridge",
            ),
            qualification="user_model",
        ),
    ]
