"""Remap immobile crevice solid inventories across an exact geometry boundary."""

from __future__ import annotations

import math
from typing import Literal

from pydantic import Field, model_validator

from .contracts import Calculation, Contract, canonical_digest
from .multiphase_kinetic_transport import CompetingSolidKineticTransport
from .registry import ModelSpec

MODEL_ID = "integration.crevice_solid_inventory_geometry_boundary_remap"
SOURCE_ID = "caller_crevice_solid_inventory_immobile_geometry_remap"
MAX_CELLS = 2000


class CreviceSolidInventoryGeometryRemapRequest(Contract):
    schema_version: Literal["matintegrity.crevice_solid_inventory_geometry_remap.v1"] = (
        "matintegrity.crevice_solid_inventory_geometry_remap.v1"
    )
    remap_id: str = Field(min_length=1)
    source_kinetic_campaign: CompetingSolidKineticTransport
    source_kinetic_result: dict
    source_kinetic_result_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    target_geometry_history: dict
    target_geometry_history_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    target_geometry_state_index: int = Field(ge=0)
    same_cell_solid_immobility_reviewed: bool
    exact_source_target_time_mapping_reviewed: bool
    reference_area_and_cell_volume_basis_reviewed: bool
    no_solid_creation_or_loss_during_remap_reviewed: bool

    @model_validator(mode="after")
    def validate_boundaries(self):
        if canonical_digest(self.source_kinetic_result) != self.source_kinetic_result_sha256:
            raise ValueError("source kinetic result digest mismatch")
        if canonical_digest(self.target_geometry_history) != self.target_geometry_history_sha256:
            raise ValueError("target geometry history digest mismatch")
        source = self.source_kinetic_result
        if (
            source.get("status") != "computed"
            or source.get("input_sha256") != canonical_digest(self.source_kinetic_campaign.model_dump(mode="json"))
            or source.get("campaign_id") != self.source_kinetic_campaign.campaign_id
            or source.get("physical_scope_id") != self.source_kinetic_campaign.physical_scope_id
            or not source.get("inventory_balance_within_declared_tolerance", False)
        ):
            raise ValueError("computed, closed source kinetic history for the exact campaign is required")
        history = self.target_geometry_history
        states = history.get("geometry_states")
        if history.get("status") != "computed" or not isinstance(states, list) or not states:
            raise ValueError("computed target geometry history is required")
        if self.target_geometry_state_index >= len(states):
            raise ValueError("target geometry state index is outside the source history")
        transport = self.source_kinetic_campaign.transport
        if transport.reference_cross_section_m2 is None or transport.cell_count > MAX_CELLS:
            raise ValueError("explicit reference area and bounded source transport geometry are required")
        return self


