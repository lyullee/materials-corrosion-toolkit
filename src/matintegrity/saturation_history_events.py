"""Audit threshold crossings in caller-computed aqueous saturation histories."""

from __future__ import annotations

import math
from typing import Literal

from pydantic import Field, model_validator

from .contracts import AssessmentResult, Calculation, Contract, Nonnegative, RunContext, canonical_digest
from .registry import ModelSpec


class SaturationHistoryKnot(Contract):
    """One caller-computed log10 saturation ratio at an exact time knot."""

    time_s: Nonnegative
    log10_saturation_ratio: float = Field(allow_inf_nan=False)


class SaturationHistoryEventRequest(Contract):
    """Threshold event audit for one consistently defined candidate solid."""

    schema_version: Literal["matintegrity.saturation_history_events.v1"] = "matintegrity.saturation_history_events.v1"
    solid_id: str = Field(min_length=1)
    solution_scope_id: str = Field(min_length=1)
    provider_id: str = Field(min_length=1)
    provider_revision: str = Field(min_length=1)
    provider_configuration_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    input_history_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    knots: tuple[SaturationHistoryKnot, ...] = Field(min_length=2, max_length=100_000)
    threshold_log10_saturation_ratio: float = Field(default=0.0, allow_inf_nan=False)
    consistent_solid_and_standard_state_reviewed: bool
    time_basis_and_order_reviewed: bool
    piecewise_linear_interpolation_reviewed: bool
    computational_use_authorized: bool

    @model_validator(mode="after")
    def validate_history(self):
        times = [row.time_s for row in self.knots]
        if any(b <= a for a, b in zip(times, times[1:])):
            raise ValueError("saturation history times must be strictly increasing")
        if canonical_digest([row.model_dump(mode="json") for row in self.knots]) != self.input_history_sha256:
            raise ValueError("input_history_sha256 must match the canonical ordered knot payload")
        return self


class SaturationHistoryAssessmentBinding(Contract):
    """Select one candidate from a digest-pinned computed van't Hoff history."""

    schema_version: Literal["matintegrity.saturation_history_assessment_binding.v1"] = (
        "matintegrity.saturation_history_assessment_binding.v1"
    )
    saturation_assessment: AssessmentResult
    expected_assessment_result_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    solid_id: str = Field(min_length=1)
    threshold_log10_saturation_ratio: float = Field(default=0.0, allow_inf_nan=False)
    consistent_solid_and_standard_state_reviewed: bool
    time_basis_and_order_reviewed: bool
    piecewise_linear_interpolation_reviewed: bool
    computational_use_authorized: bool


def _validate_binding_context(request: SaturationHistoryAssessmentBinding, context: RunContext) -> None:
    upstream = request.saturation_assessment.context
    if (context.asset_id, context.location_id, context.time_basis) != (
        upstream.asset_id, upstream.location_id, upstream.time_basis,
    ):
        raise ValueError("event-binding RunContext must match the source saturation history")


