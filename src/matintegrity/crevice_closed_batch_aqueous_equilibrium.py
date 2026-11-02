"""Closed-batch aqueous equilibrium from explicit conserved-component inventories."""

from __future__ import annotations

import math
from typing import Literal

from pydantic import Field, model_validator

from .contracts import Calculation, Contract, Positive, canonical_digest
from .crevice_aqueous_component_ledger import (
    ConservedAqueousComponent,
    ConstraintRoleAssignment,
)
from .models.aqueous_activity_iteration import (
    AqueousDaviesIteration,
    aqueous_davies_self_consistent_speciation,
)
from .registry import ModelSpec

MODEL_ID = "chemistry.crevice_closed_batch_aqueous_equilibrium"
METHOD_SOURCE_ID = "closed_batch_conserved_aqueous_component_mass_action_davies"


class InitialSpeciesAmount(Contract):
    species_id: str = Field(min_length=1)
    amount_mol: float = Field(ge=0.0)

    @model_validator(mode="after")
    def finite_amount(self):
        if not math.isfinite(self.amount_mol):
            raise ValueError("initial species amount must be finite")
        return self


class CreviceClosedBatchAqueousEquilibriumRequest(Contract):
    schema_version: Literal["matintegrity.crevice_closed_batch_aqueous_equilibrium.v1"] = (
        "matintegrity.crevice_closed_batch_aqueous_equilibrium.v1"
    )
    assessment_id: str = Field(min_length=1)
    cell_id: str = Field(min_length=1)
    solution_volume_L: Positive
    aqueous_activity_request: AqueousDaviesIteration
    initial_species_amounts: tuple[InitialSpeciesAmount, ...] = Field(min_length=2, max_length=100)
    constraint_roles: tuple[ConstraintRoleAssignment, ...] = Field(min_length=1, max_length=100)
    conserved_components: tuple[ConservedAqueousComponent, ...] = Field(min_length=1, max_length=100)
    maximum_total_equilibrium_iterations: int = Field(default=20_000, ge=1, le=2_000_000)
    absolute_charge_inventory_tolerance_mol_eq: Positive = 1e-12
    absolute_component_closure_tolerance_mol: Positive = 1e-12
    relative_component_closure_tolerance: Positive = Field(default=1e-8, le=1e-2)
    role_map_and_charge_scope_reviewed: bool
    closed_inventory_scope_reviewed: bool
    single_liquid_no_precipitation_scope_reviewed: bool
    equilibrium_and_activity_provider_scope_reviewed: bool
    computational_use_authorized: bool

    @model_validator(mode="after")
    def validate_closed_component_basis(self):
        system = self.aqueous_activity_request.system
        species_ids = tuple(row.species_id for row in system.species)
        species_set = set(species_ids)
        initial_by_id = {row.species_id: row.amount_mol for row in self.initial_species_amounts}
        if len(initial_by_id) != len(self.initial_species_amounts) or set(initial_by_id) != species_set:
            raise ValueError("initial inventory must include each declared aqueous species exactly once")
        constraints = {row.constraint_id: row for row in system.constraints}
        roles = {row.constraint_id: row for row in self.constraint_roles}
        if len(roles) != len(self.constraint_roles) or set(roles) != set(constraints):
            raise ValueError("constraint roles must partition every and only declared constraint ID")
        components = {row.component_id: row for row in self.conserved_components}
        if len(components) != len(self.conserved_components):
            raise ValueError("conserved component IDs must be unique")
        component_roles = [row for row in self.constraint_roles if row.role == "conserved_component"]
        if {row.component_id for row in component_roles} != set(components) or len(component_roles) != len(components):
            raise ValueError("each component must map one-to-one to a conserved_component constraint")
        charge_roles = [row for row in self.constraint_roles if row.role == "charge_neutrality"]
        if len(charge_roles) != 1:
            raise ValueError("exactly one charge_neutrality constraint role is required")
        charge = constraints[charge_roles[0].constraint_id]
        expected_charge = {row.species_id: row.charge_number for row in system.species if row.charge_number != 0}
        if ({term.species_id: term.coefficient for term in charge.terms} != expected_charge
                or charge.target_mol_L != 0.0):
            raise ValueError("charge row must exactly match declared species charges and have a zero target")
        for assignment in component_roles:
            component = components[assignment.component_id]
            component_map = {row.species_id: row.coefficient for row in component.species_coefficients}
            row_map = {term.species_id: term.coefficient for term in constraints[assignment.constraint_id].terms}
            if component_map.keys() - species_set or component_map != row_map:
                raise ValueError("component map must exactly match its declared constraint coefficient row")
            for reaction in system.reactions:
                reaction_terms = {term.species_id: term.coefficient for term in reaction.terms}
                residual = math.fsum(component_map.get(sid, 0.0) * coefficient
                                     for sid, coefficient in reaction_terms.items())
                scale = max(1.0, math.fsum(abs(component_map.get(sid, 0.0) * coefficient)
                                          for sid, coefficient in reaction_terms.items()))
                if not math.isfinite(residual) or abs(residual) > 1e-12 * scale:
                    raise ValueError(f"reaction {reaction.reaction_id} does not conserve {component.component_id}")
        required_reviews = (
            self.role_map_and_charge_scope_reviewed,
            self.closed_inventory_scope_reviewed,
            self.single_liquid_no_precipitation_scope_reviewed,
            self.equilibrium_and_activity_provider_scope_reviewed,
            self.computational_use_authorized,
        )
        if not all(required_reviews):
            raise ValueError("closed inventory, charge, phase, provider and computational reviews are required")
        solver = self.aqueous_activity_request
        max_steps = solver.maximum_outer_iterations * (system.maximum_iterations + 1)
        if max_steps > self.maximum_total_equilibrium_iterations:
            raise ValueError("nested Davies and mass-action iteration limits exceed maximum_total_equilibrium_iterations")
        return self


