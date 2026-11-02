from __future__ import annotations

import math
from typing import Literal

from pydantic import Field, model_validator

from .contracts import Calculation, Contract, canonical_digest
from .registry import ModelSpec
from .wet_co2_cylindrical_scale_geometry import (
    WetCo2CylindricalScaleGeometryHistory,
)

MODEL_ID = "integration.wet_co2_cylindrical_scale_kinetics_to_geometry"
GEOMETRY_SOURCE_ID = "caller_cylindrical_scale_geometry_record"
KINETICS_SOURCE_ID = "caller_scale_thickness_kinetics_history"
BRIDGE_SOURCE_ID = "cylindrical_annular_layer_inventory_geometry_handoff"


class WetCo2CylindricalScaleKineticsGeometryHandoff(Contract):
    """Convert exact-knot phase thickness outputs into cylindrical phase inventories."""

    schema_version: Literal["matintegrity.wet_co2_cylindrical_scale_kinetics_geometry_handoff.v1"] = (
        "matintegrity.wet_co2_cylindrical_scale_kinetics_geometry_handoff.v1"
    )
    assessment_id: str = Field(min_length=1, max_length=160)
    geometry: WetCo2CylindricalScaleGeometryHistory
    phase_kinetics_results: dict[str, Calculation] = Field(min_length=1, max_length=32)
    layer_order_steel_to_bore: tuple[str, ...] = Field(min_length=1, max_length=32)
    exact_knot_mapping_reviewed: bool
    dense_contiguous_layers_reviewed: bool

    @model_validator(mode="after")
    def validate_phase_mapping(self):
        expected = {row.phase_id for row in self.geometry.phases}
        if set(self.phase_kinetics_results) != expected or set(self.layer_order_steel_to_bore) != expected:
            raise ValueError("provide exactly one kinetics result and one radial order entry for each geometry phase")
        if len(self.layer_order_steel_to_bore) != len(set(self.layer_order_steel_to_bore)):
            raise ValueError("radial layer order must not repeat phase IDs")
        if any(result.status != "computed" for result in self.phase_kinetics_results.values()):
            raise ValueError("each phase kinetics input must be a computed Calculation")
        return self


def _thickness_history(result: Calculation) -> list[dict]:
    """Accept direct surface kinetics results and the cylindrical saturation adapter envelope."""
    values = result.values
    nested = values.get("surface_scale_kinetics")
    if isinstance(nested, dict):
        values = nested.get("values", {})
    rows = values.get("scale_history")
    if not isinstance(rows, list) or not rows:
        raise ValueError("kinetics result must contain a non-empty scale_history")
    return rows


