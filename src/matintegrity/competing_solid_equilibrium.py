"""Fixed-gamma equilibrium among caller-declared competing neutral solids."""

from __future__ import annotations

import math

import numpy as np
from pydantic import Field, model_validator

from .contracts import Contract, Nonnegative, Positive, canonical_digest


class CompetitiveAqueousSpecies(Contract):
    species_id: str = Field(min_length=1)
    initial_concentration_mol_m3: Nonnegative
    activity_reference_concentration_mol_m3: Positive
    activity_coefficient: Positive
    charge_number: int
    elemental_composition: dict[str, int]

    @model_validator(mode="after")
    def valid_composition(self):
        if not self.elemental_composition or any(value < 0 for value in self.elemental_composition.values()):
            raise ValueError("aqueous species require explicit nonnegative elemental composition")
        if not any(self.elemental_composition.values()):
            raise ValueError("aqueous species elemental composition cannot be all zero")
        return self


class CompetitiveSolidPhase(Contract):
    solid_species_id: str = Field(min_length=1)
    precipitation_stoichiometry: dict[str, Positive]
    solid_elemental_composition: dict[str, int]
    initial_solid_moles_per_solution_volume_mol_m3: Nonnegative
    dimensionless_solubility_product: Positive
    equilibrium_constant_source_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")


class CompetitiveSolidEquilibrium(Contract):
    equilibrium_id: str = Field(min_length=1)
    aqueous_species: tuple[CompetitiveAqueousSpecies, ...] = Field(min_length=1)
    candidate_solid_phases: tuple[CompetitiveSolidPhase, ...] = Field(min_length=2, max_length=16)
    temperature_K: Positive
    standard_state_id: str = Field(min_length=1)
    candidate_phase_set_completeness_reviewed: bool
    fixed_activity_coefficients_and_standard_states_reviewed: bool
    equilibrium_constant_temperature_and_computational_use_reviewed: bool
    single_liquid_fixed_volume_and_neutral_solid_assumptions_reviewed: bool
    optimizer_maximum_iterations: int = Field(default=2000, ge=50, le=20000)
    maximum_absolute_log_saturation_residual: float = Field(default=1e-7, gt=0, le=0.01)
    absolute_extent_balance_tolerance_mol_m3: Positive = 1e-10
    relative_extent_balance_tolerance: float = Field(default=1e-9, gt=0, le=0.01)

    @model_validator(mode="after")
    def validate_network(self):
        species = {row.species_id: row for row in self.aqueous_species}
        if len(species) != len(self.aqueous_species):
            raise ValueError("aqueous species IDs must be unique")
        phases = {row.solid_species_id: row for row in self.candidate_solid_phases}
        if len(phases) != len(self.candidate_solid_phases):
            raise ValueError("candidate solid IDs must be unique")
        if set(species) & set(phases):
            raise ValueError("solid and aqueous species identities must be distinct")
        for phase in self.candidate_solid_phases:
            if not phase.solid_elemental_composition or any(value < 0 for value in phase.solid_elemental_composition.values()):
                raise ValueError("each neutral solid requires explicit nonnegative elemental composition")
            if not any(phase.solid_elemental_composition.values()):
                raise ValueError("solid elemental composition cannot be all zero")
            if not phase.precipitation_stoichiometry or not set(phase.precipitation_stoichiometry) <= set(species):
                raise ValueError("each phase must use a nonempty subset of declared aqueous species")
            charge = math.fsum(species[key].charge_number * value for key, value in phase.precipitation_stoichiometry.items())
            if not math.isfinite(charge) or not math.isclose(charge, 0.0, rel_tol=0.0, abs_tol=1e-12):
                raise ValueError("every declared precipitation reaction must conserve charge")
            elements = set(phase.solid_elemental_composition)
            for species_id in phase.precipitation_stoichiometry:
                elements.update(species[species_id].elemental_composition)
            for element in elements:
                aqueous_count = math.fsum(
                    species[species_id].elemental_composition.get(element, 0) * coefficient
                    for species_id, coefficient in phase.precipitation_stoichiometry.items()
                )
                solid_count = phase.solid_elemental_composition.get(element, 0)
                if not math.isfinite(aqueous_count) or not math.isclose(
                    aqueous_count, solid_count, rel_tol=1e-12, abs_tol=1e-12
                ):
                    raise ValueError("each precipitation reaction must conserve declared elements")
        return self