def evaluate_crevice_closed_batch_aqueous_equilibrium(
    request: CreviceClosedBatchAqueousEquilibriumRequest,
) -> Calculation:
    """Solve a closed aqueous batch while holding explicit component totals fixed."""
    input_sha = canonical_digest(request.model_dump(mode="json"))
    activity_request = request.aqueous_activity_request
    system = activity_request.system
    initial_mol = {row.species_id: row.amount_mol for row in request.initial_species_amounts}
    initial_charge_mol_eq = math.fsum(
        row.charge_number * initial_mol[row.species_id] for row in system.species
    )
    if abs(initial_charge_mol_eq) > request.absolute_charge_inventory_tolerance_mol_eq:
        return Calculation(status="needs_data", values={
            "model_id": MODEL_ID,
            "assessment_id": request.assessment_id,
            "cell_id": request.cell_id,
            "input_sha256": input_sha,
            "reason": "initial_inventory_charge_does_not_match_zero_target",
            "initial_charge_inventory_mol_eq": initial_charge_mol_eq,
            "allowed_charge_inventory_mol_eq": request.absolute_charge_inventory_tolerance_mol_eq,
            "committed": False,
        })
    component_by_id = {row.component_id: row for row in request.conserved_components}
    target_by_constraint = {}
    component_initial = {}
    for assignment in request.constraint_roles:
        if assignment.role != "conserved_component":
            continue
        component = component_by_id[assignment.component_id]
        total_mol = math.fsum(term.coefficient * initial_mol[term.species_id]
                              for term in component.species_coefficients)
        target = total_mol / request.solution_volume_L
        if not math.isfinite(target):
            return Calculation(status="needs_data", values={
                "model_id": MODEL_ID,
                "assessment_id": request.assessment_id,
                "input_sha256": input_sha,
                "reason": "conserved_component_target_not_finite",
                "component_id": component.component_id,
                "target_mol_L": target,
                "committed": False,
            })
        target_by_constraint[assignment.constraint_id] = target
        component_initial[component.component_id] = total_mol
    constraints = tuple(
        row.model_copy(update={"target_mol_L": target_by_constraint[row.constraint_id]})
        if row.constraint_id in target_by_constraint else row
        for row in system.constraints
    )
    stage_system = system.model_copy(update={"constraints": constraints})
    stage_request = activity_request.model_copy(update={"system": stage_system})
    result = aqueous_davies_self_consistent_speciation(stage_request)
    if result.status != "computed":
        return Calculation(status="needs_data", values={
            "model_id": MODEL_ID,
            "assessment_id": request.assessment_id,
            "cell_id": request.cell_id,
            "input_sha256": input_sha,
            "stage_equilibrium_input_sha256": canonical_digest(stage_request.model_dump(mode="json")),
            "inner_result": result.model_dump(mode="json"),
            "committed": False,
            "qualification_claimed": False,
        })
    output_species = result.values.get("species")
    if not isinstance(output_species, (list, tuple)):
        return Calculation(status="needs_data", values={
            "model_id": MODEL_ID, "assessment_id": request.assessment_id,
            "input_sha256": input_sha, "reason": "equilibrium_species_output_missing",
            "inner_result_sha256": canonical_digest(result.model_dump(mode="json")),
            "committed": False,
        })
    final_by_species = {row["species_id"]: row for row in output_species}
    if set(final_by_species) != set(initial_mol):
        return Calculation(status="needs_data", values={
            "model_id": MODEL_ID, "assessment_id": request.assessment_id,
            "input_sha256": input_sha, "reason": "equilibrium_species_identity_mismatch",
            "inner_result_sha256": canonical_digest(result.model_dump(mode="json")),
            "committed": False,
        })
    component_results = []
    closure_ok = True
    maximum_normalized_residual = 0.0
    for component in request.conserved_components:
        coefficients = {row.species_id: row.coefficient for row in component.species_coefficients}
        final_concentration = math.fsum(
            coefficients.get(species_id, 0.0) * float(final_by_species[species_id]["concentration_mol_L"])
            for species_id in final_by_species
        )
        final_mol = final_concentration * request.solution_volume_L
        initial_mol_component = component_initial[component.component_id]
        residual = final_mol - initial_mol_component
        allowed = request.absolute_component_closure_tolerance_mol + request.relative_component_closure_tolerance \
            * max(abs(final_mol), abs(initial_mol_component), 1e-30)
        normalized = abs(residual) / allowed
        maximum_normalized_residual = max(maximum_normalized_residual, normalized)
        closure_ok = closure_ok and normalized <= 1.0
        component_results.append({
            "component_id": component.component_id,
            "initial_inventory_mol": initial_mol_component,
            "final_inventory_mol": final_mol,
            "inventory_residual_mol": residual,
            "allowed_residual_mol": allowed,
            "target_mol_L": target_by_constraint[next(
                row.constraint_id for row in request.constraint_roles
                if row.role == "conserved_component" and row.component_id == component.component_id
            )],
        })
    status = "computed" if closure_ok else "needs_data"
    return Calculation(status=status, values={
        "model_id": MODEL_ID,
        "assessment_id": request.assessment_id,
        "cell_id": request.cell_id,
        "input_sha256": input_sha,
        "stage_equilibrium_input_sha256": canonical_digest(stage_request.model_dump(mode="json")),
        "equilibrium_result_sha256": canonical_digest(result.model_dump(mode="json")),
        "solution_volume_L": request.solution_volume_L,
        "temperature_K": system.temperature_K,
        "component_inventory_closure": component_results,
        "maximum_normalized_component_residual": maximum_normalized_residual,
        "aqueous_equilibrium": result.values,
        "committed": closure_ok,
        "qualification_claimed": False,
        "limitations": [
            "Closed single-liquid aqueous equilibrium only; no solid transfer, precipitation, gas exchange, reservoir, transport or BDF coupling.",
            "Caller-defined fixed-gamma mass action is iterated with the supplied Davies activity model and caller-owned parameter evidence.",
            "Component inventories are closed under the explicit linear maps; any unclassified constraint must be assigned fixed_target by the caller.",
        ],
    })


