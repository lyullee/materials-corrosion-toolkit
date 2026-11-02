"""Caller-reviewed subdivision of a pinned crevice aperture history.

This adapter refines geometry output intervals by linear interpolation only. It
does not rerun electrochemistry, transport, or the upstream recession model.
"""

from __future__ import annotations

import math
from collections import deque
from typing import Any, Literal

from pydantic import Field, model_validator

from ..contracts import AssessmentResult, Calculation, Contract, RunContext, canonical_digest
from ..registry import ModelSpec


class CreviceApertureHistoryRefinement(Contract):
    """Bounded, deterministic subdivision request for an existing aperture path."""

    schema_version: Literal["matintegrity.crevice_aperture_history_refinement.v1"] = (
        "matintegrity.crevice_aperture_history_refinement.v1"
    )
    refinement_id: str = Field(min_length=1)
    source_geometry_result: dict[str, Any]
    source_geometry_result_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    source_geometry_assessment_result: AssessmentResult | None = None
    source_geometry_assessment_result_sha256: str | None = Field(default=None, pattern=r"^[a-f0-9]{64}$")
    maximum_relative_aperture_change_per_segment: float = Field(gt=0, le=1)
    maximum_internal_segments: int = Field(ge=1, le=100_000)
    maximum_bisection_refinements: int = Field(ge=0, le=100_000)
    # This explicit review records that linear interpolation is acceptable for
    # the caller's intended use; it does not establish physical validity.
    linear_geometry_interpolation_reviewed: bool

    @model_validator(mode="after")
    def validate_source(self):
        if canonical_digest(self.source_geometry_result) != self.source_geometry_result_sha256:
            raise ValueError("complete source geometry result digest mismatch")
        if (self.source_geometry_assessment_result is None) != (
            self.source_geometry_assessment_result_sha256 is None
        ):
            raise ValueError("source AssessmentResult and its digest must be supplied together")
        if self.source_geometry_assessment_result is not None:
            result = self.source_geometry_assessment_result
            expected_input = canonical_digest(
                {
                    "model_id": result.model_id,
                    "model_version": result.model_version,
                    "inputs": result.inputs,
                    "context": result.context.model_dump(mode="json"),
                }
            )
            if result.status not in {"computed", "out_of_scope"} or result.input_digest != expected_input:
                raise ValueError(
                    "source geometry AssessmentResult must be computed or carry an out-of-scope prefix"
                )
            if (
                canonical_digest(result.model_dump(mode="json"))
                != self.source_geometry_assessment_result_sha256
            ):
                raise ValueError("source geometry AssessmentResult digest mismatch")
            if result.model_dump(mode="json") != self.source_geometry_result:
                raise ValueError("pinned geometry JSON must equal the supplied AssessmentResult")
            if result.status == "out_of_scope" and (
                not isinstance(result.values.get("geometry_states"), list)
                or len(result.values["geometry_states"]) < 2
                or not isinstance(result.values.get("failed_interval_time_s"), dict)
            ):
                raise ValueError(
                    "out-of-scope source must include at least one accepted interval and its failed interval"
                )
        if not self.linear_geometry_interpolation_reviewed:
            raise ValueError("caller review of linear geometry interpolation is required")
        states = _geometry_states(self.source_geometry_result)
        if len(states) < 2:
            raise ValueError("source geometry history requires at least two states")
        return self


def _geometry_states(source: dict[str, Any]) -> list[tuple[float, tuple[float, ...]]]:
    # Accept the direct geometry mapping and the Calculation JSON form.
    body = source.get("values", source)
    states = body.get("geometry_states") if isinstance(body, dict) else None
    if not isinstance(states, list) or len(states) < 2:
        raise ValueError("source must contain at least two geometry_states")
    normalized: list[tuple[float, tuple[float, ...]]] = []
    ncell: int | None = None
    for index, row in enumerate(states):
        if not isinstance(row, dict):
            raise ValueError("each geometry state must be an object")
        time_s = row.get("elapsed_time_s")
        apertures = row.get("cell_aperture_m")
        if (
            isinstance(time_s, bool)
            or not isinstance(time_s, (int, float))
            or not math.isfinite(time_s)
            or not isinstance(apertures, list)
            or not apertures
        ):
            raise ValueError("geometry states require finite time and a nonempty aperture vector")
        if any(
            isinstance(value, bool)
            or not isinstance(value, (int, float))
            or not math.isfinite(value)
            or value <= 0
            for value in apertures
        ):
            raise ValueError("cell apertures must be finite positive numbers")
        if ncell is None:
            ncell = len(apertures)
        if len(apertures) != ncell:
            raise ValueError("cell aperture vectors must have a stable cell count")
        if index == 0 and time_s != 0:
            raise ValueError("source geometry history must begin at zero elapsed time")
        if index and time_s <= normalized[-1][0]:
            raise ValueError("geometry state times must increase strictly")
        normalized.append((float(time_s), tuple(float(v) for v in apertures)))
    return normalized


