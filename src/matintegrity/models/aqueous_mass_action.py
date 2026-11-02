"""Caller-defined single-phase aqueous mass-action equilibrium networks."""

from __future__ import annotations

import math
import json
from itertools import combinations_with_replacement
from typing import Literal

import numpy as np
from pydantic import Field, StrictInt, ValidationError, model_validator

from ..contracts import Calculation, Contract, Evidence, Positive, canonical_digest
from ..registry import ModelSpec


def _validate_local_parameter_covariance(covariance, reviewed: bool, expected_size: int | None = None) -> None:
    if covariance is None:
        if reviewed:
            raise ValueError("local covariance review requires a covariance matrix")
        return
    if not reviewed:
        raise ValueError("local parameter covariance requires explicit review")
    matrix = np.asarray(covariance, dtype=float)
    if matrix.ndim != 2 or matrix.shape[0] != matrix.shape[1] or matrix.shape[0] == 0:
        raise ValueError("local parameter covariance must be a nonempty square matrix")
    if expected_size is not None and matrix.shape != (expected_size, expected_size):
        raise ValueError("local parameter covariance dimension must match the declared parameter order")
    if not np.isfinite(matrix).all():
        raise ValueError("local parameter covariance must be finite")
    scale = max(float(np.linalg.norm(matrix, ord=np.inf)), np.finfo(float).tiny)
    asymmetry = float(np.max(np.abs(matrix - matrix.T)))
    if asymmetry > 1e-10 * scale:
        raise ValueError("local parameter covariance must be symmetric")
    try:
        minimum_eigenvalue = float(np.linalg.eigvalsh(0.5 * (matrix + matrix.T))[0])
    except np.linalg.LinAlgError as error:
        raise ValueError("local parameter covariance positive-semidefinite check failed") from error
    if not math.isfinite(minimum_eigenvalue) or minimum_eigenvalue < -1e-10 * scale:
        raise ValueError("local parameter covariance must be positive semidefinite")


class AqueousActivitySpecies(Contract):
    species_id: str = Field(min_length=1)
    charge_number: int = Field(ge=-8, le=8)
    activity_coefficient: Positive
    initial_activity: Positive
    elemental_composition: dict[str, StrictInt] | None = None

    @model_validator(mode="after")
    def valid_elemental_composition(self):
        if self.elemental_composition is not None and any(
            not element.strip() or count < 0
            for element, count in self.elemental_composition.items()
        ):
            raise ValueError("elemental composition requires nonempty element symbols and nonnegative integer counts")
        return self


class AqueousStoichiometricTerm(Contract):
    species_id: str = Field(min_length=1)
    coefficient: float


class AqueousEquilibriumReaction(Contract):
    reaction_id: str = Field(min_length=1)
    log10_equilibrium_constant: float
    terms: tuple[AqueousStoichiometricTerm, ...] = Field(min_length=2, max_length=100)

    @model_validator(mode="after")
    def unique_nonzero_terms(self):
        ids = [term.species_id for term in self.terms]
        if len(ids) != len(set(ids)) or any(term.coefficient == 0 for term in self.terms):
            raise ValueError("reaction species terms must be unique and nonzero")
        return self


class AqueousLinearConstraint(Contract):
    constraint_id: str = Field(min_length=1)
    target_mol_L: float
    residual_scale_mol_L: Positive
    terms: tuple[AqueousStoichiometricTerm, ...] = Field(min_length=1, max_length=100)

    @model_validator(mode="after")
    def unique_nonzero_terms(self):
        ids = [term.species_id for term in self.terms]
        if len(ids) != len(set(ids)) or any(term.coefficient == 0 for term in self.terms):
            raise ValueError("constraint species terms must be unique and nonzero")
        return self


class AqueousMassActionSystem(Contract):
    schema_version: Literal["matintegrity.aqueous_mass_action.v1"] = "matintegrity.aqueous_mass_action.v1"
    assessment_id: str = Field(min_length=1)
    solution_id: str = Field(min_length=1)
    temperature_K: Positive
    activity_standard_state: Literal["molarity_1_mol_L"]
    species: tuple[AqueousActivitySpecies, ...] = Field(min_length=2, max_length=100)
    reactions: tuple[AqueousEquilibriumReaction, ...] = Field(min_length=1, max_length=100)
    constraints: tuple[AqueousLinearConstraint, ...] = Field(min_length=1, max_length=100)
    maximum_iterations: int = Field(default=100, ge=1, le=1000)
    normalized_residual_tolerance: Positive = Field(default=1e-10, le=1e-4)
    maximum_jacobian_condition_number: Positive = Field(default=1e14, le=1e16)
    local_parameter_covariance: tuple[tuple[float, ...], ...] | None = None
    local_parameter_covariance_reviewed: bool = False
    activity_provider_id: str = Field(min_length=1)
    activity_provider_revision: str = Field(min_length=1)
    activity_configuration_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    activity_record_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    equilibrium_provider_id: str = Field(min_length=1)
    equilibrium_provider_revision: str = Field(min_length=1)
    equilibrium_configuration_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    equilibrium_record_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    complete_aqueous_species_inventory_reviewed: bool
    reaction_stoichiometry_and_constant_reviewed: bool
    balance_constraints_and_charge_scope_reviewed: bool
    fixed_activity_coefficients_and_standard_state_reviewed: bool
    temperature_and_provider_lineage_reviewed: bool
    initial_activity_guess_and_solver_tolerance_reviewed: bool
    single_liquid_phase_and_no_precipitation_reviewed: bool
    elemental_formula_and_reaction_balance_reviewed: bool = False
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def coherent_network(self):
        species_ids = [row.species_id for row in self.species]
        reaction_ids = [row.reaction_id for row in self.reactions]
        constraint_ids = [row.constraint_id for row in self.constraints]
        if len(species_ids) != len(set(species_ids)):
            raise ValueError("aqueous species IDs must be unique")
        if len(reaction_ids) != len(set(reaction_ids)):
            raise ValueError("reaction IDs must be unique")
        if len(constraint_ids) != len(set(constraint_ids)):
            raise ValueError("constraint IDs must be unique")
        species_set = set(species_ids)
        formula_count = sum(row.elemental_composition is not None for row in self.species)
        if formula_count not in (0, len(self.species)):
            raise ValueError("elemental composition must be supplied for every species or none")
        has_formula_inventory = formula_count == len(self.species)
        for row in (*self.reactions, *self.constraints):
            unknown = {term.species_id for term in row.terms} - species_set
            if unknown:
                raise ValueError(f"network equation references unknown species: {sorted(unknown)}")
        if len(self.reactions) + len(self.constraints) != len(self.species):
            raise ValueError("reaction and constraint equation count must equal the aqueous species count")
        _validate_local_parameter_covariance(
            self.local_parameter_covariance,
            self.local_parameter_covariance_reviewed,
            len(self.reactions) + len(self.constraints) + len(self.species),
        )
        covered = {
            term.species_id
            for row in (*self.reactions, *self.constraints)
            for term in row.terms
        }
        if covered != species_set:
            raise ValueError("each declared species must occur in at least one network equation")
        charges = {row.species_id: row.charge_number for row in self.species}
        for reaction in self.reactions:
            charge_residual = math.fsum(
                term.coefficient * charges[term.species_id] for term in reaction.terms
            )
            charge_scale = max(
                1.0,
                math.fsum(abs(term.coefficient * charges[term.species_id]) for term in reaction.terms),
            )
            if abs(charge_residual) > 1e-12 * charge_scale:
                raise ValueError(f"reaction {reaction.reaction_id} does not conserve declared charge")
            if has_formula_inventory:
                elements = set().union(*(row.elemental_composition or {} for row in self.species))
                formula = {row.species_id: row.elemental_composition or {} for row in self.species}
                for element in elements:
                    residual = math.fsum(
                        term.coefficient * formula[term.species_id].get(element, 0)
                        for term in reaction.terms
                    )
                    scale = max(
                        1.0,
                        math.fsum(
                            abs(term.coefficient * formula[term.species_id].get(element, 0))
                            for term in reaction.terms
                        ),
                    )
                    if abs(residual) > 1e-12 * scale:
                        raise ValueError(
                            f"reaction {reaction.reaction_id} does not conserve declared element {element}"
                        )
        return self