def audit_saturation_history_events(request: SaturationHistoryEventRequest) -> Calculation:
    """Report exact linear threshold crossings and above-threshold durations.

    This is a descriptive interpolation over caller-computed saturation ratios; it
    does not calculate chemistry, phase stability, precipitation, or corrosion.
    """
    digest = canonical_digest(request.model_dump(mode="json"))
    missing = [name for name in (
        "consistent_solid_and_standard_state_reviewed",
        "time_basis_and_order_reviewed",
        "piecewise_linear_interpolation_reviewed",
        "computational_use_authorized",
    ) if not getattr(request, name)]
    base = {
        "request_sha256": digest,
        "input_history_sha256": request.input_history_sha256,
        "solid_id": request.solid_id,
        "solution_scope_id": request.solution_scope_id,
        "provider_id": request.provider_id,
        "provider_revision": request.provider_revision,
        "provider_configuration_sha256": request.provider_configuration_sha256,
        "threshold_log10_saturation_ratio": request.threshold_log10_saturation_ratio,
        "review_flags": {
            name: getattr(request, name) for name in (
                "consistent_solid_and_standard_state_reviewed",
                "time_basis_and_order_reviewed",
                "piecewise_linear_interpolation_reviewed",
                "computational_use_authorized",
            )
        },
        "knot_count": len(request.knots),
    }
    if missing:
        return Calculation(status="needs_data", values=base | {"missing_reviews": missing}, notes=("Resolve the listed provenance and interpretation reviews before using saturation-history event results.",))

    threshold = request.threshold_log10_saturation_ratio
    events: list[dict[str, object]] = []
    active_start: float | None = None
    left_censored = request.knots[0].log10_saturation_ratio > threshold
    for left, right in zip(request.knots, request.knots[1:]):
        a = left.log10_saturation_ratio - threshold
        b = right.log10_saturation_ratio - threshold
        dt = right.time_s - left.time_s
        if not (math.isfinite(a) and math.isfinite(b) and math.isfinite(dt) and dt > 0.0):
            return Calculation(status="out_of_scope", values=base | {"out_of_scope_reason": "nonfinite_interval_arithmetic", "completed_event_count": len(events), "events": events}, notes=("Finite threshold event times could not be represented; no clipping was applied.",))
        left_above, right_above = a > 0.0, b > 0.0
        crossing: float | None = None
        if (a < 0.0 < b) or (b < 0.0 < a):
            # Avoid b-a overflow for finite, opposite-sign endpoint values.
            # The fraction from the left endpoint is |a| / (|a| + |b|),
            # evaluated as a ratio of the larger magnitude to stay finite.
            magnitude_a = abs(a)
            magnitude_b = abs(b)
            if magnitude_a >= magnitude_b:
                fraction = 1.0 / (1.0 + magnitude_b / magnitude_a)
            else:
                ratio = magnitude_a / magnitude_b
                fraction = ratio / (1.0 + ratio)
            crossing = left.time_s + dt * fraction
            if not math.isfinite(crossing):
                return Calculation(status="out_of_scope", values=base | {"out_of_scope_reason": "nonfinite_crossing_time", "completed_event_count": len(events), "events": events}, notes=("A finite threshold crossing time could not be represented.",))
        if left_above and active_start is None:
            active_start = left.time_s
        if not left_above and right_above:
            active_start = crossing if crossing is not None else (left.time_s if a == 0.0 else right.time_s)
            events.append({"event": "above_threshold_start", "time_s": active_start})
        elif left_above and not right_above:
            end = crossing if crossing is not None else right.time_s
            start = active_start if active_start is not None else left.time_s
            events.append({"event": "above_threshold_interval", "start_time_s": start, "end_time_s": end, "duration_s": end - start, "left_censored": left_censored, "right_censored": False})
            events.append({"event": "above_threshold_end", "time_s": end})
            active_start = None
            left_censored = False
        elif not left_above and not right_above and crossing is not None:
            # A line segment cannot cross twice; this guards inconsistent numeric input.
            return Calculation(status="out_of_scope", values=base | {"out_of_scope_reason": "inconsistent_crossing_classification"}, notes=("Threshold classification was numerically inconsistent.",))
    if active_start is not None:
        end = request.knots[-1].time_s
        events.append({"event": "above_threshold_interval", "start_time_s": active_start, "end_time_s": end, "duration_s": end - active_start, "left_censored": left_censored, "right_censored": True})
    crossings = [row["time_s"] for row in events if row.get("event") in ("above_threshold_start", "above_threshold_end")]
    total_duration = math.fsum(float(row["duration_s"]) for row in events if row.get("event") == "above_threshold_interval")
    return Calculation(status="computed", values=base | {
        "crossing_times_s": crossings,
        "above_threshold_intervals": [row for row in events if row.get("event") == "above_threshold_interval"],
        "above_threshold_duration_s": total_duration,
        "right_censored_at_final_knot": active_start is not None,
        "events": events,
        "interpolation": "piecewise_linear_between_caller_knots",
        "chemical_or_corrosion_rate_inferred": False,
    }, notes=("Threshold events are descriptive linear interpolations of caller-supplied saturation ratios. They are not phase selection, precipitation extent or kinetics, or a corrosion rate.",))