def evaluate_competitive_solid_equilibrium(request: CompetitiveSolidEquilibrium) -> dict:
    """Minimize fixed-gamma aqueous-plus-solid Gibbs potential over phase extents.

    Candidate solids are pure neutral phases. Their identities and complete candidate
    list are caller-supplied. The optimizer solves one closed, single-liquid, fixed-volume
    system; no speciation, activity iteration, phase transition or kinetic law is inferred.
    """
    input_digest = canonical_digest(request.model_dump(mode="json"))
    base = {
        "equilibrium_id": request.equilibrium_id,
        "status": "needs_data",
        "input_sha256": input_digest,
        "temperature_K": request.temperature_K,
        "standard_state_id": request.standard_state_id,
        "candidate_solid_species_ids": [phase.solid_species_id for phase in request.candidate_solid_phases],
        "candidate_phase_set_completeness_reviewed": request.candidate_phase_set_completeness_reviewed,
        "basis": "Caller-declared competing pure neutral solids; one liquid, fixed volume and fixed activity coefficients.",
    }
    reviews = {
        "candidate_phase_set_completeness_reviewed": request.candidate_phase_set_completeness_reviewed,
        "fixed_activity_coefficients_and_standard_states_reviewed": request.fixed_activity_coefficients_and_standard_states_reviewed,
        "equilibrium_constant_temperature_and_computational_use_reviewed": request.equilibrium_constant_temperature_and_computational_use_reviewed,
        "single_liquid_fixed_volume_and_neutral_solid_assumptions_reviewed": request.single_liquid_fixed_volume_and_neutral_solid_assumptions_reviewed,
    }
    missing = [key for key, reviewed in reviews.items() if not reviewed]
    if missing:
        return base | {"missing_reviews": missing}

    species = request.aqueous_species
    phases = request.candidate_solid_phases
    c0 = np.asarray([row.initial_concentration_mol_m3 for row in species], dtype=float)
    refs = np.asarray([row.activity_reference_concentration_mol_m3 for row in species], dtype=float)
    gamma = np.asarray([row.activity_coefficient for row in species], dtype=float)
    s0 = np.asarray([phase.initial_solid_moles_per_solution_volume_mol_m3 for phase in phases], dtype=float)
    nu = np.zeros((len(species), len(phases)), dtype=float)
    index = {row.species_id: i for i, row in enumerate(species)}
    for j, phase in enumerate(phases):
        for species_id, coefficient in phase.precipitation_stoichiometry.items():
            nu[index[species_id], j] = float(coefficient)
    log_k = np.log(np.asarray([phase.dimensionless_solubility_product for phase in phases], dtype=float))
    scale = max(1.0, float(np.max(c0, initial=0.0)), float(np.max(s0, initial=0.0)))

    def state(z):
        extent = np.asarray(z, dtype=float) * scale
        concentration = c0 - nu @ extent
        log_activity = (
            np.log(gamma)
            + np.log(np.maximum(concentration, np.finfo(float).tiny))
            - np.log(refs)
        )
        return extent, concentration, log_activity

    def objective(z):
        extent, concentration, log_activity = state(z)
        aqueous = np.sum((concentration / scale) * (log_activity - 1.0))
        solid = np.dot(extent / scale, log_k)
        value = float(aqueous + solid)
        if not math.isfinite(value):
            return float("inf")
        return value

    def gradient(z):
        _, _, log_activity = state(z)
        value = log_k - nu.T @ log_activity
        if not np.isfinite(value).all():
            raise ArithmeticError("Gibbs-potential gradient exceeds finite support")
        return value

    constraints = ({
        "type": "ineq",
        "fun": lambda z: (c0 - nu @ (np.asarray(z, dtype=float) * scale)) / scale,
        "jac": lambda z: -nu,
    },)
    bounds = [(-float(solid) / scale, None) for solid in s0]
    try:
        from scipy.optimize import minimize

        solved = minimize(
            objective,
            np.zeros(len(phases), dtype=float),
            method="SLSQP",
            jac=gradient,
            bounds=bounds,
            constraints=constraints,
            options={"maxiter": request.optimizer_maximum_iterations, "ftol": 1e-12, "disp": False},
        )
    except (ArithmeticError, FloatingPointError, OverflowError, ValueError, ImportError) as error:
        return base | {"status": "out_of_scope", "reason": str(error)}
    if not solved.success or not np.isfinite(solved.x).all():
        return base | {
            "status": "out_of_scope",
            "optimizer_status": int(solved.status),
            "optimizer_message": str(solved.message),
            "optimizer_iterations": int(getattr(solved, "nit", 0)),
        }

    extent, final_c, log_activity = state(solved.x)
    final_s = s0 + extent
    if not np.isfinite(final_c).all() or not np.isfinite(final_s).all() or np.any(final_c < 0) or np.any(final_s < 0):
        return base | {"status": "out_of_scope", "reason": "Optimizer returned a nonphysical state; values were not clipped"}
    log_q = np.empty(len(phases), dtype=float)
    for j in range(len(phases)):
        participating = nu[:, j] > 0
        if np.any(final_c[participating] == 0):
            log_q[j] = -math.inf
        else:
            log_q[j] = float(np.dot(nu[participating, j], log_activity[participating]))
    phase_rows = []
    phase_acceptable = True
    phase_tol = np.zeros(len(phases), dtype=float)
    for j, phase in enumerate(phases):
        phase_tol[j] = request.absolute_extent_balance_tolerance_mol_m3 + request.relative_extent_balance_tolerance * max(
            final_s[j], s0[j], abs(extent[j])
        )
        present = final_s[j] > phase_tol[j]
        saturation_residual = float(log_q[j] - log_k[j])
        if present:
            acceptable = math.isfinite(saturation_residual) and abs(saturation_residual) <= request.maximum_absolute_log_saturation_residual
        else:
            acceptable = saturation_residual <= request.maximum_absolute_log_saturation_residual
        phase_acceptable &= acceptable
        phase_rows.append({
            "solid_species_id": phase.solid_species_id,
            "initial_solid_moles_per_solution_volume_mol_m3": float(s0[j]),
            "reaction_extent_mol_m3": float(extent[j]),
            "final_solid_moles_per_solution_volume_mol_m3": float(final_s[j]),
            "solid_present": bool(present),
            "equilibrium_state": (
                "saturated" if present else
                "saturated_no_solid" if math.isfinite(saturation_residual) and abs(saturation_residual) <= request.maximum_absolute_log_saturation_residual else
                "undersaturated_no_solid"
            ),
            "log_ion_activity_product": float(log_q[j]) if math.isfinite(log_q[j]) else None,
            "log_ion_activity_product_is_zero": bool(log_q[j] == -math.inf),
            "log_solubility_product": float(log_k[j]),
            "log_saturation_residual": saturation_residual if math.isfinite(saturation_residual) else None,
            "log_saturation_inequality_satisfied": bool(acceptable),
            "equilibrium_constant_source_sha256": phase.equilibrium_constant_source_sha256,
        })
    gradient_final = gradient(solved.x)
    kkt = []
    kkt_ok = True
    for j, phase in enumerate(phases):
        if final_s[j] > phase_tol[j]:
            residual = abs(float(gradient_final[j]))
            acceptable = residual <= request.maximum_absolute_log_saturation_residual
        else:
            residual = max(0.0, -float(gradient_final[j]))
            acceptable = residual <= request.maximum_absolute_log_saturation_residual
        kkt_ok &= acceptable
        kkt.append({"solid_species_id": phase.solid_species_id, "complementarity_residual": residual, "within_tolerance": bool(acceptable)})
    concentration_balance = final_c - c0 + nu @ extent
    balance_limits = request.absolute_extent_balance_tolerance_mol_m3 + request.relative_extent_balance_tolerance * np.maximum.reduce(
        [np.abs(final_c), c0, np.abs(nu @ extent)]
    )
    balance_ok = bool(np.isfinite(concentration_balance).all() and np.all(np.abs(concentration_balance) <= balance_limits))
    final_activity = gamma * final_c / refs
    finite = bool(np.isfinite(log_activity).all() and np.isfinite(extent).all() and np.isfinite(final_activity).all()
                  and np.all(np.isfinite(log_q) | np.isneginf(log_q)))
    status = "computed" if finite and phase_acceptable and kkt_ok and balance_ok else "out_of_scope"
    return base | {
        "status": status,
        "optimizer_status": int(solved.status),
        "optimizer_message": str(solved.message),
        "optimizer_iterations": int(getattr(solved, "nit", 0)),
        "aqueous_species_ids": [row.species_id for row in species],
        "final_aqueous_concentration_mol_m3": {row.species_id: float(final_c[i]) for i, row in enumerate(species)},
        "final_aqueous_activity": {row.species_id: float(final_activity[i]) for i, row in enumerate(species)},
        "solid_phase_results": phase_rows,
        "complementarity_diagnostics": kkt,
        "concentration_extent_balance_residual_mol_m3": {row.species_id: float(concentration_balance[i]) for i, row in enumerate(species)},
        "concentration_extent_balance_limit_mol_m3": {row.species_id: float(balance_limits[i]) for i, row in enumerate(species)},
        "phase_equilibrium_conditions_satisfied": bool(phase_acceptable),
        "complementarity_conditions_satisfied": bool(kkt_ok),
        "aqueous_extent_balances_satisfied": balance_ok,
        "fixed_gibbs_potential": float(solved.fun),
    }
