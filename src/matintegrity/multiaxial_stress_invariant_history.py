"""Finite-sample stress-invariant descriptors for one caller-reviewed closed cycle.

These descriptors are intended as transparent inputs to a separately calibrated
fatigue criterion. They are not a fatigue-life or acceptance model.
"""

from __future__ import annotations

import math

from pydantic import Field, model_validator

from .contracts import Contract, canonical_digest
from .registry import ModelSpec


MODEL_ID = "fatigue.sampled_stress_invariant_history"
SOURCE_ID = "caller_sampled_stress_invariant_history"


class SampledStressInvariantHistory(Contract):
    """Ordered symmetric stress tensors at caller-declared cycle samples."""

    analysis_id: str = Field(min_length=1)
    material_condition_id: str = Field(min_length=1)
    location_id: str = Field(min_length=1)
    source_id: str = Field(min_length=1)
    source_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    sample_ids: list[str] = Field(min_length=3, max_length=10000)
    stress_tensor_components_Pa: list[list[float]] = Field(min_length=3, max_length=10000)
    tensor_component_order: tuple[str, ...] = ("xx", "yy", "zz", "xy", "yz", "zx")
    closed_cycle_and_sample_order_reviewed: bool
    stress_tensor_basis_reviewed: bool
    maximum_pair_evaluations: int = Field(default=2_000_000, ge=1, le=20_000_000)

    @model_validator(mode="after")
    def aligned_closed_history(self):
        if self.tensor_component_order != ("xx", "yy", "zz", "xy", "yz", "zx"):
            raise ValueError("stress tensors must use [xx, yy, zz, xy, yz, zx] order")
        if len(self.sample_ids) != len(self.stress_tensor_components_Pa):
            raise ValueError("sample identifiers and stress tensors must align")
        if len(set(self.sample_ids)) != len(self.sample_ids):
            raise ValueError("sample identifiers must be unique while retaining path order")
        if any(len(row) != 6 for row in self.stress_tensor_components_Pa):
            raise ValueError("each stress tensor requires six symmetric components")
        if self.stress_tensor_components_Pa[0] != self.stress_tensor_components_Pa[-1]:
            raise ValueError("closed cycle requires exactly matching endpoint stress tensors")
        if any(not math.isfinite(value) for row in self.stress_tensor_components_Pa for value in row):
            raise ValueError("stress samples must be finite")
        return self


def _j2_metric_distance(left: tuple[float, ...], right: tuple[float, ...]) -> float:
    """Return sqrt(J2) for a deviatoric tensor difference, in Pa."""
    delta = tuple(a - b for a, b in zip(left, right, strict=True))
    return math.sqrt(0.5 * (
        delta[0] * delta[0] + delta[1] * delta[1] + delta[2] * delta[2]
        + 2.0 * (delta[3] * delta[3] + delta[4] * delta[4] + delta[5] * delta[5])
    ))


def evaluate_sampled_stress_invariant_history(request: SampledStressInvariantHistory) -> dict:
    """Summarize hydrostatic peak and finite sampled deviatoric-path diameter.

    The half-diameter equals a conventional amplitude for a collinear path. For
    a non-proportional path it is only the maximum pairwise sampled separation
    divided by two; it is not a minimum enclosing hypersphere or a continuous
    path extremum.
    """
    payload = request.model_dump(mode="json")
    input_digest = canonical_digest(payload)
    base = {
        "analysis_id": request.analysis_id,
        "material_condition_id": request.material_condition_id,
        "location_id": request.location_id,
        "source_id": request.source_id,
        "source_sha256": request.source_sha256,
        "input_sha256": input_digest,
        "sample_count": len(request.sample_ids),
    }
    if not request.closed_cycle_and_sample_order_reviewed or not request.stress_tensor_basis_reviewed:
        return base | {
            "status": "needs_data",
            "reason": "reviewed_closed_cycle_order_and_stress_tensor_basis_required",
            "values": None,
        }
    pair_count = len(request.sample_ids) * (len(request.sample_ids) - 1) // 2
    if pair_count > request.maximum_pair_evaluations:
        return base | {
            "status": "out_of_scope",
            "reason": "pairwise_sample_work_limit_exceeded",
            "pair_evaluations_required": pair_count,
            "pair_evaluations_allowed": request.maximum_pair_evaluations,
            "values": None,
        }

    rows = request.stress_tensor_components_Pa
    hydrostatic = [(row[0] + row[1] + row[2]) / 3.0 for row in rows]
    deviatoric = [
        (row[0] - mean, row[1] - mean, row[2] - mean, row[3], row[4], row[5])
        for row, mean in zip(rows, hydrostatic, strict=True)
    ]
    peak_index = max(range(len(rows)), key=lambda index: hydrostatic[index])
    maximum_distance = -1.0
    witness = (0, 0)
    for left_index in range(len(rows) - 1):
        for right_index in range(left_index + 1, len(rows)):
            distance = _j2_metric_distance(deviatoric[left_index], deviatoric[right_index])
            if distance > maximum_distance:
                maximum_distance = distance
                witness = (left_index, right_index)
    return base | {
        "status": "computed",
        "values": {
            "maximum_sampled_hydrostatic_stress_Pa": hydrostatic[peak_index],
            "maximum_hydrostatic_sample_id": request.sample_ids[peak_index],
            "sampled_deviatoric_J2_metric_diameter_Pa": maximum_distance,
            "sampled_deviatoric_J2_half_diameter_Pa": maximum_distance / 2.0,
            "diameter_witness_sample_ids": [request.sample_ids[witness[0]], request.sample_ids[witness[1]]],
            "amplitude_interpretation": (
                "half the maximum pairwise sqrt(J2) separation among supplied samples; "
                "conventional amplitude only for a collinear stress path"
            ),
            "scope": "finite supplied samples only; no interpolation, cycle extraction, fatigue law, life, probability, acceptance or qualification",
        },
    }


def _registered_evaluator(request: SampledStressInvariantHistory):
    from .contracts import Calculation

    result = evaluate_sampled_stress_invariant_history(request)
    status = result.pop("status")
    return Calculation(status=status, values=result)


def specifications() -> list[ModelSpec]:
    return [ModelSpec(
        model_id=MODEL_ID,
        input_type=SampledStressInvariantHistory,
        evaluator=_registered_evaluator,
        units={
            "values.maximum_sampled_hydrostatic_stress_Pa": "Pa",
            "values.sampled_deviatoric_J2_metric_diameter_Pa": "Pa",
            "values.sampled_deviatoric_J2_half_diameter_Pa": "Pa",
        },
        assumptions=(
            "Only caller-reviewed, exactly closed finite samples in the declared symmetric tensor basis are summarized.",
            "The half-diameter is a conventional amplitude only for a collinear stress path; other paths retain a finite-sample descriptor interpretation.",
            "No interpolation, cycle extraction, fatigue law, life, probability, acceptance or qualification is inferred.",
        ),
        source_ids=(SOURCE_ID,),
        qualification="user_model",
    )]
