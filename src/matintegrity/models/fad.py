"""Provider-driven failure-assessment points without bundled standard curves."""

from __future__ import annotations

import math
from typing import Literal

import numpy as np
from pydantic import Field, model_validator

from ..contracts import Calculation, Contract, Evidence, Nonnegative, Positive, canonical_digest
from ..registry import ModelSpec


class FailureAssessmentCurve(Contract):
    curve_id: str = Field(min_length=1)
    assessment_basis_id: str = Field(min_length=1)
    load_ratio: tuple[Nonnegative, ...] = Field(min_length=2, max_length=1000)
    allowable_toughness_ratio: tuple[Nonnegative, ...] = Field(min_length=2, max_length=1000)
    interpolation: Literal["linear"] = "linear"
    validity_description: str = Field(min_length=1)
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_curve(self):
        if len(self.load_ratio) != len(self.allowable_toughness_ratio):
            raise ValueError("one allowable toughness ratio is required per load-ratio knot")
        if self.load_ratio[0] != 0:
            raise ValueError("the declared FAD curve must start at load ratio zero")
        if np.any(np.diff(self.load_ratio) <= 0):
            raise ValueError("load-ratio knots must be strictly increasing")
        if self.allowable_toughness_ratio[0] <= 0:
            raise ValueError("the zero-load allowable toughness ratio must be positive")
        if np.any(np.diff(self.allowable_toughness_ratio) > 0):
            raise ValueError("the declared allowable toughness boundary must be nonincreasing")
        if any(not item.license_id for item in self.evidence):
            raise ValueError("the FAD provider needs a declared source license or entitlement")
        return self


class FailureAssessmentPoint(Contract):
    point_id: str = Field(min_length=1)
    load_case_id: str = Field(min_length=1)
    location_id: str = Field(min_length=1)
    material_condition_id: str = Field(min_length=1)
    geometry_solution_id: str = Field(min_length=1)
    reference_stress_solution_id: str = Field(min_length=1)
    toughness_source_id: str = Field(min_length=1)
    effective_stress_intensity_Pa_sqrt_m: Nonnegative
    fracture_resistance_Pa_sqrt_m: Positive
    reference_stress_Pa: Nonnegative
    normalizing_strength_Pa: Positive


class FailureAssessment(Contract):
    material_condition_id: str = Field(min_length=1)
    curve: FailureAssessmentCurve
    points: tuple[FailureAssessmentPoint, ...] = Field(min_length=1, max_length=10000)
    linear_elastic_k_solution_reviewed: bool
    reference_stress_solution_reviewed: bool
    toughness_applicability_reviewed: bool
    load_combination_reviewed: bool
    curve_applicability_reviewed: bool

    @model_validator(mode="after")
    def unique_points(self):
        identities = [(p.point_id, p.load_case_id, p.location_id) for p in self.points]
        if len(identities) != len(set(identities)):
            raise ValueError("point, load-case and location identities must be unique")
        return self


def assess_failure_diagram(x: FailureAssessment) -> Calculation:
    reviews = (
        x.linear_elastic_k_solution_reviewed,
        x.reference_stress_solution_reviewed,
        x.toughness_applicability_reviewed,
        x.load_combination_reviewed,
        x.curve_applicability_reviewed,
    )
    if not all(reviews):
        return Calculation(
            status="needs_data",
            values={},
            notes=(
                "Review the K solution, reference-stress solution, toughness applicability, load combination and user-supplied boundary before evaluation.",
            ),
        )
    if any(point.material_condition_id != x.material_condition_id for point in x.points):
        return Calculation(
            status="needs_data",
            values={},
            notes=("Every point must match the assessment material condition exactly.",),
        )

    maximum_lr = x.curve.load_ratio[-1]
    rows = []
    supported = True
    any_outside = False
    for point in x.points:
        kr = point.effective_stress_intensity_Pa_sqrt_m / point.fracture_resistance_Pa_sqrt_m
        lr = point.reference_stress_Pa / point.normalizing_strength_Pa
        if not math.isfinite(kr) or not math.isfinite(lr):
            return Calculation(
                status="out_of_scope",
                values={},
                notes=("A normalized assessment coordinate exceeds the finite numerical range.",),
            )
        row = dict(
            point_id=point.point_id,
            load_case_id=point.load_case_id,
            location_id=point.location_id,
            material_condition_id=point.material_condition_id,
            geometry_solution_id=point.geometry_solution_id,
            reference_stress_solution_id=point.reference_stress_solution_id,
            toughness_source_id=point.toughness_source_id,
            toughness_ratio_Kr=kr,
            load_ratio_Lr=lr,
        )
        if lr > maximum_lr:
            supported = False
            row.update(
                allowable_toughness_ratio=None,
                vertical_toughness_ratio_margin=None,
                point_outcome="outside_declared_curve_support",
            )
        else:
            allowable = float(np.interp(lr, x.curve.load_ratio, x.curve.allowable_toughness_ratio))
            margin = allowable - kr
            outside = kr > allowable
            any_outside = any_outside or outside
            row.update(
                allowable_toughness_ratio=allowable,
                vertical_toughness_ratio_margin=margin,
                point_outcome=("outside_declared_boundary" if outside else "inside_or_on_declared_boundary"),
            )
        rows.append(row)

    if not supported:
        status = "out_of_scope"
        outcome = "unknown"
    else:
        status = "computed"
        outcome = "not_satisfied" if any_outside else "satisfied"
    finite_margins = [
        row["vertical_toughness_ratio_margin"]
        for row in rows
        if row["vertical_toughness_ratio_margin"] is not None
    ]
    return Calculation(
        status=status,
        values=dict(
            curve_id=x.curve.curve_id,
            assessment_basis_id=x.curve.assessment_basis_id,
            maximum_supported_load_ratio_Lr=maximum_lr,
            points=rows,
            declared_boundary_outcome=outcome,
            minimum_supported_vertical_toughness_ratio_margin=(
                min(finite_margins) if finite_margins else None
            ),
            curve_digest=canonical_digest(x.curve.model_dump(mode="json")),
        ),
        notes=(
            "Kr is supplied effective mode-I stress intensity divided by supplied fracture resistance; Lr is supplied reference stress divided by supplied normalizing strength. The declared boundary is linearly interpolated without extrapolation.",
            "The curve, K/reference-stress solutions, toughness and strength are caller-controlled qualified inputs. No proprietary standard curve, residual-stress interaction rule, constraint correction, safety factor or acceptance table is bundled.",
            "Inside a declared curve is a deterministic screening outcome, not proof of test validity, code acceptance, remaining life or failure probability. Points beyond the final Lr knot remain outside scope rather than being clipped.",
        ),
    )


def specifications():
    return [
        ModelSpec(
            "structural.failure_assessment_points",
            FailureAssessment,
            assess_failure_diagram,
            {
                "points.toughness_ratio_Kr": "1",
                "points.load_ratio_Lr": "1",
                "points.allowable_toughness_ratio": "1",
                "points.vertical_toughness_ratio_margin": "1",
                "minimum_supported_vertical_toughness_ratio_margin": "1",
                "maximum_supported_load_ratio_Lr": "1",
            },
            (
                "Deterministic assessment points against a caller-licensed, nonincreasing piecewise-linear FAD boundary; all physical solutions and applicability remain external evidence.",
            ),
            ("linear_elastic_fracture_ratios", "user_supplied_failure_assessment_boundary"),
        )
    ]
