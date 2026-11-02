"""Finite sampled oriented area of a closed two-component shear-strain path."""

from __future__ import annotations

import math

from pydantic import Field, model_validator

from .contracts import Calculation, Contract, Evidence, canonical_digest
from .registry import ModelSpec


class SampledShearPathArea(Contract):
    """Shoelace area for a caller-reviewed closed path in a plane's shear space."""

    analysis_id: str = Field(min_length=1)
    source_id: str = Field(min_length=1)
    source_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    evidence: Evidence
    sample_ids: list[str] = Field(min_length=3, max_length=100000)
    shear_strain_a: list[float] = Field(min_length=3, max_length=100000)
    shear_strain_b: list[float] = Field(min_length=3, max_length=100000)
    closure_tolerance: float = Field(ge=0, le=0.1)
    plane_and_axis_orientation_reviewed: bool
    path_order_and_closure_reviewed: bool
    engineering_shear_convention_reviewed: bool

    @model_validator(mode="after")
    def aligned_finite_sources(self):
        size = len(self.sample_ids)
        if len(self.shear_strain_a) != size or len(self.shear_strain_b) != size:
            raise ValueError("sample IDs and both shear-strain coordinates must have equal lengths")
        if len(set(self.sample_ids)) != size:
            raise ValueError("sample IDs must be unique")
        if not all(math.isfinite(value) for value in (*self.shear_strain_a, *self.shear_strain_b)):
            raise ValueError("shear-strain coordinates must be finite")
        if self.evidence.source_id != self.source_id or self.evidence.sha256 != self.source_sha256:
            raise ValueError("Evidence must match the declared source ID and digest")
        return self


def evaluate_sampled_shear_path_area(request: SampledShearPathArea) -> Calculation:
    """Calculate signed polygon area; no fatigue damage or life is inferred."""
    x, y = request.shear_strain_a, request.shear_strain_b
    base = {
        "analysis_id": request.analysis_id,
        "source_id": request.source_id,
        "source_sha256": request.source_sha256,
        "input_sha256": canonical_digest(request.model_dump(mode="json")),
        "sample_count": len(x),
        "area_unit": "strain^2",
        "area_method": "chronological shoelace sum with final-to-first closure edge",
        "fatigue_damage_or_life": None,
    }
    if not all((
        request.plane_and_axis_orientation_reviewed,
        request.path_order_and_closure_reviewed,
        request.engineering_shear_convention_reviewed,
    )):
        return Calculation(status="needs_data", values=base | {
            "reason": "plane_path_order_closure_and_shear_convention_reviews_required",
            "signed_area": None,
            "absolute_area": None,
        })
    dx = x[-1] - x[0]
    dy = y[-1] - y[0]
    if math.hypot(dx, dy) > request.closure_tolerance:
        return Calculation(status="needs_data", values=base | {
            "reason": "path_endpoints_exceed_caller_closure_tolerance",
            "endpoint_gap": math.hypot(dx, dy),
            "closure_tolerance": request.closure_tolerance,
            "signed_area": None,
            "absolute_area": None,
        })
    terms = [
        x[index] * y[(index + 1) % len(x)] - x[(index + 1) % len(x)] * y[index]
        for index in range(len(x))
    ]
    try:
        signed_area = 0.5 * math.fsum(terms)
    except (OverflowError, ValueError):
        signed_area = math.inf
    if not math.isfinite(signed_area):
        return Calculation(status="out_of_scope", values=base | {
            "reason": "finite_coordinates_produce_nonfinite_polygon_area",
            "signed_area": None,
            "absolute_area": None,
        })
    return Calculation(values=base | {
        "status": "computed",
        "signed_area": signed_area,
        "absolute_area": abs(signed_area),
        "closure_endpoint_gap": math.hypot(dx, dy),
        "closure_tolerance": request.closure_tolerance,
        "orientation": "positive" if signed_area > 0 else "negative" if signed_area < 0 else "zero",
        "limitations": [
            "The result is a finite polygon descriptor in the caller's selected two-axis shear-strain coordinates.",
            "No interpolation, smoothing, path reconstruction, normalization, cycle counting or omitted-sample correction is performed.",
            "The area is not a calibrated nonproportionality factor or a material damage/life law; qualification is external.",
        ],
    })


def specifications() -> list[ModelSpec]:
    return [ModelSpec(
        "fatigue.multiaxial_sampled_shear_path_area",
        SampledShearPathArea,
        evaluate_sampled_shear_path_area,
        {"signed_area": "strain^2", "absolute_area": "strain^2", "closure_endpoint_gap": "strain"},
        (
            "Uses caller-ordered finite samples and caller-reviewed shear axes on one selected material plane.",
            "A caller tolerance gates closed-cycle endpoint mismatch; the polygon includes a last-to-first closure edge.",
            "This unnormalized geometric descriptor does not predict fatigue damage, life, acceptance or qualification.",
        ),
        ("caller_finite_shear_path_polygon_area_nonproportional_loading_descriptor",),
        qualification="user_model",
    )]