class AqueousMassActionSystemAssemblyRequest(Contract):
    """All non-reaction inputs needed to assemble a solver system from a binding result."""

    schema_version: Literal["matintegrity.aqueous_mass_action_assembly.v1"] = (
        "matintegrity.aqueous_mass_action_assembly.v1"
    )
    assessment_id: str = Field(min_length=1)
    solution_id: str = Field(min_length=1)
    temperature_K: Positive
    activity_standard_state: Literal["molarity_1_mol_L"]
    species: tuple[AqueousActivitySpecies, ...] = Field(min_length=2, max_length=100)
    constraints: tuple[AqueousLinearConstraint, ...] = Field(min_length=1, max_length=100)
    maximum_iterations: int = Field(default=100, ge=1, le=1000)
    normalized_residual_tolerance: Positive = Field(default=1e-10, le=1e-4)
    maximum_jacobian_condition_number: Positive = Field(default=1e14, le=1e16)
    local_parameter_covariance: tuple[tuple[float, ...], ...] | None = None
    local_parameter_covariance_reviewed: bool = False
    activity_provider_id: str = Field(min_length=1)
    activity_provider_revision: str = Field(min_length=1)
    activity_configuration_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    activity_record_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    equilibrium_provider_id: str = Field(min_length=1)
    equilibrium_provider_revision: str = Field(min_length=1)
    equilibrium_configuration_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    complete_aqueous_species_inventory_reviewed: bool
    reaction_stoichiometry_and_constant_reviewed: bool
    balance_constraints_and_charge_scope_reviewed: bool
    fixed_activity_coefficients_and_standard_state_reviewed: bool
    temperature_and_provider_lineage_reviewed: bool
    initial_activity_guess_and_solver_tolerance_reviewed: bool
    single_liquid_phase_and_no_precipitation_reviewed: bool
    elemental_formula_and_reaction_balance_reviewed: bool = False
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def unique_assembly_species_and_constraints(self):
        if len({row.species_id for row in self.species}) != len(self.species):
            raise ValueError("assembly species identifiers must be unique")
        if len({row.constraint_id for row in self.constraints}) != len(self.constraints):
            raise ValueError("assembly constraint identifiers must be unique")
        _validate_local_parameter_covariance(self.local_parameter_covariance, self.local_parameter_covariance_reviewed)
        return self


class AqueousReactionCandidateSpecies(Contract):
    """Caller-declared formula and charge used only for stoichiometric screening."""

    species_id: str = Field(min_length=1)
    charge_number: StrictInt = Field(ge=-8, le=8)
    elemental_composition: dict[str, StrictInt]

    @model_validator(mode="after")
    def valid_formula(self):
        if not self.elemental_composition or any(
            not element.strip() or count < 0
            for element, count in self.elemental_composition.items()
        ) or not any(self.elemental_composition.values()):
            raise ValueError("candidate enumeration requires complete nonnegative elemental formulas")
        return self


class AqueousReactionCandidateEnumeration(Contract):
    """Enumerate bounded, element/charge-balanced stoichiometries without assigning chemistry."""

    enumeration_id: str = Field(min_length=1)
    species: tuple[AqueousReactionCandidateSpecies, ...] = Field(min_length=2, max_length=12)
    maximum_total_stoichiometric_order: int = Field(default=4, ge=2, le=8)
    maximum_side_multisets: int = Field(default=250_000, ge=1, le=2_000_000)
    maximum_candidate_pair_checks: int = Field(default=250_000, ge=1, le=2_000_000)
    maximum_candidate_reactions: int = Field(default=50_000, ge=1, le=100_000)
    species_formula_and_charge_reviewed: bool
    closed_candidate_species_inventory_reviewed: bool
    candidate_use_and_manual_selection_reviewed: bool
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def unique_species_and_budget(self):
        ids = [row.species_id for row in self.species]
        if len(set(ids)) != len(ids):
            raise ValueError("candidate enumeration species IDs must be unique")
        order = self.maximum_total_stoichiometric_order
        side_count = sum(math.comb(len(ids) + degree - 1, degree) for degree in range(1, order + 1))
        if side_count > self.maximum_side_multisets:
            raise ValueError("enumeration side-multiset budget is insufficient for the declared species/order")
        return self


class AqueousCandidateReactionSelection(Contract):
    """A manually selected balanced candidate with caller-owned equilibrium data."""

    candidate_id: str = Field(min_length=1)
    candidate_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    reaction_id: str = Field(min_length=1)
    direction: Literal["candidate_forward", "candidate_reverse"]
    log10_equilibrium_constant: float
    temperature_K: Positive
    equilibrium_parameter_set_id: str = Field(min_length=1)
    equilibrium_record_id: str = Field(min_length=1)
    equilibrium_record_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")


