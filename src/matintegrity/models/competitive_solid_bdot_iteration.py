"""Self-consistent extended Debye-Huckel B-dot coupling for caller phases."""

from __future__ import annotations

import math
from typing import Literal

import numpy as np
from pydantic import Field

from ..competing_solid_equilibrium import CompetitiveSolidEquilibrium, evaluate_competitive_solid_equilibrium
from ..contracts import Calculation, Contract, Evidence, Positive, canonical_digest
from ..registry import ModelSpec
from .aqueous_activity_iteration import (
    BdotSpeciesParameter,
    _aqueous_bdot_log10_gamma,
    molality_gamma_to_molarity_standard_state,
)


class CompetitiveSolidBdotIteration(Contract):
    schema_version: Literal["matintegrity.competitive_solid_bdot_iteration.v1"] = "matintegrity.competitive_solid_bdot_iteration.v1"
    equilibrium: CompetitiveSolidEquilibrium
    water_mass_per_solution_volume_kg_L: Positive
    debye_huckel_A_at_temperature: Positive
    debye_huckel_B_at_temperature_sqrt_kg_mol_per_angstrom: Positive
    parameter_temperature_K: Positive
    temperature_match_tolerance_K: float = Field(default=0.01, ge=0.0, le=5.0)
    provider_id: str = Field(min_length=1)
    provider_revision: str = Field(min_length=1)
    configuration_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    parameter_record_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    species_parameters: tuple[BdotSpeciesParameter, ...] = Field(min_length=1, max_length=100)
    evidence: tuple[Evidence, ...] = Field(min_length=1)
    maximum_supported_ionic_strength_mol_kg: Positive
    charge_balance_tolerance_mol_kg: Positive
    maximum_outer_iterations: int = Field(default=100, ge=1, le=1000)
    log_gamma_tolerance: Positive = Field(default=1e-9, le=1e-3)
    damping_fraction: Positive = Field(default=0.5, le=1.0)
    water_mass_conversion_reviewed: bool
    temperature_parameter_and_standard_state_reviewed: bool
    complete_species_parameter_set_and_applicability_reviewed: bool
    competing_solid_bdot_applicability_reviewed: bool
    charge_scope_and_solver_settings_reviewed: bool


