"""Integrate positive log-saturation exposure from exact crevice cell screens."""

from __future__ import annotations

import math
from typing import Literal

from pydantic import Field, model_validator

from .contracts import Calculation, Contract, canonical_digest
from .registry import ModelSpec

MODEL_ID = "integration.crevice_saturation_exposure_history"
SOURCE_ID = "caller_crevice_cell_saturation_exposure_reconstruction"
MAX_KNOTS = 5000
MAX_CELLS = 200
MAX_SOLIDS = 100


class CreviceSaturationHistoryKnot(Contract):
    elapsed_time_s: float = Field(ge=0)
    saturation_result: dict
    saturation_result_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")

    @model_validator(mode="after")
    def validate_digest(self):
        if canonical_digest(self.saturation_result) != self.saturation_result_sha256:
            raise ValueError("spatial saturation result digest mismatch")
        return self


class CreviceSaturationExposureHistoryRequest(Contract):
    schema_version: Literal["matintegrity.crevice_saturation_exposure_history.v1"] = (
        "matintegrity.crevice_saturation_exposure_history.v1"
    )
    assessment_id: str = Field(min_length=1)
    physical_scope_id: str = Field(min_length=1)
    knots: tuple[CreviceSaturationHistoryKnot, ...] = Field(min_length=2, max_length=MAX_KNOTS)
    piecewise_linear_log10_saturation_path_reviewed: bool
    exact_knot_lineage_and_spatial_cell_identity_reviewed: bool
    same_candidate_solubility_basis_across_knots_reviewed: bool
    exposure_metric_is_not_a_rate_law_reviewed: bool

    @model_validator(mode="after")
    def strict_clock(self):
        if self.knots[0].elapsed_time_s != 0.0:
            raise ValueError("history must start at elapsed time zero")
        if any(right.elapsed_time_s <= left.elapsed_time_s for left, right in zip(self.knots[:-1], self.knots[1:])):
            raise ValueError("knot times must be strictly increasing")
        return self


def _values(result: dict) -> dict | None:
    if result.get("status") != "computed":
        return None
    nested = result.get("values")
    return nested if isinstance(nested, dict) else result


def crevice_saturation_history_knot(
    saturation_result: dict,
) -> CreviceSaturationHistoryKnot:
    """Build a digest-pinned history knot from a computed saturation result."""
    values = _values(saturation_result)
    if values is None:
        raise ValueError("saturation result must have computed status")
    elapsed_time_s = values.get("elapsed_time_s")
    if (
        isinstance(elapsed_time_s, bool)
        or not isinstance(elapsed_time_s, (int, float))
        or not math.isfinite(elapsed_time_s)
        or elapsed_time_s < 0.0
    ):
        raise ValueError("computed saturation result must include a finite nonnegative elapsed_time_s")
    return CreviceSaturationHistoryKnot(
        elapsed_time_s=float(elapsed_time_s),
        saturation_result=saturation_result,
        saturation_result_sha256=canonical_digest(saturation_result),
    )


def _integrate_positive_linear(left: float, right: float, duration: float) -> tuple[float, float]:
    """Return integral(max(0,y),dt) and duration(y>0) for a linear segment."""
    if left >= 0.0 and right >= 0.0:
        integral = 0.5 * (left + right) * duration
        positive_duration = duration if left > 0.0 or right > 0.0 else 0.0
        return integral, positive_duration
    if left <= 0.0 and right <= 0.0:
        return 0.0, 0.0
    if left < 0.0 < right:
        fraction = right / (right - left)
        return duration * right * fraction / 2.0, duration * fraction
    if right < 0.0 < left:
        fraction = left / (left - right)
        return duration * left * fraction / 2.0, duration * fraction
    # One endpoint is exactly zero; the interior is positive except at that endpoint.
    positive = right if left == 0.0 else left
    return duration * positive / 2.0, duration