class AqueousCandidateReactionBindingRequest(Contract):
    """Bind selected balance proposals to explicitly reviewed thermodynamic data."""

    schema_version: Literal["matintegrity.aqueous_candidate_reaction_binding.v1"] = (
        "matintegrity.aqueous_candidate_reaction_binding.v1"
    )
    binding_id: str = Field(min_length=1)
    candidate_enumeration_input_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    target_mass_action_temperature_K: Positive
    temperature_match_tolerance_K: float = Field(default=0.0, ge=0.0, le=5.0)
    target_activity_standard_state: Literal["molarity_1_mol_L"]
    selections: tuple[AqueousCandidateReactionSelection, ...] = Field(min_length=1, max_length=100)
    reaction_selection_and_constant_reviewed: bool
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def unique_selection_ids_and_parameter_evidence(self):
        if len({row.candidate_id for row in self.selections}) != len(self.selections):
            raise ValueError("each candidate may be selected at most once in one binding request")
        if len({row.reaction_id for row in self.selections}) != len(self.selections):
            raise ValueError("bound reaction IDs must be unique")
        evidence = {(row.source_id, row.sha256) for row in self.evidence}
        for row in self.selections:
            if (row.equilibrium_parameter_set_id, row.equilibrium_record_sha256) not in evidence:
                raise ValueError("each equilibrium record must match a declared Evidence source and SHA-256")
            if abs(row.temperature_K - self.target_mass_action_temperature_K) > self.temperature_match_tolerance_K:
                raise ValueError("each equilibrium parameter temperature must match the target mass-action temperature")
        return self


def bind_aqueous_candidate_reactions(
    candidate_enumeration: Calculation,
    request: AqueousCandidateReactionBindingRequest,
) -> Calculation:
    """Convert explicitly selected balanced candidates into signed mass-action reactions.

    No chemical selection, reaction direction, equilibrium constant, or temperature
    applicability is inferred. All thermodynamic records are supplied by the caller.
    """
    input_digest = canonical_digest(request.model_dump(mode="json"))
    candidate_result_digest = canonical_digest(candidate_enumeration.model_dump(mode="json"))
    base = {
        "binding_id": request.binding_id,
        "input_sha256": input_digest,
        "candidate_enumeration_input_sha256": request.candidate_enumeration_input_sha256,
        "candidate_enumeration_result_sha256": candidate_result_digest,
        "target_mass_action_temperature_K": request.target_mass_action_temperature_K,
        "temperature_match_tolerance_K": request.temperature_match_tolerance_K,
        "activity_standard_state": request.target_activity_standard_state,
        "temperature_K_by_reaction": [
            {"reaction_id": row.reaction_id, "temperature_K": row.temperature_K}
            for row in request.selections
        ],
    }
    if not request.reaction_selection_and_constant_reviewed:
        return Calculation(status="needs_data", values=base | {
            "missing_reviews": ["reaction_selection_and_constant_reviewed"],
            "reactions": [],
        })
    if candidate_enumeration.status != "computed":
        return Calculation(status="needs_data", values=base | {
            "reason": "candidate_enumeration_result_is_not_computed",
            "upstream_status": candidate_enumeration.status,
            "reactions": [],
        })
    if candidate_enumeration.values.get("input_sha256") != request.candidate_enumeration_input_sha256:
        return Calculation(status="needs_data", values=base | {
            "reason": "candidate_enumeration_input_digest_mismatch",
            "reactions": [],
        })
    if candidate_enumeration.values.get("enumerated_chemical_reactions") is not False:
        return Calculation(status="needs_data", values=base | {
            "reason": "upstream_result_is_not_a_balance_candidate_enumeration",
            "reactions": [],
        })

    candidates = candidate_enumeration.values.get("candidate_reactions")
    if not isinstance(candidates, list):
        return Calculation(status="needs_data", values=base | {
            "reason": "candidate_rows_are_missing_or_malformed",
            "reactions": [],
        })
    by_id: dict[str, dict] = {}
    for candidate in candidates:
        if not isinstance(candidate, dict):
            return Calculation(status="needs_data", values=base | {
                "reason": "candidate_row_is_malformed",
                "reactions": [],
            })
        candidate_id = candidate.get("candidate_id")
        candidate_sha256 = candidate.get("candidate_sha256")
        payload = {key: value for key, value in candidate.items() if key not in {"candidate_id", "candidate_sha256"}}
        if (
            not isinstance(candidate_id, str)
            or not isinstance(candidate_sha256, str)
            or canonical_digest(payload) != candidate_sha256
            or candidate_id != f"balanced-reaction:{candidate_sha256[:24]}"
            or candidate_id in by_id
        ):
            return Calculation(status="needs_data", values=base | {
                "reason": "candidate_identity_digest_invalid_or_duplicate",
                "reactions": [],
            })
        reactants = candidate.get("reactants")
        products = candidate.get("products")
        if not isinstance(reactants, list) or not isinstance(products, list) or not reactants or not products:
            return Calculation(status="needs_data", values=base | {
                "reason": "candidate_reactant_or_product_rows_are_malformed",
                "reactions": [],
            })
        for side in (reactants, products):
            for term in side:
                if (
                    not isinstance(term, dict)
                    or not isinstance(term.get("species_id"), str)
                    or not term["species_id"]
                    or isinstance(term.get("coefficient"), bool)
                    or not isinstance(term.get("coefficient"), int)
                    or term["coefficient"] <= 0
                ):
                    return Calculation(status="needs_data", values=base | {
                        "reason": "candidate_stoichiometric_term_is_malformed",
                        "reactions": [],
                    })
        reactant_ids = {term["species_id"] for term in reactants}
        product_ids = {term["species_id"] for term in products}
        if (
            len(reactant_ids) != len(reactants)
            or len(product_ids) != len(products)
            or reactant_ids.intersection(product_ids)
        ):
            return Calculation(status="needs_data", values=base | {
                "reason": "candidate_species_terms_are_duplicate_or_overlap_sides",
                "reactions": [],
            })
        by_id[candidate_id] = candidate

    reactions = []
    lineage = []
    for selection in request.selections:
        candidate = by_id.get(selection.candidate_id)
        if candidate is None or candidate.get("candidate_sha256") != selection.candidate_sha256:
            return Calculation(status="needs_data", values=base | {
                "reason": "selected_candidate_missing_or_digest_mismatch",
                "candidate_id": selection.candidate_id,
                "reactions": [],
            })
        signed_terms: list[dict] = []
        sign = 1.0 if selection.direction == "candidate_forward" else -1.0
        for term in candidate.get("reactants", []):
            signed_terms.append({"species_id": term["species_id"], "coefficient": -sign * term["coefficient"]})
        for term in candidate.get("products", []):
            signed_terms.append({"species_id": term["species_id"], "coefficient": sign * term["coefficient"]})
        reaction_payload = {
            "reaction_id": selection.reaction_id,
            "log10_equilibrium_constant": selection.log10_equilibrium_constant * sign,
            "terms": signed_terms,
        }
        reactions.append(reaction_payload)
        lineage.append({
            "reaction_id": selection.reaction_id,
            "candidate_id": selection.candidate_id,
            "candidate_sha256": selection.candidate_sha256,
            "direction": selection.direction,
            "source_log10_equilibrium_constant": selection.log10_equilibrium_constant,
            "signed_log10_equilibrium_constant": reaction_payload["log10_equilibrium_constant"],
            "bound_reaction_sha256": canonical_digest(reaction_payload),
            "temperature_K": selection.temperature_K,
            "equilibrium_parameter_set_id": selection.equilibrium_parameter_set_id,
            "equilibrium_record_id": selection.equilibrium_record_id,
            "equilibrium_record_sha256": selection.equilibrium_record_sha256,
        })
    return Calculation(values=base | {
        "reactions": reactions,
        "reaction_lineage": lineage,
        "reaction_count": len(reactions),
        "source_candidate_enumeration_sha256": candidate_result_digest,
        "equilibrium_data_inferred": False,
        "chemical_feasibility_inferred": False,
    }, notes=(
        "Candidate selection, reaction direction, equilibrium constants and temperature applicability are caller-supplied. Verify each bound reaction against the mass-action system temperature and standard state before use.",
    ))


