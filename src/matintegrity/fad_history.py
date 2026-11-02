"""Finite, caller-reviewed FAD histories against a digest-pinned user boundary.

This model evaluates normalized coordinates at the supplied knots only. It does
not create provider mechanics, interpolate a crossing time, infer probability,
or estimate remaining life.
"""

from __future__ import annotations

import math
from bisect import bisect_right
from typing import Literal

from pydantic import Field, model_validator

from .contracts import Calculation, Contract, Evidence, Nonnegative, Positive, RunContext, canonical_digest
from .models.fad import FailureAssessmentCurve
from .registry import ModelSpec

MODEL_ID = "structural.failure_assessment_history"
FAD_HISTORY_SOURCE_ID = "caller_pinned_fad_curve_and_reviewed_provider_histories"


class FADHistoryProviderReceipt(Contract):
    """Digest and evidence receipt for one caller-produced physical history value."""

    quantity: Literal[
        "effective_mode_i_stress_intensity",
        "fracture_resistance",
        "reference_stress",
        "normalizing_strength",
    ]
    asset_id: str = Field(min_length=1)
    location_id: str = Field(min_length=1)
    physical_scope_id: str = Field(min_length=1)
    clock_id: str = Field(min_length=1)
    time_s: Nonnegative
    material_condition_id: str = Field(min_length=1)
    geometry_basis_id: str = Field(min_length=1)
    load_history_id: str = Field(min_length=1)
    provider_id: str = Field(min_length=1)
    result_id: str = Field(min_length=1)
    result_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    evidence: tuple[Evidence, ...] = Field(min_length=1, max_length=32)


class FADAssessmentHistoryKnot(Contract):
    """One exact time knot with provider-calculated FAD coordinates and receipts."""

    time_s: Nonnegative
    effective_stress_intensity_Pa_sqrt_m: Nonnegative
    fracture_resistance_Pa_sqrt_m: Positive
    reference_stress_Pa: Nonnegative
    normalizing_strength_Pa: Positive
    provider_receipts: tuple[FADHistoryProviderReceipt, ...] = Field(min_length=4, max_length=4)

    @model_validator(mode="after")
    def exactly_one_receipt_per_quantity(self):
        expected = {
            "effective_mode_i_stress_intensity",
            "fracture_resistance",
            "reference_stress",
            "normalizing_strength",
        }
        quantities = [receipt.quantity for receipt in self.provider_receipts]
        if len(set(quantities)) != 4 or set(quantities) != expected:
            raise ValueError("each FAD history knot requires one provider receipt for every physical input")
        if any(not evidence.license_id for receipt in self.provider_receipts for evidence in receipt.evidence):
            raise ValueError("each provider result receipt requires a declared license or use entitlement")
        return self


class FADAssessmentHistoryRequest(Contract):
    """Bounded FAD time history; every physical input remains caller/provider owned."""

    schema_version: Literal["matintegrity.fad_assessment_history.v1"] = (
        "matintegrity.fad_assessment_history.v1"
    )
    assessment_id: str = Field(min_length=1)
    asset_id: str = Field(min_length=1)
    location_id: str = Field(min_length=1)
    physical_scope_id: str = Field(min_length=1)
    clock_id: str = Field(min_length=1)
    material_condition_id: str = Field(min_length=1)
    geometry_basis_id: str = Field(min_length=1)
    load_history_id: str = Field(min_length=1)
    curve: FailureAssessmentCurve
    curve_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    knots: tuple[FADAssessmentHistoryKnot, ...] = Field(min_length=2, max_length=10000)
    linear_elastic_k_solution_reviewed: bool
    reference_stress_solution_reviewed: bool
    toughness_and_strength_applicability_reviewed: bool
    load_history_and_combination_reviewed: bool
    geometry_and_material_scope_reviewed: bool
    curve_applicability_reviewed: bool
    maximum_curve_evaluations: int = Field(default=10000, ge=2, le=10000)
    maximum_output_knots: int = Field(default=10000, ge=2, le=10000)

    @model_validator(mode="after")
    def validate_pinned_history(self):
        if canonical_digest(self.curve.model_dump(mode="json")) != self.curve_sha256:
            raise ValueError("curve_sha256 must pin the exact embedded FAD curve contract")
        times = [knot.time_s for knot in self.knots]
        if any(not math.isfinite(value) for value in times):
            raise ValueError("FAD history times must be finite")
        if any(right <= left for left, right in zip(times, times[1:])):
            raise ValueError("FAD history time knots must be strictly increasing")
        if len(times) > self.maximum_curve_evaluations:
            raise ValueError("FAD history knot count exceeds maximum_curve_evaluations")
        if len(times) > self.maximum_output_knots:
            raise ValueError("FAD history knot count exceeds maximum_output_knots")
        for knot in self.knots:
            for receipt in knot.provider_receipts:
                expected = (
                    self.asset_id,
                    self.location_id,
                    self.physical_scope_id,
                    self.clock_id,
                    knot.time_s,
                    self.material_condition_id,
                    self.geometry_basis_id,
                    self.load_history_id,
                )
                actual = (
                    receipt.asset_id,
                    receipt.location_id,
                    receipt.physical_scope_id,
                    receipt.clock_id,
                    receipt.time_s,
                    receipt.material_condition_id,
                    receipt.geometry_basis_id,
                    receipt.load_history_id,
                )
                if actual != expected:
                    raise ValueError("provider receipt asset/scope/clock/time/material/geometry/load identity must exactly match its FAD history knot")
        return self


