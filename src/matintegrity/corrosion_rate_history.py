"""Integrate caller-evidenced corrosion-rate knots as a finite thickness history."""

from __future__ import annotations

import math
from typing import Literal

from pydantic import Field, StrictInt, model_validator

from .contracts import Calculation, Contract, Evidence, Nonnegative, Positive, RunContext, canonical_digest
from .registry import ModelSpec

SOURCE_ID = "caller_piecewise_linear_corrosion_rate_thickness_history"
MODEL_ID = "corrosion.piecewise_linear_rate_thickness_history"


class CorrosionRateHistoryKnot(Contract):
    """One caller-provided, provenance-bearing point in a corrosion-rate history."""

    knot_index: StrictInt = Field(ge=0)
    time_s: Nonnegative
    corrosion_rate_m_s: Nonnegative
    evidence: tuple[Evidence, ...] = Field(min_length=1)


class CorrosionRateThicknessHistoryRequest(Contract):
    """Finite thickness history under a caller-reviewed linear rate path."""

    schema_version: Literal["matintegrity.corrosion_rate_thickness_history.v1"] = (
        "matintegrity.corrosion_rate_thickness_history.v1"
    )
    history_id: str = Field(min_length=1)
    asset_id: str = Field(min_length=1)
    location_id: str = Field(min_length=1)
    material_id: str = Field(min_length=1)
    material_condition_id: str = Field(min_length=1)
    physical_scope_id: str = Field(min_length=1)
    time_basis: str = Field(min_length=1)
    knots: tuple[CorrosionRateHistoryKnot, ...] = Field(min_length=2, max_length=100_000)
    baseline_thickness_m: Positive
    baseline_evidence: Evidence
    required_thickness_m: Nonnegative
    required_thickness_evidence: Evidence
    ordered_history_reviewed: bool
    rate_source_mapping_reviewed: bool
    piecewise_linear_rate_reconstruction_reviewed: bool
    uniform_area_average_loss_reviewed: bool
    material_condition_and_location_reviewed: bool
    finite_support_no_extrapolation_reviewed: bool

    @model_validator(mode="after")
    def validate_history(self):
        if self.required_thickness_m >= self.baseline_thickness_m:
            raise ValueError("required thickness must be below the measured baseline")
        if self.baseline_evidence.origin != "measured":
            raise ValueError("baseline thickness evidence must be measured")
        if self.required_thickness_evidence.origin not in {"user_declared", "open_dataset"}:
            raise ValueError("required-thickness evidence must be caller-declared or from an open dataset")
        if tuple(row.knot_index for row in self.knots) != tuple(range(len(self.knots))):
            raise ValueError("knot indices must be contiguous and follow caller order")
        if any(right.time_s <= left.time_s for left, right in zip(self.knots[:-1], self.knots[1:], strict=True)):
            raise ValueError("corrosion-rate knot times must be strictly increasing")
        if self.knots[0].time_s != 0.0:
            raise ValueError("rate history must begin at elapsed exposure time zero")
        return self


def _validate_context(request: CorrosionRateThicknessHistoryRequest, context: RunContext) -> None:
    if (context.asset_id, context.location_id, context.time_basis) != (
        request.asset_id,
        request.location_id,
        request.time_basis,
    ):
        raise ValueError("RunContext must match the asset, location and clock declared in the rate history")


def _crossing_offset(
    rate_start_m_s: float,
    rate_end_m_s: float,
    interval_s: float,
    loss_needed_m: float,
) -> tuple[float, float]:
    """Bisect the monotone integrated linear-rate path to a tight time bracket."""
    full_loss = 0.5 * (rate_start_m_s + rate_end_m_s) * interval_s
    if loss_needed_m <= 0.0:
        return 0.0, 0.0
    low, high = 0.0, interval_s
    slope = (rate_end_m_s - rate_start_m_s) / interval_s
    for _ in range(80):
        middle = low + 0.5 * (high - low)
        partial_loss = rate_start_m_s * middle + 0.5 * slope * middle * middle
        if partial_loss < loss_needed_m:
            low = middle
        else:
            high = middle
        if math.nextafter(low, math.inf) >= high:
            break
    if full_loss < loss_needed_m:
        raise ValueError("requested crossing lies beyond this rate interval")
    return low, high


