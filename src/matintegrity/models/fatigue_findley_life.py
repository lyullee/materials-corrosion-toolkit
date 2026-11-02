"""Caller-calibrated life interpolation from a finite-plane Findley parameter."""

from __future__ import annotations

import math
from typing import Literal

from pydantic import Field, model_validator

from ..contracts import Calculation, Contract, Evidence, Positive, RunContext, canonical_digest
from ..registry import ModelSpec
from .fatigue_findley import CriticalPlaneFindleyStressHistory, _validate_context, critical_plane_findley_parameter


class FindleyParameterLifePoint(Contract):
    """One caller supplied parameter/life pair for a single material condition."""

    point_id: str = Field(min_length=1)
    parameter_Pa: Positive
    life_cycles: Positive


class CriticalPlaneFindleyCalibratedLife(Contract):
    """Map the governing finite-plane parameter to a reviewed monotone life curve."""

    stress_history: CriticalPlaneFindleyStressHistory
    life_curve_provider_id: str = Field(min_length=1)
    life_curve_provider_revision: str = Field(min_length=1)
    life_curve_record_id: str = Field(min_length=1)
    life_curve_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    life_curve_points: tuple[FindleyParameterLifePoint, ...] = Field(min_length=2, max_length=10000)
    life_curve_evidence: tuple[Evidence, ...] = Field(min_length=1)
    usage_rights_evidence: tuple[Evidence, ...] = Field(min_length=1)
    same_material_condition_and_load_basis_reviewed: bool
    monotone_curve_and_interpolation_reviewed: bool
    curve_support_and_no_extrapolation_reviewed: bool
    usage_rights_reviewed: bool
    computational_use_authorized: bool

    @model_validator(mode="after")
    def validate_curve(self):
        ids = [point.point_id for point in self.life_curve_points]
        if len(set(ids)) != len(ids):
            raise ValueError("life-curve point IDs must be unique")
        parameters = [point.parameter_Pa for point in self.life_curve_points]
        lives = [point.life_cycles for point in self.life_curve_points]
        if any(right <= left for left, right in zip(parameters[:-1], parameters[1:], strict=True)):
            raise ValueError("life-curve parameter values must increase strictly")
        if any(right >= left for left, right in zip(lives[:-1], lives[1:], strict=True)):
            raise ValueError("life must decrease strictly as the damaging parameter increases")
        expected = canonical_digest([point.model_dump(mode="json") for point in self.life_curve_points])
        if expected != self.life_curve_sha256:
            raise ValueError("life-curve point digest mismatch")
        if not any(
            row.source_id == self.life_curve_provider_id and row.sha256 == self.life_curve_sha256
            for row in self.life_curve_evidence
        ):
            raise ValueError("life-curve provider and digest must be linked to matching Evidence")
        if not any(row.license_id for row in self.usage_rights_evidence):
            raise ValueError("life-curve rights Evidence must identify a license or permitted use")
        return self


