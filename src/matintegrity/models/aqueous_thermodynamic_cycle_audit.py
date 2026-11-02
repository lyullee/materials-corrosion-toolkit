"""Audit caller-supplied aqueous equilibrium constants for reaction-cycle closure."""

from __future__ import annotations

import math
from typing import Literal

import numpy as np
from pydantic import Field, StrictInt, model_validator

from ..contracts import Calculation, Contract, Evidence, Positive, canonical_digest
from ..registry import ModelSpec
from .aqueous_mass_action import AqueousStoichiometricTerm


class AqueousCycleSpecies(Contract):
    species_id: str = Field(min_length=1)
    charge_number: StrictInt = Field(ge=-8, le=8)
    elemental_composition: dict[str, StrictInt]

    @model_validator(mode="after")
    def valid_formula(self):
        if not self.elemental_composition or any(
            not element.strip() or count < 0
            for element, count in self.elemental_composition.items()
        ):
            raise ValueError("cycle-audit species require nonempty, nonnegative elemental compositions")
        return self


class AqueousCycleReaction(Contract):
    reaction_id: str = Field(min_length=1)
    log10_equilibrium_constant: float
    terms: tuple[AqueousStoichiometricTerm, ...] = Field(min_length=2, max_length=100)
    evidence_source_id: str = Field(min_length=1)
    source_record_id: str = Field(min_length=1)
    evidence_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")

    @model_validator(mode="after")
    def valid_reaction_record(self):
        species_ids = [term.species_id for term in self.terms]
        if (
            len(species_ids) != len(set(species_ids))
            or any(term.coefficient == 0 or not math.isfinite(term.coefficient) for term in self.terms)
        ):
            raise ValueError("cycle-audit reaction terms must be unique and nonzero")
        if not math.isfinite(self.log10_equilibrium_constant):
            raise ValueError("equilibrium constants must be finite")
        return self


class AqueousThermodynamicCycleAudit(Contract):
    schema_version: Literal["matintegrity.aqueous_thermodynamic_cycle_audit.v1"] = (
        "matintegrity.aqueous_thermodynamic_cycle_audit.v1"
    )
    audit_id: str = Field(min_length=1)
    temperature_K: Positive
    activity_standard_state: Literal[
        "molarity_1_mol_L", "molality_1_mol_kg_water", "dimensionless"
    ]
    parameter_provider_id: str = Field(min_length=1)
    parameter_provider_revision: str = Field(min_length=1)
    species: tuple[AqueousCycleSpecies, ...] = Field(min_length=2, max_length=100)
    reactions: tuple[AqueousCycleReaction, ...] = Field(min_length=1, max_length=100)
    evidence: tuple[Evidence, ...] = Field(min_length=1)
    stoichiometric_balance_tolerance: Positive = Field(default=1e-10, le=1e-4)
    rank_relative_tolerance: Positive = Field(default=1e-12, le=1e-3)
    cycle_closure_tolerance_log10: Positive = Field(default=1e-8, le=1.0)
    complete_species_inventory_reviewed: bool
    elemental_formula_and_stoichiometry_reviewed: bool
    equilibrium_constant_conditions_reviewed: bool
    numerical_rank_and_cycle_tolerance_reviewed: bool
    evidence_and_usage_rights_reviewed: bool

    @model_validator(mode="after")
    def coherent_cycle_network(self):
        species_ids = [row.species_id for row in self.species]
        reaction_ids = [row.reaction_id for row in self.reactions]
        evidence_ids = [row.source_id for row in self.evidence]
        if len(species_ids) != len(set(species_ids)):
            raise ValueError("cycle-audit species IDs must be unique")
        if len(reaction_ids) != len(set(reaction_ids)):
            raise ValueError("cycle-audit reaction IDs must be unique")
        if len(evidence_ids) != len(set(evidence_ids)):
            raise ValueError("cycle-audit Evidence source IDs must be unique")
        known_species = set(species_ids)
        evidence_by_id = {row.source_id: row for row in self.evidence}
        for reaction in self.reactions:
            if any(term.species_id not in known_species for term in reaction.terms):
                raise ValueError(f"reaction {reaction.reaction_id} references an undeclared species")
            evidence = evidence_by_id.get(reaction.evidence_source_id)
            if evidence is None or evidence.sha256 != reaction.evidence_sha256:
                raise ValueError(f"reaction {reaction.reaction_id} must pin a matching Evidence source and file hash")
        if any(row.origin == "open_dataset" and not (row.license_id and row.license_id.strip()) for row in self.evidence):
            raise ValueError("open-dataset equilibrium evidence must declare a license or reuse policy")
        return self


