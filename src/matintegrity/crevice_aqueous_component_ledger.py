"""Explicit aqueous component-role mapping and finite-volume inventory ledger.

This precursor projects caller-supplied species inventories, face transfers and
sources onto declared conserved aqueous components. It does not solve equilibrium
or couple to a transport integrator.
"""

from __future__ import annotations

import math
from typing import Literal

from pydantic import Field, model_validator

from .contracts import Calculation, Contract, Positive, canonical_digest
from .models.aqueous_mass_action import AqueousMassActionSystem
from .registry import ModelSpec

MODEL_ID = "integration.crevice_aqueous_component_ledger"
ROLE_MAP_SOURCE_ID = "caller_explicit_aqueous_constraint_role_partition"
COMPONENT_MAP_SOURCE_ID = "caller_species_to_conserved_component_stoichiometric_map"
LEDGER_SOURCE_ID = "finite_volume_aqueous_component_inventory_flux_source_projection"


class ConstraintRoleAssignment(Contract):
    constraint_id: str = Field(min_length=1)
    role: Literal["conserved_component", "fixed_target", "charge_neutrality"]
    component_id: str | None = None

    @model_validator(mode="after")
    def role_payload_matches(self):
        if (self.role == "conserved_component") != (self.component_id is not None):
            raise ValueError("only a conserved_component constraint must name component_id")
        return self


class ComponentSpeciesCoefficient(Contract):
    species_id: str = Field(min_length=1)
    coefficient: float

    @model_validator(mode="after")
    def finite_nonzero(self):
        if not math.isfinite(self.coefficient) or self.coefficient == 0.0:
            raise ValueError("component coefficients must be finite and nonzero")
        return self


class ConservedAqueousComponent(Contract):
    component_id: str = Field(min_length=1)
    species_coefficients: tuple[ComponentSpeciesCoefficient, ...] = Field(min_length=1, max_length=100)

    @model_validator(mode="after")
    def unique_species(self):
        species_ids = [row.species_id for row in self.species_coefficients]
        if len(set(species_ids)) != len(species_ids):
            raise ValueError("each component map may include a species only once")
        return self


class SpeciesCellAmount(Contract):
    species_id: str = Field(min_length=1)
    amount_mol_by_cell: tuple[float, ...] = Field(min_length=1, max_length=300)


class SpeciesFaceTransfer(Contract):
    species_id: str = Field(min_length=1)
    transfer_mol_by_face: tuple[float, ...] = Field(min_length=2, max_length=301)


