"""Threshold excursions from a digest-pinned calibrated gasket leakage history."""

from __future__ import annotations

import math
from typing import Literal

from pydantic import Field, model_validator

from ..contracts import (
    AssessmentResult,
    Calculation,
    Contract,
    Evidence,
    Nonnegative,
    Positive,
    RunContext,
    canonical_digest,
)
from ..registry import ModelSpec

SOURCE_ID = "caller_gasket_leakage_rate_threshold"
MODEL_ID = "integration.gasket_leakage_rate_threshold_events"
_HISTORY_MODEL_ID = "fabrication.gasket_calibrated_leakage_history"


class GasketLeakageRateThresholdEvents(Contract):
    """Compare a calculated leakage-rate history with caller-owned bounds."""

    schema_version: Literal["matintegrity.gasket_leakage_rate_threshold_events.v1"] = (
        "matintegrity.gasket_leakage_rate_threshold_events.v1"
    )
    assessment_id: str = Field(min_length=1)
    physical_scope_id: str = Field(min_length=1)
    leakage_history: AssessmentResult
    leakage_history_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    minimum_rate_mol_s: Nonnegative
    maximum_rate_mol_s: Positive | None = None
    threshold_provider_id: str = Field(min_length=1)
    threshold_provider_revision: str = Field(min_length=1)
    threshold_record_id: str = Field(min_length=1)
    threshold_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    threshold_evidence: tuple[Evidence, ...] = Field(min_length=1)
    usage_rights_evidence: tuple[Evidence, ...] = Field(min_length=1)
    usage_license_id: str = Field(min_length=1)
    physical_scope_and_time_basis_reviewed: bool
    threshold_applicability_reviewed: bool
    piecewise_linear_rate_path_reviewed: bool
    pressure_and_rate_units_reviewed: bool
    source_result_provenance_reviewed: bool
    usage_rights_reviewed: bool
    computational_use_authorized: bool

    @model_validator(mode="after")
    def coherent_threshold_and_source(self):
        if self.maximum_rate_mol_s is not None and self.maximum_rate_mol_s < self.minimum_rate_mol_s:
            raise ValueError("maximum leakage-rate threshold must not be below the minimum")
        result = self.leakage_history
        if result.model_id != _HISTORY_MODEL_ID or result.status != "computed":
            raise ValueError("a computed calibrated gasket leakage-history assessment is required")
        if canonical_digest(result.model_dump(mode="json")) != self.leakage_history_sha256:
            raise ValueError("leakage-history digest does not match the supplied assessment")
        expected_input = canonical_digest({
            "model_id": result.model_id,
            "model_version": result.model_version,
            "inputs": result.inputs,
            "context": result.context.model_dump(mode="json"),
        })
        if result.input_digest != expected_input:
            raise ValueError("leakage-history input/context digest mismatch")
        criterion = {
            "provider_id": self.threshold_provider_id,
            "provider_revision": self.threshold_provider_revision,
            "record_id": self.threshold_record_id,
            "physical_scope_id": self.physical_scope_id,
            "minimum_rate_mol_s": self.minimum_rate_mol_s,
            "maximum_rate_mol_s": self.maximum_rate_mol_s,
        }
        if canonical_digest(criterion) != self.threshold_sha256:
            raise ValueError("threshold digest does not match its provider record and selected limits")
        if not any(row.source_id == self.threshold_provider_id for row in self.threshold_evidence):
            raise ValueError("threshold provider must appear in threshold Evidence")
        if not any(row.license_id == self.usage_license_id for row in self.usage_rights_evidence):
            raise ValueError("usage-rights Evidence must identify the declared license")
        return self


