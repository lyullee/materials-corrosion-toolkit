"""Self-consistent Davies activity iteration for caller-declared competing solids."""

from __future__ import annotations

import math
from typing import Literal

import numpy as np
from pydantic import Field

from ..competing_solid_equilibrium import (
    CompetitiveSolidEquilibrium,
    evaluate_competitive_solid_equilibrium,
)
from ..contracts import Calculation, Contract, Positive, canonical_digest
from ..registry import ModelSpec
from .aqueous_activity_iteration import _davies_gamma


class CompetitiveSolidDaviesIteration(Contract):
    schema_version: Literal["matintegrity.competitive_solid_davies_iteration.v1"] = (
        "matintegrity.competitive_solid_davies_iteration.v1"
    )
    equilibrium: CompetitiveSolidEquilibrium
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
    davies_A_temperature_solvent_basis_reviewed: bool
    molarity_standard_state_and_molality_mapping_reviewed: bool
    Davies_applicability_to_competing_solids_reviewed: bool
    charge_scope_and_solver_settings_reviewed: bool


def competitive_solid_davies_self_consistent_equilibrium(
    request: CompetitiveSolidDaviesIteration,
) -> Calculation:
    """Iterate fixed-gamma solid equilibrium against its resulting liquid ionic strength.

    The caller still defines every aqueous species, neutral solid, balanced reaction,
    phase-set boundary, equilibrium constant and initial inventory. This wrapper only
    updates Davies coefficients; it does not generate chemistry or precipitation rates.
    """
    digest = canonical_digest(request.model_dump(mode="json"))
    equilibrium = request.equilibrium
    base = {
        "equilibrium_id": equilibrium.equilibrium_id,
        "temperature_K": equilibrium.temperature_K,
        "input_digest": digest,
        "davies_A_at_temperature": request.davies_A_at_temperature,
        "davies_A_provider_id": request.davies_A_provider_id,
        "davies_A_provider_revision": request.davies_A_provider_revision,
        "davies_A_configuration_digest": request.davies_A_configuration_digest,
        "davies_A_record_digest": request.davies_A_record_digest,
        "water_mass_per_solution_volume_kg_L": request.water_mass_per_solution_volume_kg_L,
        "ionic_strength_limit_mol_kg": request.ionic_strength_limit_mol_kg,
    }
    reviews = {
        "water_mass_conversion_reviewed": request.water_mass_conversion_reviewed,
        "davies_A_temperature_solvent_basis_reviewed": request.davies_A_temperature_solvent_basis_reviewed,
        "molarity_standard_state_and_molality_mapping_reviewed": request.molarity_standard_state_and_molality_mapping_reviewed,
        "Davies_applicability_to_competing_solids_reviewed": request.Davies_applicability_to_competing_solids_reviewed,
        "charge_scope_and_solver_settings_reviewed": request.charge_scope_and_solver_settings_reviewed,
        "candidate_phase_set_completeness_reviewed": equilibrium.candidate_phase_set_completeness_reviewed,
        "equilibrium_constant_temperature_and_computational_use_reviewed": equilibrium.equilibrium_constant_temperature_and_computational_use_reviewed,
        "single_liquid_fixed_volume_and_neutral_solid_assumptions_reviewed": equilibrium.single_liquid_fixed_volume_and_neutral_solid_assumptions_reviewed,
    }
    missing = [name for name, reviewed in reviews.items() if not reviewed]
    if missing:
        return Calculation(
            status="needs_data",
            values=base | {"missing_reviews": missing, "outer_iterations": 0},
            notes=("Review the complete candidate phase set, single-liquid scope, temperature-specific Davies parameter, water conversion and ionic-strength charge inventory before solving.",),
        )
    if equilibrium.fixed_activity_coefficients_and_standard_states_reviewed is not True:
        return Calculation(
            status="needs_data",
            values=base | {"missing_reviews": ["fixed_activity_coefficients_and_standard_states_reviewed"], "outer_iterations": 0},
            notes=("The underlying equilibrium contract requires review of activity standard states; this API iterates their coefficients but does not choose them.",),
        )

    species = equilibrium.aqueous_species
    charges = np.asarray([row.charge_number for row in species], dtype=float)
    gamma = np.asarray([row.activity_coefficient for row in species], dtype=float)
    history: list[dict] = []
    last_equilibrium: dict | None = None
    try:
        for iteration in range(1, request.maximum_outer_iterations + 1):
            evaluated_input = CompetitiveSolidEquilibrium.model_validate(
                equilibrium.model_dump(mode="python")
                | {
                    "aqueous_species": tuple(
                        row.model_dump(mode="python") | {"activity_coefficient": float(gamma[i])}
                        for i, row in enumerate(species)
                    )
                }
            )
            solved = evaluate_competitive_solid_equilibrium(evaluated_input)
            last_equilibrium = solved
            if solved.get("status") != "computed":
                status = solved.get("status", "out_of_scope")
                return Calculation(
                    status=status,
                    values=base | {
                        "outer_iterations": iteration,
                        "fixed_point_history": history,
                        "inner_solver_status": status,
                        "inner_solver_values": {key: value for key, value in solved.items() if key != "status"},
                    },
                    notes=("The fixed-gamma competing-solid equilibrium did not converge; no outer activity/phase result is promoted.",),
                )

            concentrations = np.asarray(
                [solved["final_aqueous_concentration_mol_m3"][row.species_id] for row in species],
                dtype=float,
            )
            molality = concentrations / (1000.0 * request.water_mass_per_solution_volume_kg_L)
            ionic_strength = 0.5 * float(np.dot(molality, np.square(charges)))
            charge_residual = float(np.dot(molality, charges))
            if not math.isfinite(ionic_strength) or ionic_strength > request.ionic_strength_limit_mol_kg:
                return Calculation(
                    status="out_of_scope",
                    values=base | {
                        "outer_iterations": iteration,
                        "ionic_strength_mol_kg": ionic_strength,
                        "charge_balance_residual_mol_kg": charge_residual,
                        "fixed_point_history": history,
                        "out_of_scope_reason": "ionic_strength_exceeds_declared_davies_limit",
                    },
                    notes=("The phase-equilibrium liquid exceeds the caller ionic-strength ceiling; no concentrated-electrolyte model is substituted.",),
                )
            if not math.isfinite(charge_residual) or abs(charge_residual) > request.charge_balance_tolerance_mol_kg:
                return Calculation(
                    status="needs_data",
                    values=base | {
                        "outer_iterations": iteration,
                        "ionic_strength_mol_kg": ionic_strength,
                        "charge_balance_residual_mol_kg": charge_residual,
                        "fixed_point_history": history,
                        "out_of_scope_reason": "competing_solid_liquid_charge_balance_tolerance_exceeded",
                    },
                    notes=("The caller-declared aqueous species inventory must represent charge closure before interpreting activity-coupled solid equilibrium.",),
                )

            target_gamma = _davies_gamma(charges, ionic_strength, request.davies_A_at_temperature)
            residual = float(np.max(np.abs(np.log(target_gamma) - np.log(gamma))))
            history.append({
                "iteration": iteration,
                "ionic_strength_mol_kg": ionic_strength,
                "charge_balance_residual_mol_kg": charge_residual,
                "maximum_log_gamma_fixed_point_residual": residual,
                "inner_optimizer_iterations": solved.get("optimizer_iterations"),
                "inner_maximum_complementarity_residual": max(
                    (row["complementarity_residual"] for row in solved.get("complementarity_diagnostics", [])),
                    default=0.0,
                ),
            })
            if not math.isfinite(residual):
                raise ArithmeticError("activity-coefficient fixed-point residual is nonfinite")
            if residual <= request.log_gamma_tolerance:
                values = {key: value for key, value in solved.items() if key not in {"status", "basis"}}
                values.update({
                    **base,
                    "outer_iterations": iteration,
                    "ionic_strength_mol_kg": ionic_strength,
                    "charge_balance_residual_mol_kg": charge_residual,
                    "maximum_log_gamma_fixed_point_residual": residual,
                    "activity_coefficient_by_species": {row.species_id: float(gamma[i]) for i, row in enumerate(species)},
                    "davies_target_activity_coefficient_by_species": {row.species_id: float(target_gamma[i]) for i, row in enumerate(species)},
                    "molality_by_species_mol_kg": {row.species_id: float(molality[i]) for i, row in enumerate(species)},
                    "fixed_point_history": history,
                    "activity_model": "caller-supplied temperature-specific Davies A over molal ionic strength",
                })
                return Calculation(
                    values=values,
                    notes=(
                        "Caller-declared competing neutral pure-solid Gibbs equilibrium is iterated against Davies activity coefficients from the resulting liquid ionic strength.",
                        "Species, balanced reactions, candidate phases, Ksp values, charge inventory and water conversion remain caller-owned and reviewed. No kinetic precipitation, phase discovery, concentrated-electrolyte model or corrosion rate is inferred.",
                    ),
                )
            gamma = np.exp(np.log(gamma) + request.damping_fraction * (np.log(target_gamma) - np.log(gamma)))
            if np.any(~np.isfinite(gamma)) or np.any(gamma <= 0.0):
                raise ArithmeticError("damped activity coefficient update is not finite and positive")
    except (ArithmeticError, FloatingPointError, OverflowError, ValueError, np.linalg.LinAlgError) as error:
        return Calculation(
            status="out_of_scope",
            values=base | {
                "outer_iterations": len(history),
                "out_of_scope_reason": str(error),
                "fixed_point_history": history,
                "inner_solver_status": last_equilibrium.get("status") if last_equilibrium else None,
            },
            notes=("The coupled activity/phase iteration encountered an unsupported numerical state; no unconverged result is presented as equilibrium.",),
        )
    return Calculation(
        status="out_of_scope",
        values=base | {
            "outer_iterations": len(history),
            "out_of_scope_reason": "competitive_solid_activity_fixed_point_not_converged",
            "maximum_log_gamma_fixed_point_residual": history[-1]["maximum_log_gamma_fixed_point_residual"] if history else None,
            "fixed_point_history": history,
            "inner_solver_status": last_equilibrium.get("status") if last_equilibrium else None,
        },
        notes=("The caller iteration limit was reached before activity coefficients and competing phase equilibrium met the declared tolerance.",),
    )


