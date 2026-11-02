"""Map a computed finite-plane GSA value through a caller-owned life curve."""

from __future__ import annotations

import math
from typing import Literal

from pydantic import Field, model_validator

from .contracts import Calculation, Contract, Evidence, Positive, canonical_digest
from .models.ince_glinka_gsa import InceGlinkaGSACalculation, ince_glinka_gsa_parameter
from .registry import ModelSpec


class GSALifeCurvePoint(Contract):
    """One caller-provided GSA-to-life calibration point."""

    point_id: str = Field(min_length=1)
    gsa_parameter: Positive
    cycles_to_failure: Positive
    source_record_id: str = Field(min_length=1)
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def evidence_identifies_record(self):
        if self.source_record_id not in {item.source_id for item in self.evidence}:
            raise ValueError("each curve point source_record_id must be identified in Evidence")
        return self


class InceGlinkaGSACurveLife(Contract):
    """Evaluate one repeated closed cycle against a caller-reviewed life curve.

    The curve abscissa is the dimensionless maximum GSA parameter returned by
    ``ince_glinka_gsa_parameter``. Interpolation is linear in log(GSA) and
    log(cycles), strictly between caller-supplied points.
    """

    schema_version: Literal["matintegrity.ince_glinka_gsa_curve_life.v1"] = (
        "matintegrity.ince_glinka_gsa_curve_life.v1"
    )
    calculation: InceGlinkaGSACalculation
    calibration_id: str = Field(min_length=1)
    calibration_material_condition_id: str = Field(min_length=1)
    cycles_definition: str = Field(min_length=1)
    curve_points: tuple[GSALifeCurvePoint, ...] = Field(min_length=2, max_length=10000)
    interpolation_reviewed: bool
    repeated_cycle_assumption_reviewed: bool
    material_condition_and_curve_applicability_reviewed: bool

    @model_validator(mode="after")
    def curve_contract(self):
        if self.calculation.material_condition_id != self.calibration_material_condition_id:
            raise ValueError("GSA calculation and life curve must use the same material condition")
        if len({point.point_id for point in self.curve_points}) != len(self.curve_points):
            raise ValueError("life-curve point IDs must be unique")
        for left, right in zip(self.curve_points[:-1], self.curve_points[1:], strict=True):
            if right.gsa_parameter <= left.gsa_parameter:
                raise ValueError("curve points must be supplied in strictly increasing GSA order")
            if right.cycles_to_failure >= left.cycles_to_failure:
                raise ValueError("cycles to failure must strictly decrease with increasing GSA")
        return self