def _outside_intervals(
    times: list[float], rates: list[float], bound: float, *, below: bool
) -> list[dict[str, float | bool]]:
    """Return exact crossings for a piecewise-linear rate reconstruction."""

    outside = (lambda value: value < bound) if below else (lambda value: value > bound)
    active = outside(rates[0])
    active_start = times[0] if active else None
    left_censored = active
    intervals: list[dict[str, float | bool]] = []
    for i, (time0, time1) in enumerate(zip(times[:-1], times[1:], strict=True)):
        rate0, rate1 = rates[i], rates[i + 1]
        outside0, outside1 = outside(rate0), outside(rate1)
        crossing: float | None = None
        if outside0 != outside1:
            delta = rate1 - rate0
            if delta == 0.0:
                crossing = time1
            else:
                fraction = (bound - rate0) / delta
                crossing = time0 + (time1 - time0) * fraction
                crossing = min(max(crossing, time0), time1)
        if not outside0 and outside1:
            active_start = crossing if crossing is not None else time1
            left_censored = False
        elif outside0 and not outside1:
            end = crossing if crossing is not None else time1
            start = active_start if active_start is not None else time0
            intervals.append({
                "start_time_s": start,
                "end_time_s": end,
                "duration_s": end - start,
                "left_censored": left_censored,
                "right_censored": False,
            })
            active_start = None
            left_censored = False
    if active_start is not None:
        end = times[-1]
        intervals.append({
            "start_time_s": active_start,
            "end_time_s": end,
            "duration_s": end - active_start,
            "left_censored": left_censored,
            "right_censored": True,
        })
    return intervals


def evaluate_gasket_leakage_rate_threshold_events(
    request: GasketLeakageRateThresholdEvents,
) -> Calculation:
    """Report rate excursions without converting them to seal failure or probability."""

    result = request.leakage_history
    base = {
        "assessment_id": request.assessment_id,
        "asset_id": result.context.asset_id,
        "location_id": result.context.location_id,
        "time_basis": result.context.time_basis,
        "physical_scope_id": request.physical_scope_id,
        "leakage_history_model_id": result.model_id,
        "leakage_history_sha256": request.leakage_history_sha256,
        "leakage_history_input_digest": result.input_digest,
        "threshold_provider_id": request.threshold_provider_id,
        "threshold_provider_revision": request.threshold_provider_revision,
        "threshold_record_id": request.threshold_record_id,
        "threshold_sha256": request.threshold_sha256,
        "minimum_rate_mol_s": request.minimum_rate_mol_s,
        "maximum_rate_mol_s": request.maximum_rate_mol_s,
        "threshold_evidence": [row.model_dump(mode="json") for row in request.threshold_evidence],
        "usage_rights_evidence": [row.model_dump(mode="json") for row in request.usage_rights_evidence],
        "seal_acceptance_or_failure_inferred": False,
        "probability_inferred": False,
    }
    reviews = {
        "physical_scope_and_time_basis_reviewed": request.physical_scope_and_time_basis_reviewed,
        "threshold_applicability_reviewed": request.threshold_applicability_reviewed,
        "piecewise_linear_rate_path_reviewed": request.piecewise_linear_rate_path_reviewed,
        "pressure_and_rate_units_reviewed": request.pressure_and_rate_units_reviewed,
        "source_result_provenance_reviewed": request.source_result_provenance_reviewed,
        "usage_rights_reviewed": request.usage_rights_reviewed,
        "computational_use_authorized": request.computational_use_authorized,
    }
    missing = [name for name, accepted in reviews.items() if not accepted]
    if missing:
        return Calculation(status="needs_data", values=base | {"missing_reviews": missing})
    if result.units.get("time_history[].time_s") != "s":
        return Calculation(status="out_of_scope", values=base | {"out_of_scope_reason": "source_time_unit_not_seconds"})
    if result.units.get("time_history[].molar_leak_rate_mol_s") != "mol/s":
        return Calculation(status="out_of_scope", values=base | {"out_of_scope_reason": "source_rate_unit_not_mol_per_second"})

    history = result.values.get("time_history")
    if not isinstance(history, list) or len(history) < 2:
        return Calculation(status="out_of_scope", values=base | {"out_of_scope_reason": "source_history_missing_or_too_short"})
    times: list[float] = []
    rates: list[float] = []
    for index, row in enumerate(history):
        if not isinstance(row, dict):
            return Calculation(status="out_of_scope", values=base | {"out_of_scope_reason": "malformed_source_history_row", "failed_knot_index": index})
        time_s, rate = row.get("time_s"), row.get("molar_leak_rate_mol_s")
        if isinstance(time_s, bool) or not isinstance(time_s, (int, float)) or not math.isfinite(time_s) or time_s < 0:
            return Calculation(status="out_of_scope", values=base | {"out_of_scope_reason": "invalid_source_time", "failed_knot_index": index})
        if isinstance(rate, bool) or not isinstance(rate, (int, float)) or not math.isfinite(rate) or rate < 0:
            return Calculation(status="out_of_scope", values=base | {"out_of_scope_reason": "invalid_source_leakage_rate", "failed_knot_index": index})
        times.append(float(time_s))
        rates.append(float(rate))
    if any(right <= left for left, right in zip(times[:-1], times[1:], strict=True)):
        return Calculation(status="out_of_scope", values=base | {"out_of_scope_reason": "source_times_not_strictly_increasing"})

    below = _outside_intervals(times, rates, request.minimum_rate_mol_s, below=True)
    above = [] if request.maximum_rate_mol_s is None else _outside_intervals(
        times, rates, request.maximum_rate_mol_s, below=False
    )
    return Calculation(values=base | {
        "time_points_s": times,
        "molar_leak_rate_points_mol_s": rates,
        "below_minimum_intervals": below,
        "below_minimum_duration_s": math.fsum(float(row["duration_s"]) for row in below),
        "above_maximum_intervals": above,
        "above_maximum_duration_s": math.fsum(float(row["duration_s"]) for row in above),
        "interpolation": "piecewise_linear_between_computed_leakage_rate_knots",
        "threshold_is_seal_acceptance": False,
    }, notes=(
        "Excursion times are conditional on the caller-reviewed piecewise-linear reconstruction between computed leakage-rate knots.",
        "The caller thresholds are comparison criteria only; they do not establish sealing acceptance, leak failure, consequence or probability.",
    ))


