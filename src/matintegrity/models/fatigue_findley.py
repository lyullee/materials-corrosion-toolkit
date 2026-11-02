"""Caller-calibrated finite-plane Findley stress parameter screening."""

from __future__ import annotations

import math
from typing import Literal

from pydantic import Field, model_validator

from ..contracts import Calculation, Contract, Evidence, Nonnegative, Positive, RunContext, canonical_digest
from ..registry import ModelSpec
from .fatigue import CriticalPlaneCandidate


class CriticalPlaneFindleyStressHistory(Contract):
    """Digest-bound Cauchy stress samples for one caller-declared representative cycle."""

    assessment_id: str = Field(min_length=1)
    asset_id: str = Field(min_length=1)
    location_id: str = Field(min_length=1)
    time_basis_id: str = Field(min_length=1)
    material_condition_id: str = Field(min_length=1)
    load_case_id: str = Field(min_length=1)
    cycle_id: str = Field(min_length=1)
    tensor_source_id: str = Field(min_length=1)
    tensor_provider_id: str = Field(min_length=1)
    tensor_provider_revision: str = Field(min_length=1)
    tensor_record_id: str = Field(min_length=1)
    tensor_content_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    coordinate_frame_id: str = Field(min_length=1)
    stress_measure: Literal["cauchy"]
    component_order: Literal["xx,yy,zz,xy,yz,zx"]
    sample_ids: tuple[str, ...] = Field(min_length=3, max_length=20_000)
    sample_times_s: tuple[Nonnegative, ...] | None = None
    stress_tensor_components_Pa: tuple[tuple[float, float, float, float, float, float], ...] = Field(
        min_length=3, max_length=20_000
    )
    candidate_planes: tuple[CriticalPlaneCandidate, ...] = Field(min_length=1, max_length=20_000)
    representative_cycle_declared: bool
    maximum_stress_closure_error_Pa: Nonnegative
    findley_coefficient: Nonnegative
    reference_parameter_strength_Pa: Positive
    reference_life_cycles: Positive
    calibration_provider_id: str = Field(min_length=1)
    calibration_provider_revision: str = Field(min_length=1)
    calibration_record_id: str = Field(min_length=1)
    calibration_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    evidence: tuple[Evidence, ...] = Field(min_length=2)
    usage_rights_evidence: tuple[Evidence, ...] = Field(min_length=1)
    maximum_shear_pair_evaluations: int = Field(default=50_000_000, ge=1, le=2_000_000_000)
    tensor_units_and_component_order_reviewed: bool
    candidate_plane_set_and_coverage_reviewed: bool
    cycle_definition_and_closure_reviewed: bool
    findley_coefficient_and_calibration_basis_reviewed: bool
    calibration_same_material_and_reference_life_reviewed: bool
    usage_rights_reviewed: bool
    computational_use_authorized: bool

    @model_validator(mode="after")
    def validate_history_and_evidence(self):
        count = len(self.sample_ids)
        if len(set(self.sample_ids)) != count:
            raise ValueError("sample IDs must be unique and preserve supplied cycle order")
        if len(self.stress_tensor_components_Pa) != count:
            raise ValueError("stress tensor samples must align with sample IDs")
        if self.sample_times_s is not None:
            if len(self.sample_times_s) != count or any(
                right <= left for left, right in zip(self.sample_times_s[:-1], self.sample_times_s[1:], strict=True)
            ):
                raise ValueError("optional sample times must align and increase strictly")
        plane_ids = tuple(plane.plane_id for plane in self.candidate_planes)
        if len(set(plane_ids)) != len(plane_ids):
            raise ValueError("candidate plane IDs must be unique")
        evidence_keys = {(row.source_id, row.sha256) for row in self.evidence}
        if (self.tensor_provider_id, self.tensor_content_sha256) not in evidence_keys:
            raise ValueError("tensor provider and content digest require matching Evidence")
        if (self.calibration_provider_id, self.calibration_sha256) not in evidence_keys:
            raise ValueError("calibration provider and record digest require matching Evidence")
        if not any(row.source_id and (row.license_id or row.origin == "user_declared") for row in self.usage_rights_evidence):
            raise ValueError("usage-rights evidence must identify a source and license or user-declared entitlement")
        return self


