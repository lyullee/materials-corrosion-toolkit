"""Map committed crevice Faradaic extents to caller-defined metal loss."""

from __future__ import annotations

import math
from typing import Literal

from pydantic import Field, model_validator

from .contracts import AssessmentResult, Calculation, Contract, Evidence, Positive, RunContext, canonical_digest
from .crevice_current_carrying_np_faradaic import CreviceCurrentCarryingNernstPlanckRequest
from .registry import ModelSpec

MODEL_ID = "integration.crevice_current_carrying_extent_to_metal_loss"
UPSTREAM_MODEL_ID = "integration.crevice_current_carrying_np_faradaic"
MAPPING_SOURCE_ID = "caller_crevice_current_branch_metal_mapping"
DISPOSITION_SOURCE_ID = "caller_crevice_current_branch_disposition"
METHOD_SOURCE_ID = "faradaic_extent_to_cellwise_metal_volume_and_recession"


class CreviceCurrentBranchMetalMapping(Contract):
    """Caller-reviewed stoichiometry and material mapping for a dissolution branch."""

    reaction_id: str = Field(min_length=1)
    metal_species_id: str = Field(min_length=1)
    metal_moles_per_reaction_extent: Positive
    metal_molar_mass_kg_mol: Positive
    metal_density_kg_m3: Positive
    reactive_area_m2_by_cell: tuple[Positive, ...] = Field(min_length=2, max_length=300)
    mapping_record_id: str = Field(min_length=1)
    mapping_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    evidence: tuple[Evidence, ...] = Field(min_length=1, max_length=32)
    metal_identity_and_stoichiometry_reviewed: bool
    extent_is_net_dissolution_only_reviewed: bool
    cell_area_and_uniform_recession_reviewed: bool

    @classmethod
    def _mapping_digest_payload(cls, values: dict) -> dict:
        return {
            "reaction_id": values["reaction_id"],
            "metal_species_id": values["metal_species_id"],
            "metal_moles_per_reaction_extent": values["metal_moles_per_reaction_extent"],
            "metal_molar_mass_kg_mol": values["metal_molar_mass_kg_mol"],
            "metal_density_kg_m3": values["metal_density_kg_m3"],
            "reactive_area_m2_by_cell": list(values["reactive_area_m2_by_cell"]),
            "mapping_record_id": values["mapping_record_id"],
        }

    def mapping_digest(self) -> str:
        return canonical_digest(self._mapping_digest_payload(self.model_dump(mode="python")))

    @model_validator(mode="after")
    def validate_mapping_evidence(self) -> "CreviceCurrentBranchMetalMapping":
        payload = self._mapping_digest_payload(self.model_dump(mode="python"))
        expected = canonical_digest(payload)
        if expected != self.mapping_sha256:
            raise ValueError("metal mapping digest must bind the complete stoichiometry and cell-area map")
        if not any(
            row.source_id == MAPPING_SOURCE_ID and row.origin == "user_declared" and row.sha256 == expected
            for row in self.evidence
        ):
            raise ValueError("metal mapping Evidence must pin its mapping digest")
        return self