def evaluate_ince_glinka_gsa_curve_life(request: InceGlinkaGSACurveLife) -> Calculation:
    """Return an interpolation-conditional repeated-cycle life estimate.

    The caller's sampled tensor cycle and finite plane set are evaluated by the
    existing GSA calculator. No cycle counting, fatigue coefficients, curve
    fitting, extrapolation, probability or acceptance decision is introduced.
    """
    digest = canonical_digest(request.model_dump(mode="json"))
    missing = [
        name
        for name, accepted in (
            ("interpolation_reviewed", request.interpolation_reviewed),
            ("repeated_cycle_assumption_reviewed", request.repeated_cycle_assumption_reviewed),
            (
                "material_condition_and_curve_applicability_reviewed",
                request.material_condition_and_curve_applicability_reviewed,
            ),
        )
        if not accepted
    ]
    lineage = {
        "assessment_id": request.calculation.assessment_id,
        "physical_scope_id": request.calculation.physical_scope_id,
        "material_condition_id": request.calculation.material_condition_id,
        "location_id": request.calculation.location_id,
        "calibration_id": request.calibration_id,
        "calibration_material_condition_id": request.calibration_material_condition_id,
        "cycles_definition": request.cycles_definition,
        "input_sha256": digest,
        "curve_point_ids": [point.point_id for point in request.curve_points],
        "curve_point_source_record_ids": [point.source_record_id for point in request.curve_points],
        "curve_evidence": [
            evidence.model_dump(mode="json")
            for point in request.curve_points
            for evidence in point.evidence
        ],
        "calculation_input_sha256": canonical_digest(request.calculation.model_dump(mode="json")),
        "cycle_counting": "not_performed_one_repeated_closed_cycle_assumption",
        "extrapolation": "not_performed",
    }
    if missing:
        return Calculation(
            status="needs_data",
            values=lineage | {"missing_reviews": missing},
            notes=("Life mapping is withheld until the interpolation, repeated-cycle and applicability bases are reviewed.",),
        )

    gsa = ince_glinka_gsa_parameter(request.calculation)
    if gsa.status != "computed":
        return Calculation(
            status=gsa.status,
            values=lineage | {
                "upstream_gsa_status": gsa.status,
                "upstream_gsa_values": gsa.values,
                "cycles_to_failure": None,
            },
            notes=("The upstream finite-plane GSA calculation did not produce a value for life mapping.",),
        )
    target = gsa.values.get("maximum_gsa_parameter")
    if not isinstance(target, (int, float)) or not math.isfinite(target) or target <= 0:
        return Calculation(
            status="out_of_scope",
            values=lineage | {"reason": "upstream_gsa_value_outside_positive_finite_support", "cycles_to_failure": None},
        )

    points = request.curve_points
    if target < points[0].gsa_parameter or target > points[-1].gsa_parameter:
        return Calculation(
            status="out_of_scope",
            values=lineage | {
                "gsa_parameter": target,
                "curve_gsa_support": [points[0].gsa_parameter, points[-1].gsa_parameter],
                "cycles_to_failure": None,
                "reason": "GSA value lies outside caller-supplied life-curve support; extrapolation is withheld",
            },
            notes=("Life is reported only within the supplied calibration curve support.",),
        )

    for point in points:
        if target == point.gsa_parameter:
            cycles = point.cycles_to_failure
            bracket = (point.point_id, point.point_id)
            fraction = 0.0
            break
    else:
        cycles = math.nan
        bracket = ("", "")
        fraction = math.nan
        for left, right in zip(points[:-1], points[1:], strict=True):
            if left.gsa_parameter < target < right.gsa_parameter:
                fraction = (
                    math.log(target) - math.log(left.gsa_parameter)
                ) / (math.log(right.gsa_parameter) - math.log(left.gsa_parameter))
                log_cycles = math.log(left.cycles_to_failure) + fraction * (
                    math.log(right.cycles_to_failure) - math.log(left.cycles_to_failure)
                )
                cycles = math.exp(log_cycles)
                bracket = (left.point_id, right.point_id)
                break
    if not math.isfinite(cycles) or cycles <= 0:
        return Calculation(
            status="out_of_scope",
            values=lineage | {"reason": "life_curve_interpolation_not_representable", "cycles_to_failure": None},
        )
    return Calculation(
        status="computed",
        values=lineage | {
            "gsa_parameter": float(target),
            "critical_plane_id": gsa.values.get("critical_plane_id"),
            "cycles_to_failure": cycles,
            "interpolation_point_ids": list(bracket),
            "log_gsa_interpolation_fraction": fraction,
            "curve_gsa_support": [points[0].gsa_parameter, points[-1].gsa_parameter],
            "life_mapping_basis": "caller-supplied finite monotone GSA-to-life curve; log-log interpolation only",
            "fatigue_life_qualification_inferred": False,
        },
        notes=(
            "The result is conditional on the caller's closed sampled cycle, finite plane set, curve and repeated-cycle assumption.",
            "No cycle counting, curve fitting, extrapolation, material transfer, acceptance decision or failure probability is performed.",
        ),
    )


def specifications() -> list[ModelSpec]:
    return [ModelSpec(
        "fatigue.ince_glinka_gsa_life_from_curve",
        InceGlinkaGSACurveLife,
        evaluate_ince_glinka_gsa_curve_life,
        {
            "gsa_parameter": "1",
            "cycles_to_failure": "cycle",
            "curve_gsa_support": "1",
        },
        (
            "One caller-reviewed repeated closed tensor cycle evaluated over the finite supplied plane set.",
            "The caller supplies an ordered monotone GSA-to-life curve with record-level Evidence.",
            "Log-log interpolation is restricted to the supplied support; no curve fit, cycle counting, extrapolation or qualification.",
        ),
        ("caller_ince_glinka_gsa_life_curve",),
        qualification="user_model",
    )]