class CreviceAqueousComponentLedgerRequest(Contract):
    schema_version: Literal["matintegrity.crevice_aqueous_component_ledger.v1"] = (
        "matintegrity.crevice_aqueous_component_ledger.v1"
    )
    assessment_id: str = Field(min_length=1)
    aqueous_system: AqueousMassActionSystem
    cell_ids: tuple[str, ...] = Field(min_length=1, max_length=300)
    duration_s: Positive
    constraint_roles: tuple[ConstraintRoleAssignment, ...] = Field(min_length=1, max_length=100)
    conserved_components: tuple[ConservedAqueousComponent, ...] = Field(min_length=1, max_length=100)
    species_inventory_start: tuple[SpeciesCellAmount, ...] = Field(min_length=2, max_length=100)
    species_inventory_end: tuple[SpeciesCellAmount, ...] = Field(min_length=2, max_length=100)
    species_face_transfers: tuple[SpeciesFaceTransfer, ...] = Field(min_length=2, max_length=100)
    species_source_transfers: tuple[SpeciesCellAmount, ...] = Field(min_length=2, max_length=100)
    absolute_component_closure_tolerance_mol: Positive
    relative_component_closure_tolerance: Positive = Field(default=1e-8, le=1e-2)
    maximum_projection_operations: int = Field(default=2_000_000, ge=1, le=20_000_000)
    role_map_and_charge_scope_reviewed: bool
    component_map_and_reaction_conservation_reviewed: bool
    finite_volume_face_orientation_and_source_sign_reviewed: bool
    computational_use_authorized: bool

    @model_validator(mode="after")
    def coherent_component_ledger(self):
        system = self.aqueous_system
        species_ids = tuple(row.species_id for row in system.species)
        species_set = set(species_ids)
        if len(set(self.cell_ids)) != len(self.cell_ids):
            raise ValueError("cell identifiers must be unique")
        constraints = {row.constraint_id: row for row in system.constraints}
        if any(not math.isfinite(row.target_mol_L)
               or any(not math.isfinite(term.coefficient) for term in row.terms)
               for row in system.constraints):
            raise ValueError("constraint targets and coefficients must be finite")
        if any(not math.isfinite(term.coefficient)
               for reaction in system.reactions for term in reaction.terms):
            raise ValueError("reaction coefficients must be finite")
        roles = {row.constraint_id: row for row in self.constraint_roles}
        if len(roles) != len(self.constraint_roles) or set(roles) != set(constraints):
            raise ValueError("constraint roles must partition every and only declared constraint ID")
        components = {row.component_id: row for row in self.conserved_components}
        if len(components) != len(self.conserved_components):
            raise ValueError("conserved component IDs must be unique")
        conserved_assignments = [row for row in self.constraint_roles if row.role == "conserved_component"]
        if {row.component_id for row in conserved_assignments} != set(components):
            raise ValueError("each conserved component must map one-to-one to a conserved_component constraint")
        if len(conserved_assignments) != len(components):
            raise ValueError("each conserved component must have exactly one constraint role")
        charge_rows = [row for row in self.constraint_roles if row.role == "charge_neutrality"]
        if len(charge_rows) != 1:
            raise ValueError("exactly one explicit charge_neutrality constraint role is required")
        charge_constraint = constraints[charge_rows[0].constraint_id]
        expected_charge = {row.species_id: row.charge_number for row in system.species if row.charge_number != 0}
        declared_charge = {term.species_id: term.coefficient for term in charge_constraint.terms}
        if declared_charge != expected_charge or charge_constraint.target_mol_L != 0.0:
            raise ValueError("charge-neutrality row must exactly equal declared species charges with a zero target")
        for assignment in conserved_assignments:
            constraint = constraints[assignment.constraint_id]
            component = components[assignment.component_id]
            constraint_map = {term.species_id: term.coefficient for term in constraint.terms}
            component_map = {term.species_id: term.coefficient for term in component.species_coefficients}
            if component_map.keys() - species_set or constraint_map != component_map:
                raise ValueError("conserved component map must exactly match its declared linear constraint coefficient map")
            for reaction in system.reactions:
                reaction_map = {term.species_id: term.coefficient for term in reaction.terms}
                residual = math.fsum(component_map.get(sid, 0.0) * coefficient
                                     for sid, coefficient in reaction_map.items())
                scale = max(1.0, math.fsum(abs(component_map.get(sid, 0.0) * coefficient)
                                          for sid, coefficient in reaction_map.items()))
                if abs(residual) > 1e-12 * scale:
                    raise ValueError(f"reaction {reaction.reaction_id} does not conserve component {component.component_id}")
        for rows, name in (
            (self.species_inventory_start, "inventory start"),
            (self.species_inventory_end, "inventory end"),
            (self.species_face_transfers, "face transfers"),
            (self.species_source_transfers, "source transfers"),
        ):
            row_ids = tuple(row.species_id for row in rows)
            if len(set(row_ids)) != len(row_ids) or set(row_ids) != species_set:
                raise ValueError(f"{name} must include each declared aqueous species exactly once")
        nc = len(self.cell_ids)
        for row in (*self.species_inventory_start, *self.species_inventory_end,
                    *self.species_source_transfers):
            if len(row.amount_mol_by_cell) != nc or any(not math.isfinite(x) for x in row.amount_mol_by_cell):
                raise ValueError("cell amount vectors must be finite and match the declared cell count")
        if any(value < 0.0 for row in (*self.species_inventory_start, *self.species_inventory_end)
               for value in row.amount_mol_by_cell):
            raise ValueError("species inventories must be nonnegative")
        if any(len(row.transfer_mol_by_face) != nc + 1
               or any(not math.isfinite(x) for x in row.transfer_mol_by_face)
               for row in self.species_face_transfers):
            raise ValueError("face transfer vectors must be finite and have cell_count + 1 entries")
        required_operations = sum(len(row.species_coefficients) for row in self.conserved_components) \
            * (2 * nc + nc + 1 + nc)
        if required_operations > self.maximum_projection_operations:
            raise ValueError("declared component projection exceeds maximum_projection_operations")
        reviews = (self.role_map_and_charge_scope_reviewed,
                   self.component_map_and_reaction_conservation_reviewed,
                   self.finite_volume_face_orientation_and_source_sign_reviewed,
                   self.computational_use_authorized)
        if not all(reviews):
            raise ValueError("role, charge, component, sign convention and computational reviews are required")
        return self