def critical_plane_findley_calibrated_life(request: CriticalPlaneFindleyCalibratedLife) -> Calculation:
    """Evaluate finite-plane Findley response, then log-log interpolate within its life curve."""
    input_digest = canonical_digest(request.model_dump(mode="json"))
    reviews = {
        "same_material_condition_and_load_basis_reviewed": request.same_material_condition_and_load_basis_reviewed,
        "monotone_curve_and_interpolation_reviewed": request.monotone_curve_and_interpolation_reviewed,
        "curve_support_and_no_extrapolation_reviewed": request.curve_support_and_no_extrapolation_reviewed,
        "usage_rights_reviewed": request.usage_rights_reviewed,
        "computational_use_authorized": request.computational_use_authorized,
    }
    base = {
        "input_digest": input_digest,
        "material_condition_id": request.stress_history.material_condition_id,
        "life_curve_provider_id": request.life_curve_provider_id,
        "life_curve_provider_revision": request.life_curve_provider_revision,
        "life_curve_record_id": request.life_curve_record_id,
        "life_curve_sha256": request.life_curve_sha256,
        "life_curve_point_count": len(request.life_curve_points),
        "life_curve_interpolation": "piecewise_linear_in_log_parameter_log_life",
        "extrapolation": "forbidden",
        "stress_result_status": "not_evaluated",
    }
    missing = [key for key, value in reviews.items() if not value]
    if missing:
        return Calculation(status="needs_data", values=base | {"missing_reviews": missing})

    stress_result = critical_plane_findley_parameter(request.stress_history)
    base["stress_result_status"] = stress_result.status
    base["stress_result_input_digest"] = stress_result.values.get("input_digest")
    if stress_result.status != "computed":
        return Calculation(status=stress_result.status, values=base | {
            "reason": "underlying_findley_parameter_result_not_computed",
            "upstream_values": stress_result.values,
        }, notes=stress_result.notes)

    parameter = stress_result.values["maximum_findley_parameter_Pa"]
    points = request.life_curve_points
    if parameter < points[0].parameter_Pa or parameter > points[-1].parameter_Pa:
        return Calculation(status="out_of_scope", values=base | {
            "governing_findley_parameter_Pa": parameter,
            "supported_parameter_interval_Pa": [points[0].parameter_Pa, points[-1].parameter_Pa],
            "reason": "governing_parameter_outside_caller_life_curve_support_no_extrapolation",
        })

    if parameter == points[-1].parameter_Pa:
        lower_index = len(points) - 2
        fraction = 1.0
    else:
        lower_index = next(
            index for index in range(len(points) - 1)
            if points[index].parameter_Pa <= parameter <= points[index + 1].parameter_Pa
        )
        lo, hi = points[lower_index], points[lower_index + 1]
        fraction = (math.log(parameter) - math.log(lo.parameter_Pa)) / (
            math.log(hi.parameter_Pa) - math.log(lo.parameter_Pa)
        )
    lower, upper = points[lower_index], points[lower_index + 1]
    log_life = math.log(lower.life_cycles) + fraction * (
        math.log(upper.life_cycles) - math.log(lower.life_cycles)
    )
    try:
        life_cycles = math.exp(log_life)
    except OverflowError:
        return Calculation(status="out_of_scope", values=base | {
            "governing_findley_parameter_Pa": parameter,
            "reason": "interpolated_life_exceeded_finite_numeric_support",
        })
    if not math.isfinite(life_cycles) or life_cycles <= 0.0:
        return Calculation(status="out_of_scope", values=base | {
            "governing_findley_parameter_Pa": parameter,
            "reason": "interpolated_life_exceeded_finite_numeric_support",
        })
    return Calculation(values=base | {
        "governing_findley_parameter_Pa": parameter,
        "governing_plane_id": stress_result.values["governing_plane_id"],
        "governing_plane_ids_within_numeric_tie_tolerance": stress_result.values[
            "governing_plane_ids_within_numeric_tie_tolerance"
        ],
        "cycles_to_failure": life_cycles,
        "interpolation_point_ids": [lower.point_id, upper.point_id],
        "log_interpolation_fraction": fraction,
        "stress_result_input_digest": stress_result.values["input_digest"],
    }, notes=(
        "Life is a caller-curve interpolation over a finite-plane Findley parameter evaluated with the nested stress-history request.",
        "The result is not an independently validated fatigue law, a code acceptance decision, a probability, a transfer across material conditions, or qualification.",
    ))


def _validate_life_context(request: CriticalPlaneFindleyCalibratedLife, context: RunContext) -> None:
    _validate_context(request.stress_history, context)


def specifications() -> list[ModelSpec]:
    return [ModelSpec(
        "fatigue.critical_plane_findley_calibrated_life",
        CriticalPlaneFindleyCalibratedLife,
        critical_plane_findley_calibrated_life,
        {
            "governing_findley_parameter_Pa": "Pa",
            "cycles_to_failure": "cycle",
            "supported_parameter_interval_Pa[]": "Pa",
            "log_interpolation_fraction": "1",
        },
        (
            "Uses the independent finite-sample Findley parameter evaluator and an explicitly supplied, digest-bound monotone parameter-life curve.",
            "Life interpolation is piecewise linear in log(parameter) and log(cycles), within the supplied support only.",
            "No fatigue life, calibration, transfer rule or acceptance criterion is inferred from missing inputs.",
        ),
        ("findley_1959_mean_stress_critical_plane", "caller_findley_parameter_life_curve"),
        qualification="user_model",
        context_validator=_validate_life_context,
    )]