def evaluate_corrosion_rate_thickness_history(
    request: CorrosionRateThicknessHistoryRequest,
) -> Calculation:
    """Integrate exact trapezoids and report crossings only within supplied support."""
    review_fields = (
        "ordered_history_reviewed",
        "rate_source_mapping_reviewed",
        "piecewise_linear_rate_reconstruction_reviewed",
        "uniform_area_average_loss_reviewed",
        "material_condition_and_location_reviewed",
        "finite_support_no_extrapolation_reviewed",
    )
    missing_reviews = [name for name in review_fields if not getattr(request, name)]
    request_digest = canonical_digest(request.model_dump(mode="json"))
    knot_digests = [canonical_digest(row.model_dump(mode="json")) for row in request.knots]
    base = {
        "model_id": MODEL_ID,
        "history_id": request.history_id,
        "asset_id": request.asset_id,
        "location_id": request.location_id,
        "material_id": request.material_id,
        "material_condition_id": request.material_condition_id,
        "physical_scope_id": request.physical_scope_id,
        "time_basis": request.time_basis,
        "baseline_thickness_m": request.baseline_thickness_m,
        "baseline_evidence": request.baseline_evidence.model_dump(mode="json"),
        "required_thickness_m": request.required_thickness_m,
        "required_thickness_evidence": request.required_thickness_evidence.model_dump(mode="json"),
        "request_sha256": request_digest,
        "ordered_knot_digests": knot_digests,
        "support_start_s": request.knots[0].time_s,
        "support_end_s": request.knots[-1].time_s,
        "extrapolation_performed": False,
        "probability_inferred": False,
        "field_transferability_inferred": False,
        "acceptance_inferred": False,
        "qualification_inferred": False,
    }
    if missing_reviews:
        return Calculation(status="needs_data", values=base | {"missing_reviews": missing_reviews})

    completed: list[dict] = []
    cumulative_loss = 0.0
    first_crossing: dict | None = None
    threshold_loss = request.baseline_thickness_m - request.required_thickness_m
    for interval_index, (left, right) in enumerate(zip(request.knots[:-1], request.knots[1:], strict=True)):
        dt = right.time_s - left.time_s
        if dt <= 0.0 or not math.isfinite(dt):
            return Calculation(status="out_of_scope", values=base | {
                "completed_intervals": completed,
                "failed_interval_index": interval_index,
                "reason": "rate_history_interval_duration_outside_finite_support",
            })
        interval_loss = 0.5 * (left.corrosion_rate_m_s + right.corrosion_rate_m_s) * dt
        end_loss = cumulative_loss + interval_loss
        if not math.isfinite(interval_loss) or not math.isfinite(end_loss):
            return Calculation(status="out_of_scope", values=base | {
                "completed_intervals": completed,
                "failed_interval_index": interval_index,
                "reason": "integrated_wall_loss_exceeds_finite_numeric_support",
            })
        if end_loss > request.baseline_thickness_m:
            return Calculation(status="out_of_scope", values=base | {
                "completed_intervals": completed,
                "failed_interval_index": interval_index,
                "uncommitted_interval": {
                    "time_start_s": left.time_s,
                    "time_end_s": right.time_s,
                    "source_knot_sha256": [knot_digests[interval_index], knot_digests[interval_index + 1]],
                    "proposed_interval_loss_m": interval_loss,
                    "cumulative_loss_at_end_m": end_loss,
                    "reason": "cumulative_loss_exceeds_measured_baseline",
                },
                "committed_cumulative_loss_m": cumulative_loss,
                "reason": "rate path consumes more than measured baseline before the supplied history ends",
            })

        if first_crossing is None and cumulative_loss < threshold_loss <= end_loss:
            if cumulative_loss == threshold_loss:
                lower_offset = upper_offset = 0.0
            else:
                lower_offset, upper_offset = _crossing_offset(
                    left.corrosion_rate_m_s,
                    right.corrosion_rate_m_s,
                    dt,
                    threshold_loss - cumulative_loss,
                )
            first_crossing = {
                "time_lower_s": left.time_s + lower_offset,
                "time_upper_s": left.time_s + upper_offset,
                "time_estimate_s": left.time_s + 0.5 * (lower_offset + upper_offset),
                "interval_start_s": left.time_s,
                "interval_end_s": right.time_s,
                "source_knot_sha256": [knot_digests[interval_index], knot_digests[interval_index + 1]],
                "reconstruction": "piecewise_linear_rate_exact_integral_with_bisection_time_bracket",
                "conditional_on_reviewed_rate_path": True,
            }

        start_remaining = request.baseline_thickness_m - cumulative_loss
        end_remaining = request.baseline_thickness_m - end_loss
        completed.append({
            "interval_index": interval_index,
            "time_start_s": left.time_s,
            "time_end_s": right.time_s,
            "source_knot_sha256": [knot_digests[interval_index], knot_digests[interval_index + 1]],
            "rate_start_m_s": left.corrosion_rate_m_s,
            "rate_end_m_s": right.corrosion_rate_m_s,
            "interval_wall_loss_m": interval_loss,
            "cumulative_wall_loss_start_m": cumulative_loss,
            "cumulative_wall_loss_end_m": end_loss,
            "remaining_thickness_start_m": start_remaining,
            "remaining_thickness_end_m": end_remaining,
            "rate_evidence_start": [row.model_dump(mode="json") for row in left.evidence],
            "rate_evidence_end": [row.model_dump(mode="json") for row in right.evidence],
        })
        cumulative_loss = end_loss

    return Calculation(values=base | {
        "status": "computed",
        "interval_count": len(completed),
        "cumulative_wall_loss_m": cumulative_loss,
        "remaining_thickness_m": request.baseline_thickness_m - cumulative_loss,
        "remaining_thickness_margin_m": request.baseline_thickness_m - cumulative_loss - request.required_thickness_m,
        "first_required_thickness_crossing": first_crossing,
        "interval_history": completed,
        "rate_interpolation": "piecewise_linear_between_exact_caller_knots",
        "wall_loss_integration": "exact_trapezoid_per_interval",
    }, notes=(
        "The result covers only the finite caller-supplied rate support and does not extrapolate.",
        "Thickness is a uniform area-average bookkeeping result under the caller-reviewed rate-to-wall-loss mapping.",
        "A crossing time is conditional on the reviewed piecewise-linear rate reconstruction and is not a life, probability, acceptance, transferability or qualification statement.",
    ))