def _cross(left: list[float], right: list[float]) -> list[float]:
    return [
        left[1] * right[2] - left[2] * right[1],
        left[2] * right[0] - left[0] * right[2],
        left[0] * right[1] - left[1] * right[0],
    ]


def _stress_closure_error(first: tuple[float, ...], last: tuple[float, ...]) -> float:
    return math.sqrt(
        (last[0] - first[0]) ** 2
        + (last[1] - first[1]) ** 2
        + (last[2] - first[2]) ** 2
        + 2.0 * ((last[3] - first[3]) ** 2 + (last[4] - first[4]) ** 2 + (last[5] - first[5]) ** 2)
    )


def _project_stress(normal: list[float], direction: list[float], tensor: tuple[float, ...]):
    xx, yy, zz, xy, yz, zx = tensor
    traction = [
        xx * normal[0] + xy * normal[1] + zx * normal[2],
        xy * normal[0] + yy * normal[1] + yz * normal[2],
        zx * normal[0] + yz * normal[1] + zz * normal[2],
    ]
    transverse_direction = _cross(normal, direction)
    normal_stress = math.fsum(normal[index] * traction[index] for index in range(3))
    shear_1 = math.fsum(direction[index] * traction[index] for index in range(3))
    shear_2 = math.fsum(transverse_direction[index] * traction[index] for index in range(3))
    return normal_stress, (shear_1, shear_2)