def evaluate_crevice_saturation_exposure_history(
    request: CreviceSaturationExposureHistoryRequest,
) -> Calculation:
    """Integrate a caller-reviewed linear-in-time log10 saturation path per cell."""
    request_sha = canonical_digest(request.model_dump(mode="json"))
    base = {
        "assessment_id": request.assessment_id,
        "physical_scope_id": request.physical_scope_id,
        "input_sha256": request_sha,
        "representation": "piecewise_linear_log10_saturation_excess_integral_by_solid_and_cell",
    }
    review_fields = (
        "piecewise_linear_log10_saturation_path_reviewed",
        "exact_knot_lineage_and_spatial_cell_identity_reviewed",
        "same_candidate_solubility_basis_across_knots_reviewed",
        "exposure_metric_is_not_a_rate_law_reviewed",
    )
    missing = [name for name in review_fields if not getattr(request, name)]
    if missing:
        return Calculation(status="needs_data", values=base | {
            "missing_reviews": missing, "committed_knot_count": 0, "knots": [],
        })

    committed: list[dict] = []
    phase_ids: list[str] | None = None
    cell_count: int | None = None
    values_by_knot: list[list[dict[str, float]]] = []
    for index, knot in enumerate(request.knots):
        values = _values(knot.saturation_result)
        if values is None:
            return Calculation(status="needs_data", values=base | {
                "committed_knot_count": len(committed), "knots": committed,
                "failed_knot_index": index, "failure_reason": "spatial saturation result is not computed",
            })
        solids = values.get("candidate_solid_ids")
        cells = values.get("completed_cells")
        if (
            values.get("physical_scope_id") != request.physical_scope_id
            or values.get("elapsed_time_s") != knot.elapsed_time_s
            or not isinstance(solids, list) or not solids or len(solids) > MAX_SOLIDS
            or not isinstance(cells, list) or not cells or len(cells) > MAX_CELLS
        ):
            return Calculation(status="out_of_scope", values=base | {
                "committed_knot_count": len(committed), "knots": committed,
                "failed_knot_index": index,
                "failure_reason": "result scope, exact time, candidate list or cell count is outside the supported contract",
            })
        if phase_ids is None:
            phase_ids = list(solids)
            cell_count = len(cells)
        if list(solids) != phase_ids or len(cells) != cell_count:
            return Calculation(status="out_of_scope", values=base | {
                "committed_knot_count": len(committed), "knots": committed,
                "failed_knot_index": index,
                "failure_reason": "candidate-solid order or spatial cell count changed between knots",
            })
        knot_rows: list[dict[str, float]] = []
        for cell_index, cell in enumerate(cells):
            if not isinstance(cell, dict) or cell.get("cell_index") != cell_index:
                return Calculation(status="out_of_scope", values=base | {
                    "committed_knot_count": len(committed), "knots": committed,
                    "failed_knot_index": index, "failed_cell_index": cell_index,
                    "failure_reason": "cell identity/order is not spatially contiguous",
                })
            candidates = cell.get("candidate_results")
            if not isinstance(candidates, list):
                return Calculation(status="out_of_scope", values=base | {
                    "committed_knot_count": len(committed), "knots": committed,
                    "failed_knot_index": index, "failed_cell_index": cell_index,
                    "failure_reason": "candidate results are missing for this cell",
                })
            candidates_by_id = {row.get("solid_id"): row for row in candidates if isinstance(row, dict)}
            if len(candidates_by_id) != len(candidates) or set(candidates_by_id) != set(phase_ids):
                return Calculation(status="out_of_scope", values=base | {
                    "committed_knot_count": len(committed), "knots": committed,
                    "failed_knot_index": index, "failed_cell_index": cell_index,
                    "failure_reason": "candidate solid identity set changed or contains duplicates",
                })
            saturation_map: dict[str, float] = {}
            for solid_id in phase_ids:
                candidate = candidates_by_id[solid_id]
                saturation = candidate.get("log10_saturation_ratio")
                if isinstance(saturation, bool) or not isinstance(saturation, (int, float)) or not math.isfinite(saturation):
                    return Calculation(status="out_of_scope", values=base | {
                        "committed_knot_count": len(committed), "knots": committed,
                        "failed_knot_index": index, "failed_cell_index": cell_index,
                        "failure_reason": "finite numeric log10 saturation ratio is required",
                    })
                saturation_map[solid_id] = float(saturation)
            knot_rows.append(saturation_map)
        values_by_knot.append(knot_rows)
        committed.append({
            "knot_index": index,
            "elapsed_time_s": knot.elapsed_time_s,
            "saturation_result_sha256": knot.saturation_result_sha256,
            "cell_count": len(cells),
            "candidate_solid_ids": list(phase_ids),
        })

    assert phase_ids is not None and cell_count is not None
    exposure: dict[str, list[float]] = {solid_id: [0.0] * cell_count for solid_id in phase_ids}
    duration_above: dict[str, list[float]] = {solid_id: [0.0] * cell_count for solid_id in phase_ids}
    maximum_sampled: dict[str, list[float]] = {solid_id: [] for solid_id in phase_ids}
    for solid_id in phase_ids:
        for cell_index in range(cell_count):
            samples = [knot_values[cell_index][solid_id] for knot_values in values_by_knot]
            maximum_sampled[solid_id].append(max(samples))
            for index, (left, right) in enumerate(zip(samples[:-1], samples[1:])):
                duration = request.knots[index + 1].elapsed_time_s - request.knots[index].elapsed_time_s
                if not math.isfinite(duration) or duration <= 0.0:
                    return Calculation(status="out_of_scope", values=base | {
                        "committed_knot_count": len(committed), "knots": committed,
                        "failed_interval_index": index,
                        "failure_reason": "elapsed-time interval exceeds finite support",
                    })
                integral, positive_duration = _integrate_positive_linear(left, right, duration)
                exposure[solid_id][cell_index] += integral
                duration_above[solid_id][cell_index] += positive_duration
                if not math.isfinite(exposure[solid_id][cell_index]) or not math.isfinite(duration_above[solid_id][cell_index]):
                    return Calculation(status="out_of_scope", values=base | {
                        "committed_knot_count": len(committed), "knots": committed,
                        "failed_interval_index": index, "failed_cell_index": cell_index,
                        "failed_solid_id": solid_id,
                        "failure_reason": "integrated exposure exceeds finite numeric support",
                    })

    return Calculation(values=base | {
        "status": "computed",
        "committed_knot_count": len(committed),
        "knots": committed,
        "candidate_solid_ids": phase_ids,
        "cell_count": cell_count,
        "positive_log10_saturation_exposure_s_by_solid_and_cell": exposure,
        "duration_above_saturation_s_by_solid_and_cell": duration_above,
        "maximum_sampled_log10_saturation_ratio_by_solid_and_cell": maximum_sampled,
        "interpolation_assumption": "log10 saturation ratio varies linearly between supplied exact knots; positive-part exposure is integrated analytically for each segment",
        "interpretation_boundary": "Exposure integrates only the positive part of log10(Q/K) over the caller-reviewed reconstruction. It is a diagnostic index, not a precipitation/dissolution rate, amount, nucleation model, or phase stability claim.",
    })


def specifications() -> list[ModelSpec]:
    return [ModelSpec(
        model_id=MODEL_ID,
        input_type=CreviceSaturationExposureHistoryRequest,
        evaluator=evaluate_crevice_saturation_exposure_history,
        units={
            "knots[].elapsed_time_s": "s",
            "positive_log10_saturation_exposure_s_by_solid_and_cell.*": "s",
            "duration_above_saturation_s_by_solid_and_cell.*": "s",
            "maximum_sampled_log10_saturation_ratio_by_solid_and_cell.*": "1",
        },
        assumptions=(
            "Every upstream exact-knot saturation result is computed, digest-pinned, and belongs to the declared physical scope and exact time.",
            "Candidate solid ordering and cell ordering remain identical at every knot; cells are not mixed or remapped.",
            "Log10 saturation ratio is reconstructed as piecewise linear in time only because the caller explicitly reviews that path.",
            "The API analytically integrates max(0, log10(Q/K)) and the time for which the reconstructed value is positive; these diagnostics do not define a kinetic law or precipitation amount.",
            "Ksp/activity standard-state comparability across supplied knots is caller reviewed and is not automatically validated from underlying source records.",
        ),
        source_ids=(SOURCE_ID,),
        qualification="user_model",
    )]
