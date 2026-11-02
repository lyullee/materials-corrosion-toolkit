"""Digest-bound spatial ledger for caller-computed crevice cell speciation."""

from __future__ import annotations

import math
from typing import Any, Literal

from pydantic import Field, model_validator

from .contracts import Calculation, Contract, Positive, canonical_digest
from .crevice_transport_composition_bridge import CreviceTransportCompositionBridge
from .models.aqueous_mass_action import (
    AqueousMassActionSystem,
    AqueousLinearConstraint,
    aqueous_mass_action_speciation,
)
from .models.aqueous_external_activity import (
    ExternalAqueousActivityIteration,
    aqueous_external_activity_self_consistent_speciation,
)
from .registry import ModelSpec

PROJECTION_MODEL_ID = "integration.crevice_local_mass_action_projection"
EXTERNAL_PROJECTION_MODEL_ID = "integration.crevice_local_external_activity_projection"
PROJECTION_SOURCE_ID = "caller_component_constraint_basis_for_crevice_local_speciation"
MAX_PROJECTION_SOLVES = 10000


class CreviceCellSpeciationRecord(Contract):
    """One exact transport-knot cell and its separately calculated chemistry."""

    cell_index: int = Field(ge=0)
    transport_cell_context_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    aqueous_mass_action_input: AqueousMassActionSystem
    aqueous_mass_action_result: dict[str, Any]