class CreviceCurrentCarryingExtentMetalLossRequest(Contract):
    schema_version: Literal["matintegrity.crevice_current_carrying_extent_to_metal_loss.v1"] = (
        "matintegrity.crevice_current_carrying_extent_to_metal_loss.v1"
    )
    assessment_id: str = Field(min_length=1)
    material_condition_id: str = Field(min_length=1)
    current_carrying_request: CreviceCurrentCarryingNernstPlanckRequest
    current_carrying_result: AssessmentResult
    current_carrying_result_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    mappings: tuple[CreviceCurrentBranchMetalMapping, ...] = Field(min_length=1, max_length=64)
    excluded_non_dissolution_reaction_ids: tuple[str, ...] = Field(default=(), max_length=64)
    branch_disposition_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    branch_disposition_evidence: tuple[Evidence, ...] = Field(min_length=1, max_length=32)
    branch_disposition_reviewed: bool
    computational_use_authorized: bool

    @staticmethod
    def disposition_digest(mapped_ids: tuple[str, ...], excluded_ids: tuple[str, ...]) -> str:
        return canonical_digest({
            "mapped_dissolution_reaction_ids": list(mapped_ids),
            "excluded_non_dissolution_reaction_ids": list(excluded_ids),
        })

    @staticmethod
    def _verified_assessment_digest(result: AssessmentResult) -> str:
        return canonical_digest({
            "model_id": result.model_id,
            "model_version": result.model_version,
            "inputs": result.inputs,
            "context": result.context.model_dump(mode="json"),
        })

    @model_validator(mode="after")
    def validate_source_and_mapping(self) -> "CreviceCurrentCarryingExtentMetalLossRequest":
        result = self.current_carrying_result
        request_dump = self.current_carrying_request.model_dump(mode="json")
        if result.model_id != UPSTREAM_MODEL_ID or result.status != "computed":
            raise ValueError("a computed current-carrying crevice assessment is required")
        if result.input_digest != self._verified_assessment_digest(result):
            raise ValueError("upstream assessment input digest mismatch")
        if canonical_digest(result.model_dump(mode="json")) != self.current_carrying_result_sha256:
            raise ValueError("complete upstream assessment digest mismatch")
        if result.inputs != request_dump:
            raise ValueError("upstream result inputs do not match the supplied current-carrying request")
        values = result.values
        if values.get("model_id") != UPSTREAM_MODEL_ID:
            raise ValueError("upstream output model identity mismatch")
        if values.get("input_sha256") != canonical_digest(request_dump):
            raise ValueError("upstream calculation input digest mismatch")
        if values.get("all_requested_intervals_committed") is not True:
            raise ValueError("all current-carrying intervals must be committed before metal mapping")
        if values.get("committed") is False:
            raise ValueError("failed current-carrying prefixes cannot be promoted to metal loss")

        coupling = self.current_carrying_request.faradaic_coupling
        declared = tuple(row.reaction_id for row in coupling.faradaic_branch_maps)
        if not declared or len(declared) != len(set(declared)):
            raise ValueError("upstream Faradaic branch IDs must be nonempty and unique")
        mapped = tuple(row.reaction_id for row in self.mappings)
        excluded = self.excluded_non_dissolution_reaction_ids
        if len(mapped) != len(set(mapped)) or len(excluded) != len(set(excluded)):
            raise ValueError("branch disposition IDs must be unique")
        if set(mapped).intersection(excluded) or set(mapped).union(excluded) != set(declared):
            raise ValueError("every upstream reaction branch must be mapped or explicitly excluded")
        expected_disposition = self.disposition_digest(mapped, excluded)
        if expected_disposition != self.branch_disposition_sha256 or not any(
            row.source_id == DISPOSITION_SOURCE_ID and row.origin == "user_declared"
            and row.sha256 == expected_disposition
            for row in self.branch_disposition_evidence
        ):
            raise ValueError("branch disposition Evidence must pin the complete branch coverage")
        if not self.branch_disposition_reviewed or not self.computational_use_authorized:
            raise ValueError("branch disposition review and computational-use authorization are required")

        cell_ids = coupling.mixed_potential_template.cell_ids
        if len(cell_ids) < 2 or len(set(cell_ids)) != len(cell_ids):
            raise ValueError("upstream ordered cell IDs must be unique and contain at least two cells")
        for mapping in self.mappings:
            if len(mapping.reactive_area_m2_by_cell) != len(cell_ids):
                raise ValueError("each mapped cell-area vector must align with upstream cell order")
            if not (mapping.metal_identity_and_stoichiometry_reviewed
                    and mapping.extent_is_net_dissolution_only_reviewed
                    and mapping.cell_area_and_uniform_recession_reviewed):
                raise ValueError(f"all metal, extent-sign and cell-area reviews are required: {mapping.reaction_id}")
            mapping.validate_mapping_evidence()

        intervals = values.get("accepted_intervals")
        transport = coupling.transport_chemistry.transport.transport_request
        times = transport.output_time_s
        if not isinstance(intervals, list) or len(intervals) != len(times) - 1:
            raise ValueError("upstream committed intervals must match the full requested clock")
        for index, interval in enumerate(intervals):
            if (not isinstance(interval, dict) or interval.get("committed") is False
                    or interval.get("interval_index") != index
                    or interval.get("start_time_s") != times[index]
                    or interval.get("end_time_s") != times[index + 1]):
                raise ValueError("upstream intervals must preserve contiguous exact requested knots")
            extents = interval.get("faradaic_extent_mol_by_branch_and_cell")
            if not isinstance(extents, dict) or tuple(extents) != declared:
                raise ValueError("each committed interval must preserve all declared branch identities and order")
            for reaction_id in declared:
                vector = extents[reaction_id]
                if (not isinstance(vector, list) or len(vector) != len(cell_ids)
                        or any(isinstance(value, bool) or not isinstance(value, (int, float))
                               or not math.isfinite(value) for value in vector)):
                    raise ValueError("each Faradaic extent vector must be finite and align with upstream cells")
                if reaction_id in mapped and any(value < 0.0 for value in vector):
                    raise ValueError("mapped dissolution extent is signed negative; net-reversal mapping is unsupported")
        return self