def assemble_aqueous_mass_action_system(
    binding_result: Calculation,
    request: AqueousMassActionSystemAssemblyRequest,
) -> Calculation:
    """Assemble a strict solver input from non-reaction data and a binding result."""
    request_digest = canonical_digest(request.model_dump(mode="json"))
    binding_digest = canonical_digest(binding_result.model_dump(mode="json"))
    base = {
        "assessment_id": request.assessment_id,
        "solution_id": request.solution_id,
        "input_sha256": request_digest,
        "binding_result_sha256": binding_digest,
        "temperature_K": request.temperature_K,
        "activity_standard_state": request.activity_standard_state,
    }
    if binding_result.status != "computed":
        return Calculation(status="needs_data", values=base | {
            "reason": "candidate_binding_result_is_not_computed",
            "upstream_status": binding_result.status,
        })
    bound_values = binding_result.values
    binding_temperature = bound_values.get("target_mass_action_temperature_K")
    binding_tolerance = bound_values.get("temperature_match_tolerance_K")
    if (
        not isinstance(binding_temperature, (int, float))
        or isinstance(binding_temperature, bool)
        or not isinstance(binding_tolerance, (int, float))
        or isinstance(binding_tolerance, bool)
        or not math.isfinite(float(binding_tolerance))
        or float(binding_tolerance) < 0.0
        or abs(float(binding_temperature) - request.temperature_K)
            > float(binding_tolerance)
    ):
        return Calculation(status="needs_data", values=base | {
            "reason": "binding_target_temperature_does_not_match_assembly_temperature",
        })
    if bound_values.get("activity_standard_state") != request.activity_standard_state:
        return Calculation(status="needs_data", values=base | {
            "reason": "binding_activity_standard_state_does_not_match_assembly",
        })
    if bound_values.get("source_candidate_enumeration_sha256") != bound_values.get("candidate_enumeration_result_sha256"):
        return Calculation(status="needs_data", values=base | {
            "reason": "candidate_enumeration_result_digest_lineage_is_inconsistent",
        })
    reactions_raw = bound_values.get("reactions")
    lineage = bound_values.get("reaction_lineage")
    if (
        not isinstance(reactions_raw, list)
        or not isinstance(lineage, list)
        or not reactions_raw
        or len(reactions_raw) != len(lineage)
    ):
        return Calculation(status="needs_data", values=base | {
            "reason": "binding_reactions_or_lineage_are_missing_or_misaligned",
        })
    try:
        reactions = tuple(
            AqueousEquilibriumReaction.model_validate_json(json.dumps(row)) for row in reactions_raw
        )
        reaction_by_id = {row.reaction_id: row for row in reactions}
        evidence_records = {(row.source_id, row.sha256) for row in request.evidence}
        lineage_by_reaction: dict[str, dict] = {}
        for row in lineage:
            if not isinstance(row, dict):
                raise ValueError("reaction lineage row is not an object")
            reaction_id = row.get("reaction_id")
            candidate_id = row.get("candidate_id")
            candidate_sha256 = row.get("candidate_sha256")
            parameter_set_id = row.get("equilibrium_parameter_set_id")
            record_sha256 = row.get("equilibrium_record_sha256")
            row_temperature = row.get("temperature_K")
            direction = row.get("direction")
            source_log_k = row.get("source_log10_equilibrium_constant")
            signed_log_k = row.get("signed_log10_equilibrium_constant")
            bound_reaction_sha256 = row.get("bound_reaction_sha256")
            tolerance = float(bound_values["temperature_match_tolerance_K"])
            if (
                not isinstance(reaction_id, str)
                or reaction_id in lineage_by_reaction
                or not isinstance(candidate_sha256, str)
                or len(candidate_sha256) != 64
                or any(char not in "0123456789abcdef" for char in candidate_sha256)
                or candidate_id != f"balanced-reaction:{candidate_sha256[:24]}"
                or direction not in {"candidate_forward", "candidate_reverse"}
                or not isinstance(parameter_set_id, str)
                or (parameter_set_id, record_sha256) not in evidence_records
                or not isinstance(bound_reaction_sha256, str)
                or len(bound_reaction_sha256) != 64
                or any(char not in "0123456789abcdef" for char in bound_reaction_sha256)
                or not isinstance(source_log_k, (int, float))
                or isinstance(source_log_k, bool)
                or not isinstance(signed_log_k, (int, float))
                or isinstance(signed_log_k, bool)
                or not isinstance(row_temperature, (int, float))
                or isinstance(row_temperature, bool)
                or abs(float(row_temperature) - request.temperature_K) > tolerance
            ):
                raise ValueError("reaction lineage identity, evidence, or applicability check failed")
            reaction = reaction_by_id.get(reaction_id)
            direction_sign = 1.0 if direction == "candidate_forward" else -1.0
            if (
                reaction is None
                or reaction.log10_equilibrium_constant != float(signed_log_k)
                or float(signed_log_k) != float(source_log_k) * direction_sign
                or canonical_digest(reaction.model_dump(mode="json")) != bound_reaction_sha256
            ):
                raise ValueError("bound reaction payload differs from its signed-constant lineage")
            lineage_by_reaction[reaction_id] = row
        if set(lineage_by_reaction) != {row.reaction_id for row in reactions}:
            raise ValueError("reaction IDs and lineage IDs differ")
        system_payload = request.model_dump(mode="json")
        system_payload["schema_version"] = "matintegrity.aqueous_mass_action.v1"
        system_payload["reactions"] = [row.model_dump(mode="json") for row in reactions]
        equilibrium_record_digest = canonical_digest(lineage)
        system_payload["equilibrium_record_digest"] = equilibrium_record_digest
        system = AqueousMassActionSystem.model_validate_json(json.dumps(system_payload))
    except (ValidationError, TypeError, ValueError, KeyError) as exc:
        details = exc.errors(include_context=False) if isinstance(exc, ValidationError) else [{"message": str(exc)}]
        return Calculation(status="needs_data", values=base | {
            "reason": "assembled_mass_action_system_contract_rejected",
            "contract_errors": details,
            "reaction_count": len(reactions_raw),
            "constraint_count": len(request.constraints),
            "species_count": len(request.species),
        })
    system_digest = canonical_digest(system.model_dump(mode="json"))
    return Calculation(values=base | {
        "mass_action_system": system.model_dump(mode="json"),
        "mass_action_system_sha256": system_digest,
        "equilibrium_record_digest": equilibrium_record_digest,
        "reaction_lineage": lineage,
        "reaction_count": len(reactions),
        "species_count": len(system.species),
        "constraint_count": len(system.constraints),
    }, notes=(
        "The returned mass_action_system can be passed as inputs to chemistry.aqueous_mass_action_speciation. Its equilibrium_record_digest is the digest of the ordered bound reaction lineage; retain reaction_lineage with the result.",
        "This assembly applies the declared square-system contract. It does not check convergence, chemical feasibility, thermodynamic quality, or independent validation.",
    ))


