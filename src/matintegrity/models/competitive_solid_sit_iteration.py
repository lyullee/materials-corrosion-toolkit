"""Self-consistent caller-parameterized SIT iteration for competing solids."""

from __future__ import annotations

import math
from typing import Literal

import numpy as np
from pydantic import Field

from ..competing_solid_equilibrium import CompetitiveSolidEquilibrium, evaluate_competitive_solid_equilibrium
from ..contracts import Calculation, Contract, Evidence, Positive, canonical_digest
from ..registry import ModelSpec
from .aqueous_activity_iteration import molality_gamma_to_molarity_standard_state
from .sit_activity import (
    IMPLEMENTATION_SOURCE_ID,
    SOURCE_ID,
    SITActivityCoefficientInput,
    SITInteraction,
    SITSpecies,
    sit_activity_coefficients,
)


class CompetitiveSolidSITIteration(Contract):
    schema_version: Literal["matintegrity.competitive_solid_sit_iteration.v1"] = "matintegrity.competitive_solid_sit_iteration.v1"
    equilibrium: CompetitiveSolidEquilibrium
    water_mass_per_solution_volume_kg_L: Positive
    debye_huckel_A_at_temperature: Positive
    A_evidence_source_id: str = Field(min_length=1)
    provider_id: str = Field(min_length=1)
    provider_revision: str = Field(min_length=1)
    configuration_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    record_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    interactions: tuple[SITInteraction, ...] = Field(default=(), max_length=100_000)
    evidence: tuple[Evidence, ...] = Field(min_length=1)
    ionic_strength_limit_mol_kg: Positive = Field(le=6.0)
    charge_balance_tolerance_mol_kg: Positive
    maximum_outer_iterations: int = Field(default=100, ge=1, le=1000)
    log_gamma_tolerance: Positive = Field(default=1e-9, le=1e-3)
    damping_fraction: Positive = Field(default=0.5, le=1.0)
    water_mass_conversion_reviewed: bool
    temperature_solvent_A_and_standard_state_reviewed: bool
    molarity_standard_state_mapping_reviewed: bool
    complete_interaction_set_and_applicability_reviewed: bool
    competing_solid_sit_applicability_reviewed: bool
    charge_scope_and_solver_settings_reviewed: bool