def convert_current_carrying_extent_to_metal_loss(
    request: CreviceCurrentCarryingExtentMetalLossRequest,
) -> Calculation:
    """Convert already-integrated positive reaction extents without re-integrating current."""
    source = request.current_carrying_result
    source_values = source.values
    accepted = source_values["accepted_intervals"]
    cell_ids = list(request.current_carrying_request.faradaic_coupling.mixed_potential_template.cell_ids)
    mapping_by_id = {row.reaction_id: row for row in request.mappings}
    cumulative_mass = {reaction_id: [0.0] * len(cell_ids) for reaction_id in mapping_by_id}
    cumulative_volume = {reaction_id: [0.0] * len(cell_ids) for reaction_id in mapping_by_id}
    interval_metal_loss = []
    interval_cell_ledger = []

    for interval in accepted:
        reaction_rows = []
        cell_rows = []
        branch_extents = interval["faradaic_extent_mol_by_branch_and_cell"]
        for reaction_id, mapping in mapping_by_id.items():
            reaction_cell_rows = []
            for cell_index, cell_id in enumerate(cell_ids):
                reaction_extent = float(branch_extents[reaction_id][cell_index])
                metal_moles = reaction_extent * mapping.metal_moles_per_reaction_extent
                mass = metal_moles * mapping.metal_molar_mass_kg_mol
                volume = mass / mapping.metal_density_kg_m3
                area = mapping.reactive_area_m2_by_cell[cell_index]
                recession = volume / area
                if not all(math.isfinite(value) and value >= 0.0 for value in (metal_moles, mass, volume, recession)):
                    return Calculation(status="needs_data", values={
                        "model_id": MODEL_ID, "assessment_id": request.assessment_id,
                        "reason": "nonfinite_or_negative_metal_loss_mapping",
                        "failed_interval_index": interval["interval_index"],
                        "failed_reaction_id": reaction_id, "failed_cell_id": cell_id,
                        "committed_interval_prefix": len(interval_metal_loss),
                        "upstream_assessment_sha256": request.current_carrying_result_sha256,
                    })
                cumulative_mass[reaction_id][cell_index] += mass
                cumulative_volume[reaction_id][cell_index] += volume
                reaction_cell_rows.append({
                    "cell_id": cell_id,
                    "reaction_extent_mol": reaction_extent,
                    "metal_dissolved_mol": metal_moles,
                    "mass_loss_kg": mass,
                    "metal_volume_m3": volume,
                    "reactive_area_m2": area,
                    "uniform_cell_recession_m": recession,
                    "cumulative_mass_loss_kg": cumulative_mass[reaction_id][cell_index],
                    "cumulative_metal_volume_m3": cumulative_volume[reaction_id][cell_index],
                })
            total_mass = math.fsum(cumulative_mass[reaction_id])
            reaction_rows.append({
                "reaction_id": reaction_id,
                "cumulative": {"signed_mass_loss_kg": total_mass},
            })
            cell_rows.append({"reaction_id": reaction_id, "cells": reaction_cell_rows})
        interval_metal_loss.append({
            "start_time_s": interval["start_time_s"],
            "end_time_s": interval["end_time_s"],
            "reaction_metal_loss": reaction_rows,
        })
        interval_cell_ledger.append({
            "interval_index": interval["interval_index"],
            "start_time_s": interval["start_time_s"],
            "end_time_s": interval["end_time_s"],
            "branches": cell_rows,
        })

    return Calculation(status="computed", values={
        "model_id": MODEL_ID,
        "assessment_id": request.assessment_id,
        "material_condition_id": request.material_condition_id,
        "input_sha256": canonical_digest(request.model_dump(mode="json")),
        "upstream_model_id": source.model_id,
        "upstream_assessment_sha256": request.current_carrying_result_sha256,
        "upstream_input_sha256": source.input_digest,
        "cell_ids": cell_ids,
        "reaction_to_metal_mapping": [
            {
                "reaction_id": reaction_id,
                "metal_species_id": mapping_by_id[reaction_id].metal_species_id,
                "metal_moles_per_reaction_extent": mapping_by_id[reaction_id].metal_moles_per_reaction_extent,
                "molar_mass_kg_mol": mapping_by_id[reaction_id].metal_molar_mass_kg_mol,
                "density_kg_m3": mapping_by_id[reaction_id].metal_density_kg_m3,
                "mapping_record_id": mapping_by_id[reaction_id].mapping_record_id,
                "mapping_sha256": mapping_by_id[reaction_id].mapping_sha256,
            }
            for reaction_id in mapping_by_id
        ],
        "interval_metal_loss": interval_metal_loss,
        "cellwise_interval_metal_loss": interval_cell_ledger,
        "excluded_non_dissolution_reaction_ids": list(request.excluded_non_dissolution_reaction_ids),
        "branch_disposition_sha256": request.branch_disposition_sha256,
        "integration_method": "map_committed_faradic_extent_to_metal_moles_mass_volume_and_cell_recession",
        "metal_volume_balance_m3_by_reaction": {
            reaction_id: math.fsum(cumulative_volume[reaction_id]) for reaction_id in mapping_by_id
        },
        "limitations": [
            "Faradaic reaction extents are already time-integrated upstream and are not integrated again here.",
            "Only caller-declared dissolution branches with nonnegative net interval extents are mapped; sign reversals within an interval cannot be recovered.",
            "Metal identity, reaction stoichiometry, molar mass, density and per-cell reactive area are caller supplied and evidence bound.",
            "Recession is uniform over each declared cell reactive area; no pit shape, moving-boundary transport or material qualification is inferred.",
        ],
        "qualification_claimed": False,
    })


