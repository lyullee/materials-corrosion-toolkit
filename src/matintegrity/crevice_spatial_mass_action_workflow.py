"""Run caller-defined local mass-action systems across exact crevice cells."""

from __future__ import annotations

from typing import Literal

from pydantic import Field, model_validator

from .contracts import Calculation, Contract, canonical_digest
from .crevice_local_speciation_ledger import (
    CreviceLocalSpeciationLedgerRequest,
    CreviceSpeciationKnot,
    assemble_crevice_local_speciation_ledger,
)
from .models.aqueous_mass_action import (
    AqueousMassActionSystem,
    aqueous_mass_action_speciation,
)
from .registry import ModelSpec


class CreviceSpatialMassActionWorkflow(Contract):
    """Explicitly solve one complete caller system per exact transport cell."""

    schema_version: Literal["matintegrity.crevice_spatial_mass_action_workflow.v1"] = (
        "matintegrity.crevice_spatial_mass_action_workflow.v1"
    )
    assessment_id: str = Field(min_length=1)
    ledger_request: CreviceLocalSpeciationLedgerRequest
    local_solver_execution_authorized: bool
    cell_specific_chemistry_mapping_reviewed: bool

    @model_validator(mode="after")
    def require_empty_result_slots_and_unique_systems(self):
        requests = [
            cell.aqueous_mass_action_input
            for knot in self.ledger_request.knots
            for cell in knot.cells
        ]
        ids = [row.assessment_id for row in requests]
        if len(ids) != len(set(ids)):
            raise ValueError("each local mass-action system must have a unique assessment ID")
        if any(cell.aqueous_mass_action_result for knot in self.ledger_request.knots for cell in knot.cells):
            raise ValueError("local result slots must be empty; this workflow computes each result itself")
        return self


def solve_crevice_spatial_mass_action_workflow(
    request: CreviceSpatialMassActionWorkflow,
) -> Calculation:
    """Solve exact caller systems in knot/cell order, then assemble the existing inventory ledger."""
    digest = canonical_digest(request.model_dump(mode="json"))
    transport = request.ledger_request.transport_binding_result
    transport_values = transport.get("values", {})
    base = {
        "assessment_id": request.assessment_id,
        "workflow_input_sha256": digest,
        "transport_binding_result_sha256": request.ledger_request.transport_binding_result_sha256,
        "transport_campaign_input_sha256": transport_values.get("campaign_input_sha256"),
        "geometry_history_sha256": transport_values.get("geometry_history_sha256"),
        "solver": "caller_parameterized_aqueous_mass_action_per_exact_transport_cell",
        "automatic_cell_chemistry_mapping": False,
        "automatic_phase_selection": False,
    }
    missing = [name for name, accepted in (
        ("local_solver_execution_authorized", request.local_solver_execution_authorized),
        ("cell_specific_chemistry_mapping_reviewed", request.cell_specific_chemistry_mapping_reviewed),
    ) if not accepted]
    if missing:
        return Calculation(status="needs_data", values=base | {
            "missing_reviews": missing,
            "completed_cell_solve_count": 0,
            "local_solve_results": [],
        })

    completed: list[dict] = []
    resolved_knots: list[CreviceSpeciationKnot] = []
    for knot_index, knot in enumerate(request.ledger_request.knots):
        resolved_cells = []
        for cell in knot.cells:
            system: AqueousMassActionSystem = cell.aqueous_mass_action_input
            result = aqueous_mass_action_speciation(system)
            result_data = result.model_dump(mode="json")
            completed.append({
                "knot_summary_index": knot.knot_summary_index,
                "cell_index": cell.cell_index,
                "time_s": knot.time_s,
                "geometry_side": knot.geometry_side,
                "aqueous_mass_action_input_sha256": canonical_digest(system.model_dump(mode="json")),
                "aqueous_mass_action_result_sha256": canonical_digest(result_data),
                "status": result.status,
                "result": result_data,
            })
            if result.status != "computed":
                return Calculation(status=result.status, values=base | {
                    "completed_cell_solve_count": len(completed) - 1,
                    "local_solve_results": completed,
                    "failed_knot_index": knot_index,
                    "failed_knot_summary_index": knot.knot_summary_index,
                    "failed_cell_index": cell.cell_index,
                    "failed_cell_result": result_data,
                    "ledger_result": None,
                    "prefix_policy": "do not assemble a complete local inventory ledger after any cell solve is incomplete",
                }, notes=(
                    "Local solver results are committed in knot/cell order; downstream volume-ledger assembly is withheld unless every requested cell system computes.",
                ))
            resolved_cells.append(cell.model_copy(update={"aqueous_mass_action_result": result_data}))
        resolved_knots.append(knot.model_copy(update={"cells": tuple(resolved_cells)}))

    ledger_request = request.ledger_request.model_copy(update={"knots": tuple(resolved_knots)})
    ledger_result = assemble_crevice_local_speciation_ledger(ledger_request)
    return Calculation(status=ledger_result.status, values=base | {
        "completed_cell_solve_count": len(completed),
        "local_solve_results": completed,
        "ledger_request_sha256": canonical_digest(ledger_request.model_dump(mode="json")),
        "ledger_result_sha256": canonical_digest(ledger_result.model_dump(mode="json")),
        "ledger_result": ledger_result.model_dump(mode="json"),
        "complete_knot_ledger_assembled": ledger_result.status == "computed",
        "interpretation_boundary": "Independent caller-defined cell equilibrium solves followed by the existing cell-volume ledger; no cell-to-cell transfer or equilibrium, phase transition, inter-knot continuity, kinetic law, corrosion or qualification is inferred.",
    }, notes=(
        "Every species, reaction, equilibrium record, activity coefficient, constraint, temperature and local system is supplied by the caller and passed unchanged to the existing aqueous mass-action solver.",
        "The downstream ledger retains exact transport cell digests and volumes; it does not map transport concentrations into chemical constraints automatically.",
    ) + ledger_result.notes)


def specifications() -> list[ModelSpec]:
    return [ModelSpec(
        model_id="integration.crevice_spatial_mass_action_workflow",
        input_type=CreviceSpatialMassActionWorkflow,
        evaluator=solve_crevice_spatial_mass_action_workflow,
        units={
            "ledger_request.knots[].time_s": "s",
            "ledger_request.knots[].cells[].aqueous_mass_action_input.temperature_K": "K",
            "ledger_result.values.knots[].cells[].cell_volume_m3": "m3",
            "ledger_result.values.knots[].cells[].species_concentration_mol_L.*": "mol/L",
            "ledger_result.values.knots[].cells[].species_inventory_mol.*": "mol",
        },
        assumptions=(
            "A complete caller-provided aqueous mass-action system is solved independently at each exact transport knot and cell; only the existing solver is used.",
            "Cell chemistry mapping, species basis, volume interpretation and phase scope remain caller-owned; no concentrations or constraints are inferred from transport fields.",
            "The existing local speciation ledger is assembled only after all cell systems compute, preserving exact geometry-side and cell context lineage.",
        ),
        source_ids=("caller_crevice_spatial_mass_action_workflow",),
        qualification="user_model",
    )]