def evaluate_wet_co2_cylindrical_scale_kinetics_geometry_handoff(
    request: WetCo2CylindricalScaleKineticsGeometryHandoff,
) -> Calculation:
    """Map phase thickness histories to exact annular volumes, inventories and bore dimensions."""
    request_digest = canonical_digest(request.model_dump(mode="json"))
    base = {
        "assessment_id": request.assessment_id,
        "asset_id": request.geometry.asset_id,
        "location_id": request.geometry.location_id,
        "model_id": MODEL_ID,
        "input_sha256": request_digest,
        "geometry_record_sha256": request.geometry.geometry_record_sha256,
        "source_ids": [GEOMETRY_SOURCE_ID, KINETICS_SOURCE_ID, BRIDGE_SOURCE_ID],
        "phase_kinetics_result_sha256": {
            phase_id: canonical_digest(result.model_dump(mode="json"))
            for phase_id, result in request.phase_kinetics_results.items()
        },
    }
    if not request.exact_knot_mapping_reviewed or not request.dense_contiguous_layers_reviewed:
        return Calculation(status="needs_data", values=base | {
            "reason": "exact_knot_and_dense_contiguous_layer_review_required",
        })
    geometry = request.geometry
    phase_by_id = {phase.phase_id: phase for phase in geometry.phases}
    reference_times = tuple(row.time_s for row in geometry.history)
    phase_rows: dict[str, list[dict]] = {}
    try:
        for phase_id, result in request.phase_kinetics_results.items():
            rows = _thickness_history(result)
            times = tuple(float(row["time_s"]) for row in rows)
            if times != reference_times:
                raise ValueError(f"{phase_id}: phase thickness times must exactly match cylindrical geometry knots")
            if any("scale_thickness_m" not in row or not math.isfinite(float(row["scale_thickness_m"]))
                   or float(row["scale_thickness_m"]) < 0.0 for row in rows):
                raise ValueError(f"{phase_id}: thickness history must be finite and nonnegative")
            phase_rows[phase_id] = rows
    except (KeyError, TypeError, ValueError, OverflowError) as exc:
        return Calculation(status="needs_data", values=base | {
            "reason": "phase_thickness_history_invalid_or_not_exactly_aligned",
            "detail": str(exc),
        })

    outer = geometry.outer_radius_m
    inner0 = geometry.initial_inner_radius_m
    result_rows = []
    for index, knot in enumerate(geometry.history):
        steel_inner = inner0 + knot.wall_recession_m
        wall_remaining = outer - steel_inner
        radius_cursor = steel_inner
        inventories = {}
        phase_volumes = {}
        for phase_id in request.layer_order_steel_to_bore:
            thickness = float(phase_rows[phase_id][index]["scale_thickness_m"])
            next_inner = radius_cursor - thickness
            if next_inner <= 0.0 or next_inner > radius_cursor:
                return Calculation(status="out_of_scope", values=base | {
                    "reason": "layer_thickness_exceeds_positive_cylindrical_radius",
                    "failed_knot_index": index,
                    "failed_time_s": knot.time_s,
                    "phase_id": phase_id,
                })
            volume_per_m = math.pi * (radius_cursor * radius_cursor - next_inner * next_inner)
            phase = phase_by_id[phase_id]
            moles_per_m = volume_per_m / phase.molar_volume_m3_mol
            if not math.isfinite(moles_per_m) or moles_per_m < 0.0:
                return Calculation(status="out_of_scope", values=base | {
                    "reason": "annular_phase_inventory_outside_finite_support",
                    "failed_knot_index": index,
                    "phase_id": phase_id,
                })
            inventories[phase_id] = moles_per_m
            phase_volumes[phase_id] = volume_per_m * geometry.segment_length_m
            radius_cursor = next_inner
        bore = radius_cursor
        if wall_remaining <= 0.0 or not math.isfinite(bore) or bore <= 0.0 or bore > steel_inner:
            return Calculation(status="out_of_scope", values=base | {
                "reason": "wall_recession_or_layer_stack_exceeds_supported_pipe_geometry",
                "failed_knot_index": index,
                "failed_time_s": knot.time_s,
                "wall_remaining_m": wall_remaining,
            })
        scale_volume_per_m = math.pi * (steel_inner * steel_inner - bore * bore)
        inventory_volume_per_m = math.fsum(
            inventories[phase_id] * phase_by_id[phase_id].molar_volume_m3_mol
            for phase_id in inventories
        )
        if not math.isclose(scale_volume_per_m, inventory_volume_per_m, rel_tol=1e-11, abs_tol=1e-14):
            return Calculation(status="out_of_scope", values=base | {
                "reason": "annular_phase_volume_closure_failed",
                "failed_knot_index": index,
            })
        result_rows.append({
            "time_s": knot.time_s,
            "wall_recession_m": knot.wall_recession_m,
            "wall_remaining_m": wall_remaining,
            "steel_inner_radius_m": steel_inner,
            "bore_radius_m": bore,
            "scale_thickness_equivalent_m": steel_inner - bore,
            "bore_flow_area_m2": math.pi * bore * bore,
            "bore_wetted_perimeter_m": 2.0 * math.pi * bore,
            "steel_cross_section_area_m2": math.pi * (outer * outer - steel_inner * steel_inner),
            "scale_volume_per_axial_metre_m2": scale_volume_per_m,
            "scale_volume_m3": scale_volume_per_m * geometry.segment_length_m,
            "scale_phase_volume_m3_by_phase": phase_volumes,
            "phase_inventory_mol_m_by_phase": inventories,
            "radial_layer_order_steel_to_bore": list(request.layer_order_steel_to_bore),
        })
    return Calculation(values=base | {
        "status": "computed",
        "knot_count": len(result_rows),
        "outer_radius_m": outer,
        "segment_length_m": geometry.segment_length_m,
        "history": result_rows,
        "geometry_handoff": "phase_kinetics_thickness_to_exact_annular_phase_inventory.v1",
        "limitations": [
            "Each input phase thickness is treated as a dense, contiguous radial layer in the explicitly supplied order from steel toward bore.",
            "Wall recession remains caller supplied; no electrochemical rate, transport, precipitation law, or geometry feedback is solved.",
            "The calculation consumes exact knots only and does not interpolate phase kinetics or create missing phases.",
            "Axisymmetric uniformity, layer ordering, density/porosity effects, adhesion, cracking, spallation, and circumferential heterogeneity require external review.",
        ],
    })


def specifications() -> list[ModelSpec]:
    return [ModelSpec(
        model_id=MODEL_ID,
        input_type=WetCo2CylindricalScaleKineticsGeometryHandoff,
        evaluator=evaluate_wet_co2_cylindrical_scale_kinetics_geometry_handoff,
        units={
            "history[].time_s": "s",
            "history[].phase_inventory_mol_m_by_phase.*": "mol/m",
            "history[].scale_phase_volume_m3_by_phase.*": "m^3",
            "history[].scale_thickness_equivalent_m": "m",
            "history[].bore_radius_m": "m",
        },
        assumptions=(
            "Caller phase thickness histories and wall recession are exact-knot aligned and independently reviewed.",
            "Each dense layer occupies an annulus in caller-declared steel-to-bore order.",
            "Annular inventory is computed from exact cylindrical shell volume divided by caller phase molar volume.",
        ),
        source_ids=(GEOMETRY_SOURCE_ID, KINETICS_SOURCE_ID, BRIDGE_SOURCE_ID),
        qualification="user_model",
    )]
