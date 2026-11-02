"""Bind one crevice transport knot's local speciation to solid saturation screens."""

from __future__ import annotations

from typing import Literal

from pydantic import Field, model_validator

from .contracts import Calculation, Contract, Evidence, canonical_digest
from .crevice_local_speciation_ledger import (
    CreviceLocalSpeciationLedgerRequest,
    transport_cell_context_digest,
)
from .models.aqueous_mass_action import AqueousMassActionSystem
from .models.aqueous_saturation_screening import CandidateSolid, screen_mass_action_calculation
from .registry import ModelSpec

MODEL_ID = "integration.crevice_local_solid_saturation"
SOURCE_ID = "caller_crevice_cell_local_candidate_saturation_screen"
MAX_CELLS = 200


class CreviceLocalSolidSaturationRequest(Contract):
    """Screen candidate-solid saturation from one digest-bound spatial knot."""

    schema_version: Literal["matintegrity.crevice_local_solid_saturation.v1"] = (
        "matintegrity.crevice_local_solid_saturation.v1"
    )
    assessment_id: str = Field(min_length=1)
    local_speciation_ledger: CreviceLocalSpeciationLedgerRequest
    local_speciation_ledger_result: dict
    local_speciation_ledger_result_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    knot_index: int = Field(ge=0)
    candidate_solids: tuple[CandidateSolid, ...] = Field(min_length=1, max_length=100)
    solubility_data_provider_id: str = Field(min_length=1)
    solubility_data_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    evidence: tuple[Evidence, ...] = Field(min_length=1, max_length=256)
    complete_species_inventory_reviewed: bool
    compatible_standard_states_reviewed: bool
    equilibrium_constants_temperature_reviewed: bool
    spatial_cell_mapping_and_candidate_support_reviewed: bool
    no_phase_selection_or_precipitation_inference_reviewed: bool

    @model_validator(mode="after")
    def validate_source_and_bounds(self):
        if canonical_digest(self.local_speciation_ledger_result) != self.local_speciation_ledger_result_sha256:
            raise ValueError("local speciation ledger result digest mismatch")
        if self.local_speciation_ledger_result.get("status") != "computed":
            raise ValueError("computed local speciation ledger result is required")
        knots = self.local_speciation_ledger.knots
        if self.knot_index >= len(knots):
            raise ValueError("selected knot index is outside the local speciation input")
        cells = knots[self.knot_index].cells
        if len(cells) > MAX_CELLS:
            raise ValueError("at most 200 local cells may be screened in one call")
        result_values = self.local_speciation_ledger_result.get("values", {})
        if result_values.get("assessment_id") != self.local_speciation_ledger.assessment_id:
            raise ValueError("local speciation ledger result belongs to another assessment")
        result_knots = result_values.get("knots")
        if not isinstance(result_knots, list) or len(result_knots) != len(knots):
            raise ValueError("local speciation result knot count differs from its typed input")
        upstream_knot = result_knots[self.knot_index]
        if (
            not isinstance(upstream_knot, dict)
            or upstream_knot.get("knot_summary_index") != self.knot_index
            or not isinstance(upstream_knot.get("cells"), list)
            or len(upstream_knot["cells"]) != len(cells)
        ):
            raise ValueError("selected local speciation result cells do not match its typed input")
        solid_ids = [row.solid_id for row in self.candidate_solids]
        if len(solid_ids) != len(set(solid_ids)):
            raise ValueError("candidate solid IDs must be unique")
        evidence_ids = [row.source_id for row in self.evidence]
        if len(evidence_ids) != len(set(evidence_ids)):
            raise ValueError("evidence source IDs must be unique")
        missing_evidence = {
            row.solubility_evidence_source_id for row in self.candidate_solids
        } - set(evidence_ids)
        if missing_evidence:
            raise ValueError("candidate solubility evidence source IDs must be supplied")
        known_species = {row.species_id for row in cells[0].aqueous_mass_action_input.species}
        if any({term.species_id for term in solid.terms} - known_species for solid in self.candidate_solids):
            raise ValueError("candidate solid activity terms must match local mass-action species")
        return self