def _validate_context(request: GasketLeakageRateThresholdEvents, context: RunContext) -> None:
    source = request.leakage_history.context
    if (context.asset_id, context.location_id, context.time_basis) != (
        source.asset_id, source.location_id, source.time_basis
    ):
        raise ValueError("threshold-event RunContext must match the source leakage-history identity and clock")


def specifications() -> list[ModelSpec]:
    return [ModelSpec(
        model_id=MODEL_ID,
        input_type=GasketLeakageRateThresholdEvents,
        evaluator=evaluate_gasket_leakage_rate_threshold_events,
        units={
            "minimum_rate_mol_s": "mol/s",
            "maximum_rate_mol_s": "mol/s",
            "time_points_s[]": "s",
            "molar_leak_rate_points_mol_s[]": "mol/s",
            "below_minimum_intervals[].start_time_s": "s",
            "below_minimum_intervals[].end_time_s": "s",
            "below_minimum_intervals[].duration_s": "s",
            "above_maximum_intervals[].start_time_s": "s",
            "above_maximum_intervals[].end_time_s": "s",
            "above_maximum_intervals[].duration_s": "s",
        },
        assumptions=(
            "The source must be a digest-pinned computed gasket leakage history with explicit mol/s and s units.",
            "Excursion intervals use only caller-reviewed piecewise-linear interpolation between source knots.",
            "Thresholds are caller-owned comparison criteria and do not establish leak-tightness, acceptance, failure or probability.",
        ),
        source_ids=(SOURCE_ID,),
        qualification="user_model",
        context_validator=_validate_context,
    )]
