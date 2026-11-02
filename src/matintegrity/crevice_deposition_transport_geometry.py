"""Adapt deposition-derived aperture snapshots to the crevice transport geometry contract."""

from __future__ import annotations

import math
from typing import Literal

from pydantic import Field, model_validator

from .contracts import Calculation, Contract, canonical_digest
from .crevice_deposition_aperture_history import CreviceDepositionApertureHistoryRequest
from .registry import ModelSpec

MODEL_ID = "integration.crevice_deposition_transport_geometry"
SOURCE_ID = "caller_deposition_aperture_to_transport_geometry_mapping"
MAX_CELLS = 2000
MAX_STATES = 5001


class CreviceDepositionTransportGeometryRequest(Contract):
    schema_version: Literal["matintegrity.crevice_deposition_transport_geometry.v1"] = (
        "matintegrity.crevice_deposition_transport_geometry.v1"
    )
    geometry_id: str = Field(min_length=1)
    deposition_aperture_request: CreviceDepositionApertureHistoryRequest
    deposition_aperture_result: dict
    deposition_aperture_result_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    transport_reference_cross_section_m2: float = Field(gt=0)
    transport_reactive_broad_face_count: Literal[1, 2]
    mean_aperture_represents_transport_cell_reviewed: bool
    transport_reference_cross_section_basis_reviewed: bool
    face_area_center_interpolation_and_boundary_extrapolation_reviewed: bool
    reactive_transport_wall_area_mapping_reviewed: bool
    operator_split_fixed_geometry_segments_reviewed: bool

    @model_validator(mode="after")
    def validate_lineage_and_budget(self):
        if canonical_digest(self.deposition_aperture_result) != self.deposition_aperture_result_sha256:
            raise ValueError("deposition aperture result digest mismatch")
        result = self.deposition_aperture_result
        if result.get("status") != "computed":
            raise ValueError("computed deposition aperture history is required")
        values = result.get("values")
        values = values if isinstance(values, dict) else result
        expected = canonical_digest(self.deposition_aperture_request.model_dump(mode="json"))
        if (
            values.get("input_sha256") != expected
            or values.get("physical_scope_id") != self.deposition_aperture_request.physical_scope_id
        ):
            raise ValueError("deposition aperture result is not bound to the supplied typed request")
        knots = values.get("knots")
        if not isinstance(knots, list) or len(knots) < 2 or len(knots) > MAX_STATES:
            raise ValueError("deposition result needs 2..5001 exact geometry snapshots")
        cell_count = len(self.deposition_aperture_request.initial_aperture_m)
        if cell_count < 2 or cell_count > MAX_CELLS:
            raise ValueError("transport geometry requires 2..2000 cells")
        return self