def remap_crevice_solid_inventory_at_geometry_boundary(
    request: CreviceSolidInventoryGeometryRemapRequest,
) -> Calculation:
    """Preserve each cell/phase solid amount and update its target volume concentration."""
    campaign = request.source_kinetic_campaign
    transport = campaign.transport
    source = request.source_kinetic_result
    history = request.target_geometry_history
    target_state = history["geometry_states"][request.target_geometry_state_index]
    source_times = source.get("elapsed_time_s")
    source_time = source_times[-1] if isinstance(source_times, list) and source_times else None
    target_time = target_state.get("elapsed_time_s")
    phase_ids = [row.solid_species_id for row in campaign.candidate_solid_phases]
    source_phase_ids = source.get("solid_phase_ids")
    base = {
        "remap_id": request.remap_id,
        "campaign_id": campaign.campaign_id,
        "physical_scope_id": campaign.physical_scope_id,
        "source_kinetic_result_sha256": request.source_kinetic_result_sha256,
        "target_geometry_history_sha256": request.target_geometry_history_sha256,
        "source_elapsed_time_s": source_time,
        "target_elapsed_time_s": target_time,
        "target_geometry_state_index": request.target_geometry_state_index,
        "solid_phase_ids": phase_ids,
    }
    review_names = (
        "same_cell_solid_immobility_reviewed",
        "exact_source_target_time_mapping_reviewed",
        "reference_area_and_cell_volume_basis_reviewed",
        "no_solid_creation_or_loss_during_remap_reviewed",
    )
    missing = [name for name in review_names if not getattr(request, name)]
    if missing:
        return Calculation(status="needs_data", values=base | {"missing_reviews": missing})
    if source_time != target_time:
        return Calculation(status="out_of_scope", values=base | {
            "reason": "source solid inventory time and target geometry time must match exactly",
        })
    if source_phase_ids != phase_ids:
        return Calculation(status="out_of_scope", values=base | {
            "reason": "source solid phase order differs from the typed kinetic campaign",
        })
    if history.get("cell_count") != transport.cell_count or tuple(history.get("cell_widths_m", ())) != tuple(
        transport.cell_widths_m or (transport.length_m / transport.cell_count,) * transport.cell_count
    ):
        return Calculation(status="out_of_scope", values=base | {
            "reason": "source kinetic cell grid and target geometry grid do not match",
        })
    if history.get("reference_cross_section_m2") != transport.reference_cross_section_m2:
        return Calculation(status="out_of_scope", values=base | {
            "reason": "source kinetic and target geometry reference cross sections differ",
        })

    states = source.get("solid_inventory_mol_m3_by_phase")
    if (
        not isinstance(states, list)
        or not states
        or not isinstance(source_times, list)
        or not source_times
        or source_times[-1] != source_time
    ):
        return Calculation(status="out_of_scope", values=base | {"reason": "source solid state history lacks the final campaign knot"})
    final_solid_state = states[-1]
    source_area = (
        list(transport.cell_cross_section_m2)
        if transport.cell_cross_section_m2 is not None
        else [transport.reference_cross_section_m2] * transport.cell_count
    )
    source_area_ratio = [area / transport.reference_cross_section_m2 for area in source_area]
    widths = list(transport.cell_widths_m or (transport.length_m / transport.cell_count,) * transport.cell_count)
    source_volume_per_area = [ratio * width for ratio, width in zip(source_area_ratio, widths, strict=True)]

    target_geometry = target_state.get("restricted_transport_geometry")
    target_areas = target_geometry.get("cell_cross_section_m2") if isinstance(target_geometry, dict) else None
    if (
        not isinstance(target_areas, list) or len(target_areas) != transport.cell_count
        or any(not isinstance(area, (int, float)) or isinstance(area, bool) or not math.isfinite(area) or area <= 0 for area in target_areas)
    ):
        return Calculation(status="out_of_scope", values=base | {"reason": "target geometry has no complete positive cell cross-section vector"})
    target_volume_per_area = [
        area / transport.reference_cross_section_m2 * width
        for area, width in zip(target_areas, widths, strict=True)
    ]
    if any(not math.isfinite(value) or value <= 0 for value in target_volume_per_area):
        return Calculation(status="out_of_scope", values=base | {"reason": "target cell liquid volumes per reference area are invalid"})

    if not isinstance(final_solid_state, dict) or set(final_solid_state) != set(phase_ids):
        return Calculation(status="out_of_scope", values=base | {"reason": "final solid inventory phase set is invalid"})
    areal_inventory: dict[str, list[float]] = {}
    target_concentration: dict[str, list[float]] = {}
    phase_closure: dict[str, dict[str, float]] = {}
    for phase_id in phase_ids:
        concentrations = final_solid_state[phase_id]
        if not isinstance(concentrations, list) or len(concentrations) != transport.cell_count:
            return Calculation(status="out_of_scope", values=base | {"failed_solid_phase_id": phase_id, "reason": "source solid field cell count is invalid"})
        amounts: list[float] = []
        mapped: list[float] = []
        for cell, (concentration, old_volume, new_volume) in enumerate(zip(
            concentrations, source_volume_per_area, target_volume_per_area, strict=True
        )):
            if isinstance(concentration, bool) or not isinstance(concentration, (int, float)) or not math.isfinite(concentration) or concentration < 0:
                return Calculation(status="out_of_scope", values=base | {"failed_solid_phase_id": phase_id, "failed_cell_index": cell, "reason": "source solid concentration is invalid"})
            amount = float(concentration) * old_volume
            new_concentration = amount / new_volume
            if not math.isfinite(amount) or not math.isfinite(new_concentration):
                return Calculation(status="out_of_scope", values=base | {"failed_solid_phase_id": phase_id, "failed_cell_index": cell, "reason": "solid inventory remap exceeds finite support"})
            amounts.append(amount)
            mapped.append(new_concentration)
        areal_inventory[phase_id] = amounts
        target_concentration[phase_id] = mapped
        before = math.fsum(amounts)
        after = math.fsum(value * volume for value, volume in zip(mapped, target_volume_per_area, strict=True))
        phase_closure[phase_id] = {
            "source_total_inventory_mol_m2": before,
            "target_total_inventory_mol_m2": after,
            "balance_residual_mol_m2": after - before,
        }

    return Calculation(values=base | {
        "status": "computed",
        "source_cell_volume_per_reference_area_m": source_volume_per_area,
        "target_cell_volume_per_reference_area_m": target_volume_per_area,
        "solid_inventory_mol_m2_by_phase": areal_inventory,
        "target_initial_solid_inventory_mol_m3_by_phase": target_concentration,
        "phase_inventory_balance_by_phase": phase_closure,
        "remap_basis": "same cell and phase solid amount is preserved across the geometry boundary; only concentration normalization changes with target liquid volume",
        "target_campaign_input_field": "CompetingSolidKineticTransport.initial_solid_inventory_mol_m3_by_phase",
        "interpretation_boundary": "This is an operator-split inventory remap at one exact geometry boundary. No phase reaction, cross-cell solid motion, deposit dissolution, precipitation or morphology update occurs during the remap.",
    })


def specifications() -> list[ModelSpec]:
    return [ModelSpec(
        model_id=MODEL_ID,
        input_type=CreviceSolidInventoryGeometryRemapRequest,
        evaluator=remap_crevice_solid_inventory_at_geometry_boundary,
        units={
            "source_elapsed_time_s": "s",
            "target_elapsed_time_s": "s",
            "source_cell_volume_per_reference_area_m": "m3/m2",
            "target_cell_volume_per_reference_area_m": "m3/m2",
            "solid_inventory_mol_m2_by_phase.*": "mol/m2",
            "target_initial_solid_inventory_mol_m3_by_phase.*": "mol/m3",
            "phase_inventory_balance_by_phase.*.balance_residual_mol_m2": "mol/m2",
        },
        assumptions=(
            "The source kinetic result is computed, digest-bound, closed within its declared tolerance, and uses the typed fixed-geometry campaign.",
            "At the exact boundary, each solid phase remains in the same axial cell with no creation, loss or cross-cell redistribution.",
            "Source and target transport use the same cell grid and reference cross section; target solid concentration is inventory per reference area divided by target liquid volume per reference area.",
            "The target geometry is supplied as a computed geometry-history state with complete positive cell cross sections.",
            "This remap is sequential and does not perform a coupled kinetic/geometry/transport solve.",
        ),
        source_ids=(SOURCE_ID,),
        qualification="user_model",
    )]