def enumerate_aqueous_reaction_candidates(x: AqueousReactionCandidateEnumeration) -> Calculation:
    """Return primitive balanced integer reactions; this is not reaction discovery or selection."""
    digest = canonical_digest(x.model_dump(mode="json"))
    reviews = {
        "species_formula_and_charge_reviewed": x.species_formula_and_charge_reviewed,
        "closed_candidate_species_inventory_reviewed": x.closed_candidate_species_inventory_reviewed,
        "candidate_use_and_manual_selection_reviewed": x.candidate_use_and_manual_selection_reviewed,
    }
    missing = [name for name, accepted in reviews.items() if not accepted]
    base = {
        "enumeration_id": x.enumeration_id,
        "input_sha256": digest,
        "species_ids": [row.species_id for row in x.species],
        "maximum_total_stoichiometric_order": x.maximum_total_stoichiometric_order,
        "maximum_side_multisets": x.maximum_side_multisets,
        "maximum_candidate_pair_checks": x.maximum_candidate_pair_checks,
        "maximum_candidate_reactions": x.maximum_candidate_reactions,
        "enumerated_chemical_reactions": False,
        "equilibrium_constants_assigned": False,
        "reaction_direction_selected": False,
    }
    if missing:
        return Calculation(status="needs_data", values=base | {"missing_reviews": missing})

    elements = sorted({element for row in x.species for element in row.elemental_composition})
    species = tuple(x.species)
    composition_vectors = tuple(
        tuple(row.elemental_composition.get(element, 0) for element in elements)
        + (row.charge_number,)
        for row in species
    )
    vectors: dict[tuple[int, ...], list[tuple[int, ...]]] = {}
    side_multisets = 0
    pair_checks = 0
    for degree in range(1, x.maximum_total_stoichiometric_order + 1):
        for selected in combinations_with_replacement(range(len(species)), degree):
            counts = [0] * len(species)
            for index in selected:
                counts[index] += 1
            side_multisets += 1
            signature = tuple(
                sum(composition_vectors[index][axis] for index in selected)
                for axis in range(len(elements) + 1)
            )
            bucket = vectors.setdefault(signature, [])
            # Adding one side changes n**2 ordered pairs by 2*n + 1.
            # This monotone lower bound permits an early budget exit without
            # storing the rest of a catalog that cannot be evaluated.
            pair_checks += 2 * len(bucket) + 1
            if pair_checks > x.maximum_candidate_pair_checks:
                return Calculation(status="out_of_scope", values=base | {
                    "enumerated_side_multiset_count": side_multisets,
                    "required_candidate_pair_checks_lower_bound": pair_checks,
                    "side_enumeration_complete": False,
                    "out_of_scope_reason": "candidate_pair_check_budget_exceeded_no_partial_catalog_returned",
                })
            bucket.append(tuple(counts))

    pair_checks = sum(len(sides) ** 2 for sides in vectors.values())
    if pair_checks > x.maximum_candidate_pair_checks:
        return Calculation(status="out_of_scope", values=base | {
            "enumerated_side_multiset_count": side_multisets,
            "required_candidate_pair_checks": pair_checks,
            "out_of_scope_reason": "candidate_pair_check_budget_exceeded_no_partial_catalog_returned",
        })

    candidates: dict[tuple[tuple[str, int], ...], dict] = {}
    evaluated_unordered_pair_checks = 0
    for signature, sides in vectors.items():
        for reactant_index, reactants in enumerate(sides):
            for product_index in range(reactant_index + 1, len(sides)):
                products = sides[product_index]
                evaluated_unordered_pair_checks += 1
                if not any(reactants) or not any(products):
                    continue
                if sum(reactants) + sum(products) > x.maximum_total_stoichiometric_order:
                    continue
                if any(reactants[i] and products[i] for i in range(len(species))):
                    continue
                coefficients = [value for value in (*reactants, *products) if value]
                if math.gcd(*coefficients) != 1:
                    continue
                left = tuple((species[i].species_id, value) for i, value in enumerate(reactants) if value)
                right = tuple((species[i].species_id, value) for i, value in enumerate(products) if value)
                if right < left:
                    left, right = right, left
                key = left + (("->", 0),) + right
                if key in candidates:
                    continue
                if len(candidates) >= x.maximum_candidate_reactions:
                    return Calculation(status="out_of_scope", values=base | {
                        "enumerated_side_multiset_count": side_multisets,
                        "out_of_scope_reason": "candidate_reaction_budget_exceeded_no_partial_catalog_returned",
                    })
                candidate_payload = {
                    "reactants": [{"species_id": name, "coefficient": value} for name, value in left],
                    "products": [{"species_id": name, "coefficient": value} for name, value in right],
                    "balanced_elements": elements,
                    "charge_stoichiometric_residual": 0,
                }
                candidate_digest = canonical_digest(candidate_payload)
                candidates[key] = candidate_payload | {
                    "candidate_id": f"balanced-reaction:{candidate_digest[:24]}",
                    "candidate_sha256": candidate_digest,
                }
    ordered = [candidates[key] for key in sorted(candidates)]
    return Calculation(status="computed", values=base | {
        "enumerated_side_multiset_count": side_multisets,
        "side_enumeration_complete": True,
        "candidate_pair_checks": pair_checks,
        "candidate_pair_budget_basis": "ordered_pairs_including_self_pairs",
        "evaluated_unordered_pair_checks": evaluated_unordered_pair_checks,
        "candidate_reaction_count": len(ordered),
        "candidate_reactions": ordered,
    }, notes=(
        "Candidates are bounded integer stoichiometries satisfying only caller-supplied elemental and charge balances. This enumeration does not establish chemical feasibility, reaction mechanism, phases, kinetics, equilibrium constants, direction, or completeness outside the declared species/order bounds; every candidate requires independent review before use.",
        "candidate_id is a stable digest-derived reference to the normalized, direction-neutral stoichiometric split; it does not identify a validated chemical reaction or provide thermodynamic data.",
    ))


