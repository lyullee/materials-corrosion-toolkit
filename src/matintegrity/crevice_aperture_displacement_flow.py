"""Kinematic displacement-flow ledger induced by a pinned slit volume history."""

from __future__ import annotations

import math
from typing import Any, Literal

from pydantic import Field, model_validator

from .contracts import Calculation, Contract, Nonnegative, RunContext, canonical_digest
from .registry import ModelSpec

MODEL_ID = "degradation.crevice_aperture_displacement_flow"
SOURCE_ID = "caller_crevice_aperture_displacement_flow_continuity"


def _payload(source: dict[str, Any]) -> dict[str, Any]:
    nested = source.get("values")
    return nested if isinstance(nested, dict) else source


class CreviceApertureDisplacementFlowRequest(Contract):
    """Convert exact geometry-volume increments to 1-D incompressible flow."""

    schema_version: Literal["matintegrity.crevice_aperture_displacement_flow.v1"] = (
        "matintegrity.crevice_aperture_displacement_flow.v1"
    )
    history_id: str = Field(min_length=1)
    asset_id: str = Field(min_length=1)
    location_id: str = Field(min_length=1)
    time_basis: str = Field(min_length=1)
    geometry_id: str = Field(min_length=1)
    geometry_history_result: dict[str, Any]
    geometry_history_result_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    blind_end_single_mouth_reviewed: bool
    incompressible_liquid_reviewed: bool
    one_dimensional_cellwise_continuity_reviewed: bool
    linear_cell_volume_change_between_knots_reviewed: bool
    displacement_flow_only_interpretation_reviewed: bool

    @model_validator(mode="after")
    def validate_source_geometry(self):
        source = self.geometry_history_result
        if canonical_digest(source) != self.geometry_history_result_sha256:
            raise ValueError("complete geometry-history result digest mismatch")
        values = _payload(source)
        status = source.get("status", values.get("status"))
        if status != "computed":
            raise ValueError("a complete computed aperture-history result is required")
        if values.get("geometry_id") != self.geometry_id:
            raise ValueError("pinned geometry-history identity differs from the requested geometry")
        widths = values.get("cell_widths_m")
        width = values.get("transverse_width_m")
        states = values.get("geometry_states")
        if (
            not isinstance(widths, list) or not widths
            or isinstance(width, bool) or not isinstance(width, (int, float))
            or not math.isfinite(width) or width <= 0
            or not isinstance(states, list) or len(states) < 2 or len(states) > 5001
        ):
            raise ValueError("geometry result must contain cell widths, transverse width and a bounded state history")
        if any(
            isinstance(value, bool) or not isinstance(value, (int, float))
            or not math.isfinite(value) or value <= 0
            for value in widths
        ):
            raise ValueError("all geometry cell widths must be finite and positive")
        if (len(states) - 1) * len(widths) > 1_000_000:
            raise ValueError("geometry history cell-interval product exceeds the bounded ledger limit")
        previous_time = None
        cell_count = len(widths)
        for index, state in enumerate(states):
            if not isinstance(state, dict):
                raise ValueError("each geometry state must be an object")
            time_s = state.get("elapsed_time_s")
            apertures = state.get("cell_aperture_m")
            volumes = state.get("cell_volume_m3")
            face_areas = state.get("face_cross_section_m2")
            if (
                isinstance(time_s, bool) or not isinstance(time_s, (int, float))
                or not math.isfinite(time_s) or time_s < 0
                or not isinstance(apertures, list) or len(apertures) != cell_count
                or not isinstance(volumes, list) or len(volumes) != cell_count
                or not isinstance(face_areas, list) or len(face_areas) != cell_count + 1
            ):
                raise ValueError("geometry state clock, cell arrays or face-area array are misaligned")
            if index == 0 and time_s != 0.0:
                raise ValueError("aperture history must start at elapsed time zero")
            if previous_time is not None and time_s <= previous_time:
                raise ValueError("geometry state times must increase strictly in source order")
            previous_time = float(time_s)
            if any(
                isinstance(value, bool) or not isinstance(value, (int, float))
                or not math.isfinite(value) or value <= 0
                for value in (*apertures, *volumes, *face_areas)
            ):
                raise ValueError("apertures, cell volumes and face areas must be finite and positive")
            for cell_index, (aperture, volume, cell_width) in enumerate(zip(
                apertures, volumes, widths, strict=True
            )):
                expected_volume = float(aperture) * float(width) * float(cell_width)
                if not math.isfinite(expected_volume) or not math.isclose(
                    float(volume), expected_volume, rel_tol=1e-10, abs_tol=0.0
                ):
                    raise ValueError(f"cell volume does not match aperture geometry at state {index}, cell {cell_index}")
        return self