def specifications() -> tuple[ModelSpec, ...]:
    return (ModelSpec(
        model_id=MODEL_ID,
        input_type=CreviceClosedBatchAqueousEquilibriumRequest,
        evaluator=evaluate_crevice_closed_batch_aqueous_equilibrium,
        units={
            "solution_volume_L": "L",
            "initial_species_amounts[].amount_mol": "mol",
            "component_inventory_closure[].initial_inventory_mol": "mol",
            "component_inventory_closure[].final_inventory_mol": "mol",
            "component_inventory_closure[].target_mol_L": "mol/L",
        },
        assumptions=(
            "A complete explicit constraint role map distinguishes dynamic conserved components from caller-fixed targets and exact zero-target charge neutrality.",
            "Only caller-declared aqueous reactions, fixed activity model, equilibrium constants and single-liquid phase scope are used.",
            "Conserved component totals are computed from initial species amounts and fixed solution volume, then checked against the final aqueous equilibrium.",
            "No solid phase, gas exchange, transport, external reservoir, corrosion acceptance or qualification is modeled.",
        ),
        source_ids=(METHOD_SOURCE_ID, "caller_general_aqueous_mass_action_speciation",
                    "caller_explicit_aqueous_constraint_role_partition",
                    "caller_species_to_conserved_component_stoichiometric_map"),
        qualification="user_model",
    ),)