def competitive_solid_bdot_self_consistent_equilibrium(request: CompetitiveSolidBdotIteration) -> Calculation:
    """Iterate neutral-solid Gibbs equilibrium with evidence-bound B-dot coefficients."""
    equilibrium = request.equilibrium
    species = equilibrium.aqueous_species
    parameter_rows = request.species_parameters
    digest = canonical_digest(request.model_dump(mode="json"))
    base = {
        "equilibrium_id": equilibrium.equilibrium_id,
        "temperature_K": equilibrium.temperature_K,
        "parameter_temperature_K": request.parameter_temperature_K,
        "input_digest": digest,
        "provider_id": request.provider_id,
        "provider_revision": request.provider_revision,
        "configuration_sha256": request.configuration_sha256,
        "parameter_record_sha256": request.parameter_record_sha256,
        "water_mass_per_solution_volume_kg_L": request.water_mass_per_solution_volume_kg_L,
        "maximum_supported_ionic_strength_mol_kg": request.maximum_supported_ionic_strength_mol_kg,
        "activity_model": "caller-parameterized extended Debye-Huckel B-dot",
        "activity_standard_state": "1 mol/L concentration; molality gamma mapped by gamma_c=gamma_m/w",
    }
    reviews = {
        "water_mass_conversion_reviewed": request.water_mass_conversion_reviewed,
        "temperature_parameter_and_standard_state_reviewed": request.temperature_parameter_and_standard_state_reviewed,
        "complete_species_parameter_set_and_applicability_reviewed": request.complete_species_parameter_set_and_applicability_reviewed,
        "competing_solid_bdot_applicability_reviewed": request.competing_solid_bdot_applicability_reviewed,
        "charge_scope_and_solver_settings_reviewed": request.charge_scope_and_solver_settings_reviewed,
        "candidate_phase_set_completeness_reviewed": equilibrium.candidate_phase_set_completeness_reviewed,
        "fixed_activity_coefficients_and_standard_states_reviewed": equilibrium.fixed_activity_coefficients_and_standard_states_reviewed,
        "equilibrium_constant_temperature_and_computational_use_reviewed": equilibrium.equilibrium_constant_temperature_and_computational_use_reviewed,
        "single_liquid_fixed_volume_and_neutral_solid_assumptions_reviewed": equilibrium.single_liquid_fixed_volume_and_neutral_solid_assumptions_reviewed,
    }
    missing = [name for name, reviewed in reviews.items() if not reviewed]
    if missing:
        return Calculation(status="needs_data", values=base | {"missing_reviews": missing, "outer_iterations": 0})
    if any(not math.isclose(row.activity_reference_concentration_mol_m3, 1000.0, rel_tol=0.0, abs_tol=1e-12) for row in species):
        return Calculation(status="needs_data", values=base | {"missing_reviews": ["activity_reference_concentration_mol_m3_equals_1000_mol_m3"], "outer_iterations": 0}, notes=(
            "The B-dot adapter maps molality gamma to a 1 mol/L concentration reference; another concentration standard state requires its own reviewed conversion.",
        ))
    if abs(equilibrium.temperature_K - request.parameter_temperature_K) > request.temperature_match_tolerance_K:
        return Calculation(status="out_of_scope", values=base | {"out_of_scope_reason": "Bdot_parameter_temperature_mismatch", "outer_iterations": 0})
    expected_ids = tuple(row.species_id for row in species)
    if tuple(row.species_id for row in parameter_rows) != expected_ids:
        return Calculation(status="needs_data", values=base | {"out_of_scope_reason": "Bdot_parameters_do_not_match_phase_species_order", "outer_iterations": 0})
    if any(species[i].charge_number != 0 and row.ion_size_angstrom <= 0.0 for i, row in enumerate(parameter_rows)):
        return Calculation(status="needs_data", values=base | {"out_of_scope_reason": "charged_species_requires_positive_Bdot_ion_size", "outer_iterations": 0})
    evidence_pairs = {(row.source_id, row.sha256) for row in request.evidence}
    parameter_evidence_missing = (
        len(evidence_pairs) != len(request.evidence)
        or (request.provider_id, request.parameter_record_sha256) not in evidence_pairs
        or any((row.source_id, row.source_record_sha256) not in evidence_pairs for row in parameter_rows)
    )
    if parameter_evidence_missing:
        return Calculation(status="needs_data", values=base | {"out_of_scope_reason": "Bdot_parameter_evidence_digest_mismatch", "outer_iterations": 0})

    charges = np.asarray([row.charge_number for row in species], dtype=float)
    ion_sizes = np.asarray([row.ion_size_angstrom for row in parameter_rows], dtype=float)
    bdot = np.asarray([row.bdot_kg_per_mol for row in parameter_rows], dtype=float)
    gamma = np.asarray([row.activity_coefficient for row in species], dtype=float)
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
                    "outer_iterations": iteration, "fixed_point_history": history,
                    "inner_solver_status": solved.get("status"),
                    "inner_solver_values": {key: value for key, value in solved.items() if key != "status"},
                })
            molality = np.asarray([
                solved["final_aqueous_concentration_mol_m3"][row.species_id]
                / (1000.0 * request.water_mass_per_solution_volume_kg_L)
                for row in species
            ], dtype=float)
            ionic_strength = 0.5 * float(np.dot(molality, np.square(charges)))
            charge_residual = float(np.dot(molality, charges))
            if not math.isfinite(ionic_strength) or ionic_strength > request.maximum_supported_ionic_strength_mol_kg:
                return Calculation(status="out_of_scope", values=base | {
                    "outer_iterations": iteration, "ionic_strength_mol_kg": ionic_strength,
                    "out_of_scope_reason": "ionic_strength_exceeds_caller_declared_Bdot_support", "fixed_point_history": history,
                })
            if not math.isfinite(charge_residual) or abs(charge_residual) > request.charge_balance_tolerance_mol_kg:
                return Calculation(status="needs_data", values=base | {
                    "outer_iterations": iteration, "ionic_strength_mol_kg": ionic_strength,
                    "charge_balance_residual_mol_kg": charge_residual,
                    "out_of_scope_reason": "competing_solid_liquid_charge_balance_tolerance_exceeded", "fixed_point_history": history,
                })
            log10_gamma_m = _aqueous_bdot_log10_gamma(
                charges, ion_sizes, bdot, ionic_strength,
                request.debye_huckel_A_at_temperature,
                request.debye_huckel_B_at_temperature_sqrt_kg_mol_per_angstrom,
            )
            log_gamma_m = log10_gamma_m * math.log(10.0)
            if not np.isfinite(log_gamma_m).all() or np.any(log_gamma_m > math.log(np.finfo(float).max)) or np.any(log_gamma_m < math.log(np.nextafter(0.0, 1.0))):
                raise ArithmeticError("B-dot molality activity coefficient is outside finite binary64 support")
            target_gamma_m = np.exp(log_gamma_m)
            target_gamma = molality_gamma_to_molarity_standard_state(target_gamma_m, request.water_mass_per_solution_volume_kg_L)
            residual = float(np.max(np.abs(np.log(target_gamma) - np.log(gamma))))
            history.append({
                "iteration": iteration, "ionic_strength_mol_kg": ionic_strength,
                "charge_balance_residual_mol_kg": charge_residual,
                "maximum_log_gamma_fixed_point_residual": residual,
                "inner_optimizer_iterations": solved.get("optimizer_iterations"),
            })
            if not math.isfinite(residual):
                raise ArithmeticError("B-dot activity fixed-point residual is nonfinite")
            if residual <= request.log_gamma_tolerance:
                values = {key: value for key, value in solved.items() if key not in {"status", "basis"}}
                values.update(base | {
                    "outer_iterations": iteration,
                    "ionic_strength_mol_kg": ionic_strength,
                    "charge_balance_residual_mol_kg": charge_residual,
                    "maximum_log_gamma_fixed_point_residual": residual,
                    "activity_coefficient_by_species": {row.species_id: float(gamma[i]) for i, row in enumerate(species)},
                    "Bdot_target_log10_gamma_molality_by_species": {row.species_id: float(log10_gamma_m[i]) for i, row in enumerate(species)},
                    "Bdot_target_gamma_molality_by_species": {row.species_id: float(target_gamma_m[i]) for i, row in enumerate(species)},
                    "Bdot_target_gamma_molarity_by_species": {row.species_id: float(target_gamma[i]) for i, row in enumerate(species)},
                    "molality_by_species_mol_kg": {row.species_id: float(molality[i]) for i, row in enumerate(species)},
                    "fixed_point_history": history,
                })
                return Calculation(values=values, notes=(
                    "Caller-declared competing neutral-solid equilibrium is iterated with evidence-bound species B-dot parameters evaluated from the resulting molal ionic strength.",
                    "Species, balanced reactions, candidate phases, equilibrium constants, B-dot coefficients, water conversion and support remain caller-owned. This does not infer neutral-species salting, concentrated-mixture qualification, precipitation kinetics, phase discovery or corrosion rate.",
                ))
            gamma = np.exp(np.log(gamma) + request.damping_fraction * (np.log(target_gamma) - np.log(gamma)))
            if np.any(~np.isfinite(gamma)) or np.any(gamma <= 0.0):
                raise ArithmeticError("damped B-dot activity update is not finite and positive")
    except (ArithmeticError, FloatingPointError, OverflowError, ValueError, np.linalg.LinAlgError) as error:
        return Calculation(status="out_of_scope", values=base | {
            "outer_iterations": len(history), "out_of_scope_reason": str(error),
            "fixed_point_history": history,
            "inner_solver_status": last_solved.get("status") if last_solved else None,
        })
    return Calculation(status="out_of_scope", values=base | {
        "outer_iterations": len(history), "out_of_scope_reason": "competitive_solid_Bdot_fixed_point_not_converged",
        "maximum_log_gamma_fixed_point_residual": history[-1]["maximum_log_gamma_fixed_point_residual"] if history else None,
        "fixed_point_history": history, "inner_solver_status": last_solved.get("status") if last_solved else None,
    })