def refine_crevice_aperture_history(x: CreviceApertureHistoryRefinement) -> Calculation:
    """Subdivide source intervals until each piece meets the caller's change cap.

    A piece is accepted if every cell's absolute aperture change divided by its
    aperture at the piece start is no greater than the requested limit. Midpoint
    states are linear interpolants of the pinned source endpoints.
    """
    states = _geometry_states(x.source_geometry_result)
    source_values = x.source_geometry_result.get("values", x.source_geometry_result)
    source_status = x.source_geometry_result.get("status", source_values.get("status", "computed"))
    source_failure_interval = source_values.get("failed_interval_time_s")
    source_failure_reason = source_values.get("reason")
    out_states: list[dict[str, Any]] = [
        {
            "state_index": 0,
            "elapsed_time_s": states[0][0],
            "cell_aperture_m": list(states[0][1]),
            "source_state_index": 0,
            "interpolated": False,
        }
    ]
    segments: list[dict[str, Any]] = []
    refinements: list[dict[str, Any]] = []

    def fail(source_interval_index: int, start: float, end: float, reason: str) -> Calculation:
        return Calculation(
            status="out_of_scope",
            values={
                "refinement_id": x.refinement_id,
                "source_geometry_result_sha256": x.source_geometry_result_sha256,
                "source_geometry_assessment_result_sha256": x.source_geometry_assessment_result_sha256,
                "source_geometry_result_model_id": x.source_geometry_result.get("model_id"),
                "source_geometry_result_model_version": x.source_geometry_result.get("model_version"),
                "source_geometry_input_digest": x.source_geometry_result.get("input_digest"),
                "source_geometry_context_sha256": canonical_digest(
                    x.source_geometry_result.get("context", {})
                ),
                "source_geometry_status": source_status,
                "source_geometry_failure_interval_time_s": source_failure_interval,
                "source_geometry_failure_reason": source_failure_reason,
                "refinement_request_sha256": canonical_digest(x.model_dump(mode="json")),
                "status_detail": "bounded_refinement_incomplete",
                "interpolation_policy": "piecewise_linear_between_pinned_source_geometry_states",
                "interpolated_geometry_states": [row for row in out_states if row["interpolated"]],
                "resolved_geometry_states": [row for row in out_states if not row["interpolated"]],
                "source_state_count": len(states),
                "interpolated_state_count": sum(row["interpolated"] for row in out_states),
                "computed_prefix": segments,
                "computed_prefix_states": out_states,
                "failed_source_interval_index": source_interval_index,
                "failed_interval_time_s": {"start": start, "end": end},
                "failure_reason": reason,
                "adaptive_bisection_refinements": refinements,
                "segment_count": len(segments),
                "maximum_internal_segments": x.maximum_internal_segments,
                "maximum_bisection_refinements": x.maximum_bisection_refinements,
            },
        )

    pending = deque(
        (i, states[i][0], states[i][1], states[i + 1][0], states[i + 1][1]) for i in range(len(states) - 1)
    )
    while pending:
        source_index, start, aperture_start, end, aperture_end = pending.popleft()
        changes = [abs(b - a) / a for a, b in zip(aperture_start, aperture_end, strict=True)]
        max_change = max(changes)
        if max_change > x.maximum_relative_aperture_change_per_segment:
            if len(refinements) >= x.maximum_bisection_refinements:
                return fail(source_index, start, end, "maximum_bisection_refinements_exhausted")
            if len(segments) + len(pending) + 2 > x.maximum_internal_segments:
                return fail(source_index, start, end, "maximum_internal_segments_would_be_exceeded")
            middle = start + (end - start) * 0.5
            if not start < middle < end:
                return fail(source_index, start, end, "interval_cannot_be_bisected_at_float_resolution")
            fraction = (middle - start) / (end - start)
            aperture_middle = tuple(
                a + fraction * (b - a) for a, b in zip(aperture_start, aperture_end, strict=True)
            )
            refinements.append(
                {
                    "refinement_index": len(refinements),
                    "source_interval_index": source_index,
                    "rejected_interval_time_s": {"start": start, "end": end},
                    "maximum_relative_aperture_change": max_change,
                    "start_state_is_interpolated": start != states[source_index][0],
                    "end_state_is_interpolated": end != states[source_index + 1][0],
                    "proposed_split_time_s": middle,
                    "interpolation": "piecewise_linear_between_pinned_source_geometry_states",
                }
            )
            pending.appendleft((source_index, middle, aperture_middle, end, aperture_end))
            pending.appendleft((source_index, start, aperture_start, middle, aperture_middle))
            continue
        if len(segments) >= x.maximum_internal_segments:
            return fail(source_index, start, end, "maximum_internal_segments_exhausted")
        segment_index = len(segments)
        record = {
            "segment_index": segment_index,
            "source_interval_index": source_index,
            "start_time_s": start,
            "end_time_s": end,
            "start_aperture_m": list(aperture_start),
            "end_aperture_m": list(aperture_end),
            "maximum_relative_aperture_change": max_change,
            "start_state_is_interpolated": start != states[source_index][0],
            "end_state_is_interpolated": end != states[source_index + 1][0],
            "source_geometry_result_sha256": x.source_geometry_result_sha256,
        }
        segments.append(record)
        is_original_endpoint = end == states[source_index + 1][0]
        out_states.append(
            {
                "state_index": len(out_states),
                "elapsed_time_s": end,
                "cell_aperture_m": list(aperture_end),
                "source_state_index": source_index + 1 if is_original_endpoint else None,
                "interpolated": not is_original_endpoint,
            }
        )

    return Calculation(
        status="out_of_scope" if source_status == "out_of_scope" else "computed",
        values={
            "refinement_id": x.refinement_id,
            "source_geometry_result_sha256": x.source_geometry_result_sha256,
            "source_geometry_assessment_result_sha256": x.source_geometry_assessment_result_sha256,
            "source_geometry_result_model_id": x.source_geometry_result.get("model_id"),
            "source_geometry_result_model_version": x.source_geometry_result.get("model_version"),
            "source_geometry_input_digest": x.source_geometry_result.get("input_digest"),
            "source_geometry_context_sha256": canonical_digest(x.source_geometry_result.get("context", {})),
            "source_geometry_status": source_status,
            "source_geometry_failure_interval_time_s": source_failure_interval,
            "source_geometry_failure_reason": source_failure_reason,
            "refinement_request_sha256": canonical_digest(x.model_dump(mode="json")),
            "refined_geometry_states": out_states,
            "resolved_geometry_states": [row for row in out_states if not row["interpolated"]],
            "interpolated_geometry_states": [row for row in out_states if row["interpolated"]],
            "source_state_count": len(states),
            "interpolated_state_count": sum(row["interpolated"] for row in out_states),
            "refined_segments": segments,
            "segment_count": len(segments),
            "adaptive_bisection_refinements": refinements,
            "maximum_relative_aperture_change_per_segment": x.maximum_relative_aperture_change_per_segment,
            "maximum_internal_segments": x.maximum_internal_segments,
            "maximum_bisection_refinements": x.maximum_bisection_refinements,
            "interpolation_policy": "piecewise_linear_between_pinned_source_geometry_states",
            "limitations": [
                "This adapter only subdivides an existing aperture trajectory; it does not recalculate electrochemical metal loss, transport, chemistry, or recession.",
                "The refined points are interpolation states, not independently computed physics states or evidence of time-step convergence.",
                "Coupling to transport remains operator-split when a downstream campaign holds geometry fixed within each segment; this adapter does not remove that limitation.",
                "A refined prefix inherited from an out-of-scope source remains out_of_scope and cannot be treated as a complete geometry history.",
            ],
        },
        notes=(
            "The complete source result digest and bounded interpolation request are retained for reproducibility.",
            "A non-computed result retains all accepted segments as a successful prefix and identifies the first unaccepted interval and reason.",
        ),
    )


def _validate_context(x: CreviceApertureHistoryRefinement, context: RunContext) -> None:
    result = x.source_geometry_assessment_result
    if result is None:
        return
    if (result.context.asset_id, result.context.location_id, result.context.time_basis) != (
        context.asset_id,
        context.location_id,
        context.time_basis,
    ):
        raise ValueError("refinement RunContext must match the source geometry result identity")


def specifications() -> list[ModelSpec]:
    return [
        ModelSpec(
            "integration.crevice_aperture_history_refinement",
            CreviceApertureHistoryRefinement,
            refine_crevice_aperture_history,
            {
                "refined_geometry_states[].elapsed_time_s": "s",
                "refined_geometry_states[].cell_aperture_m": "m",
            },
            (
                "The source geometry result is pinned by digest and input state vectors are required to be finite, positive and time ordered.",
                "Inserted states use piecewise-linear interpolation only and do not represent recomputed corrosion, transport or moving-boundary physics.",
                "The caller sets relative-change, segment and bisection limits and explicitly reviews interpolation applicability.",
            ),
            ("caller_reviewed_crevice_aperture_history_refinement",),
            qualification="user_model",
            context_validator=_validate_context,
        )
    ]