def evaluate_crevice_deposition_transport_geometry(
    request: CreviceDepositionTransportGeometryRequest,
) -> Calculation:
    """Build transport-compatible cross-section states from reviewed mean gaps."""
    source_values = request.deposition_aperture_result.get("values", request.deposition_aperture_result)
    source_knots = source_values["knots"]
    source_digest = request.deposition_aperture_result_sha256
    deposition_request = request.deposition_aperture_request
    widths = list(deposition_request.cell_length_m)
    transverse_width = deposition_request.transverse_width_m
    cell_count = len(widths)
    request_sha = canonical_digest(request.model_dump(mode="json"))
    base = {
        "geometry_id": request.geometry_id,
        "physical_scope_id": deposition_request.physical_scope_id,
        "input_sha256": request_sha,
        "deposition_aperture_result_sha256": source_digest,
        "transport_reference_cross_section_m2": request.transport_reference_cross_section_m2,
        "transport_reactive_broad_face_count": request.transport_reactive_broad_face_count,
    }
    required = (
        "mean_aperture_represents_transport_cell_reviewed",
        "transport_reference_cross_section_basis_reviewed",
        "face_area_center_interpolation_and_boundary_extrapolation_reviewed",
        "reactive_transport_wall_area_mapping_reviewed",
        "operator_split_fixed_geometry_segments_reviewed",
    )
    missing = [name for name in required if not getattr(request, name)]
    if missing:
        return Calculation(status="needs_data", values=base | {"missing_reviews": missing})

    states: list[dict] = []
    for knot_index, source_knot in enumerate(source_knots):
        apertures = source_knot.get("equivalent_mean_remaining_aperture_m_by_cell")
        time_s = source_knot.get("elapsed_time_s")
        if (
            not isinstance(apertures, list) or len(apertures) != cell_count
            or isinstance(time_s, bool) or not isinstance(time_s, (int, float)) or not math.isfinite(time_s)
        ):
            return Calculation(status="out_of_scope", values=base | {
                "committed_state_count": len(states), "geometry_states": states,
                "failed_knot_index": knot_index,
                "failure_reason": "source knot lacks finite exact time or a complete mean-gap cell vector",
            })
        if any(
            isinstance(value, bool) or not isinstance(value, (int, float))
            or not math.isfinite(value) or value <= 0
            for value in apertures
        ):
            return Calculation(status="out_of_scope", values=base | {
                "committed_state_count": len(states), "geometry_states": states,
                "failed_knot_index": knot_index,
                "failure_reason": "remaining mean aperture must be finite and strictly positive",
            })
        cross_sections = [float(aperture) * transverse_width for aperture in apertures]
        face_cross_sections = [cross_sections[0]]
        for index in range(1, cell_count):
            left_half = widths[index - 1] / 2.0
            right_half = widths[index] / 2.0
            face_cross_sections.append(
                (cross_sections[index - 1] * right_half + cross_sections[index] * left_half)
                / (left_half + right_half)
            )
        face_cross_sections.append(cross_sections[-1])
        volumes = [area * width for area, width in zip(cross_sections, widths, strict=True)]
        wall_areas = [
            request.transport_reactive_broad_face_count * transverse_width * width
            for width in widths
        ]
        all_geometry_numbers = cross_sections + face_cross_sections + volumes + wall_areas
        if not all(math.isfinite(value) and value > 0 for value in all_geometry_numbers):
            return Calculation(status="out_of_scope", values=base | {
                "committed_state_count": len(states), "geometry_states": states,
                "failed_knot_index": knot_index,
                "failure_reason": "mapped slit geometry exceeds finite positive support",
            })
        wall_area_density = [area / volume for area, volume in zip(wall_areas, volumes, strict=True)]
        transport_geometry = {
            "cell_count": cell_count,
            "length_m": math.fsum(widths),
            "cell_widths_m": widths,
            "cell_cross_section_m2": cross_sections,
            "face_cross_section_m2": face_cross_sections,
            "reference_cross_section_m2": request.transport_reference_cross_section_m2,
            "wall_area_per_volume_m2_m3": wall_area_density,
        }
        states.append({
            "elapsed_time_s": float(time_s),
            "cell_aperture_m": [float(value) for value in apertures],
            "axial_cross_section_m2": cross_sections,
            "cell_cross_section_m2": cross_sections,
            "face_cross_section_m2": face_cross_sections,
            "cell_volume_m3": volumes,
            "reactive_broad_wall_area_m2": wall_areas,
            "wall_area_per_volume_m2_m3": wall_area_density,
            "source_knot_index": knot_index,
            "source_solid_volume_result_sha256": source_knot.get("solid_volume_result_sha256"),
            "source_equivalent_mean_aperture_loss_m_by_cell": source_knot.get("equivalent_mean_aperture_loss_m_by_cell"),
            "restricted_transport_geometry": transport_geometry,
        })
    if states[0]["elapsed_time_s"] != 0.0 or any(
        right["elapsed_time_s"] <= left["elapsed_time_s"] for left, right in zip(states[:-1], states[1:])
    ):
        return Calculation(status="out_of_scope", values=base | {
            "committed_state_count": 0, "geometry_states": [],
            "failure_reason": "source geometry clock must start at zero and increase strictly",
        })
    geometry_history = {
        "geometry_id": request.geometry_id,
        "status": "computed",
        "source_deposition_aperture_result_sha256": source_digest,
        "cell_count": cell_count,
        "cell_widths_m": widths,
        "length_m": math.fsum(widths),
        "transverse_width_m": transverse_width,
        "reference_cross_section_m2": request.transport_reference_cross_section_m2,
        "reactive_broad_face_count": request.transport_reactive_broad_face_count,
        "geometry_states": states,
        "basis": "Caller-reviewed mean-aperture mapping of deposition-derived solid-volume history to fixed-geometry operator-split transport states. Face areas use center-linear interpolation and constant boundary extrapolation.",
    }
    return Calculation(values=base | {
        "status": "computed",
        "geometry_history": geometry_history,
        "geometry_history_sha256": canonical_digest(geometry_history),
        "state_count": len(states),
        "downstream_contract": "CreviceGeometryTransportCampaign.geometry_history",
        "interpretation_boundary": "This bridge formats an already computed mean-gap history for sequential fixed-geometry transport segments. It does not solve coupled precipitation, geometry, flow and chemistry or resolve within-cell coverage morphology.",
    })


def specifications() -> list[ModelSpec]:
    return [ModelSpec(
        model_id=MODEL_ID,
        input_type=CreviceDepositionTransportGeometryRequest,
        evaluator=evaluate_crevice_deposition_transport_geometry,
        units={
            "transport_reference_cross_section_m2": "m2",
            "geometry_history.geometry_states[].elapsed_time_s": "s",
            "geometry_history.geometry_states[].cell_aperture_m": "m",
            "geometry_history.geometry_states[].cell_cross_section_m2": "m2",
            "geometry_history.geometry_states[].face_cross_section_m2": "m2",
            "geometry_history.geometry_states[].cell_volume_m3": "m3",
            "geometry_history.geometry_states[].wall_area_per_volume_m2_m3": "1/m",
        },
        assumptions=(
            "Only the upstream volume-conserving equivalent mean aperture is forwarded; it is treated as uniform within each transport cell after explicit caller review.",
            "The transport reference cross section and reactive broad-face count are caller declarations and must match the downstream transport request.",
            "Cell and face areas use slit cross section = mean aperture times transverse width; interior face areas use linear interpolation between cell centers and end faces use nearest-cell constant extrapolation.",
            "Each state is prepared for a subsequent fixed-geometry operator-split transport campaign; the bridge does not iterate deposition and transport together.",
            "Coverage heterogeneity, deposit morphology, porosity, adhesion, transient momentum and chemistry/geometry feedback within a time segment are not resolved.",
        ),
        source_ids=(SOURCE_ID,),
        qualification="user_model",
    )]