def specifications() -> list[ModelSpec]:
    return [ModelSpec(
        "chemistry.competitive_solid_bdot_equilibrium",
        CompetitiveSolidBdotIteration,
        competitive_solid_bdot_self_consistent_equilibrium,
        {
            "temperature_K": "K", "ionic_strength_mol_kg": "mol/kg",
            "charge_balance_residual_mol_kg": "mol/kg",
            "activity_coefficient_by_species.*": "1",
            "Bdot_target_log10_gamma_molality_by_species.*": "1",
            "Bdot_target_gamma_molality_by_species.*": "1",
            "Bdot_target_gamma_molarity_by_species.*": "1",
            "molality_by_species_mol_kg.*": "mol/kg",
            "maximum_log_gamma_fixed_point_residual": "1", "outer_iterations": "1",
        },
        (
            "The caller supplies temperature-matched, Evidence-linked extended Debye-Huckel A/B, ion-size and B-dot parameters for every phase species.",
            "The caller owns species, complete phase set, Ksp values, water-mass conversion and charge review; ionic strength is limited to its declared parameter support.",
            "No species/phase discovery, precipitation kinetics, neutral-species salting or corrosion-rate qualification is inferred.",
        ),
        ("competitive_pure_solid_fixed_gamma_equilibrium", "usgs_phreeqc_llnl_bdot_activity", "molality_to_molarity_activity_standard_state_bridge"),
        qualification="user_model",
    )]