def critical_plane_findley_parameter(x: CriticalPlaneFindleyStressHistory) -> Calculation:
    """Evaluate the finite-sample Findley parameter on caller-declared planes.

    For each plane, the sampled shear-stress amplitude is one half of the largest
    pairwise Euclidean chord of its two-component in-plane shear-traction path.
    This explicit discrete amplitude construction is retained in the result.
    """
    input_digest = canonical_digest(x.model_dump(mode="json"))
    closure = _stress_closure_error(x.stress_tensor_components_Pa[0], x.stress_tensor_components_Pa[-1])
    base = {
        "assessment_id": x.assessment_id,
        "asset_id": x.asset_id,
        "location_id": x.location_id,
        "time_basis_id": x.time_basis_id,
        "material_condition_id": x.material_condition_id,
        "load_case_id": x.load_case_id,
        "cycle_id": x.cycle_id,
        "tensor_provider_id": x.tensor_provider_id,
        "tensor_provider_revision": x.tensor_provider_revision,
        "tensor_record_id": x.tensor_record_id,
        "tensor_content_sha256": x.tensor_content_sha256,
        "calibration_provider_id": x.calibration_provider_id,
        "calibration_provider_revision": x.calibration_provider_revision,
        "calibration_record_id": x.calibration_record_id,
        "calibration_sha256": x.calibration_sha256,
        "input_digest": input_digest,
        "sample_count": len(x.sample_ids),
        "candidate_plane_count": len(x.candidate_planes),
        "stress_cycle_closure_error_Pa": closure,
        "representative_cycle_usable": (
            x.representative_cycle_declared and closure <= x.maximum_stress_closure_error_Pa
        ),
    }
    required_reviews = {
        "tensor_units_and_component_order_reviewed": x.tensor_units_and_component_order_reviewed,
        "candidate_plane_set_and_coverage_reviewed": x.candidate_plane_set_and_coverage_reviewed,
        "cycle_definition_and_closure_reviewed": x.cycle_definition_and_closure_reviewed,
        "findley_coefficient_and_calibration_basis_reviewed": x.findley_coefficient_and_calibration_basis_reviewed,
        "calibration_same_material_and_reference_life_reviewed": x.calibration_same_material_and_reference_life_reviewed,
        "usage_rights_reviewed": x.usage_rights_reviewed,
        "computational_use_authorized": x.computational_use_authorized,
    }
    missing_reviews = [key for key, reviewed in required_reviews.items() if not reviewed]
    if missing_reviews:
        return Calculation(status="needs_data", values=base | {"missing_reviews": missing_reviews})
    if not base["representative_cycle_usable"]:
        return Calculation(status="needs_data", values=base | {
            "reason": "representative_cycle_or_stress_endpoint_closure_is_unresolved",
            "maximum_stress_closure_error_Pa": x.maximum_stress_closure_error_Pa,
        })
    pair_count = len(x.sample_ids) * (len(x.sample_ids) - 1) // 2
    pair_evaluations = pair_count * len(x.candidate_planes)
    if pair_evaluations > x.maximum_shear_pair_evaluations:
        return Calculation(status="out_of_scope", values=base | {
            "reason": "maximum_shear_pair_evaluation_budget_exceeded",
            "required_shear_pair_evaluations": pair_evaluations,
            "maximum_shear_pair_evaluations": x.maximum_shear_pair_evaluations,
        })

    candidates = []
    for plane in x.candidate_planes:
        normal = plane.normal
        direction = plane.in_plane_direction
        normal_history = []
        shear_history = []
        for tensor in x.stress_tensor_components_Pa:
            try:
                normal_stress, shear_vector = _project_stress(normal, direction, tensor)
            except OverflowError:
                return Calculation(status="out_of_scope", values=base | {
                    "reason": "stress_projection_exceeded_finite_numeric_support",
                    "failed_plane_id": plane.plane_id,
                })
            if not math.isfinite(normal_stress) or not all(math.isfinite(value) for value in shear_vector):
                return Calculation(status="out_of_scope", values=base | {
                    "reason": "stress_projection_exceeded_finite_numeric_support",
                    "failed_plane_id": plane.plane_id,
                })
            normal_history.append(normal_stress)
            shear_history.append(shear_vector)
        maximum_squared = -1.0
        endpoint_indices = (0, 1)
        for first in range(len(shear_history) - 1):
            for second in range(first + 1, len(shear_history)):
                delta_1 = shear_history[second][0] - shear_history[first][0]
                delta_2 = shear_history[second][1] - shear_history[first][1]
                chord = math.hypot(delta_1, delta_2)
                if not math.isfinite(chord):
                    return Calculation(status="out_of_scope", values=base | {
                        "reason": "shear_traction_chord_exceeded_finite_numeric_support",
                        "failed_plane_id": plane.plane_id,
                    })
                squared = chord * chord
                if squared > maximum_squared:
                    maximum_squared = squared
                    endpoint_indices = (first, second)
        shear_amplitude = math.sqrt(maximum_squared) / 2.0
        maximum_normal = max(normal_history)
        normal_index = normal_history.index(maximum_normal)
        parameter = shear_amplitude + x.findley_coefficient * maximum_normal
        if not all(math.isfinite(value) for value in (shear_amplitude, maximum_normal, parameter)):
            return Calculation(status="out_of_scope", values=base | {
                "reason": "Findley_parameter_exceeded_finite_numeric_support",
                "failed_plane_id": plane.plane_id,
            })
        try:
            strength_ratio = parameter / x.reference_parameter_strength_Pa
            strength_margin = x.reference_parameter_strength_Pa - parameter
        except OverflowError:
            return Calculation(status="out_of_scope", values=base | {
                "reason": "reference_strength_comparison_exceeded_finite_numeric_support",
                "failed_plane_id": plane.plane_id,
            })
        if not math.isfinite(strength_ratio) or not math.isfinite(strength_margin):
            return Calculation(status="out_of_scope", values=base | {
                "reason": "reference_strength_comparison_exceeded_finite_numeric_support",
                "failed_plane_id": plane.plane_id,
            })
        first_index, second_index = endpoint_indices
        candidates.append({
            "plane_id": plane.plane_id,
            "normal": list(normal),
            "in_plane_direction": list(direction),
            "maximum_pairwise_shear_chord_Pa": 2.0 * shear_amplitude,
            "shear_stress_amplitude_Pa": shear_amplitude,
            "shear_amplitude_endpoint_sample_ids": [x.sample_ids[first_index], x.sample_ids[second_index]],
            "maximum_normal_stress_Pa": maximum_normal,
            "maximum_normal_stress_sample_id": x.sample_ids[normal_index],
            "findley_parameter_Pa": parameter,
            "reference_parameter_strength_Pa": x.reference_parameter_strength_Pa,
            "reference_life_cycles": x.reference_life_cycles,
            "parameter_to_reference_strength_ratio": strength_ratio,
            "margin_to_reference_strength_Pa": strength_margin,
        })

    maximum_parameter = max(row["findley_parameter_Pa"] for row in candidates)
    scale = max(abs(maximum_parameter), 1.0)
    critical_planes = [
        row["plane_id"] for row in candidates
        if math.isclose(row["findley_parameter_Pa"], maximum_parameter, rel_tol=1e-12, abs_tol=1e-12 * scale)
    ]
    governing = next(row for row in candidates if row["plane_id"] == critical_planes[0])
    return Calculation(values=base | {
        "findley_coefficient": x.findley_coefficient,
        "reference_parameter_strength_Pa": x.reference_parameter_strength_Pa,
        "reference_life_cycles": x.reference_life_cycles,
        "maximum_findley_parameter_Pa": maximum_parameter,
        "governing_plane_id": governing["plane_id"],
        "governing_plane_ids_within_numeric_tie_tolerance": critical_planes,
        "reference_strength_utilization_ratio": governing["parameter_to_reference_strength_ratio"],
        "margin_to_reference_strength_Pa": governing["margin_to_reference_strength_Pa"],
        "candidate_plane_results": candidates,
        "evaluated_shear_pair_count": pair_evaluations,
        "shear_amplitude_construction": "one_half_of_maximum_pairwise_euclidean_chord_of_the_sampled_two_component_in_plane_shear_traction_path",
        "basis": "Finite-sample Findley stress parameter tau_a + k_F * sigma_n,max, evaluated only on the caller-supplied plane set using caller calibration at one reference life.",
    }, notes=(
        "The original Findley parameter combines plane shear-stress amplitude with maximum plane normal stress. This independent implementation keeps the caller's finite tensor samples, candidate planes, calibration and amplitude construction explicit.",
        "The reference-strength ratio is a deterministic comparison to the caller's calibrated strength at one stated life. It is not a life prediction, acceptance rule, fatigue probability or material qualification.",
        "The maximum pairwise shear-vector chord is an explicit discrete-path extension; it does not bound unsampled times or untested plane orientations.",
    ))