def aqueous_mass_action_speciation(x: AqueousMassActionSystem) -> Calculation:
    """Solve caller-declared fixed-gamma aqueous reactions and linear constraints.

    The unknowns are natural logarithms of dimensionless species activities. Mass
    constraints are normalized by caller scales, and equilibrium residuals use
    natural-log K. A damped Newton step solves the square system without clipping
    concentrations or imposing a default charge balance.
    """
    input_digest = canonical_digest(x.model_dump(mode="json"))
    base = {
        "assessment_id": x.assessment_id,
        "solution_id": x.solution_id,
        "temperature_K": x.temperature_K,
        "activity_standard_state": x.activity_standard_state,
        "activity_provider_id": x.activity_provider_id,
        "activity_provider_revision": x.activity_provider_revision,
        "activity_configuration_digest": x.activity_configuration_digest,
        "activity_record_digest": x.activity_record_digest,
        "equilibrium_provider_id": x.equilibrium_provider_id,
        "equilibrium_provider_revision": x.equilibrium_provider_revision,
        "equilibrium_configuration_digest": x.equilibrium_configuration_digest,
        "equilibrium_record_digest": x.equilibrium_record_digest,
        "input_digest": input_digest,
    }
    reviews = {
        "complete_aqueous_species_inventory_reviewed": x.complete_aqueous_species_inventory_reviewed,
        "reaction_stoichiometry_and_constant_reviewed": x.reaction_stoichiometry_and_constant_reviewed,
        "balance_constraints_and_charge_scope_reviewed": x.balance_constraints_and_charge_scope_reviewed,
        "fixed_activity_coefficients_and_standard_state_reviewed": x.fixed_activity_coefficients_and_standard_state_reviewed,
        "temperature_and_provider_lineage_reviewed": x.temperature_and_provider_lineage_reviewed,
        "initial_activity_guess_and_solver_tolerance_reviewed": x.initial_activity_guess_and_solver_tolerance_reviewed,
        "single_liquid_phase_and_no_precipitation_reviewed": x.single_liquid_phase_and_no_precipitation_reviewed,
    }
    if any(row.elemental_composition is not None for row in x.species):
        reviews["elemental_formula_and_reaction_balance_reviewed"] = x.elemental_formula_and_reaction_balance_reviewed
    missing_reviews = [name for name, reviewed in reviews.items() if not reviewed]
    if missing_reviews:
        return Calculation(
            status="needs_data",
            values=base | {"missing_reviews": missing_reviews},
            notes=("Complete species inventory, caller equations, activity convention, phase scope, and provider lineage must be reviewed.",),
        )

    species = x.species
    index = {row.species_id: i for i, row in enumerate(species)}
    count = len(species)
    charges = {row.species_id: row.charge_number for row in species}
    formulas = {row.species_id: row.elemental_composition or {} for row in species}
    elements = sorted(set().union(*(formula.keys() for formula in formulas.values())))
    reaction_balance_diagnostics = []
    reaction_matrix = np.zeros((len(x.reactions), count), dtype=float)
    log_constants = np.zeros(len(x.reactions), dtype=float)
    for row_index, reaction in enumerate(x.reactions):
        charge_residual = math.fsum(term.coefficient * charges[term.species_id] for term in reaction.terms)
        elemental_residuals = {
            element: math.fsum(
                term.coefficient * formulas[term.species_id].get(element, 0)
                for term in reaction.terms
            )
            for element in elements
        }
        reaction_balance_diagnostics.append({
            "reaction_id": reaction.reaction_id,
            "charge_stoichiometric_residual": charge_residual,
            "elemental_stoichiometric_residuals": elemental_residuals if elements else None,
        })
        for term in reaction.terms:
            reaction_matrix[row_index, index[term.species_id]] = term.coefficient
        log_constants[row_index] = math.log(10.0) * reaction.log10_equilibrium_constant

    balance_matrix = np.zeros((len(x.constraints), count), dtype=float)
    targets = np.zeros(len(x.constraints), dtype=float)
    scales = np.zeros(len(x.constraints), dtype=float)
    for row_index, constraint in enumerate(x.constraints):
        for term in constraint.terms:
            balance_matrix[row_index, index[term.species_id]] = term.coefficient
        targets[row_index] = constraint.target_mol_L
        scales[row_index] = constraint.residual_scale_mol_L

    equation_matrix = np.vstack((balance_matrix, reaction_matrix))
    row_maximums = np.max(np.abs(equation_matrix), axis=1)
    scaled_equation_matrix = equation_matrix / row_maximums[:, np.newaxis]
    equation_row_norms = np.linalg.norm(scaled_equation_matrix, axis=1)
    normalized_equation_matrix = scaled_equation_matrix / equation_row_norms[:, np.newaxis]
    try:
        structural_rank = int(np.linalg.matrix_rank(normalized_equation_matrix))
    except np.linalg.LinAlgError:
        structural_rank = 0
    solver_basis = {
        "solver_id": "damped_newton_log_activity_v1",
        "unknown_count": count,
        "equation_count": equation_matrix.shape[0],
        "structural_equation_rank": structural_rank,
        "maximum_jacobian_condition_number": x.maximum_jacobian_condition_number,
    }
    if structural_rank < count:
        return Calculation(
            status="out_of_scope",
            values=base | solver_basis | {
                "out_of_scope_reason": "rank_deficient_equation_system",
                "rank_deficiency": count - structural_rank,
                "iterations": 0,
            },
            notes=("Caller equations do not independently constrain all species activities; revise the species/reaction/constraint basis.",),
        )

    gamma = np.asarray([row.activity_coefficient for row in species], dtype=float)
    initial_activities = np.asarray([row.initial_activity for row in species], dtype=float)
    log_activity = np.log(initial_activities)
    if np.any(~np.isfinite(log_activity)) or np.any(log_activity < -700.0) or np.any(log_activity > 700.0):
        return Calculation(
            status="out_of_scope",
            values=base | solver_basis | {
                "out_of_scope_reason": "initial_activity_outside_finite_exponential_range",
                "termination_reason": "initial_activity_outside_finite_exponential_range",
                "iterations": 0,
            },
            notes=("Initial activities must be representable without concentration clipping.",),
        )

    def evaluate(vector: np.ndarray):
        if np.any(~np.isfinite(vector)) or np.any(vector < -700.0) or np.any(vector > 700.0):
            return None
        activities = np.exp(vector)
        concentrations = activities / gamma
        if np.any(~np.isfinite(concentrations)) or np.any(concentrations <= 0.0):
            return None
        totals = balance_matrix @ concentrations
        balance_residual = (totals - targets) / scales
        reaction_residual = reaction_matrix @ vector - log_constants
        residual = np.concatenate((balance_residual, reaction_residual))
        if np.any(~np.isfinite(residual)):
            return None
        jac_balance = (balance_matrix * concentrations[np.newaxis, :]) / scales[:, np.newaxis]
        jacobian = np.vstack((jac_balance, reaction_matrix))
        if np.any(~np.isfinite(jacobian)):
            return None
        return activities, concentrations, totals, balance_residual, reaction_residual, residual, jacobian

    iteration = 0
    norm = math.inf
    initial_norm = math.inf
    converged = False
    termination_reason = "maximum_iterations_reached"
    jacobian_rank: int | None = None
    jacobian_condition_number: float | None = None
    solver_steps = []
    for iteration in range(x.maximum_iterations + 1):
        state = evaluate(log_activity)
        if state is None:
            termination_reason = "nonfinite_or_unrepresentable_iterate"
            break
        norm = float(np.linalg.norm(state[5], ord=np.inf))
        if iteration == 0:
            initial_norm = norm
        if norm <= x.normalized_residual_tolerance:
            converged = True
            termination_reason = "residual_tolerance_reached"
            break
        if iteration == x.maximum_iterations:
            termination_reason = "maximum_iterations_reached"
            break
        jacobian = state[6]
        try:
            jacobian_rank = int(np.linalg.matrix_rank(jacobian))
            condition_number = float(np.linalg.cond(jacobian))
            jacobian_condition_number = condition_number if math.isfinite(condition_number) else None
            if jacobian_rank < count:
                termination_reason = "rank_deficient_jacobian"
                break
            if not math.isfinite(condition_number) or condition_number > x.maximum_jacobian_condition_number:
                termination_reason = "jacobian_condition_limit_exceeded"
                break
            step = np.linalg.solve(jacobian, -state[5])
        except np.linalg.LinAlgError:
            termination_reason = "singular_jacobian_factorization"
            break
        if np.any(~np.isfinite(step)):
            termination_reason = "nonfinite_newton_step"
            break
        accepted = False
        damping = 1.0
        for _ in range(32):
            candidate = log_activity + damping * step
            candidate_state = evaluate(candidate)
            if candidate_state is not None:
                candidate_norm = float(np.linalg.norm(candidate_state[5], ord=np.inf))
                if candidate_norm < norm or candidate_norm <= x.normalized_residual_tolerance:
                    log_activity = candidate
                    solver_steps.append({"iteration": iteration, "accepted_damping": damping, "residual_norm": candidate_norm})
                    accepted = True
                    break
            damping *= 0.5
        if not accepted:
            termination_reason = "damped_line_search_failed"
            break

    solver_diagnostics = solver_basis | {
        "iterations": iteration,
        "initial_normalized_residual_norm": initial_norm if math.isfinite(initial_norm) else None,
        "final_normalized_residual_norm": norm if math.isfinite(norm) else None,
        "jacobian_rank": jacobian_rank,
        "jacobian_condition_number": jacobian_condition_number,
        "termination_reason": termination_reason,
        "accepted_steps": solver_steps,
    }

    state = evaluate(log_activity)
    if state is None:
        return Calculation(
            status="out_of_scope",
            values=base | solver_diagnostics | {"out_of_scope_reason": termination_reason},
            notes=("No clipping or fallback equilibrium model is applied.",),
        )
    activities, concentrations, totals, balance_residual, reaction_residual, residual, final_jacobian = state
    norm = float(np.linalg.norm(residual, ord=np.inf))
    if not converged or norm > x.normalized_residual_tolerance:
        return Calculation(
            status="out_of_scope",
            values=base | solver_diagnostics | {
                "out_of_scope_reason": termination_reason,
                "normalized_balance_residuals": [
                    {"constraint_id": row.constraint_id, "residual": float(balance_residual[i])}
                    for i, row in enumerate(x.constraints)
                ],
                "log_equilibrium_residuals": [
                    {"reaction_id": row.reaction_id, "residual_ln": float(reaction_residual[i])}
                    for i, row in enumerate(x.reactions)
                ],
            },
            notes=("The caller-supplied initial guess and equation system did not yield a supported finite closure within the declared iteration budget.",),
        )

    # Local implicit derivatives of the converged fixed-gamma equilibrium.
    # The Newton Jacobian is also the derivative of the residual with respect
    # to log activities, so one bounded linear solve yields all requested
    # parameter columns without finite-difference perturbations.
    constraint_count = len(x.constraints)
    reaction_count = len(x.reactions)
    parameter_count = reaction_count + constraint_count + count
    sensitivity_parameters = (
        [{"kind": "log10_equilibrium_constant", "id": row.reaction_id, "unit": "1"}
         for row in x.reactions]
        + [{"kind": "constraint_target", "id": row.constraint_id, "unit": "mol/L"}
           for row in x.constraints]
        + [{"kind": "ln_activity_coefficient", "id": row.species_id, "unit": "1"}
           for row in species]
    )
    sensitivity_rhs = np.zeros((count, parameter_count), dtype=float)
    for j in range(reaction_count):
        sensitivity_rhs[constraint_count + j, j] = math.log(10.0)
    for j, constraint in enumerate(x.constraints):
        sensitivity_rhs[j, reaction_count + j] = 1.0 / constraint.residual_scale_mol_L
    for j in range(count):
        sensitivity_rhs[:constraint_count, reaction_count + constraint_count + j] = (
            balance_matrix[:, j] * concentrations[j] / scales
        )
    local_sensitivities = None
    sensitivity_status = "computed"
    try:
        sensitivity_condition = float(np.linalg.cond(final_jacobian))
        if (
            not math.isfinite(sensitivity_condition)
            or sensitivity_condition > x.maximum_jacobian_condition_number
        ):
            sensitivity_status = "out_of_scope_jacobian_condition_limit"
        else:
            d_log_activity = np.linalg.solve(final_jacobian, sensitivity_rhs)
            d_log_concentration = d_log_activity.copy()
            for j in range(count):
                d_log_concentration[j, reaction_count + constraint_count + j] -= 1.0
            d_concentration = concentrations[:, np.newaxis] * d_log_concentration
            if not all(np.all(np.isfinite(values)) for values in (d_log_activity, d_log_concentration, d_concentration)):
                sensitivity_status = "out_of_scope_nonfinite_sensitivity"
            else:
                local_sensitivities = {
                    "method": "implicit_derivative_of_converged_log_activity_system",
                    "jacobian_condition_number": sensitivity_condition,
                    "parameter_order": sensitivity_parameters,
                    "species": [
                        {
                            "species_id": row.species_id,
                            "d_ln_activity_d_parameter": d_log_activity[i].tolist(),
                            "d_ln_concentration_d_parameter": d_log_concentration[i].tolist(),
                            "d_concentration_mol_L_d_parameter": d_concentration[i].tolist(),
                        }
                        for i, row in enumerate(species)
                    ],
                }
    except np.linalg.LinAlgError:
        sensitivity_status = "out_of_scope_singular_sensitivity_jacobian"

    covariance_result = {"status": "not_requested"}
    if x.local_parameter_covariance is not None:
        covariance_result = {"status": "sensitivity_unavailable"}
        if local_sensitivities is not None:
            parameter_covariance = np.asarray(x.local_parameter_covariance, dtype=float)
            parameter_covariance = 0.5 * (parameter_covariance + parameter_covariance.T)
            with np.errstate(over="ignore", invalid="ignore", under="ignore"):
                log_activity_covariance = d_log_activity @ parameter_covariance @ d_log_activity.T
                log_concentration_covariance = d_log_concentration @ parameter_covariance @ d_log_concentration.T
                concentration_covariance = d_concentration @ parameter_covariance @ d_concentration.T
            covariance_matrices = (
                log_activity_covariance,
                log_concentration_covariance,
                concentration_covariance,
            )
            for matrix in covariance_matrices:
                matrix[:] = 0.5 * (matrix + matrix.T)
            if not all(np.all(np.isfinite(matrix)) for matrix in covariance_matrices):
                covariance_result = {"status": "out_of_scope_nonfinite_covariance"}
            else:
                covariance_result = {
                    "status": "computed_first_order_covariance",
                    "parameter_order": sensitivity_parameters,
                    "species_order": [row.species_id for row in species],
                    "ln_activity_covariance": log_activity_covariance.tolist(),
                    "ln_concentration_covariance": log_concentration_covariance.tolist(),
                    "concentration_covariance_mol2_L2": concentration_covariance.tolist(),
                    "concentration_standard_deviation_mol_L": [
                        math.sqrt(max(0.0, float(concentration_covariance[i, i])))
                        for i in range(count)
                    ],
                }

    return Calculation(
        values=base | {
            **solver_diagnostics,
            "normalized_residual_norm": norm,
            "species": [
                {
                    "species_id": row.species_id,
                    "charge_number": row.charge_number,
                    "elemental_composition": row.elemental_composition,
                    "activity_coefficient": row.activity_coefficient,
                    "dimensionless_activity": float(activities[i]),
                    "concentration_mol_L": float(concentrations[i]),
                }
                for i, row in enumerate(species)
            ],
            "constraint_closure": [
                {
                    "constraint_id": row.constraint_id,
                    "target_mol_L": row.target_mol_L,
                    "reconstructed_mol_L": float(totals[i]),
                    "residual_mol_L": float(totals[i] - targets[i]),
                    "normalized_residual": float(balance_residual[i]),
                    "scale_mol_L": row.residual_scale_mol_L,
                }
                for i, row in enumerate(x.constraints)
            ],
            "reaction_closure": [
                reaction_balance_diagnostics[i] | {"residual_ln": float(reaction_residual[i])}
                for i, row in enumerate(x.reactions)
            ],
            "charge_balance_is_user_declared": True,
            "reaction_charge_conservation_checked": True,
            "elemental_balance_checked": bool(elements),
            "elemental_formula_and_reaction_balance_reviewed": x.elemental_formula_and_reaction_balance_reviewed,
            "activity_coefficients_are_fixed": True,
            "aqueous_liquid_only": True,
            "local_sensitivity_status": sensitivity_status,
            "local_sensitivities": local_sensitivities,
            "local_sensitivity_covariance": covariance_result,
        },
        notes=(
            "Activities use the declared 1 mol/L standard state and caller-supplied fixed activity coefficients; the square user reaction/constraint system is solved in log-activity coordinates. Signed reaction charge balance is checked, and complete caller elemental formulas enable per-reaction elemental conservation checks.",
            "Only the declared single aqueous liquid phase is represented. No automatic water balance, ionic strength iteration, gas-liquid equilibrium, precipitation, kinetic response, corrosion rate, or acceptance is inferred.",
            "Local sensitivities are implicit derivatives at the computed state for log10(K), declared constraint targets and fixed activity coefficients. They are not uncertainty intervals, covariance propagation, global response bounds or model validation.",
        ),
    )