def bind_vant_hoff_saturation_events(
    request: SaturationHistoryAssessmentBinding,
) -> Calculation:
    """Extract one candidate from an exact computed saturation-history result."""
    upstream = request.saturation_assessment
    full_digest = canonical_digest(upstream.model_dump(mode="json"))
    input_payload = {
        "model_id": upstream.model_id,
        "model_version": upstream.model_version,
        "inputs": upstream.inputs,
        "context": upstream.context.model_dump(mode="json"),
    }
    calculated_input_digest = canonical_digest(input_payload)
    lineage = {
        "upstream_model_id": upstream.model_id,
        "upstream_model_version": upstream.model_version,
        "upstream_result_sha256": full_digest,
        "upstream_input_digest": calculated_input_digest,
        "selected_solid_id": request.solid_id,
    }
    if full_digest != request.expected_assessment_result_sha256:
        return Calculation(status="needs_data", values=lineage | {"missing_or_mismatched_lineage": "expected_assessment_result_sha256"}, notes=("Pin the exact saturation AssessmentResult digest before extracting its knots.",))
    if upstream.input_digest != calculated_input_digest:
        return Calculation(status="needs_data", values=lineage | {"missing_or_mismatched_lineage": "upstream_input_digest"}, notes=("The upstream registry input/context digest does not match the embedded assessment.",))
    if upstream.model_id != "integration.aqueous_vant_hoff_saturation_history":
        return Calculation(status="out_of_scope", values=lineage | {"out_of_scope_reason": "unsupported_upstream_model"}, notes=("This binding accepts only the registered aqueous van't Hoff saturation-history model.",))
    if upstream.status != "computed":
        return Calculation(status=upstream.status, values=lineage | {"upstream_status": upstream.status}, notes=("The upstream saturation history is incomplete; no threshold events were extracted.",))

    times = upstream.values.get("times_s")
    rows = upstream.values.get("saturation_history")
    history_id = upstream.values.get("history_id")
    if not isinstance(times, list) or not isinstance(rows, list) or len(times) != len(rows) or len(rows) < 2:
        return Calculation(status="out_of_scope", values=lineage | {"out_of_scope_reason": "malformed_upstream_saturation_history"}, notes=("The upstream result does not contain an aligned multi-knot saturation history.",))

    knots: list[SaturationHistoryKnot] = []
    for index, (time_s, row) in enumerate(zip(times, rows, strict=True)):
        if not isinstance(row, dict) or row.get("time_s") != time_s:
            return Calculation(status="out_of_scope", values=lineage | {"out_of_scope_reason": "upstream_time_alignment_mismatch", "failed_knot_index": index}, notes=("The upstream saturation knot clock does not exactly match its declared time vector.",))
        if row.get("status") != "computed":
            return Calculation(status="needs_data", values=lineage | {"upstream_knot_status": row.get("status"), "failed_knot_index": index}, notes=("Every selected candidate requires a computed saturation result at every exact knot.",))
        screen = row.get("screen")
        screen_values = screen.get("values") if isinstance(screen, dict) else None
        candidates = screen_values.get("candidate_results") if isinstance(screen_values, dict) else None
        selected = [item for item in candidates or () if isinstance(item, dict) and item.get("solid_id") == request.solid_id]
        if len(selected) != 1:
            return Calculation(status="needs_data", values=lineage | {"failed_knot_index": index, "candidate_match_count": len(selected)}, notes=("The selected solid must appear exactly once at every upstream time knot.",))
        try:
            knot = SaturationHistoryKnot.model_validate({
                "time_s": time_s,
                "log10_saturation_ratio": selected[0]["log10_saturation_ratio"],
            })
        except (KeyError, TypeError, ValueError):
            return Calculation(status="out_of_scope", values=lineage | {"failed_knot_index": index, "out_of_scope_reason": "invalid_selected_saturation_value"}, notes=("The selected upstream saturation ratio is missing or nonfinite.",))
        knots.append(knot)

    provider_configuration_sha256 = canonical_digest({
        "upstream_result_sha256": full_digest,
        "upstream_input_digest": calculated_input_digest,
        "selected_solid_id": request.solid_id,
    })
    event_request = SaturationHistoryEventRequest(
        solid_id=request.solid_id,
        solution_scope_id=str(history_id or "unlabeled-history"),
        provider_id=upstream.model_id,
        provider_revision=upstream.model_version,
        provider_configuration_sha256=provider_configuration_sha256,
        input_history_sha256=canonical_digest([row.model_dump(mode="json") for row in knots]),
        knots=tuple(knots),
        threshold_log10_saturation_ratio=request.threshold_log10_saturation_ratio,
        consistent_solid_and_standard_state_reviewed=request.consistent_solid_and_standard_state_reviewed,
        time_basis_and_order_reviewed=request.time_basis_and_order_reviewed,
        piecewise_linear_interpolation_reviewed=request.piecewise_linear_interpolation_reviewed,
        computational_use_authorized=request.computational_use_authorized,
    )
    event_result = audit_saturation_history_events(event_request)
    return Calculation(
        status=event_result.status,
        values=lineage | {
            "solution_scope_id": event_request.solution_scope_id,
            "event_request_sha256": canonical_digest(event_request.model_dump(mode="json")),
            "event_audit": event_result.model_dump(mode="json"),
            "upstream_saturation_knots_used": [row.model_dump(mode="json") for row in knots],
            "chemical_or_corrosion_rate_inferred": False,
        },
        notes=("The selected candidate is extracted from an exact digest-pinned van't Hoff saturation result; threshold interpolation remains a descriptive caller-reviewed event audit.",) + event_result.notes,
    )


def specifications() -> list[ModelSpec]:
    return [ModelSpec(
        "chemistry.aqueous_saturation_history_events",
        SaturationHistoryEventRequest,
        audit_saturation_history_events,
        {
            "crossing_times_s[]": "s",
            "above_threshold_duration_s": "s",
            "threshold_log10_saturation_ratio": "1",
        },
        (
            "Audit threshold crossings between caller-computed, strictly ordered saturation-ratio knots by reviewed piecewise-linear interpolation.",
            "The event record is descriptive and digest-bound; it does not compute aqueous chemistry, choose phases, predict precipitation kinetics, or estimate corrosion.",
        ),
        ("caller_aqueous_saturation_history_event_audit",),
        qualification="user_model",
    ), ModelSpec(
        "integration.aqueous_vant_hoff_saturation_events",
        SaturationHistoryAssessmentBinding,
        bind_vant_hoff_saturation_events,
        {
            "event_audit.values.crossing_times_s[]": "s",
            "event_audit.values.above_threshold_duration_s": "s",
            "threshold_log10_saturation_ratio": "1",
        },
        (
            "Extract one explicitly selected solid from every exact computed knot of a digest-pinned aqueous van't Hoff saturation AssessmentResult and audit reviewed threshold crossings.",
            "The adapter preserves the parent assessment digest and selected-solid lineage; it does not infer phase selection, precipitation kinetics, scale protection, or corrosion rate.",
        ),
        ("caller_aqueous_saturation_history_event_audit",),
        qualification="user_model",
        context_validator=_validate_binding_context,
    )]
