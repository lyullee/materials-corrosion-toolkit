"""Expose spatial transport output as an explicit volume-averaged chemistry handoff."""

from __future__ import annotations

import math
from typing import Any, Literal

import numpy as np
from pydantic import Field, model_validator

from .contracts import Calculation, Contract, canonical_digest
from .crevice_campaign import CreviceGeometryTransportCampaign
from .registry import ModelSpec


class CreviceTransportCompositionBridge(Contract):
    """Bind campaign output and calculate cell-volume-weighted knot summaries.

    Geometry discontinuities retain both their left/pre-remap and
    right/post-remap state. This is a summary handoff, not a local cell
    chemistry solver or an automatic mass-action input conversion.
    """

    schema_version: Literal["matintegrity.crevice_transport_composition_bridge.v1"] = (
        "matintegrity.crevice_transport_composition_bridge.v1"
    )
    assessment_id: str = Field(min_length=1)
    campaign: CreviceGeometryTransportCampaign
    campaign_result: dict[str, Any]
    campaign_result_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    cell_volume_weighted_bulk_summary_reviewed: bool
    local_cell_heterogeneity_must_be_preserved_reviewed: bool
    no_automatic_equilibrium_or_kinetic_interpretation_reviewed: bool

    @model_validator(mode="after")
    def validate_result_identity(self):
        if canonical_digest(self.campaign_result) != self.campaign_result_sha256:
            raise ValueError("transport campaign result digest mismatch")
        if self.campaign_result.get("status") != "computed":
            raise ValueError("a computed geometry-transport campaign is required")
        if self.campaign_result.get("campaign_id") != self.campaign.campaign_id:
            raise ValueError("campaign result identity differs from the pinned request")
        if self.campaign_result.get("geometry_id") != self.campaign.geometry_id:
            raise ValueError("campaign result geometry differs from the pinned request")
        if self.campaign_result.get("geometry_history_sha256") != self.campaign.geometry_history_sha256:
            raise ValueError("campaign result geometry digest differs from the pinned request")
        if self.campaign_result.get("campaign_input_sha256") != canonical_digest(
            self.campaign.model_dump(mode="json")
        ):
            raise ValueError("campaign result input digest differs from the supplied request")
        return self


