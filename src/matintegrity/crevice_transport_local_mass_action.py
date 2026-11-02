"""Bind exact transported cell concentrations to reviewed local equilibrium constraints."""

from __future__ import annotations

import math
from typing import Any, Literal

from pydantic import Field, model_validator

from .contracts import AssessmentResult, Calculation, Contract, Evidence, Positive, canonical_digest
from .models.aqueous_mass_action import (
    AqueousLinearConstraint,
    AqueousMassActionSystem,
    aqueous_mass_action_speciation,
)
from .registry import ModelSpec

MODEL_ID = "integration.crevice_transport_to_local_mass_action"
MAPPING_SOURCE_ID = "caller_crevice_transport_to_mass_action_constraint_mapping"
METHOD_SOURCE_ID = "exact_cell_transport_field_mass_action_constraint_binding"
VOLUME_SOURCE_ID = "caller_crevice_transport_cell_volume_mapping"
ACCEPTED_TRANSPORT_MODELS = frozenset({
    "integration.crevice_neutral_reactive_transport_1d",
    "transport.crevice_electroneutral_multispecies_diffusion_1d",
})


class CreviceTransportConstraintBinding(Contract):
    """Caller-owned mapping from one transported total to one equilibrium constraint."""

    constraint_id: str = Field(min_length=1)
    transported_species_id: str = Field(min_length=1)
    concentration_scale: Positive = 1.0
    mapping_record_id: str = Field(min_length=1)
    mapping_record_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    evidence: tuple[Evidence, ...] = Field(min_length=1, max_length=32)

    @model_validator(mode="after")
    def evidence_binds_mapping(self):
        if not any(row.source_id == MAPPING_SOURCE_ID and row.sha256 == self.mapping_record_sha256
                   for row in self.evidence):
            raise ValueError("mapping Evidence must match the declared source ID and digest")
        return self


class CreviceLocalEquilibriumKnot(Contract):
    """Per-cell caller chemistry networks and explicit concentration mappings at one exact knot."""

    time_s: float = Field(ge=0)
    cell_templates: tuple[AqueousMassActionSystem, ...] = Field(min_length=2, max_length=500)
    constraint_bindings: tuple[CreviceTransportConstraintBinding, ...] = Field(min_length=1, max_length=100)

    @model_validator(mode="after")
    def finite_time_and_complete_mapping(self):
        if not math.isfinite(self.time_s):
            raise ValueError("knot time must be finite")
        constraint_ids = [row.constraint_id for row in self.cell_templates[0].constraints]
        if len(constraint_ids) != len(set(constraint_ids)):
            raise ValueError("template constraint IDs must be unique")
        binding_ids = [row.constraint_id for row in self.constraint_bindings]
        if len(binding_ids) != len(set(binding_ids)) or set(binding_ids) != set(constraint_ids):
            raise ValueError("each local mass-action constraint must have exactly one explicit transported mapping")
        for template in self.cell_templates[1:]:
            if tuple(row.constraint_id for row in template.constraints) != tuple(constraint_ids):
                raise ValueError("all cells at a knot must preserve the same caller constraint order")
        return self