def specifications() -> list[ModelSpec]:
    return [ModelSpec(
        model_id=MODEL_ID,
        input_type=CorrosionRateThicknessHistoryRequest,
        evaluator=evaluate_corrosion_rate_thickness_history,
        units={
            "support_start_s": "s",
            "support_end_s": "s",
            "baseline_thickness_m": "m",
            "required_thickness_m": "m",
            "interval_count": "1",
            "cumulative_wall_loss_m": "m",
            "remaining_thickness_m": "m",
            "remaining_thickness_margin_m": "m",
            "interval_history[].time_start_s": "s",
            "interval_history[].time_end_s": "s",
            "interval_history[].rate_start_m_s": "m/s",
            "interval_history[].rate_end_m_s": "m/s",
            "interval_history[].interval_wall_loss_m": "m",
            "interval_history[].cumulative_wall_loss_start_m": "m",
            "interval_history[].cumulative_wall_loss_end_m": "m",
            "interval_history[].remaining_thickness_start_m": "m",
            "interval_history[].remaining_thickness_end_m": "m",
            "first_required_thickness_crossing.time_lower_s": "s",
            "first_required_thickness_crossing.time_upper_s": "s",
            "first_required_thickness_crossing.time_estimate_s": "s",
        },
        assumptions=(
            "Each rate knot is caller supplied with Evidence and a canonical record digest; the rate path is piecewise linear only between adjacent knots.",
            "Baseline thickness evidence must be measured; required-thickness evidence must be caller-declared or from an open dataset.",
            "Uniform area-average wall loss, asset/location/material identity and the rate path require explicit caller review; only finite supplied support is evaluated.",
            "No probability, future extrapolation, field transferability, acceptance or material qualification is inferred.",
        ),
        source_ids=(SOURCE_ID,),
        qualification="user_model",
        context_validator=_validate_context,
    )]