def evaluate_crevice_local_solid_saturation(
    request: CreviceLocalSolidSaturationRequest,
) -> Calculation:
    """Evaluate existing aqueous saturation screening separately for each exact cell."""
    ledger = request.local_speciation_ledger
    upstream_result = request.local_speciation_ledger_result
    ledger_values = upstream_result.get("values", {})
    knot = ledger.knots[request.knot_index]
    summaries = ledger_values.get("knots", [])
    upstream_knot = summaries[request.knot_index]
    campaign = ledger.transport_binding.campaign
    base = {
        "assessment_id": request.assessment_id,
        "campaign_id": campaign.campaign_id,
        "physical_scope_id": campaign.physical_scope_id,
        "knot_index": request.knot_index,
        "elapsed_time_s": knot.time_s,
        "geometry_side": knot.geometry_side,
        "local_speciation_ledger_result_sha256": request.local_speciation_ledger_result_sha256,
        "transport_knot_summary_sha256": upstream_knot.get("transport_knot_summary_sha256"),
        "solubility_data_provider_id": request.solubility_data_provider_id,
        "solubility_data_digest": request.solubility_data_digest,
        "candidate_solid_ids": [row.solid_id for row in request.candidate_solids],
        "phase_selection_performed": False,
        "precipitated_amount_predicted": False,
    }
    if (
        upstream_knot.get("knot_summary_index") != request.knot_index
        or upstream_knot.get("time_s") != knot.time_s
        or upstream_knot.get("geometry_side") != knot.geometry_side
    ):
        return Calculation(status="out_of_scope", values=base | {
            "completed_cell_count": 0, "completed_cells": [],
            "failure_reason": "selected upstream knot index, time or geometry side differs from the typed speciation knot",
        })
    reviews = (
        "complete_species_inventory_reviewed",
        "compatible_standard_states_reviewed",
        "equilibrium_constants_temperature_reviewed",
        "spatial_cell_mapping_and_candidate_support_reviewed",
        "no_phase_selection_or_precipitation_inference_reviewed",
    )
    missing = [name for name in reviews if not getattr(request, name)]
    if missing:
        return Calculation(status="needs_data", values=base | {
            "missing_reviews": missing, "completed_cell_count": 0, "completed_cells": [],
        })

    committed: list[dict] = []
    common_temperature: float | None = None
    common_standard_state: str | None = None
    for cell_record, result_cell in zip(knot.cells, upstream_knot["cells"], strict=True):
        index = cell_record.cell_index
        context_sha = transport_cell_context_digest(
            ledger.transport_binding_result["values"]["knot_summaries"][request.knot_index], index
        )
        mass_action = cell_record.aqueous_mass_action_input
        mass_action_result = cell_record.aqueous_mass_action_result
        expected_input_digest = canonical_digest(mass_action.model_dump(mode="json"))
        if (
            cell_record.transport_cell_context_sha256 != context_sha
            or result_cell.get("transport_cell_context_sha256") != context_sha
            or result_cell.get("aqueous_mass_action_input_sha256") != expected_input_digest
            or result_cell.get("aqueous_mass_action_result_sha256") != canonical_digest(mass_action_result)
        ):
            return Calculation(status="needs_data", values=base | {
                "completed_cell_count": len(committed), "completed_cells": committed,
                "failed_cell_index": index,
                "failure_reason": "speciation or source-cell digest does not match the selected transport cell",
            })
        try:
            calculation = Calculation.model_validate(mass_action_result)
        except (TypeError, ValueError):
            calculation = None
        values = calculation.values if calculation is not None else {}
        species = values.get("species")
        if (
            calculation is None or calculation.status != "computed"
            or values.get("input_digest") != expected_input_digest
            or not isinstance(species, list)
        ):
            return Calculation(status="needs_data", values=base | {
                "completed_cell_count": len(committed), "completed_cells": committed,
                "failed_cell_index": index,
                "failure_reason": "mass-action result is not a computed result for the supplied local request",
            })
        ids = [row.get("species_id") for row in species if isinstance(row, dict)]
        expected_ids = [row.species_id for row in mass_action.species]
        if ids != expected_ids or any("dimensionless_activity" not in row for row in species):
            return Calculation(status="out_of_scope", values=base | {
                "completed_cell_count": len(committed), "completed_cells": committed,
                "failed_cell_index": index,
                "failure_reason": "mass-action species identity/order or activity output is incompatible",
            })
        if common_temperature is None:
            common_temperature = mass_action.temperature_K
            common_standard_state = mass_action.activity_standard_state
        if mass_action.temperature_K != common_temperature or mass_action.activity_standard_state != common_standard_state:
            return Calculation(status="out_of_scope", values=base | {
                "completed_cell_count": len(committed), "completed_cells": committed,
                "failed_cell_index": index,
                "failure_reason": "one shared candidate solubility record set requires a common temperature and standard state",
            })

        saturation = screen_mass_action_calculation(
            calculation,
            assessment_id=f"{request.assessment_id}:cell:{index}",
            solution_id=mass_action.solution_id,
            candidate_solids=request.candidate_solids,
            solubility_data_provider_id=request.solubility_data_provider_id,
            solubility_data_digest=request.solubility_data_digest,
            complete_species_inventory_reviewed=request.complete_species_inventory_reviewed,
            compatible_standard_states_reviewed=request.compatible_standard_states_reviewed,
            equilibrium_constants_temperature_reviewed=request.equilibrium_constants_temperature_reviewed,
            evidence=request.evidence,
        )
        if saturation.status != "computed":
            return Calculation(status=saturation.status, values=base | {
                "completed_cell_count": len(committed), "completed_cells": committed,
                "failed_cell_index": index,
                "failure_reason": "existing aqueous saturation evaluator did not complete for this cell",
                "upstream_status": saturation.status,
                "upstream_values": saturation.values,
            })
        committed.append({
            "cell_index": index,
            "transport_cell_context_sha256": context_sha,
            "aqueous_mass_action_result_sha256": canonical_digest(mass_action_result),
            "solution_id": mass_action.solution_id,
            "temperature_K": mass_action.temperature_K,
            "saturation_result_sha256": canonical_digest(saturation.model_dump(mode="json")),
            "candidate_results": saturation.values.get("candidate_results", []),
        })

    return Calculation(values=base | {
        "status": "computed",
        "temperature_K": common_temperature,
        "activity_standard_state": common_standard_state,
        "completed_cell_count": len(committed),
        "completed_cells": committed,
        "interpretation_boundary": "Candidate-solid saturation indices are evaluated independently for each digest-pinned transport cell using the existing aqueous saturation screen. No spatial mixing, phase choice, equilibrium projection, precipitation amount, nucleation, kinetics or geometry change is inferred.",
    })