class CreviceTransportLocalMassActionRequest(Contract):
    """Run caller-defined local equilibrium systems from a pinned transport field."""

    assessment_id: str = Field(min_length=1)
    solution_id_prefix: str = Field(min_length=1)
    transport_result: AssessmentResult
    transport_result_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    cell_ids_in_transport_order: tuple[str, ...] = Field(min_length=2, max_length=500)
    cell_volume_m3_by_cell: tuple[Positive, ...] = Field(min_length=2, max_length=500)
    cell_volume_mapping_record_id: str = Field(min_length=1)
    cell_volume_mapping_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    cell_volume_mapping_evidence: tuple[Evidence, ...] = Field(min_length=1, max_length=32)
    knots: tuple[CreviceLocalEquilibriumKnot, ...] = Field(min_length=2, max_length=1000)
    rights_evidence: tuple[Evidence, ...] = Field(min_length=1, max_length=64)
    cell_order_and_geometry_mapping_reviewed: bool
    concentration_total_constraint_mapping_reviewed: bool
    independent_local_equilibrium_no_feedback_reviewed: bool
    usage_rights_reviewed: bool
    computational_use_authorized: bool

    @model_validator(mode="after")
    def validate_transport_and_spatial_alignment(self):
        result = self.transport_result
        if result.model_id not in ACCEPTED_TRANSPORT_MODELS or result.status != "computed":
            raise ValueError("a computed supported crevice transport result is required")
        expected_input_digest = canonical_digest({
            "model_id": result.model_id,
            "model_version": result.model_version,
            "inputs": result.inputs,
            "context": result.context.model_dump(mode="json"),
        })
        if result.input_digest != expected_input_digest:
            raise ValueError("transport AssessmentResult input digest mismatch")
        if canonical_digest(result.model_dump(mode="json")) != self.transport_result_sha256:
            raise ValueError("transport AssessmentResult digest mismatch")
        if len(set(self.cell_ids_in_transport_order)) != len(self.cell_ids_in_transport_order):
            raise ValueError("cell IDs must be unique in the caller-declared transport order")
        if len(self.cell_volume_m3_by_cell) != len(self.cell_ids_in_transport_order):
            raise ValueError("cell volumes must match the caller cell ordering")
        if not any(row.source_id == VOLUME_SOURCE_ID and row.sha256 == self.cell_volume_mapping_sha256
                   for row in self.cell_volume_mapping_evidence):
            raise ValueError("cell-volume Evidence must bind the declared mapping digest")
        if not any(row.license_id for row in self.rights_evidence):
            raise ValueError("rights Evidence must identify a license or permitted-use basis")
        values = result.values
        history = values.get("state_history")
        if not isinstance(history, list) or len(history) != len(self.knots):
            raise ValueError("local equilibrium knots must align one-to-one with the transport output history")
        if tuple(row.time_s for row in self.knots) != tuple(row.get("time_s") for row in history):
            raise ValueError("local chemistry must use the exact ordered transport time knots")
        for knot, state in zip(self.knots, history, strict=True):
            concentrations = _transport_concentrations(result.model_id, state)
            if len(knot.cell_templates) != len(self.cell_ids_in_transport_order):
                raise ValueError("each exact transport cell must have one chemistry template")
            if len(concentrations) != len(self.cell_ids_in_transport_order):
                raise ValueError("transport concentration field must align with declared cell order")
            for species_id, cell_values in concentrations.items():
                if len(cell_values) != len(self.cell_ids_in_transport_order):
                    raise ValueError(f"transported species {species_id!r} does not align with the cell order")
            declared_transport_species = set(concentrations)
            for binding in knot.constraint_bindings:
                if binding.transported_species_id not in declared_transport_species:
                    raise ValueError("each constraint mapping must refer to an upstream transported species")
            for template in knot.cell_templates:
                if template.temperature_K <= 0 or not math.isfinite(template.temperature_K):
                    raise ValueError("every cell chemistry template requires finite absolute temperature")
        return self


def _transport_concentrations(model_id: str, state: dict[str, Any]) -> dict[str, list[float]]:
    if model_id == "integration.crevice_neutral_reactive_transport_1d":
        key = "concentration_mol_m3_by_species"
    else:
        key = "species_concentration_mol_m3_by_id"
    field = state.get(key)
    if not isinstance(field, dict) or not field:
        raise ValueError("transport knot is missing its species concentration field")
    values: dict[str, list[float]] = {}
    for species_id, row in field.items():
        if not isinstance(species_id, str) or not species_id.strip() or not isinstance(row, list):
            raise ValueError("transport species IDs and cell concentration vectors must be valid")
        if any(isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value < 0
               for value in row):
            raise ValueError("transported concentrations must be finite, nonnegative mol/m3 values")
        values[species_id] = [float(value) for value in row]
    return values