def competitive_solid_sit_self_consistent_equilibrium(request: CompetitiveSolidSITIteration) -> Calculation:
    """Iterate a caller-defined neutral-solid equilibrium with explicit SIT parameters.

    Every species, balanced reaction, candidate phase, equilibrium constant, interaction
    coefficient and evidence record remains caller-owned. Missing directional SIT pairs
    contribute zero only after the caller's complete-set review.
    """
    equilibrium = request.equilibrium
    digest = canonical_digest(request.model_dump(mode="json"))
    base = {
        "equilibrium_id": equilibrium.equilibrium_id,
        "temperature_K": equilibrium.temperature_K,
        "input_digest": digest,
        "activity_model": "caller-parameterized SIT on molality standard state mapped to the equilibrium activity basis",
        "provider_id": request.provider_id,
        "provider_revision": request.provider_revision,
        "configuration_sha256": request.configuration_sha256,
        "record_sha256": request.record_sha256,
        "water_mass_per_solution_volume_kg_L": request.water_mass_per_solution_volume_kg_L,
        "ionic_strength_limit_mol_kg": request.ionic_strength_limit_mol_kg,
    }
    reviews = {
        "water_mass_conversion_reviewed": request.water_mass_conversion_reviewed,
        "temperature_solvent_A_and_standard_state_reviewed": request.temperature_solvent_A_and_standard_state_reviewed,
        "molarity_standard_state_mapping_reviewed": request.molarity_standard_state_mapping_reviewed,
        "complete_interaction_set_and_applicability_reviewed": request.complete_interaction_set_and_applicability_reviewed,
        "competing_solid_sit_applicability_reviewed": request.competing_solid_sit_applicability_reviewed,
        "charge_scope_and_solver_settings_reviewed": request.charge_scope_and_solver_settings_reviewed,
        "candidate_phase_set_completeness_reviewed": equilibrium.candidate_phase_set_completeness_reviewed,
        "equilibrium_constant_temperature_and_computational_use_reviewed": equilibrium.equilibrium_constant_temperature_and_computational_use_reviewed,
        "single_liquid_fixed_volume_and_neutral_solid_assumptions_reviewed": equilibrium.single_liquid_fixed_volume_and_neutral_solid_assumptions_reviewed,
        "fixed_activity_coefficients_and_standard_states_reviewed": equilibrium.fixed_activity_coefficients_and_standard_states_reviewed,
    }
    missing = [name for name, reviewed in reviews.items() if not reviewed]
    if missing:
        return Calculation(status="needs_data", values=base | {"missing_reviews": missing, "outer_iterations": 0}, notes=(
            "Review the complete aqueous and phase inventories, charge closure, water conversion, standard states, SIT parameter lineage and interaction coverage before iteration.",
        ))
    if any(not math.isclose(row.activity_reference_concentration_mol_m3, 1000.0, rel_tol=0.0, abs_tol=1e-12) for row in equilibrium.aqueous_species):
        return Calculation(status="needs_data", values=base | {"missing_reviews": ["activity_reference_concentration_mol_m3_equals_1000_mol_m3"], "outer_iterations": 0}, notes=(
            "This adapter maps SIT molality standard state to a 1 mol/L concentration standard state; provide a reviewed matching reference concentration or use a separately derived conversion.",
        ))
    evidence_by_id = {row.source_id: row for row in request.evidence}
    if len(evidence_by_id) != len(request.evidence) or request.A_evidence_source_id not in evidence_by_id:
        return Calculation(status="needs_data", values=base | {"out_of_scope_reason": "missing_or_duplicate_SIT_evidence_source", "outer_iterations": 0})
    if evidence_by_id[request.A_evidence_source_id].sha256 is None:
        return Calculation(status="needs_data", values=base | {"out_of_scope_reason": "SIT_A_parameter_evidence_missing_sha256", "outer_iterations": 0})
    if any(row.evidence_source_id not in evidence_by_id or evidence_by_id[row.evidence_source_id].sha256 != row.evidence_sha256 for row in request.interactions):
        return Calculation(status="needs_data", values=base | {"out_of_scope_reason": "SIT_interaction_evidence_digest_mismatch", "outer_iterations": 0})

    species = equilibrium.aqueous_species
    gamma = np.asarray([row.activity_coefficient for row in species], dtype=float)
    charges = [row.charge_number for row in species]
    history: list[dict] = []
    last_solved: dict | None = None
    try:
        for iteration in range(1, request.maximum_outer_iterations + 1):
            local = CompetitiveSolidEquilibrium.model_validate(equilibrium.model_dump(mode="python") | {
                "aqueous_species": tuple(row.model_dump(mode="python") | {"activity_coefficient": float(gamma[i])} for i, row in enumerate(species))
            })
            solved = evaluate_competitive_solid_equilibrium(local)
            last_solved = solved
            if solved.get("status") != "computed":
                return Calculation(status=solved.get("status", "out_of_scope"), values=base | {
                    "outer_iterations": iteration,
                    "fixed_point_history": history,
                    "inner_solver_status": solved.get("status"),
                    "inner_solver_values": {key: value for key, value in solved.items() if key != "status"},
                }, notes=("The fixed-activity phase-equilibrium subproblem did not converge; no coupled SIT result is promoted.",))
            molality = [solved["final_aqueous_concentration_mol_m3"][row.species_id] / (1000.0 * request.water_mass_per_solution_volume_kg_L) for row in species]
            ionic_strength = 0.5 * math.fsum(m * z * z for m, z in zip(molality, charges, strict=True))
            charge_residual = math.fsum(m * z for m, z in zip(molality, charges, strict=True))
            if not math.isfinite(ionic_strength) or ionic_strength > request.ionic_strength_limit_mol_kg:
                return Calculation(status="out_of_scope", values=base | {"outer_iterations": iteration, "ionic_strength_mol_kg": ionic_strength, "out_of_scope_reason": "ionic_strength_exceeds_caller_declared_SIT_limit", "fixed_point_history": history})
            if not math.isfinite(charge_residual) or abs(charge_residual) > request.charge_balance_tolerance_mol_kg:
                return Calculation(status="needs_data", values=base | {"outer_iterations": iteration, "ionic_strength_mol_kg": ionic_strength, "charge_balance_residual_mol_kg": charge_residual, "out_of_scope_reason": "competing_solid_liquid_charge_balance_tolerance_exceeded", "fixed_point_history": history})
            sit_input = SITActivityCoefficientInput(
                assessment_id=equilibrium.equilibrium_id,
                solution_id=equilibrium.equilibrium_id,
                temperature_K=equilibrium.temperature_K,
                ionic_strength_limit_mol_kg=request.ionic_strength_limit_mol_kg,
                debye_huckel_A_at_temperature=request.debye_huckel_A_at_temperature,
                A_evidence_source_id=request.A_evidence_source_id,
                A_provider_id=request.provider_id,
                A_provider_revision=request.provider_revision,
                A_configuration_sha256=request.configuration_sha256,
                A_record_sha256=request.record_sha256,
                species=tuple(SITSpecies(species_id=row.species_id, species_label=row.species_id, charge_number=row.charge_number, molality_mol_kg=float(molality[i])) for i, row in enumerate(species)),
                interactions=request.interactions,
                charge_balance_absolute_tolerance_mol_kg=request.charge_balance_tolerance_mol_kg,
                complete_ionic_inventory_reviewed=True,
                charge_balance_reviewed=True,
                ionic_strength_convention_reviewed=True,
                interaction_parameter_set_complete_and_applicable_reviewed=True,
                temperature_solvent_A_lineage_reviewed=True,
                evidence=request.evidence,
            )
            sit = sit_activity_coefficients(sit_input)
            if sit.status != "computed":
                return Calculation(status=sit.status, values=base | {"outer_iterations": iteration, "SIT_activity_status": sit.status, "SIT_activity_values": sit.values, "fixed_point_history": history})
            target_gamma = molality_gamma_to_molarity_standard_state(
                np.asarray([row["activity_coefficient"] for row in sit.values["species"]], dtype=float),
                request.water_mass_per_solution_volume_kg_L,
            )
            residual = float(np.max(np.abs(np.log(target_gamma) - np.log(gamma))))
            history.append({"iteration": iteration, "ionic_strength_mol_kg": ionic_strength, "charge_balance_residual_mol_kg": charge_residual, "maximum_log_gamma_fixed_point_residual": residual, "inner_optimizer_iterations": solved.get("optimizer_iterations")})
            if not math.isfinite(residual):
                raise ArithmeticError("SIT fixed-point residual is nonfinite")
            if residual <= request.log_gamma_tolerance:
                values = {key: value for key, value in solved.items() if key not in {"status", "basis"}}
                values.update(base | {
                    "outer_iterations": iteration,
                    "ionic_strength_mol_kg": ionic_strength,
                    "charge_balance_residual_mol_kg": charge_residual,
                    "maximum_log_gamma_fixed_point_residual": residual,
                    "activity_coefficient_by_species": {row.species_id: float(gamma[i]) for i, row in enumerate(species)},
                    "SIT_target_activity_coefficient_by_species": {row.species_id: float(target_gamma[i]) for i, row in enumerate(species)},
                    "molality_by_species_mol_kg": {row.species_id: float(molality[i]) for i, row in enumerate(species)},
                    "fixed_point_history": history,
                })
                return Calculation(values=values, notes=(
                    "Caller-declared competing neutral pure-solid equilibrium is iterated with caller-parameterized SIT coefficients recalculated from the resulting liquid ionic composition.",
                    "Species, balanced reactions, candidate phases, equilibrium constants, SIT interactions, parameter evidence and water conversion remain caller-owned. This does not infer concentrated-mixture qualification, precipitation kinetics, phase discovery or corrosion rates.",
                ))
            gamma = np.exp(np.log(gamma) + request.damping_fraction * (np.log(target_gamma) - np.log(gamma)))
            if np.any(~np.isfinite(gamma)) or np.any(gamma <= 0.0):
                raise ArithmeticError("damped SIT activity update is not finite and positive")
    except (ArithmeticError, FloatingPointError, OverflowError, ValueError, np.linalg.LinAlgError) as error:
        return Calculation(status="out_of_scope", values=base | {"outer_iterations": len(history), "out_of_scope_reason": str(error), "fixed_point_history": history, "inner_solver_status": last_solved.get("status") if last_solved else None})
    return Calculation(status="out_of_scope", values=base | {"outer_iterations": len(history), "out_of_scope_reason": "competitive_solid_SIT_fixed_point_not_converged", "maximum_log_gamma_fixed_point_residual": history[-1]["maximum_log_gamma_fixed_point_residual"] if history else None, "fixed_point_history": history, "inner_solver_status": last_solved.get("status") if last_solved else None})


def specifications() -> list[ModelSpec]:
    return [ModelSpec(
        "chemistry.competitive_solid_sit_equilibrium",
        CompetitiveSolidSITIteration,
        competitive_solid_sit_self_consistent_equilibrium,
        {"temperature_K": "K", "ionic_strength_mol_kg": "mol/kg", "charge_balance_residual_mol_kg": "mol/kg", "activity_coefficient_by_species.*": "1", "SIT_target_activity_coefficient_by_species.*": "1", "molality_by_species_mol_kg.*": "mol/kg", "maximum_log_gamma_fixed_point_residual": "1", "outer_iterations": "1"},
        ("The caller supplies source-linked directional SIT interactions, temperature-specific A, standard-state mapping and complete phase chemistry; aqueous ionic strength is limited to the caller ceiling, capped at 6 mol/kg.", "No phase or species discovery, precipitation kinetics, corrosion rate or concentrated-mixture qualification is inferred."),
        ("competitive_pure_solid_fixed_gamma_equilibrium", SOURCE_ID, IMPLEMENTATION_SOURCE_ID),
        qualification="user_model",
    )]