def _validate_context(x: CriticalPlaneFindleyStressHistory, context: RunContext) -> None:
    if (x.asset_id, x.location_id, x.time_basis_id) != (
        context.asset_id, context.location_id, context.time_basis
    ):
        raise ValueError("Findley stress-history context must match the pinned asset, location and time basis")


def specifications() -> list[ModelSpec]:
    return [ModelSpec(
        "fatigue.critical_plane_findley_parameter",
        CriticalPlaneFindleyStressHistory,
        critical_plane_findley_parameter,
        {
            "stress_cycle_closure_error_Pa": "Pa",
            "stress_tensor_components_Pa[][]": "Pa",
            "candidate_plane_results[].maximum_pairwise_shear_chord_Pa": "Pa",
            "candidate_plane_results[].shear_stress_amplitude_Pa": "Pa",
            "candidate_plane_results[].maximum_normal_stress_Pa": "Pa",
            "candidate_plane_results[].findley_parameter_Pa": "Pa",
            "maximum_findley_parameter_Pa": "Pa",
            "reference_parameter_strength_Pa": "Pa",
            "reference_life_cycles": "cycle",
            "candidate_plane_results[].parameter_to_reference_strength_ratio": "1",
            "reference_strength_utilization_ratio": "1",
            "margin_to_reference_strength_Pa": "Pa",
            "candidate_plane_results[].margin_to_reference_strength_Pa": "Pa",
            "evaluated_shear_pair_count": "1",
        },
        (
            "Uses the Findley critical-plane stress parameter with caller-supplied coefficient and reference strength; no coefficient, strength curve or cycle life is inferred.",
            "The sampled shear amplitude is one half of the maximum pairwise chord in the two-component in-plane shear-traction path and is evaluated only on caller-supplied planes.",
            "A computed value is a deterministic model output, not a code acceptance decision, life prediction, failure probability or material qualification.",
        ),
        ("findley_1959_mean_stress_critical_plane", "caller_findley_reference_strength_calibration"),
        qualification="user_model",
        context_validator=_validate_context,
    )]
