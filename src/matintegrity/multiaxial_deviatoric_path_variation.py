"""Finite-sample deviatoric and hydrostatic stress-path variation descriptors."""

from __future__ import annotations

import math

from pydantic import Field, model_validator

from .contracts import Calculation, Contract, canonical_digest
from .multiaxial_stress_invariant_history import SampledStressInvariantHistory
from .registry import ModelSpec

MODEL_ID = "fatigue.multiaxial_deviatoric_stress_path_variation"
SOURCE_ID = "caller_finite_tensor_stress_path_variation"


class MultiaxialDeviatoricStressPathVariation(Contract):
    """Characterize a caller-declared closed stress path without inferring damage."""

    analysis_id: str = Field(min_length=1)
    stress_history: SampledStressInvariantHistory
    stress_history_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    maximum_increment_evaluations: int = Field(default=10000, ge=2, le=100000)
    closed_path_and_basis_reviewed: bool
    path_sampling_scope_reviewed: bool

    @model_validator(mode="after")
    def verify_nested_history(self):
        if canonical_digest(self.stress_history.model_dump(mode="json")) != self.stress_history_sha256:
            raise ValueError("stress-history digest differs from the nested history contract")
        return self


def _deviatoric(row: list[float]) -> tuple[float, ...]:
    mean_normal = (row[0] + row[1] + row[2]) / 3.0
    return (row[0] - mean_normal, row[1] - mean_normal, row[2] - mean_normal, row[3], row[4], row[5])


def _sqrt_j2_distance(left: tuple[float, ...], right: tuple[float, ...]) -> float:
    delta = tuple(a - b for a, b in zip(left, right, strict=True))
    j2 = 0.5 * (delta[0] ** 2 + delta[1] ** 2 + delta[2] ** 2) + (
        delta[3] ** 2 + delta[4] ** 2 + delta[5] ** 2
    )
    return math.sqrt(j2)


def evaluate_multiaxial_deviatoric_stress_path_variation(
    request: MultiaxialDeviatoricStressPathVariation,
) -> Calculation:
    """Sum exact adjacent-sample increments under the J2 metric and |Δp|."""
    history = request.stress_history
    rows = history.stress_tensor_components_Pa
    segment_count = len(rows) - 1
    digest = canonical_digest(request.model_dump(mode="json"))
    base = {
        "analysis_id": request.analysis_id,
        "material_condition_id": history.material_condition_id,
        "location_id": history.location_id,
        "history_source_id": history.source_id,
        "history_source_sha256": history.source_sha256,
        "stress_history_sha256": request.stress_history_sha256,
        "input_sha256": digest,
        "tensor_component_order": ["xx", "yy", "zz", "xy", "yz", "zx"],
        "finite_path_definition": "sum_of_adjacent_sample_sqrt_J2_deviatoric_distances_and_sum_of_absolute_hydrostatic_increments",
    }
    if not all((history.closed_cycle_and_sample_order_reviewed, history.stress_tensor_basis_reviewed,
                request.closed_path_and_basis_reviewed, request.path_sampling_scope_reviewed)):
        return Calculation(status="needs_data", values=base | {
            "reason": "reviewed_closed_cycle_tensor_basis_and_sampling_scope_required",
            "deviatoric_path_variation_Pa": None,
            "hydrostatic_path_variation_Pa": None,
        })
    if segment_count > request.maximum_increment_evaluations:
        return Calculation(status="out_of_scope", values=base | {
            "reason": "finite_path_increment_work_budget_exceeded",
            "segment_count": segment_count,
            "maximum_increment_evaluations": request.maximum_increment_evaluations,
            "deviatoric_path_variation_Pa": None,
            "hydrostatic_path_variation_Pa": None,
        })

    deviatoric = [_deviatoric(row) for row in rows]
    hydrostatic = [(row[0] + row[1] + row[2]) / 3.0 for row in rows]
    try:
        deviatoric_increments = [
            _sqrt_j2_distance(deviatoric[i], deviatoric[i + 1]) for i in range(segment_count)
        ]
        hydrostatic_increments = [abs(hydrostatic[i + 1] - hydrostatic[i]) for i in range(segment_count)]
        deviatoric_variation = math.fsum(deviatoric_increments)
        hydrostatic_variation = math.fsum(hydrostatic_increments)
        max_deviatoric_increment = max(deviatoric_increments)
        max_hydrostatic_increment = max(hydrostatic_increments)
    except (ArithmeticError, OverflowError, ValueError):
        deviatoric_variation = hydrostatic_variation = math.inf
        max_deviatoric_increment = max_hydrostatic_increment = math.inf
    if not all(math.isfinite(value) for value in (
        deviatoric_variation, hydrostatic_variation, max_deviatoric_increment, max_hydrostatic_increment
    )):
        return Calculation(status="out_of_scope", values=base | {
            "reason": "finite_sample_path_variation_arithmetic_nonfinite",
            "deviatoric_path_variation_Pa": None,
            "hydrostatic_path_variation_Pa": None,
        })
    return Calculation(values=base | {
        "status": "computed",
        "sample_count": len(rows),
        "segment_count": segment_count,
        "deviatoric_path_variation_Pa": deviatoric_variation,
        "hydrostatic_path_variation_Pa": hydrostatic_variation,
        "maximum_single_segment_deviatoric_increment_Pa": max_deviatoric_increment,
        "maximum_single_segment_hydrostatic_increment_Pa": max_hydrostatic_increment,
        "deviatoric_segment_increments_Pa": deviatoric_increments,
        "hydrostatic_segment_increments_Pa": hydrostatic_increments,
        "meaning": "geometric total variation along the ordered finite samples; not damage or a fatigue criterion",
        "limitations": [
            "Each segment is represented only by its two supplied endpoints; no unsampled extrema or continuous history is reconstructed.",
            "Path variation depends on sampling density and retains the caller's ordered sample sequence.",
            "The result is a geometric descriptor, not a material response, damage, fatigue life, probability, acceptance, or qualification.",
            "Do not compare results across different tensor bases, units, material locations, or sampling protocols without reviewed harmonization.",
        ],
    })


def specifications() -> list[ModelSpec]:
    return [ModelSpec(
        model_id=MODEL_ID,
        input_type=MultiaxialDeviatoricStressPathVariation,
        evaluator=evaluate_multiaxial_deviatoric_stress_path_variation,
        units={
            "deviatoric_path_variation_Pa": "Pa",
            "hydrostatic_path_variation_Pa": "Pa",
            "maximum_single_segment_deviatoric_increment_Pa": "Pa",
            "maximum_single_segment_hydrostatic_increment_Pa": "Pa",
            "deviatoric_segment_increments_Pa[]": "Pa",
            "hydrostatic_segment_increments_Pa[]": "Pa",
        },
        assumptions=(
            "Finite path variation is the sum of adjacent-sample increments; deviatoric increments use sqrt(J2) distance.",
            "The exact caller sample order and closed cycle are preserved; no interpolation, cycle counting, or damage conversion is inferred.",
            "The output is a path descriptor and not a fatigue criterion, life, probability, acceptance decision, or qualification.",
        ),
        source_ids=(SOURCE_ID,),
        qualification="user_model",
    )]