def evaluate_crevice_transport_local_mass_action(
    request: CreviceTransportLocalMassActionRequest,
) -> Calculation:
    """Set explicit total-constraint targets from exact cell concentrations and solve each caller network."""
    transport = request.transport_result
    digest = canonical_digest(request.model_dump(mode="json"))
    base = {
        "assessment_id": request.assessment_id,
        "asset_id": transport.values.get("asset_id"),
        "location_id": transport.values.get("location_id"),
        "physical_scope_id": transport.values.get("physical_scope_id"),
        "clock_id": transport.values.get("clock_id"),
        "transport_model_id": transport.model_id,
        "transport_result_sha256": request.transport_result_sha256,
        "transport_input_sha256": transport.input_digest,
        "cell_ids_in_transport_order": list(request.cell_ids_in_transport_order),
        "input_sha256": digest,
        "cell_volume_mapping_record_id": request.cell_volume_mapping_record_id,
        "cell_volume_mapping_sha256": request.cell_volume_mapping_sha256,
        "rights_evidence": [row.model_dump(mode="json") for row in request.rights_evidence],
        "transport_to_chemistry_binding": "caller_declared_mol_m3_to_mol_L_total_constraint_scale_divided_by_1000",
    }
    reviews = {
        "cell_order_and_geometry_mapping_reviewed": request.cell_order_and_geometry_mapping_reviewed,
        "concentration_total_constraint_mapping_reviewed": request.concentration_total_constraint_mapping_reviewed,
        "independent_local_equilibrium_no_feedback_reviewed": request.independent_local_equilibrium_no_feedback_reviewed,
        "usage_rights_reviewed": request.usage_rights_reviewed,
        "computational_use_authorized": request.computational_use_authorized,
    }
    missing = [name for name, accepted in reviews.items() if not accepted]
    if missing:
        return Calculation(status="needs_data", values=base | {
            "missing_reviews": missing, "completed_cell_solve_count": 0, "local_speciation_history": [],
        })

    completed: list[dict[str, Any]] = []
    for knot_index, (knot, state) in enumerate(zip(request.knots, transport.values["state_history"], strict=True)):
        concentration_map = _transport_concentrations(transport.model_id, state)
        bindings = {row.constraint_id: row for row in knot.constraint_bindings}
        knot_results = []
        for cell_index, template in enumerate(knot.cell_templates):
            constraints = []
            constraint_mapping_rows = []
            for constraint in template.constraints:
                binding = bindings[constraint.constraint_id]
                raw_mol_m3 = concentration_map[binding.transported_species_id][cell_index]
                target_mol_l = raw_mol_m3 * binding.concentration_scale / 1000.0
                constraints.append(AqueousLinearConstraint.model_validate(
                    constraint.model_dump() | {"target_mol_L": target_mol_l}
                ))
                constraint_mapping_rows.append({
                    "constraint_id": constraint.constraint_id,
                    "transported_species_id": binding.transported_species_id,
                    "transport_concentration_mol_m3": raw_mol_m3,
                    "concentration_scale": binding.concentration_scale,
                    "generated_target_mol_L": target_mol_l,
                    "mapping_record_id": binding.mapping_record_id,
                    "mapping_record_sha256": binding.mapping_record_sha256,
                })
            local_request = AqueousMassActionSystem.model_validate(
                template.model_dump() | {
                    "assessment_id": f"{request.assessment_id}:k{knot_index}:c{cell_index}",
                    "solution_id": f"{request.solution_id_prefix}:k{knot_index}:c{cell_index}",
                    "constraints": [row.model_dump(mode="json") for row in constraints],
                }
            )
            result = aqueous_mass_action_speciation(local_request)
            result_data = result.model_dump(mode="json")
            result_digest = canonical_digest(result_data)
            cell_row = {
                "cell_id": request.cell_ids_in_transport_order[cell_index],
                "cell_index": cell_index,
                "cell_volume_m3": request.cell_volume_m3_by_cell[cell_index],
                "transport_concentration_mol_m3_by_species": {
                    species_id: values[cell_index] for species_id, values in concentration_map.items()
                },
                "constraint_target_mappings": constraint_mapping_rows,
                "mass_action_input_sha256": canonical_digest(local_request.model_dump(mode="json")),
                "mass_action_result_sha256": result_digest,
                "status": result.status,
                "result": result_data,
            }
            completed.append({"knot_index": knot_index, "time_s": knot.time_s, **cell_row})
            if result.status != "computed":
                return Calculation(status=result.status, values=base | {
                    "completed_cell_solve_count": len(completed) - 1,
                    "local_speciation_history": completed,
                    "failed_knot_index": knot_index,
                    "failed_cell_index": cell_index,
                    "failure_reason": result_data.get("notes", []),
                    "complete_spatial_knot_committed": False,
                })
            values = result.values
            species_concentration_mol_l = {
                row["species_id"]: row["concentration_mol_L"]
                for row in values.get("species", [])
            }
            inventories = {
                species_id: concentration_mol_l * 1000.0 * request.cell_volume_m3_by_cell[cell_index]
                for species_id, concentration_mol_l in species_concentration_mol_l.items()
            }
            cell_row["equilibrium_species_inventory_mol"] = inventories
            cell_row["equilibrium_species_concentration_mol_L"] = species_concentration_mol_l
            knot_results.append(cell_row)
        completed[-len(knot_results):] = [
            {"knot_index": knot_index, "time_s": knot.time_s, **row} for row in knot_results
        ]

    return Calculation(status="computed", values=base | {
        "completed_cell_solve_count": len(completed),
        "knot_count": len(request.knots),
        "local_speciation_history": completed,
        "phase_selection_performed": False,
        "transport_feedback_performed": False,
        "interpretation": "exact_knot_cellwise_caller_mapped_single_liquid_mass_action_equilibria",
        "limitations": [
            "Each caller-declared transport species is mapped one-to-one to one explicit linear constraint target; no component totals or chemistry are inferred.",
            "Each exact cell uses its caller-provided mass-action template, activity/equilibrium records, temperature and provider Evidence.",
            "Transport is not modified by equilibrium chemistry; no reaction/transport feedback, phase selection, precipitation, wall loss, corrosion rate or qualification is computed.",
            "Inventory output multiplies equilibrium mol/L values by the caller-mapped transport cell volume and is conditional on the caller volume mapping review.",
        ],
    })


def specifications() -> list[ModelSpec]:
    return [ModelSpec(
        model_id=MODEL_ID,
        input_type=CreviceTransportLocalMassActionRequest,
        evaluator=evaluate_crevice_transport_local_mass_action,
        units={
            "knots[].time_s": "s",
            "cell_volume_m3_by_cell[]": "m^3",
            "local_speciation_history[].transport_concentration_mol_m3_by_species.*": "mol/m^3",
            "local_speciation_history[].equilibrium_species_concentration_mol_L.*": "mol/L",
            "local_speciation_history[].equilibrium_species_inventory_mol.*": "mol",
        },
        assumptions=(
            "Caller-reviewed one-to-one mappings set one existing aqueous mass-action linear constraint from a transported concentration per exact cell and knot.",
            "Each cell and knot uses an independently supplied full mass-action system; temperature, activity, constants, formulae and phase scope remain caller controlled.",
            "The chemistry solve is one-way; no concentration feedback, transport update or automatic phase selection is performed.",
        ),
        source_ids=(MAPPING_SOURCE_ID, VOLUME_SOURCE_ID, METHOD_SOURCE_ID,
                    "caller_crevice_spatial_mass_action_workflow"),
    )]