def evaluate_failure_assessment_history(request: FADAssessmentHistoryRequest) -> Calculation:
    """Evaluate FAD margin at supplied knots and return only a crossing interval bracket."""

    input_digest = canonical_digest(request.model_dump(mode="json"))
    curve_digest = canonical_digest(request.curve.model_dump(mode="json"))
    review_flags = (
        request.linear_elastic_k_solution_reviewed,
        request.reference_stress_solution_reviewed,
        request.toughness_and_strength_applicability_reviewed,
        request.load_history_and_combination_reviewed,
        request.geometry_and_material_scope_reviewed,
        request.curve_applicability_reviewed,
    )
    if not all(review_flags):
        return Calculation(
            status="needs_data",
            values={
                "reason": "required_fad_history_applicability_review_missing",
                "input_sha256": input_digest,
                "curve_sha256": curve_digest,
                "probability_inferred": False,
                "remaining_life_inferred": False,
            },
            notes=("Review all K, reference-stress, toughness/strength, load-history, geometry/material and FAD-boundary applicability records before evaluation.",),
        )

    load_ratio_max = request.curve.load_ratio[-1]
    if any(
        knot.normalizing_strength_Pa <= 0
        or knot.fracture_resistance_Pa_sqrt_m <= 0
        for knot in request.knots
    ):
        # Positive field types should already make this unreachable; retain a
        # fail-closed guard at the calculation boundary.
        return Calculation(status="out_of_scope", values={
            "reason": "nonpositive_normalizing_strength_or_fracture_resistance",
            "input_sha256": input_digest,
            "probability_inferred": False,
        })

    rows: list[dict] = []
    margins: list[float] = []
    unsupported_times: list[float] = []
    load_ratios: list[float] = []
    for knot in request.knots:
        kr = knot.effective_stress_intensity_Pa_sqrt_m / knot.fracture_resistance_Pa_sqrt_m
        lr = knot.reference_stress_Pa / knot.normalizing_strength_Pa
        if not math.isfinite(kr) or not math.isfinite(lr):
            return Calculation(status="out_of_scope", values={
                "reason": "normalized_fad_coordinate_nonfinite",
                "time_s": knot.time_s,
                "input_sha256": input_digest,
                "probability_inferred": False,
            })
        load_ratios.append(lr)
        if lr < request.curve.load_ratio[0] or lr > load_ratio_max:
            unsupported_times.append(knot.time_s)
            continue
        index = min(bisect_right(request.curve.load_ratio, lr) - 1, len(request.curve.load_ratio) - 2)
        fraction = (lr - request.curve.load_ratio[index]) / (
            request.curve.load_ratio[index + 1] - request.curve.load_ratio[index]
        )
        allowable_kr = (
            (1.0 - fraction) * request.curve.allowable_toughness_ratio[index]
            + fraction * request.curve.allowable_toughness_ratio[index + 1]
        )
        margin = allowable_kr - kr
        if not math.isfinite(allowable_kr) or not math.isfinite(margin):
            return Calculation(status="out_of_scope", values={
                "reason": "fad_margin_nonfinite",
                "time_s": knot.time_s,
                "input_sha256": input_digest,
                "probability_inferred": False,
            })
        margins.append(margin)
        rows.append({
            "time_s": knot.time_s,
            "toughness_ratio_Kr": kr,
            "load_ratio_Lr": lr,
            "allowable_toughness_ratio": allowable_kr,
            "vertical_toughness_ratio_margin": margin,
            "point_outcome": "outside_declared_boundary" if margin < 0.0 else "inside_or_on_declared_boundary",
            "provider_receipts": [receipt.model_dump(mode="json") for receipt in knot.provider_receipts],
        })

    if unsupported_times:
        return Calculation(
            status="out_of_scope",
            values={
                "reason": "load_ratio_outside_pinned_curve_support",
                "unsupported_time_s": unsupported_times,
                "curve_sha256": curve_digest,
                "input_sha256": input_digest,
                "partial_history_returned": False,
                "probability_inferred": False,
                "remaining_life_inferred": False,
            },
            notes=("No curve extrapolation or partial history is returned when any knot lies outside the pinned FAD curve support.",),
        )

    first_outside = next((i for i, margin in enumerate(margins) if margin < 0.0), None)
    initially_outside = first_outside == 0
    crossing_bracket = None
    if first_outside is not None and first_outside > 0:
        left, right = first_outside - 1, first_outside
        crossing_bracket = {
            "left_time_s": request.knots[left].time_s,
            "right_time_s": request.knots[right].time_s,
            "left_margin": margins[left],
            "right_margin": margins[right],
            "exact_crossing_time_reported": False,
        }
    if initially_outside:
        endpoint_status = "already_outside_at_horizon_start"
    elif first_outside is not None:
        endpoint_status = "first_outside_boundary_knot_found"
    else:
        endpoint_status = "no_outside_boundary_knot_in_supplied_history"

    return Calculation(
        values={
            "model_id": MODEL_ID,
            "assessment_id": request.assessment_id,
            "asset_id": request.asset_id,
            "location_id": request.location_id,
            "physical_scope_id": request.physical_scope_id,
            "clock_id": request.clock_id,
            "material_condition_id": request.material_condition_id,
            "geometry_basis_id": request.geometry_basis_id,
            "load_history_id": request.load_history_id,
            "horizon_start_s": request.knots[0].time_s,
            "horizon_end_s": request.knots[-1].time_s,
            "curve_id": request.curve.curve_id,
            "assessment_basis_id": request.curve.assessment_basis_id,
            "curve_sha256": curve_digest,
            "input_sha256": input_digest,
            "knot_results": rows,
            "first_outside_boundary_status": endpoint_status,
            "first_outside_boundary_interval_bracket": crossing_bracket,
            "initially_outside_boundary": initially_outside,
            "minimum_vertical_toughness_ratio_margin": min(margins),
            "probability_inferred": False,
            "remaining_life_inferred": False,
            "exact_crossing_time_reported": False,
            "curve_extrapolation_performed": False,
        },
        notes=(
            "Kr and Lr are evaluated at the exact caller-supplied time knots; the caller FAD curve is linearly interpolated only in Lr within its pinned support.",
            "The reported first outside-boundary interval is a bracket between supplied knots. No crossing time, probability, remaining life, code acceptance or material qualification is inferred.",
            "Physical K, fracture resistance, reference stress and normalizing strength are caller/provider results; Evidence and provider digests document lineage but do not independently validate those results.",
        ),
    )