def evaluate_crevice_aqueous_component_ledger(
    request: CreviceAqueousComponentLedgerRequest,
) -> Calculation:
    """Project caller-provided species amounts/transfers onto explicit components."""
    digest = canonical_digest(request.model_dump(mode="json"))
    species = {row.species_id: row for row in request.aqueous_system.species}
    starts = {row.species_id: row.amount_mol_by_cell for row in request.species_inventory_start}
    ends = {row.species_id: row.amount_mol_by_cell for row in request.species_inventory_end}
    faces = {row.species_id: row.transfer_mol_by_face for row in request.species_face_transfers}
    sources = {row.species_id: row.amount_mol_by_cell for row in request.species_source_transfers}
    nc = len(request.cell_ids)
    results = []
    maximum_normalized_residual = 0.0
    maximum_absolute_residual = 0.0
    for component in request.conserved_components:
        coefficients = {row.species_id: row.coefficient for row in component.species_coefficients}
        start = [math.fsum(coefficients.get(sid, 0.0) * starts[sid][cell] for sid in species)
                 for cell in range(nc)]
        end = [math.fsum(coefficients.get(sid, 0.0) * ends[sid][cell] for sid in species)
               for cell in range(nc)]
        face = [math.fsum(coefficients.get(sid, 0.0) * faces[sid][index] for sid in species)
                for index in range(nc + 1)]
        source = [math.fsum(coefficients.get(sid, 0.0) * sources[sid][cell] for sid in species)
                  for cell in range(nc)]
        residual = [end[cell] - start[cell] - (face[cell] - face[cell + 1] + source[cell])
                    for cell in range(nc)]
        scales = [max(abs(start[cell]), abs(end[cell]), abs(face[cell]), abs(face[cell + 1]),
                      abs(source[cell]), 1e-30) for cell in range(nc)]
        allowed = [request.absolute_component_closure_tolerance_mol
                   + request.relative_component_closure_tolerance * scales[cell]
                   for cell in range(nc)]
        maximum_absolute_residual = max(maximum_absolute_residual, *(abs(x) for x in residual))
        maximum_normalized_residual = max(maximum_normalized_residual,
                                          *(abs(residual[i]) / allowed[i] for i in range(nc)))
        results.append({
            "component_id": component.component_id,
            "inventory_start_mol_by_cell": start,
            "inventory_end_mol_by_cell": end,
            "face_transfer_mol_by_face_left_to_right": face,
            "source_transfer_mol_by_cell": source,
            "inventory_residual_mol_by_cell": residual,
            "allowed_residual_mol_by_cell": allowed,
            "boundary_net_transfer_mol": face[0] - face[-1],
            "global_inventory_residual_mol": math.fsum(end) - math.fsum(start)
                - (face[0] - face[-1] + math.fsum(source)),
            "source_rate_mol_s_by_cell": [value / request.duration_s for value in source],
        })
    computed = maximum_normalized_residual <= 1.0
    return Calculation(
        status="computed" if computed else "needs_data",
        values={
            "model_id": MODEL_ID,
            "assessment_id": request.assessment_id,
            "input_sha256": digest,
            "aqueous_system_sha256": canonical_digest(request.aqueous_system.model_dump(mode="json")),
            "role_map_source_id": ROLE_MAP_SOURCE_ID,
            "component_map_source_id": COMPONENT_MAP_SOURCE_ID,
            "ledger_source_id": LEDGER_SOURCE_ID,
            "cell_ids": list(request.cell_ids),
            "duration_s": request.duration_s,
            "constraint_roles": [row.model_dump(mode="json") for row in request.constraint_roles],
            "components": results,
            "maximum_absolute_component_residual_mol": maximum_absolute_residual,
            "maximum_normalized_component_residual": maximum_normalized_residual,
            "all_component_cells_close": computed,
            "committed": computed,
            "qualification_claimed": False,
            "limitation": "This is an algebraic species-to-component ledger projection; it does not solve aqueous equilibrium or integrate a Crevice BDF state.",
        },
    )


def specifications() -> tuple[ModelSpec, ...]:
    return (ModelSpec(
        model_id=MODEL_ID,
        input_type=CreviceAqueousComponentLedgerRequest,
        evaluator=evaluate_crevice_aqueous_component_ledger,
        units={
            "duration_s": "s",
            "species_inventory_start[].amount_mol_by_cell[]": "mol",
            "species_inventory_end[].amount_mol_by_cell[]": "mol",
            "species_face_transfers[].transfer_mol_by_face[]": "mol",
            "species_source_transfers[].amount_mol_by_cell[]": "mol",
            "components[].source_rate_mol_s_by_cell[]": "mol/s",
            "components[].inventory_residual_mol_by_cell[]": "mol",
        },
        assumptions=(
            "Every declared mass-action constraint has exactly one explicit role; the charge-neutrality row exactly matches species charge coefficients and has a zero target.",
            "Each conserved component map exactly matches its declared linear constraint and is conserved by every caller-declared aqueous reaction.",
            "Face transfers are signed left-to-right extensive amounts; cell source transfers are positive into the aqueous inventory.",
            "The evaluator projects extensive species ledgers algebraically and performs no chemistry solve, transport integration, phase transfer, or qualification.",
        ),
        source_ids=(ROLE_MAP_SOURCE_ID, COMPONENT_MAP_SOURCE_ID, LEDGER_SOURCE_ID),
        qualification="user_model",
    ),)