def aqueous_thermodynamic_cycle_audit(x: AqueousThermodynamicCycleAudit) -> Calculation:
    """Check elemental/charge balance and the null-space closure of log10(K)."""
    digest = canonical_digest(x.model_dump(mode="json"))
    species_index = {row.species_id: index for index, row in enumerate(x.species)}
    element_ids = sorted({element for row in x.species for element in row.elemental_composition})
    element_index = {element: index for index, element in enumerate(element_ids)}
    stoichiometry = np.zeros((len(x.species), len(x.reactions)), dtype=float)
    log_k = np.asarray([row.log10_equilibrium_constant for row in x.reactions], dtype=float)
    for reaction_index, reaction in enumerate(x.reactions):
        for term in reaction.terms:
            stoichiometry[species_index[term.species_id], reaction_index] = term.coefficient
    element_matrix = np.asarray([
        [row.elemental_composition.get(element, 0) for row in x.species]
        for element in element_ids
    ], dtype=float)
    charge_row = np.asarray([row.charge_number for row in x.species], dtype=float)
    element_residuals = element_matrix @ stoichiometry
    charge_residuals = charge_row @ stoichiometry
    balance_rows = []
    for index, reaction in enumerate(x.reactions):
        element_balance = {
            element: float(element_residuals[element_idx, index])
            for element_idx, element in enumerate(element_ids)
            if abs(float(element_residuals[element_idx, index])) > x.stoichiometric_balance_tolerance
        }
        charge_balance = float(charge_residuals[index])
        balance_rows.append({
            "reaction_id": reaction.reaction_id,
            "element_balance_residuals": element_balance,
            "charge_balance_residual": charge_balance,
            "balanced": not element_balance and abs(charge_balance) <= x.stoichiometric_balance_tolerance,
        })
    base = {
        "audit_id": x.audit_id,
        "temperature_K": x.temperature_K,
        "activity_standard_state": x.activity_standard_state,
        "parameter_provider_id": x.parameter_provider_id,
        "parameter_provider_revision": x.parameter_provider_revision,
        "input_sha256": digest,
        "reaction_count": len(x.reactions),
        "species_count": len(x.species),
        "reaction_balance": balance_rows,
        "reaction_record_lineage": [
            {
                "reaction_id": row.reaction_id,
                "evidence_source_id": row.evidence_source_id,
                "source_record_id": row.source_record_id,
                "evidence_sha256": row.evidence_sha256,
            }
            for row in x.reactions
        ],
        "evidence_bundle_sha256": canonical_digest([row.model_dump(mode="json") for row in x.evidence]),
    }
    reviews = {
        "complete_species_inventory_reviewed": x.complete_species_inventory_reviewed,
        "elemental_formula_and_stoichiometry_reviewed": x.elemental_formula_and_stoichiometry_reviewed,
        "equilibrium_constant_conditions_reviewed": x.equilibrium_constant_conditions_reviewed,
        "numerical_rank_and_cycle_tolerance_reviewed": x.numerical_rank_and_cycle_tolerance_reviewed,
        "evidence_and_usage_rights_reviewed": x.evidence_and_usage_rights_reviewed,
    }
    missing_reviews = [name for name, reviewed in reviews.items() if not reviewed]
    if missing_reviews:
        return Calculation(status="needs_data", values=base | {"missing_reviews": missing_reviews})
    if any(not row["balanced"] for row in balance_rows):
        return Calculation(status="needs_data", values=base | {
            "reason": "unbalanced_reaction_stoichiometry",
        })
    if not np.isfinite(stoichiometry).all() or not np.isfinite(log_k).all():
        return Calculation(status="out_of_scope", values=base | {"reason": "nonfinite_reaction_network"})
    try:
        _, singular_values, right_vectors = np.linalg.svd(stoichiometry, full_matrices=True)
    except np.linalg.LinAlgError:
        return Calculation(status="out_of_scope", values=base | {"reason": "stoichiometric_rank_decomposition_failed"})
    largest_singular_value = float(singular_values[0]) if singular_values.size else 0.0
    rank_threshold = x.rank_relative_tolerance * largest_singular_value
    rank = int(np.count_nonzero(singular_values > rank_threshold))
    cycle_basis = right_vectors[rank:, :]
    cycle_residuals = cycle_basis @ log_k
    residual_norm = float(np.linalg.norm(cycle_residuals, ord=2))
    if not math.isfinite(residual_norm):
        return Calculation(status="out_of_scope", values=base | {"reason": "cycle_residual_not_representable"})
    cycle_rows = []
    for cycle_index, (coefficients, residual) in enumerate(zip(cycle_basis, cycle_residuals, strict=True)):
        cycle_rows.append({
            "cycle_basis_index": cycle_index,
            "reaction_coefficients_l2_normalized": {
                reaction.reaction_id: float(coefficients[index])
                for index, reaction in enumerate(x.reactions)
            },
            "log10_equilibrium_cycle_residual": float(residual),
        })
    within_tolerance = residual_norm <= x.cycle_closure_tolerance_log10
    values = base | {
        "stoichiometric_matrix_rank": rank,
        "reaction_cycle_dimension": int(cycle_basis.shape[0]),
        "singular_values": [float(value) for value in singular_values],
        "rank_relative_tolerance": x.rank_relative_tolerance,
        "rank_threshold": rank_threshold,
        "reaction_cycle_basis": cycle_rows,
        "cycle_closure_residual_l2_log10": residual_norm,
        "cycle_closure_tolerance_log10": x.cycle_closure_tolerance_log10,
        "cycle_constants_consistent_within_declared_tolerance": within_tolerance,
        "cycle_closure_status": (
            "no_reaction_cycles_to_check"
            if cycle_basis.shape[0] == 0
            else "within_tolerance"
            if within_tolerance
            else "outside_tolerance"
        ),
        "interpretation": "Basis-coordinate consistency diagnostic for caller log10 equilibrium constants; no species or phase discovery and no equilibrium solve.",
    }
    return Calculation(
        status="computed" if within_tolerance else "needs_data",
        values=values,
        notes=(
            "The orthonormal right-null-space basis spans linear reaction cycles; the L2 projection of supplied log10(K) onto that space is compared with the caller tolerance.",
            "Numerical rank and closure tolerance are caller-reviewed; passing this algebraic check does not qualify equilibrium data or prove physical completeness.",
        ),
    )


def specifications() -> list[ModelSpec]:
    return [ModelSpec(
        "chemistry.aqueous_thermodynamic_cycle_audit",
        AqueousThermodynamicCycleAudit,
        aqueous_thermodynamic_cycle_audit,
        {
            "temperature_K": "K",
            "reaction_balance[].charge_balance_residual": "1",
            "reaction_cycle_basis[].log10_equilibrium_cycle_residual": "1",
            "cycle_closure_residual_l2_log10": "1",
            "cycle_closure_tolerance_log10": "1",
            "rank_threshold": "1",
            "singular_values": "1",
        },
        (
            "All species formulas, charges, activity standard state, temperature and equilibrium-constant records are caller supplied and explicitly reviewed.",
            "The reaction-cycle basis is derived from the declared stoichiometric matrix; numerical rank and log10(K) closure tolerance are caller-reviewed.",
            "This API checks balance and algebraic cycle consistency only; it does not discover species/phases, solve speciation, infer missing constants or qualify corrosion.",
        ),
        ("aqueous_reaction_cycle_nullspace_consistency",),
        qualification="user_model",
    )]