class CreviceSpeciationKnot(Contract):
    knot_summary_index: int = Field(ge=0)
    time_s: float = Field(ge=0)
    geometry_side: Literal[
        "initial_or_interior", "left_pre_remap", "right_post_remap", "final_state"
    ]
    cells: tuple[CreviceCellSpeciationRecord, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def unique_ordered_cells(self):
        indices = [row.cell_index for row in self.cells]
        if indices != list(range(len(indices))):
            raise ValueError("cell records must enumerate every cell exactly once in spatial order")
        return self


class CreviceLocalSpeciationLedgerRequest(Contract):
    """Bind local equilibrium results to exact campaign composition states.

    The API aggregates results only. It never runs or edits the chemistry
    systems, and the caller must review how each transport cell state was
    mapped into the corresponding equilibrium constraints.
    """

    schema_version: Literal["matintegrity.crevice_local_speciation_ledger.v1"] = (
        "matintegrity.crevice_local_speciation_ledger.v1"
    )
    assessment_id: str = Field(min_length=1)
    transport_binding: CreviceTransportCompositionBridge
    transport_binding_result: dict[str, Any]
    transport_binding_result_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    knots: tuple[CreviceSpeciationKnot, ...] = Field(min_length=1)
    cell_composition_to_mass_action_constraints_reviewed: bool
    mass_action_result_lineage_reviewed: bool
    spatial_cells_must_remain_distinct_reviewed: bool
    inventory_volume_basis_reviewed: bool
    no_bulk_equilibrium_or_phase_inference_reviewed: bool

    @model_validator(mode="after")
    def check_transport_binding(self):
        if canonical_digest(self.transport_binding_result) != self.transport_binding_result_sha256:
            raise ValueError("transport composition result digest mismatch")
        result = self.transport_binding_result
        if result.get("status") != "computed":
            raise ValueError("computed transport composition result is required")
        if result.get("values", {}).get("campaign_id") != self.transport_binding.campaign.campaign_id:
            raise ValueError("transport composition result is for a different campaign")
        return self


class CreviceMassActionProjectionCell(Contract):
    """Caller-reviewed fixed-activity equilibrium system for one exact cell."""

    cell_index: int = Field(ge=0)
    transport_cell_context_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    system_template: AqueousMassActionSystem


class CreviceMassActionProjectionKnot(Contract):
    knot_summary_index: int = Field(ge=0)
    time_s: float = Field(ge=0)
    geometry_side: Literal[
        "initial_or_interior", "left_pre_remap", "right_post_remap", "final_state"
    ]
    cells: tuple[CreviceMassActionProjectionCell, ...] = Field(min_length=1, max_length=300)

    @model_validator(mode="after")
    def unique_ordered_cells(self):
        indices = [row.cell_index for row in self.cells]
        if indices != list(range(len(indices))):
            raise ValueError("projection cells must enumerate the complete spatial grid in order")
        return self


class CreviceLocalMassActionProjectionRequest(Contract):
    """Compute separate local equilibria from exact transported cell compositions.

    Each cell supplies a reviewed mass-action network template. The projection
    replaces only the linear-constraint target values, deriving each target from
    the exact cell composition using that constraint's caller-declared component
    coefficients. Activity coefficients, reactions, equilibrium constants,
    temperature, phase scope and initial guesses remain caller supplied.
    """

    schema_version: Literal["matintegrity.crevice_local_mass_action_projection.v1"] = (
        "matintegrity.crevice_local_mass_action_projection.v1"
    )
    assessment_id: str = Field(min_length=1)
    transport_binding: CreviceTransportCompositionBridge
    transport_binding_result: dict[str, Any]
    transport_binding_result_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    knots: tuple[CreviceMassActionProjectionKnot, ...] = Field(min_length=1, max_length=500)
    composition_derived_constraint_ids: tuple[str, ...] = Field(min_length=1, max_length=100)
    zero_concentration_initial_activity_guess: Positive | None = None
    cell_composition_to_constraint_basis_reviewed: bool
    complete_component_inventory_and_mapping_reviewed: bool
    fixed_activity_and_equilibrium_parameter_support_reviewed: bool
    cell_specific_temperature_and_solution_identity_reviewed: bool
    single_liquid_no_solid_transition_scope_reviewed: bool
    no_interknot_kinetics_or_transport_feedback_reviewed: bool
    zero_concentration_seed_is_numerical_only_reviewed: bool = False
    computational_use_authorized: bool

    @model_validator(mode="after")
    def check_binding_and_solve_budget(self):
        if canonical_digest(self.transport_binding_result) != self.transport_binding_result_sha256:
            raise ValueError("transport composition result digest mismatch")
        result = self.transport_binding_result
        campaign = self.transport_binding.campaign
        if result.get("status") != "computed":
            raise ValueError("computed transport composition result is required")
        if result.get("values", {}).get("campaign_id") != campaign.campaign_id:
            raise ValueError("transport composition result is for a different campaign")
        if (len(self.composition_derived_constraint_ids)
                != len(set(self.composition_derived_constraint_ids))):
            raise ValueError("composition-derived constraint IDs must be unique")
        first_template = self.knots[0].cells[0].system_template
        first_species = tuple(row.species_id for row in first_template.species)
        first_reactions = tuple(
            (row.reaction_id, tuple((term.species_id, term.coefficient) for term in row.terms))
            for row in first_template.reactions
        )
        first_constraints = tuple(
            (row.constraint_id, tuple((term.species_id, term.coefficient) for term in row.terms))
            for row in first_template.constraints
        )
        if set(self.composition_derived_constraint_ids) - {row.constraint_id for row in first_template.constraints}:
            raise ValueError("all composition-derived constraint IDs must exist in every cell template")
        for knot in self.knots:
            for cell in knot.cells:
                system = cell.system_template
                if tuple(row.species_id for row in system.species) != first_species:
                    raise ValueError("local equilibrium species order must remain fixed across all cells and knots")
                if tuple(
                    (row.reaction_id, tuple((term.species_id, term.coefficient) for term in row.terms))
                    for row in system.reactions
                ) != first_reactions:
                    raise ValueError("reaction identities and stoichiometry must remain fixed across all cells and knots")
                if tuple(
                    (row.constraint_id, tuple((term.species_id, term.coefficient) for term in row.terms))
                    for row in system.constraints
                ) != first_constraints:
                    raise ValueError("constraint identities and stoichiometry must remain fixed across all cells and knots")
        solves = sum(len(knot.cells) for knot in self.knots)
        if solves > MAX_PROJECTION_SOLVES:
            raise ValueError("local-equilibrium projection solve budget exceeded")
        summaries = result.get("values", {}).get("knot_summaries")
        has_zero_concentration = (
            isinstance(summaries, list)
            and any(
                isinstance(row, dict)
                and isinstance(row.get("cell_concentration_mol_m3"), list)
                and any(
                    isinstance(species_row, list)
                    and any(isinstance(value, (int, float)) and value == 0.0 for value in species_row)
                    for species_row in row["cell_concentration_mol_m3"]
                )
                for row in summaries
            )
        )
        if has_zero_concentration:
            if self.zero_concentration_initial_activity_guess is None:
                raise ValueError("zero concentration requires an explicit positive numerical initial-activity seed")
            if not self.zero_concentration_seed_is_numerical_only_reviewed:
                raise ValueError("zero-concentration numerical seeding requires explicit review")
        return self


class CreviceLocalExternalActivityProjectionRequest(CreviceLocalMassActionProjectionRequest):
    """Spatial projection using a reviewed external gamma model per cell."""

    activity_iteration_template: ExternalAqueousActivityIteration

    @model_validator(mode="after")
    def check_activity_template_topology(self):
        reference = self.activity_iteration_template.system
        if reference.activity_standard_state != "molarity_1_mol_L":
            raise ValueError("external molality activity providers require molarity-standard-state cell systems")

        def topology(system):
            return (
                tuple((row.species_id, row.charge_number, row.elemental_composition) for row in system.species),
                tuple((row.reaction_id, tuple((term.species_id, term.coefficient) for term in row.terms))
                      for row in system.reactions),
                tuple((row.constraint_id, tuple((term.species_id, term.coefficient) for term in row.terms))
                      for row in system.constraints),
            )

        expected = topology(reference)
        for knot in self.knots:
            for cell in knot.cells:
                if cell.system_template.activity_standard_state != "molarity_1_mol_L":
                    raise ValueError("every cell system must use the provider adapter's molarity standard state")
                if topology(cell.system_template) != expected:
                    raise ValueError("external activity and cell templates must share exact species, reaction and constraint topology")
        return self


def transport_cell_context_digest(knot_summary: dict[str, Any], cell_index: int) -> str:
    """Return the digest callers attach to a local speciation input/result pair."""
    concentrations = knot_summary.get("cell_concentration_mol_m3")
    volumes = knot_summary.get("cell_volume_m3")
    if (
        not isinstance(concentrations, list)
        or not isinstance(volumes, list)
        or cell_index < 0
        or cell_index >= len(volumes)
        or any(not isinstance(row, list) or len(row) != len(volumes) for row in concentrations)
    ):
        raise ValueError("transport knot does not contain the requested cell state")
    return canonical_digest({
        "knot_summary": knot_summary,
        "cell_index": cell_index,
        "cell_volume_m3": volumes[cell_index],
        "cell_concentration_mol_m3": [row[cell_index] for row in concentrations],
    })


def _fail(status: Literal["needs_data", "out_of_scope"], base: dict[str, Any], rows, reason: str, **where):
    return Calculation(status=status, values=base | {
        "completed_knot_count": len(rows),
        "completed_knots": rows,
        "failure_reason": reason,
        **where,
        "prefix_policy": "only complete exact transport knots are committed",
    })


def assemble_crevice_local_speciation_ledger(
    request: CreviceLocalSpeciationLedgerRequest,
) -> Calculation:
    """Assemble cell-level species moles without mixing spatial compartments."""
    result = request.transport_binding_result.get("values", {})
    summaries = result.get("knot_summaries")
    campaign = request.transport_binding.campaign
    base = {
        "assessment_id": request.assessment_id,
        "campaign_id": campaign.campaign_id,
        "transport_binding_result_sha256": request.transport_binding_result_sha256,
        "transport_campaign_input_sha256": result.get("campaign_input_sha256"),
        "geometry_history_sha256": result.get("geometry_history_sha256"),
        "representation": "exact_knot_cell_local_speciation_with_volume_inventory_ledger",
        "automatic_mass_action_input": False,
    }
    required_reviews = (
        "cell_composition_to_mass_action_constraints_reviewed",
        "mass_action_result_lineage_reviewed",
        "spatial_cells_must_remain_distinct_reviewed",
        "inventory_volume_basis_reviewed",
        "no_bulk_equilibrium_or_phase_inference_reviewed",
    )
    missing = [field for field in required_reviews if not getattr(request, field)]
    if missing:
        return Calculation(status="needs_data", values=base | {"missing_reviews": missing})
    if not isinstance(summaries, list) or len(summaries) != len(request.knots):
        return Calculation(status="out_of_scope", values=base | {
            "reason": "speciation knot count must exactly match the bound transport summary"
        })

    committed: list[dict[str, Any]] = []
    for knot_index, (knot, summary) in enumerate(zip(request.knots, summaries, strict=True)):
        if knot.knot_summary_index != knot_index:
            return _fail("out_of_scope", base, committed, "knot indices are not contiguous", failed_knot_index=knot_index)
        if knot.time_s != summary.get("time_s") or knot.geometry_side != summary.get("geometry_side"):
            return _fail("out_of_scope", base, committed, "speciation knot time or geometry side differs from transport", failed_knot_index=knot_index)
        volumes = summary.get("cell_volume_m3")
        species_ids = summary.get("species_ids")
        if not isinstance(volumes, list) or len(knot.cells) != len(volumes) or not isinstance(species_ids, list):
            return _fail("out_of_scope", base, committed, "every transport cell requires one local speciation record", failed_knot_index=knot_index)

        cell_rows: list[dict[str, Any]] = []
        species_charge: dict[str, int] = {}
        species_elements: dict[str, dict[str, int] | None] = {}
        failure: tuple[str, dict[str, Any]] | None = None
        for record in knot.cells:
            if record.transport_cell_context_sha256 != transport_cell_context_digest(summary, record.cell_index):
                failure = ("cell transport context digest differs from the exact campaign cell state", {"failed_cell_index": record.cell_index})
                break
            mass_action_request = record.aqueous_mass_action_input
            mass_action_result = record.aqueous_mass_action_result
            values = mass_action_result.get("values", {})
            if mass_action_result.get("status") != "computed":
                failure = ("local mass-action result did not compute", {"failed_cell_index": record.cell_index, "upstream_status": mass_action_result.get("status")})
                break
            expected_digest = canonical_digest(mass_action_request.model_dump(mode="json"))
            if values.get("input_digest") != expected_digest:
                failure = ("mass-action result input digest differs from the supplied cell request", {"failed_cell_index": record.cell_index})
                break
            upstream_species = values.get("species")
            if not isinstance(upstream_species, list):
                failure = ("mass-action result lacks typed species concentration rows", {"failed_cell_index": record.cell_index})
                break
            indexed = {row.get("species_id"): row for row in upstream_species if isinstance(row, dict)}
            request_indexed = {row.species_id: row for row in mass_action_request.species}
            if len(indexed) != len(upstream_species) or set(indexed) != set(species_ids) or set(request_indexed) != set(species_ids):
                failure = ("local speciation species identity/order differs from transport", {"failed_cell_index": record.cell_index})
                break
            cell_volume = float(volumes[record.cell_index])
            cell_moles = {}
            elemental_moles: dict[str, float] = {}
            charge_moles = 0.0
            for species_id in species_ids:
                output = indexed[species_id]
                request_species = request_indexed[species_id]
                concentration = output.get("concentration_mol_L")
                charge = output.get("charge_number")
                if (
                    not isinstance(concentration, (float, int))
                    or not math.isfinite(concentration)
                    or concentration < 0.0
                    or charge != request_species.charge_number
                    or output.get("elemental_composition") != request_species.elemental_composition
                ):
                    failure = ("local speciation concentration or species metadata is invalid", {"failed_cell_index": record.cell_index, "species_id": species_id})
                    break
                moles = float(concentration) * 1000.0 * cell_volume
                if not math.isfinite(moles):
                    failure = ("local species inventory exceeded finite support", {"failed_cell_index": record.cell_index, "species_id": species_id})
                    break
                cell_moles[species_id] = moles
                species_charge[species_id] = int(charge)
                formula = request_species.elemental_composition
                species_elements[species_id] = formula
                charge_moles += moles * int(charge)
                if formula is not None:
                    for element, count in formula.items():
                        elemental_moles[element] = elemental_moles.get(element, 0.0) + moles * count
            if failure:
                break
            external_activity_result = values.get("external_activity_result")
            external_activity_values = (
                external_activity_result.get("values", {})
                if isinstance(external_activity_result, dict) else {}
            )
            external_activity_history = external_activity_values.get("fixed_point_history", [])
            cell_rows.append({
                "cell_index": record.cell_index,
                "cell_volume_m3": cell_volume,
                "aqueous_mass_action_input_sha256": expected_digest,
                "aqueous_mass_action_result_sha256": canonical_digest(mass_action_result),
                "transport_cell_context_sha256": record.transport_cell_context_sha256,
                "solution_id": mass_action_request.solution_id,
                "temperature_K": mass_action_request.temperature_K,
                "activity_standard_state": mass_action_request.activity_standard_state,
                "activity_provider_id": mass_action_request.activity_provider_id,
                "activity_provider_revision": mass_action_request.activity_provider_revision,
                "activity_configuration_sha256": mass_action_request.activity_configuration_digest,
                "activity_parameter_record_sha256": mass_action_request.activity_record_digest,
                "activity_coefficient_molarity_standard_state_by_species": {
                    sid: float(request_indexed[sid].activity_coefficient) for sid in species_ids
                },
                "external_activity_fixed_point_iteration_count": external_activity_values.get("outer_iterations"),
                "external_activity_fixed_point_residual_ln": external_activity_values.get(
                    "maximum_log_gamma_fixed_point_residual"
                ),
                "external_activity_provider_result_sha256": external_activity_values.get(
                    "provider_result_sha256"
                ),
                "external_activity_provider_transcript_sha256": (
                    canonical_digest(external_activity_history)
                    if isinstance(external_activity_history, list) and external_activity_history else None
                ),
                "species_concentration_mol_L": {sid: float(indexed[sid]["concentration_mol_L"]) for sid in species_ids},
                "species_inventory_mol": cell_moles,
                "charge_equivalent_inventory_mol": charge_moles,
                "elemental_inventory_mol_atoms": elemental_moles if all(species_elements[sid] is not None for sid in species_ids) else None,
            })
        if failure:
            reason, where = failure
            return _fail("needs_data", base, committed, reason, failed_knot_index=knot_index, **where)
        committed.append({
            "knot_summary_index": knot_index,
            "time_s": knot.time_s,
            "geometry_side": knot.geometry_side,
            "transport_knot_summary_sha256": canonical_digest(summary),
            "cell_count": len(cell_rows),
            "cells": cell_rows,
            "spatial_mixing_performed": False,
        })

    final_cells = committed[-1]["cells"]
    species_totals = {
        species_id: math.fsum(cell["species_inventory_mol"][species_id] for cell in final_cells)
        for species_id in species_ids
    }
    complete_elements = all(species_elements.get(sid) is not None for sid in species_ids)
    return Calculation(values=base | {
        "status": "computed",
        "species_ids": species_ids,
        "committed_knot_count": len(committed),
        "knots": committed,
        "final_knot_total_species_inventory_mol": species_totals,
        "final_knot_charge_equivalent_inventory_mol": math.fsum(
            species_totals[sid] * species_charge[sid] for sid in species_ids
        ),
        "final_knot_elemental_inventory_mol_atoms": {
            element: math.fsum(cell["elemental_inventory_mol_atoms"].get(element, 0.0) for cell in final_cells)
            for element in sorted({key for sid in species_ids for key in (species_elements[sid] or {})})
        } if complete_elements else None,
        "interior_history_inventory_is_not_summed_across_time": True,
        "interpretation_boundary": "Molarity-derived cell inventory is conditional on the supplied liquid volumes and independent local equilibrium solves; the assembly does not establish cross-cell equilibrium, inter-knot continuity, kinetics, phase change or corrosion.",
        "not_inferred": ["water balance", "electroneutrality unless in each input system", "bulk equilibrium", "phase transitions", "corrosion rate", "material loss", "acceptance", "risk probability"],
    })


def evaluate_crevice_local_mass_action_projection(
    request: CreviceLocalMassActionProjectionRequest,
    *,
    activity_provider=None,
) -> Calculation:
    """Solve reviewed cellwise mass action, optionally with an external gamma provider."""
    result = request.transport_binding_result.get("values", {})
    summaries = result.get("knot_summaries")
    campaign = request.transport_binding.campaign
    base = {
        "assessment_id": request.assessment_id,
        "model_id": PROJECTION_MODEL_ID,
        "campaign_id": campaign.campaign_id,
        "transport_binding_result_sha256": request.transport_binding_result_sha256,
        "transport_campaign_input_sha256": result.get("campaign_input_sha256"),
        "geometry_history_sha256": result.get("geometry_history_sha256"),
        "projection_basis": "exact-knot_cellwise_fixed-activity_mass-action_operator_split.v1",
    }
    review_fields = (
        "cell_composition_to_constraint_basis_reviewed",
        "complete_component_inventory_and_mapping_reviewed",
        "fixed_activity_and_equilibrium_parameter_support_reviewed",
        "cell_specific_temperature_and_solution_identity_reviewed",
        "single_liquid_no_solid_transition_scope_reviewed",
        "no_interknot_kinetics_or_transport_feedback_reviewed",
        "computational_use_authorized",
    )
    if request.zero_concentration_initial_activity_guess is not None:
        review_fields += ("zero_concentration_seed_is_numerical_only_reviewed",)
    missing = [name for name in review_fields if not getattr(request, name)]
    if missing:
        return Calculation(status="needs_data", values=base | {
            "reason": "caller_review_gates_incomplete",
            "missing_reviews": missing,
            "committed_knot_count": 0,
        })
    if not isinstance(summaries, list) or len(summaries) != len(request.knots):
        return Calculation(status="out_of_scope", values=base | {
            "reason": "projection knots must exactly match the transport summary clock",
            "committed_knot_count": 0,
        })

    committed: list[CreviceSpeciationKnot] = []
    failures: list[dict[str, Any]] = []
    for knot_index, (projection_knot, summary) in enumerate(
        zip(request.knots, summaries, strict=True)
    ):
        if (projection_knot.knot_summary_index != knot_index
                or projection_knot.time_s != summary.get("time_s")
                or projection_knot.geometry_side != summary.get("geometry_side")):
            return Calculation(status="out_of_scope", values=base | {
                "reason": "projection knot identity differs from the exact transport summary",
                "failed_knot_index": knot_index,
                "committed_knot_count": len(committed),
                "committed_knots": [row.model_dump(mode="json") for row in committed],
            })
        species_ids = summary.get("species_ids")
        concentration_rows = summary.get("cell_concentration_mol_m3")
        volumes = summary.get("cell_volume_m3")
        if (not isinstance(species_ids, list) or not isinstance(concentration_rows, list)
                or not isinstance(volumes, list)
                or len(projection_knot.cells) != len(volumes)
                or len(concentration_rows) != len(species_ids)
                or any(not isinstance(row, list) or len(row) != len(volumes)
                       for row in concentration_rows)):
            return Calculation(status="out_of_scope", values=base | {
                "reason": "transport summary is missing aligned species, concentration or volume arrays",
                "failed_knot_index": knot_index,
                "committed_knot_count": len(committed),
                "committed_knots": [row.model_dump(mode="json") for row in committed],
            })
        index_by_species = {species_id: position for position, species_id in enumerate(species_ids)}
        if len(index_by_species) != len(species_ids):
            return Calculation(status="out_of_scope", values=base | {
                "reason": "transport species identities are not unique",
                "failed_knot_index": knot_index,
                "committed_knot_count": len(committed),
                "committed_knots": [row.model_dump(mode="json") for row in committed],
            })

        records: list[CreviceCellSpeciationRecord] = []
        failure: dict[str, Any] | None = None
        failure_status: Literal["needs_data", "out_of_scope"] = "out_of_scope"
        for cell in projection_knot.cells:
            if cell.transport_cell_context_sha256 != transport_cell_context_digest(summary, cell.cell_index):
                failure = {
                    "reason": "cell context digest differs from the exact transport concentration and volume",
                    "failed_cell_index": cell.cell_index,
                }
                break
            template = cell.system_template
            if tuple(row.species_id for row in template.species) != tuple(species_ids):
                failure = {
                    "reason": "mass-action and transport species identity/order must match exactly",
                    "failed_cell_index": cell.cell_index,
                }
                break
            cell_concentrations_mol_l = {
                species_id: float(concentration_rows[index_by_species[species_id]][cell.cell_index]) / 1000.0
                for species_id in species_ids
            }
            if any(not math.isfinite(value) or value < 0.0
                   for value in cell_concentrations_mol_l.values()):
                failure = {
                    "reason": "transport cell concentrations are outside finite nonnegative support",
                    "failed_cell_index": cell.cell_index,
                }
                break
            target_constraints: list[dict[str, Any]] = []
            try:
                selected_constraint_ids = set(request.composition_derived_constraint_ids)
                for constraint in template.constraints:
                    target = constraint.target_mol_L
                    if constraint.constraint_id in selected_constraint_ids:
                        target = math.fsum(
                            float(term.coefficient) * cell_concentrations_mol_l[term.species_id]
                            for term in constraint.terms
                        )
                    if not math.isfinite(target):
                        raise ValueError("constraint target exceeds finite support")
                    row = constraint.model_dump(mode="json")
                    row["target_mol_L"] = target
                    target_constraints.append(row)
                system_payload = template.model_dump(mode="json")
                cell_tag = f"transport-knot-{knot_index}-cell-{cell.cell_index}"
                system_payload["assessment_id"] = f"{template.assessment_id}-{cell_tag}"
                system_payload["solution_id"] = f"{template.solution_id}-{cell_tag}"
                seeded_species = []
                for species in template.species:
                    concentration = cell_concentrations_mol_l[species.species_id]
                    activity_guess = species.activity_coefficient * concentration
                    if concentration == 0.0:
                        if request.zero_concentration_initial_activity_guess is None:
                            raise ValueError("zero concentration has no positive initial-activity seed")
                        activity_guess = request.zero_concentration_initial_activity_guess
                    if not math.isfinite(activity_guess) or activity_guess <= 0.0:
                        raise ArithmeticError("composition-derived activity seed is outside positive finite support")
                    seeded_species.append(
                        species.model_dump(mode="json") | {"initial_activity": activity_guess}
                    )
                system_payload["species"] = seeded_species
                system_payload["constraints"] = target_constraints
                system = AqueousMassActionSystem.model_validate(system_payload)
                if isinstance(request, CreviceLocalExternalActivityProjectionRequest):
                    if not callable(activity_provider):
                        failure_status = "needs_data"
                        raise ValueError("a caller-owned external activity provider callback is required")
                    external_request = request.activity_iteration_template.model_copy(
                        update={"system": system}
                    )
                    external = aqueous_external_activity_self_consistent_speciation(
                        external_request, activity_provider=activity_provider
                    )
                    if external.status == "computed":
                        gamma_used = external.values.get(
                            "mass_action_activity_coefficients_molarity_standard_state"
                        )
                        if not isinstance(gamma_used, list) or len(gamma_used) != len(system.species):
                            raise ValueError("external activity result lacks its exact inner-solver gamma vector")
                        final_system = system.model_copy(update={
                            "species": tuple(
                                species.model_copy(update={"activity_coefficient": float(gamma_used[index])})
                                for index, species in enumerate(system.species)
                            ),
                            "activity_provider_id": external_request.activity_provider_id,
                            "activity_provider_revision": external_request.activity_provider_revision,
                            "activity_configuration_digest": external_request.activity_configuration_sha256,
                            "activity_record_digest": external_request.activity_parameter_record_sha256,
                        })
                        inner_digest = canonical_digest(final_system.model_dump(mode="json"))
                        if external.values.get("mass_action_input_sha256") != inner_digest:
                            raise ValueError("external activity lineage does not match the converged inner mass-action input")
                        system = final_system
                        calculation = Calculation(status="computed", values={
                            **external.values,
                            "input_digest": inner_digest,
                            "normalized_residual_norm": external.values.get("inner_normalized_residual_norm"),
                            "external_activity_result": external.model_dump(mode="json"),
                        }, notes=external.notes)
                    else:
                        calculation = external
                else:
                    calculation = aqueous_mass_action_speciation(system)
            except (ArithmeticError, ValueError, OverflowError) as exc:
                failure = {
                    "reason": "local mass-action projection input construction failed",
                    "failed_cell_index": cell.cell_index,
                    "detail": f"{type(exc).__name__}: {exc}",
                }
                break
            if calculation.status != "computed":
                failure_status = calculation.status
                failure = {
                    "reason": "local mass-action projection did not compute",
                    "failed_cell_index": cell.cell_index,
                    "upstream_status": calculation.status,
                    "upstream_result_sha256": canonical_digest(calculation.model_dump(mode="json")),
                    "upstream_result": calculation.model_dump(mode="json"),
                }
                break
            if calculation.values.get("input_digest") != canonical_digest(system.model_dump(mode="json")):
                failure = {
                    "reason": "mass-action result digest differs from the executed local system",
                    "failed_cell_index": cell.cell_index,
                }
                break
            records.append(CreviceCellSpeciationRecord(
                cell_index=cell.cell_index,
                transport_cell_context_sha256=cell.transport_cell_context_sha256,
                aqueous_mass_action_input=system,
                aqueous_mass_action_result=calculation.model_dump(mode="json"),
            ))
        if failure is not None:
            failures.append({"knot_index": knot_index, **failure})
            return Calculation(status=failure_status, values=base | {
                "failure": failures[-1],
                "committed_knot_count": len(committed),
                "committed_knots": [row.model_dump(mode="json") for row in committed],
                "current_knot_complete": False,
                "prefix_policy": "only fully computed exact transport knots are committed",
            })
        committed.append(CreviceSpeciationKnot(
            knot_summary_index=knot_index,
            time_s=projection_knot.time_s,
            geometry_side=projection_knot.geometry_side,
            cells=tuple(records),
        ))

    ledger_request = CreviceLocalSpeciationLedgerRequest(
        assessment_id=request.assessment_id,
        transport_binding=request.transport_binding,
        transport_binding_result=request.transport_binding_result,
        transport_binding_result_sha256=request.transport_binding_result_sha256,
        knots=tuple(committed),
        cell_composition_to_mass_action_constraints_reviewed=True,
        mass_action_result_lineage_reviewed=True,
        spatial_cells_must_remain_distinct_reviewed=True,
        inventory_volume_basis_reviewed=True,
        no_bulk_equilibrium_or_phase_inference_reviewed=True,
    )
    ledger = assemble_crevice_local_speciation_ledger(ledger_request)
    external_activity_mode = isinstance(request, CreviceLocalExternalActivityProjectionRequest)
    return Calculation(status=ledger.status, values=ledger.values | {
        "model_id": EXTERNAL_PROJECTION_MODEL_ID if external_activity_mode else PROJECTION_MODEL_ID,
        "projection_model_id": EXTERNAL_PROJECTION_MODEL_ID if external_activity_mode else PROJECTION_MODEL_ID,
        "projection_input_sha256": canonical_digest(request.model_dump(mode="json")),
        "transport_species_concentrations_used_only_to_set_linear_constraint_targets": True,
        "initial_activity_seed_uses_fixed_gamma_times_transported_concentration": not external_activity_mode,
        "activity_coefficients_reactions_equilibrium_constants_temperature_and_phase_scope": (
            "caller external activity iteration template; gamma is iterated against each cell composition; reaction topology, equilibrium constants, temperature and single-liquid scope remain caller supplied"
            if external_activity_mode else
            "caller templates, held fixed for each exact cell knot"
        ),
        "activity_provider_id": request.activity_iteration_template.activity_provider_id if external_activity_mode else None,
        "activity_provider_revision": request.activity_iteration_template.activity_provider_revision if external_activity_mode else None,
        "activity_fixed_point_is_independent_per_cell": external_activity_mode,
        "mass_action_solve_count": sum(len(row.cells) for row in committed),
        "inter_knot_interpolation_or_transport_feedback": False,
    }, notes=ledger.notes)


def evaluate_crevice_local_external_activity_projection(
    request: CreviceLocalExternalActivityProjectionRequest,
    *,
    activity_provider,
) -> Calculation:
    """Run an exact-cell external activity projection through the shared ledger."""
    return evaluate_crevice_local_mass_action_projection(
        request, activity_provider=activity_provider
    )


def specifications() -> list[ModelSpec]:
    return [ModelSpec(
        model_id="integration.crevice_local_speciation_volume_ledger",
        input_type=CreviceLocalSpeciationLedgerRequest,
        evaluator=assemble_crevice_local_speciation_ledger,
        units={
            "knots[].time_s": "s",
            "knots[].cells[].cell_volume_m3": "m3",
            "knots[].cells[].temperature_K": "K",
            "knots[].cells[].species_concentration_mol_L.*": "mol/L",
            "knots[].cells[].species_inventory_mol.*": "mol",
            "knots[].cells[].charge_equivalent_inventory_mol": "mol_charge_equivalent",
            "knots[].cells[].activity_coefficient_molarity_standard_state_by_species.*": "1",
            "knots[].cells[].external_activity_fixed_point_residual_ln": "1",
            "knots[].cells[].external_activity_fixed_point_iteration_count": "1",
            "final_knot_total_species_inventory_mol.*": "mol",
            "final_knot_charge_equivalent_inventory_mol": "mol_charge_equivalent",
            "final_knot_elemental_inventory_mol_atoms.*": "mol_atoms",
        },
        assumptions=(
            "Each local equilibrium result must be computed from the exact supplied mass-action request, and that request/result pair must be caller-mapped to the digest of one exact transport cell state.",
            "Concentration in mol/L times the transport cell solution volume in m3 and 1000 L/m3 defines this ledger's species amount; no bulk mixing is performed.",
            "Only complete exact geometry-side knots are committed. Charge and elemental totals are diagnostics and do not imply electroneutrality or phase balance unless separately declared by the local request.",
            "The bridge does not solve speciation or transport, transfer results between cells, interpolate time, infer kinetics, or qualify corrosion response.",
        ),
        source_ids=("caller_crevice_local_speciation_volume_ledger",),
        qualification="user_model",
    ), ModelSpec(
        model_id=PROJECTION_MODEL_ID,
        input_type=CreviceLocalMassActionProjectionRequest,
        evaluator=evaluate_crevice_local_mass_action_projection,
        units={
            "knots[].time_s": "s",
            "knots[].cells[].system_template.temperature_K": "K",
            "knots[].cells[].system_template.constraints[].target_mol_L": "mol/L",
            "knots[].cells[].species_inventory_mol.*": "mol",
            "knots[].cells[].activity_coefficient_molarity_standard_state_by_species.*": "1",
            "knots[].cells[].external_activity_fixed_point_residual_ln": "1",
            "knots[].cells[].external_activity_fixed_point_iteration_count": "1",
            "final_knot_total_species_inventory_mol.*": "mol",
        },
        assumptions=(
            "For every exact transport cell knot, the caller supplies a reviewed single-liquid mass-action system whose species order matches the transported composition.",
            "Each linear-constraint target is set to the corresponding caller-declared linear combination of transported cell concentrations converted from mol/m3 to mol/L.",
            "Fixed activity coefficients, reactions, equilibrium constants, temperature, phase scope, and initial activity guesses remain caller-supplied and reviewed.",
            "Local solves are independent and operator-split after transport; they are not fed back into inter-knot transport and do not evolve solids, wall loss, corrosion rate, or qualification.",
        ),
        source_ids=(PROJECTION_SOURCE_ID, "caller_crevice_local_speciation_volume_ledger",
                    "caller_general_aqueous_mass_action_speciation"),
        qualification="user_model",
    ), ModelSpec(
        model_id=EXTERNAL_PROJECTION_MODEL_ID,
        input_type=CreviceLocalExternalActivityProjectionRequest,
        evaluator=evaluate_crevice_local_external_activity_projection,
        units={
            "knots[].time_s": "s",
            "knots[].cells[].system_template.temperature_K": "K",
            "knots[].cells[].system_template.constraints[].target_mol_L": "mol/L",
            "knots[].cells[].species_inventory_mol.*": "mol",
            "knots[].cells[].activity_coefficient_molarity_standard_state_by_species.*": "1",
            "knots[].cells[].external_activity_fixed_point_residual_ln": "1",
            "knots[].cells[].external_activity_fixed_point_iteration_count": "1",
            "final_knot_total_species_inventory_mol.*": "mol",
        },
        assumptions=(
            "Transported cell compositions set only the explicitly selected mass-action constraint targets; each exact cell then solves an independent caller-reviewed activity fixed point.",
            "The activity provider is injected as an explicit runtime dependency and must match the provider identity, revision, configuration digest, parameter digest, species ordering and molality standard state in the request.",
            "Reaction topology, equilibrium constants, cell temperature, water-mass conversion, activity convention and one-liquid scope are caller declared; no phase transition, inter-knot kinetic evolution or transport feedback is computed.",
            "Only complete exact transport knots are committed, and the mass-action ledger retains both the converged inner-system input digest and external-provider transcript.",
        ),
        source_ids=(PROJECTION_SOURCE_ID, "caller_crevice_local_speciation_volume_ledger",
                    "caller_external_aqueous_activity_provider",
                    "caller_crevice_local_external_activity_projection"),
        qualification="user_model",
        runtime_dependency_names=("activity_provider",),
    )]