def _validate_fad_history_context(request: FADAssessmentHistoryRequest, context: RunContext) -> None:
    if (request.asset_id, request.location_id, request.clock_id) != (
        context.asset_id, context.location_id, context.time_basis
    ):
        raise ValueError("FAD history asset, location and clock must match RunContext")


def specifications() -> list[ModelSpec]:
    return [ModelSpec(
        model_id=MODEL_ID,
        input_type=FADAssessmentHistoryRequest,
        evaluator=evaluate_failure_assessment_history,
        units={
            "horizon_start_s": "s",
            "horizon_end_s": "s",
            "knot_results[].time_s": "s",
            "knot_results[].toughness_ratio_Kr": "1",
            "knot_results[].load_ratio_Lr": "1",
            "knot_results[].allowable_toughness_ratio": "1",
            "knot_results[].vertical_toughness_ratio_margin": "1",
            "minimum_vertical_toughness_ratio_margin": "1",
            "first_outside_boundary_interval_bracket.left_time_s": "s",
            "first_outside_boundary_interval_bracket.right_time_s": "s",
        },
        assumptions=(
            "All physical input histories and the finite nonincreasing FAD boundary are caller-owned, reviewed and digest-bound.",
            "Each supplied knot is evaluated independently; the model does not interpolate physical inputs or estimate the exact boundary crossing time between knots.",
            "This is deterministic FAD screening and does not infer probability, remaining life, code acceptance or material qualification.",
        ),
        source_ids=(FAD_HISTORY_SOURCE_ID,),
        qualification="user_model",
        context_validator=_validate_fad_history_context,
    )]