def specifications() -> tuple[ModelSpec, ...]:
    return (ModelSpec(
        model_id=MODEL_ID,
        input_type=CreviceCurrentCarryingExtentMetalLossRequest,
        evaluator=convert_current_carrying_extent_to_metal_loss,
        units={
            "interval_metal_loss[].start_time_s": "s",
            "interval_metal_loss[].end_time_s": "s",
            "interval_metal_loss[].reaction_metal_loss[].cumulative.signed_mass_loss_kg": "kg",
            "cellwise_interval_metal_loss[].branches[].cells[].reaction_extent_mol": "mol",
            "cellwise_interval_metal_loss[].branches[].cells[].metal_dissolved_mol": "mol",
            "cellwise_interval_metal_loss[].branches[].cells[].mass_loss_kg": "kg",
            "cellwise_interval_metal_loss[].branches[].cells[].metal_volume_m3": "m^3",
            "cellwise_interval_metal_loss[].branches[].cells[].reactive_area_m2": "m^2",
            "cellwise_interval_metal_loss[].branches[].cells[].uniform_cell_recession_m": "m",
            "cellwise_interval_metal_loss[].branches[].cells[].cumulative_mass_loss_kg": "kg",
            "cellwise_interval_metal_loss[].branches[].cells[].cumulative_metal_volume_m3": "m^3",
            "metal_volume_balance_m3_by_reaction.*": "m^3",
        },
        assumptions=(
            "Consumes a computed, complete, digest-pinned current-carrying Faradaic AssessmentResult and its exact request.",
            "Converts already-integrated per-branch/per-cell molar extents directly; it does not integrate current or apply Faraday's law a second time.",
            "Every upstream branch is either mapped as caller-reviewed net metal dissolution or explicitly excluded with digest-pinned disposition evidence.",
            "Only nonnegative net extents are accepted for mapped dissolution branches; reversals within a source interval are not identifiable from interval totals.",
            "Caller provides reaction-to-metal stoichiometry, molar mass, density and cell reactive areas; recession is a uniform cell-area average.",
        ),
        source_ids=(METHOD_SOURCE_ID, MAPPING_SOURCE_ID, DISPOSITION_SOURCE_ID),
        qualification="user_model",
        context_validator=_validate_context,
    ),)


def _validate_context(request: CreviceCurrentCarryingExtentMetalLossRequest, context: RunContext) -> None:
    upstream = request.current_carrying_result.context
    if (context.asset_id, context.location_id, context.time_basis) != (
        upstream.asset_id, upstream.location_id, upstream.time_basis
    ):
        raise ValueError("metal-loss context must match the upstream crevice asset, location and time basis")