def specifications() -> list[ModelSpec]:
    return [ModelSpec(
        "chemistry.competitive_solid_davies_equilibrium",
        CompetitiveSolidDaviesIteration,
        competitive_solid_davies_self_consistent_equilibrium,
        {
            "temperature_K": "K",
            "ionic_strength_mol_kg": "mol/kg",
            "charge_balance_residual_mol_kg": "mol/kg",
            "water_mass_per_solution_volume_kg_L": "kg/L",
            "aqueous_species.*_mol_m3": "mol/m3",
            "solid_phase_results[].final_solid_moles_per_solution_volume_mol_m3": "mol/m3",
            "activity_coefficient_by_species.*": "1",
            "davies_target_activity_coefficient_by_species.*": "1",
            "maximum_log_gamma_fixed_point_residual": "1",
            "outer_iterations": "1",
        },
        (
            "Caller-declared competing neutral pure-solid equilibrium is iterated with Davies coefficients recalculated from the resulting single-liquid ionic strength.",
            "Requires explicit complete phase/species inventory, charge closure, source-backed Ksp, caller water-mass conversion and temperature-specific Davies A; ionic strength is limited to the declared ceiling no greater than 0.5 mol/kg.",
            "No species or phase discovery, precipitation kinetics, concentrated-electrolyte law, evolving scale, corrosion rate or acceptance is inferred.",
        ),
        ("competitive_pure_solid_fixed_gamma_equilibrium", "self_consistent_davies_aqueous_speciation"),
        qualification="user_model",
    )]