def specifications() -> list[ModelSpec]:
    return [
        ModelSpec(
            "chemistry.aqueous_reaction_candidate_enumeration",
            AqueousReactionCandidateEnumeration,
            enumerate_aqueous_reaction_candidates,
            {
                "candidate_reaction_count": "1",
                "enumerated_side_multiset_count": "1",
                "candidate_reactions[].charge_stoichiometric_residual": "charge-equivalent stoichiometry",
                "candidate_reactions[].coefficient": "1",
            },
            (
                "Complete caller-supplied formulas and ionic charges define a bounded integer search; candidates satisfy atom and charge conservation within the declared species set and total order.",
                "Enumeration is a stoichiometric screen only. It does not identify feasible chemistry, phase, reaction direction, equilibrium constants, rate laws, completeness, or corrosion behavior; candidates require independent selection and qualification.",
            ),
            ("caller_element_charge_balanced_aqueous_reaction_candidate_enumeration",),
        ),
        ModelSpec(
            "chemistry.aqueous_mass_action_speciation",
            AqueousMassActionSystem,
            aqueous_mass_action_speciation,
            {
                "temperature_K": "K",
                "species.dimensionless_activity": "1",
                "species.concentration_mol_L": "mol/L",
                "constraint_closure.target_mol_L": "mol/L",
                "constraint_closure.reconstructed_mol_L": "mol/L",
                "constraint_closure.residual_mol_L": "mol/L",
                "constraint_closure.normalized_residual": "1",
                "reaction_closure.residual_ln": "1",
                "reaction_closure.charge_stoichiometric_residual": "charge-equivalent stoichiometry",
                "reaction_closure.elemental_stoichiometric_residuals": "atom stoichiometry",
                "normalized_residual_norm": "1",
                "iterations": "1",
                "unknown_count": "1",
                "equation_count": "1",
                "structural_equation_rank": "1",
                "jacobian_rank": "1",
                "jacobian_condition_number": "1",
                "maximum_jacobian_condition_number": "1",
                "initial_normalized_residual_norm": "1",
                "final_normalized_residual_norm": "1",
                "accepted_steps[].accepted_damping": "1",
                "accepted_steps[].residual_norm": "1",
                "local_sensitivities.jacobian_condition_number": "1",
                "local_sensitivities.species[].d_ln_activity_d_parameter": "parameter-specific derivative",
                "local_sensitivities.species[].d_ln_concentration_d_parameter": "parameter-specific derivative",
                "local_sensitivities.species[].d_concentration_mol_L_d_parameter": "mol/L per parameter unit",
                "local_sensitivity_covariance.ln_activity_covariance": "1^2",
                "local_sensitivity_covariance.ln_concentration_covariance": "1^2",
                "local_sensitivity_covariance.concentration_covariance_mol2_L2": "(mol/L)^2",
                "local_sensitivity_covariance.concentration_standard_deviation_mol_L": "mol/L",
            },
            (
                "Caller-supplied single-phase aqueous species, fixed activity coefficients, mass-action equilibrium constants, charge-balanced signed reaction stoichiometry, optional complete reviewed elemental formulas, linear analytical/charge constraints and explicit positive initial activities.",
                "No ionic strength iteration, gas/solid phase, precipitation, kinetic law or corrosion inference is included.",
            ),
            ("caller_general_aqueous_mass_action_speciation",),
        )
    ]