def specifications() -> list[ModelSpec]:
    return [ModelSpec(
        model_id=MODEL_ID,
        input_type=CreviceLocalSolidSaturationRequest,
        evaluator=evaluate_crevice_local_solid_saturation,
        units={
            "elapsed_time_s": "s",
            "temperature_K": "K",
            "completed_cells[].candidate_results[].log10_saturation_ratio": "1",
            "completed_cells[].candidate_results[].log10_saturation_absolute_bound": "1",
            "completed_cells[].candidate_results[].log10_saturation_ratio_lower_bound": "1",
            "completed_cells[].candidate_results[].log10_saturation_ratio_upper_bound": "1",
        },
        assumptions=(
            "The selected local-speciation ledger result and each exact transport cell context must match their supplied canonical digests.",
            "Every local mass-action result must be computed from the exact typed request and retain the same species order as the supplied candidate saturation definitions.",
            "One candidate-solubility record set is reused across the selected knot, so all cells must share the exact temperature and activity standard state declared by their local mass-action requests.",
            "Existing aqueous saturation screening uses caller-supplied dimensionless activities, candidate stoichiometric activity products, solubility constants, evidence and review gates; the adapter does not infer or qualify them.",
            "Each cell is screened independently; no phase selection, phase amount, spatial mixing, precipitation kinetics or corrosion rate is calculated.",
        ),
        source_ids=(SOURCE_ID,),
        qualification="user_model",
    )]