def evaluate_crevice_aperture_displacement_flow(
    request: CreviceApertureDisplacementFlowRequest,
) -> Calculation:
    """Return interval-mean face-flow required by changing cell volumes.

    Positive face flow is directed from the mouth toward the blind end. For an
    incompressible liquid with no other openings, cell continuity requires
    ``Q_j - Q_(j+1) = dV_j/dt`` with ``Q_n=0`` at the sealed tip. The resulting
    flux is a geometric displacement balance only; pressure, viscous momentum,
    velocity profiles and chemistry are not solved.
    """
    source = request.geometry_history_result
    values = _payload(source)
    states = values["geometry_states"]
    widths = values["cell_widths_m"]
    input_sha256 = canonical_digest(request.model_dump(mode="json"))
    base = {
        "history_id": request.history_id,
        "asset_id": request.asset_id,
        "location_id": request.location_id,
        "time_basis": request.time_basis,
        "geometry_id": request.geometry_id,
        "input_sha256": input_sha256,
        "geometry_history_result_sha256": request.geometry_history_result_sha256,
        "geometry_source_sha256": values.get("geometry_source_sha256"),
        "wall_loss_source_sha256": values.get("wall_loss_source_sha256"),
        "blind_end_single_mouth_reviewed": request.blind_end_single_mouth_reviewed,
        "incompressible_liquid_reviewed": request.incompressible_liquid_reviewed,
        "one_dimensional_cellwise_continuity_reviewed": request.one_dimensional_cellwise_continuity_reviewed,
        "linear_cell_volume_change_between_knots_reviewed": request.linear_cell_volume_change_between_knots_reviewed,
        "displacement_flow_only_interpretation_reviewed": request.displacement_flow_only_interpretation_reviewed,
    }
    missing = [
        name for name, reviewed in (
            ("blind_end_single_mouth_reviewed", request.blind_end_single_mouth_reviewed),
            ("incompressible_liquid_reviewed", request.incompressible_liquid_reviewed),
            ("one_dimensional_cellwise_continuity_reviewed", request.one_dimensional_cellwise_continuity_reviewed),
            ("linear_cell_volume_change_between_knots_reviewed", request.linear_cell_volume_change_between_knots_reviewed),
            ("displacement_flow_only_interpretation_reviewed", request.displacement_flow_only_interpretation_reviewed),
        ) if not reviewed
    ]
    if missing:
        return Calculation(status="needs_data", values=base | {
            "missing_reviews": missing,
            "committed_prefix": [],
            "committed_prefix_length": 0,
            "complete_requested_history_returned": False,
        })

    prefix = []
    for interval_index, (left, right) in enumerate(zip(states[:-1], states[1:], strict=True)):
        start_time = float(left["elapsed_time_s"])
        end_time = float(right["elapsed_time_s"])
        duration = end_time - start_time
        try:
            volume_change = [
                float(v1) - float(v0)
                for v0, v1 in zip(left["cell_volume_m3"], right["cell_volume_m3"], strict=True)
            ]
            cell_volume_rate = [value / duration for value in volume_change]
            face_flow = [
                math.fsum(cell_volume_rate[face_index:])
                for face_index in range(len(cell_volume_rate) + 1)
            ]
            residuals = [
                face_flow[cell_index] - face_flow[cell_index + 1] - cell_volume_rate[cell_index]
                for cell_index in range(len(cell_volume_rate))
            ]
            mouth_flow = face_flow[0]
            max_residual = max((abs(value) for value in residuals), default=0.0)
            numeric_values = [*volume_change, *cell_volume_rate, *face_flow, *residuals, mouth_flow, max_residual]
            if not all(math.isfinite(value) for value in numeric_values):
                raise ArithmeticError("nonfinite cell-volume rate or face displacement flow")
        except (OverflowError, ArithmeticError, ValueError) as error:
            return Calculation(status="out_of_scope", values=base | {
                "committed_prefix": prefix,
                "committed_prefix_length": len(prefix),
                "committed_prefix_sha256": canonical_digest(prefix),
                "first_failure": {
                    "interval_index": interval_index,
                    "start_time_s": start_time,
                    "end_time_s": end_time,
                    "geometry_state_start_sha256": canonical_digest(left),
                    "geometry_state_end_sha256": canonical_digest(right),
                    "reason": "displacement_flow_exceeds_finite_numeric_support",
                    "detail": str(error),
                },
                "complete_requested_history_returned": False,
            }, notes=("The failed interval was not committed; only complete preceding intervals are returned.",))

        prefix.append({
            "interval_index": interval_index,
            "start_time_s": start_time,
            "end_time_s": end_time,
            "duration_s": duration,
            "start_geometry_state_sha256": canonical_digest(left),
            "end_geometry_state_sha256": canonical_digest(right),
            "cell_volume_change_m3": volume_change,
            "cell_volume_change_rate_m3_s": cell_volume_rate,
            "face_displacement_flow_m3_s": face_flow,
            "mouth_displacement_flow_m3_s": mouth_flow,
            "blind_tip_flow_m3_s": face_flow[-1],
            "cell_continuity_residual_m3_s": residuals,
            "maximum_absolute_cell_continuity_residual_m3_s": max_residual,
            "interval_input_sha256": canonical_digest({
                "geometry_history_result_sha256": request.geometry_history_result_sha256,
                "interval_index": interval_index,
                "start_geometry_state_sha256": canonical_digest(left),
                "end_geometry_state_sha256": canonical_digest(right),
                "cell_widths_m": widths,
            }),
        })

    prefix_sha256 = canonical_digest(prefix)
    return Calculation(values=base | {
        "units": {
            "time": "s",
            "cell_volume_change": "m3",
            "cell_volume_change_rate": "m3/s",
            "face_displacement_flow": "m3/s",
            "cell_continuity_residual": "m3/s",
            "committed_prefix_length": "count",
        },
        "intervals": prefix,
        "committed_prefix": prefix,
        "committed_prefix_length": len(prefix),
        "committed_prefix_sha256": prefix_sha256,
        "first_failure": None,
        "complete_requested_history_returned": True,
        "positive_flow_direction": "mouth_toward_blind_tip",
        "pressure_solved": False,
        "viscous_momentum_solved": False,
        "face_velocity_computed": False,
        "solute_or_wall_loss_transport_solved": False,
        "corrosion_rate_inferred": False,
        "qualification_claimed": False,
    }, notes=(
        "Interval face flows are the kinematic incompressible 1-D continuity flow required by the pinned cell-volume changes under linear volume interpolation.",
        "This is not pressure-driven hydraulics, a viscous velocity field, a transport boundary condition, or a simultaneous moving-boundary solution.",
    ))