def summarize_crevice_transport_composition(
    request: CreviceTransportCompositionBridge,
) -> Calculation:
    """Summarize concentration per exact transport output knot and geometry side."""
    missing = [
        name
        for name in (
            "cell_volume_weighted_bulk_summary_reviewed",
            "local_cell_heterogeneity_must_be_preserved_reviewed",
            "no_automatic_equilibrium_or_kinetic_interpretation_reviewed",
        )
        if not getattr(request, name)
    ]
    base = {
        "assessment_id": request.assessment_id,
        "campaign_id": request.campaign.campaign_id,
        "campaign_result_sha256": request.campaign_result_sha256,
        "campaign_input_sha256": request.campaign_result["campaign_input_sha256"],
        "geometry_history_sha256": request.campaign.geometry_history_sha256,
        "geometry_id": request.campaign.geometry_id,
        "representation": "cell_volume_weighted_bulk_summary_with_explicit_geometry_side",
        "automatic_mass_action_input": False,
    }
    if missing:
        return Calculation(status="needs_data", values=base | {"missing_reviews": missing})

    states = request.campaign.geometry_history["geometry_states"]
    widths = np.asarray(request.campaign.geometry_history["cell_widths_m"], dtype=float)
    species_ids = request.campaign.base_transport_request.species_ids
    segments = request.campaign_result.get("segment_results")
    if not isinstance(segments, list) or len(segments) != len(states) - 1:
        return Calculation(status="out_of_scope", values=base | {
            "reason": "campaign segments do not match the exact geometry interval count"
        })
    remaps = request.campaign_result.get("geometry_boundary_inventory_remaps")
    if not isinstance(remaps, list) or len(remaps) != len(segments) - 1:
        return Calculation(status="out_of_scope", values=base | {
            "reason": "geometry-boundary inventory remaps do not match internal geometry knots"
        })
    rows: list[dict[str, Any]] = []
    expected_start = 0.0
    for segment_index, (segment, left_state, right_state) in enumerate(
        zip(segments, states[:-1], states[1:], strict=True)
    ):
        if segment.get("segment_index") != segment_index:
            return Calculation(status="out_of_scope", values=base | {
                "failed_segment_index": segment_index,
                "reason": "segment indices are not contiguous",
            })
        start_s = float(left_state["elapsed_time_s"])
        end_s = float(right_state["elapsed_time_s"])
        if start_s != expected_start or segment.get("global_start_time_s") != start_s or segment.get(
            "global_end_time_s"
        ) != end_s:
            return Calculation(status="out_of_scope", values=base | {
                "failed_segment_index": segment_index,
                "reason": "segment clock does not coincide with the pinned geometry clock",
            })
        geometry = left_state["restricted_transport_geometry"]
        area = np.asarray(geometry["cell_cross_section_m2"], dtype=float)
        volume = area * widths
        if volume.shape != (len(widths),) or not np.isfinite(volume).all() or np.any(volume <= 0.0):
            return Calculation(status="out_of_scope", values=base | {
                "failed_segment_index": segment_index,
                "reason": "cell volumes are outside positive finite support",
            })
        solver_result = segment.get("result")
        if not isinstance(solver_result, dict) or solver_result.get("status") != "computed":
            return Calculation(status="out_of_scope", values=base | {
                "failed_segment_index": segment_index,
                "reason": "a segment lacks computed transport rows",
            })
        local_times = solver_result.get("output_times_s")
        fields = np.asarray(solver_result.get("concentration_mol_m3"), dtype=float)
        if (
            not isinstance(local_times, list)
            or len(local_times) < 2
            or fields.shape != (len(local_times), len(species_ids), len(widths))
            or not np.isfinite(fields).all()
            or np.any(fields < 0.0)
        ):
            return Calculation(status="out_of_scope", values=base | {
                "failed_segment_index": segment_index,
                "reason": "segment concentration array has invalid dimensions or values",
            })
        global_times = [start_s + float(value) for value in local_times]
        if global_times[0] != start_s or global_times[-1] != end_s or any(
            b <= a for a, b in zip(global_times[:-1], global_times[1:], strict=True)
        ):
            return Calculation(status="out_of_scope", values=base | {
                "failed_segment_index": segment_index,
                "reason": "segment output clock is not an exact increasing geometry bracket",
            })
        for local_index, (time_s, field) in enumerate(zip(global_times, fields, strict=True)):
            if segment_index > 0 and local_index == 0:
                # The prior segment's explicit right-side remap record is the
                # unique representation of this geometry boundary state.
                continue
            # Preserve the left and right states at a geometry jump instead of
            # silently choosing one concentration basis for the same instant.
            side: Literal["initial_or_interior", "left_pre_remap", "right_post_remap", "final_state"]
            if local_index == len(global_times) - 1:
                side = "final_state" if segment_index == len(segments) - 1 else "left_pre_remap"
            else:
                side = "initial_or_interior"
            cell_moles = field * volume[None, :]
            total_volume = float(math.fsum(float(value) for value in volume))
            moles = np.sum(cell_moles, axis=1)
            bulk = moles / total_volume
            if not np.isfinite(bulk).all() or not np.isfinite(moles).all() or np.any(moles < 0.0):
                return Calculation(status="out_of_scope", values=base | {
                    "failed_segment_index": segment_index,
                    "failed_local_output_index": local_index,
                    "reason": "volume-weighted concentration exceeded finite support",
                })
            rows.append({
                "time_s": time_s,
                "geometry_side": side,
                "segment_index": segment_index,
                "local_output_index": local_index,
                "geometry_state_sha256": canonical_digest(left_state),
                "cell_volume_m3": volume.tolist(),
                "total_solution_volume_m3": total_volume,
                "species_ids": list(species_ids),
                "cell_concentration_mol_m3": field.tolist(),
                "cell_inventory_mol": cell_moles.tolist(),
                "total_inventory_mol": moles.tolist(),
                "volume_weighted_bulk_concentration_mol_m3": bulk.tolist(),
                "spatial_variation_preserved_in_cells": True,
            })
        if segment_index < len(segments) - 1:
            remap = remaps[segment_index]
            expected_from = canonical_digest(left_state)
            expected_to = canonical_digest(right_state)
            if (
                remap.get("elapsed_time_s") != end_s
                or remap.get("from_geometry_state_sha256") != expected_from
                or remap.get("to_geometry_state_sha256") != expected_to
            ):
                return Calculation(status="out_of_scope", values=base | {
                    "failed_segment_index": segment_index,
                    "reason": "geometry-boundary remap time or source/target state digest differs from the exact campaign interval",
                })
            remapped = np.asarray(remap.get("post_remap_cell_concentration_mol_m3"), dtype=float)
            if remapped.shape != (len(species_ids), len(widths)) or not np.isfinite(remapped).all() or np.any(remapped < 0.0):
                return Calculation(status="out_of_scope", values=base | {
                    "failed_segment_index": segment_index,
                    "reason": "geometry-boundary remap is missing or invalid",
                })
            next_geometry = right_state["restricted_transport_geometry"]
            next_volume = np.asarray(next_geometry["cell_cross_section_m2"], dtype=float) * widths
            if not np.isfinite(next_volume).all() or np.any(next_volume <= 0.0):
                return Calculation(status="out_of_scope", values=base | {
                    "failed_segment_index": segment_index,
                    "reason": "next-interval cell volume is invalid",
                })
            moles = np.sum(remapped * next_volume[None, :], axis=1)
            total_volume = float(math.fsum(float(value) for value in next_volume))
            rows.append({
                "time_s": end_s,
                "geometry_side": "right_post_remap",
                "segment_index": segment_index + 1,
                "local_output_index": 0,
                "geometry_state_sha256": canonical_digest(right_state),
                "cell_volume_m3": next_volume.tolist(),
                "total_solution_volume_m3": total_volume,
                "species_ids": list(species_ids),
                "cell_concentration_mol_m3": remapped.tolist(),
                "cell_inventory_mol": (remapped * next_volume[None, :]).tolist(),
                "total_inventory_mol": moles.tolist(),
                "volume_weighted_bulk_concentration_mol_m3": (moles / total_volume).tolist(),
                "spatial_variation_preserved_in_cells": True,
            })
        expected_start = end_s
    return Calculation(values=base | {
        "status": "computed",
        "species_ids": list(species_ids),
        "knot_summary_count": len(rows),
        "knot_summaries": rows,
        "interpretation_boundary": "Volume-weighted mixing is caller-reviewed bookkeeping only; use local cell states where reaction/transport gradients matter.",
        "not_inferred": ["equilibrium", "reaction rates", "phase changes", "corrosion rate", "acceptance", "risk probability"],
    })


def specifications() -> list[ModelSpec]:
    return [ModelSpec(
        model_id="integration.crevice_transport_volume_weighted_composition",
        input_type=CreviceTransportCompositionBridge,
        evaluator=summarize_crevice_transport_composition,
        units={
            "knot_summaries[].time_s": "s",
            "knot_summaries[].cell_volume_m3": "m3",
            "knot_summaries[].total_solution_volume_m3": "m3",
            "knot_summaries[].cell_concentration_mol_m3": "mol/m3",
            "knot_summaries[].cell_inventory_mol": "mol",
            "knot_summaries[].total_inventory_mol": "mol",
            "knot_summaries[].volume_weighted_bulk_concentration_mol_m3": "mol/m3",
        },
        assumptions=(
            "Only a computed transport result whose digest is bound to the exact campaign request and geometry history is accepted.",
            "Cell-volume-weighted concentration is a caller-reviewed summary and preserves the underlying cell values and inventory in every row; geometry boundaries retain left and right records.",
            "This output is not automatically accepted by mass-action/speciation APIs and does not infer equilibrium, reaction, phase change, corrosion, acceptance or probability.",
        ),
        source_ids=("caller_crevice_transport_volume_weighted_composition_handoff",),
        qualification="user_model",
    )]