def _validate_context(request: CreviceApertureDisplacementFlowRequest, context: RunContext) -> None:
    if (request.asset_id, request.location_id, request.time_basis) != (
        context.asset_id, context.location_id, context.time_basis
    ):
        raise ValueError("aperture displacement-flow RunContext must match asset, location and time basis")


def specifications() -> list[ModelSpec]:
    """Expose the pinned geometry continuity ledger for registry integration."""
    return [ModelSpec(
        MODEL_ID,
        CreviceApertureDisplacementFlowRequest,
        evaluate_crevice_aperture_displacement_flow,
        {
            "intervals[].start_time_s": "s",
            "intervals[].end_time_s": "s",
            "intervals[].duration_s": "s",
            "intervals[].cell_volume_change_m3[]": "m3",
            "intervals[].cell_volume_change_rate_m3_s[]": "m3/s",
            "intervals[].face_displacement_flow_m3_s[]": "m3/s",
            "intervals[].mouth_displacement_flow_m3_s": "m3/s",
            "intervals[].blind_tip_flow_m3_s": "m3/s",
            "intervals[].cell_continuity_residual_m3_s[]": "m3/s",
            "committed_prefix_length": "count",
        },
        (
            "A pinned complete aperture history supplies fixed cell widths, transverse width and exact cell volumes.",
            "The slit is represented as a one-dimensional incompressible control volume with one mouth and a sealed blind end.",
            "Cell volume varies linearly between adjacent supplied knots; resulting face flows are displacement continuity requirements only.",
            "No pressure drop, viscosity, momentum, velocity profile, solute transport, wall kinetics or corrosion response is inferred.",
        ),
        (SOURCE_ID,),
        qualification="user_model",
        context_validator=_validate_context,
    )]
