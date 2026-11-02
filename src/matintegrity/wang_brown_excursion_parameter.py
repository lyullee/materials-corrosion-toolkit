"""Finite-plane Wang-Brown-style shear/reversal normal-strain parameter."""

from __future__ import annotations

import math

from pydantic import Field, model_validator

from .carpinteri_spagnoli_finite_screen import CarpinteriSpagnoliPlane
from .contracts import Calculation, Contract, Evidence, Nonnegative, canonical_digest
from .registry import ModelSpec


class WangBrownPlaneReversal(Contract):
    """Caller-reviewed shear-reversal endpoints on one candidate plane."""

    plane: CarpinteriSpagnoliPlane
    reversal_start_index: int = Field(ge=0)
    reversal_end_index: int = Field(ge=0)

    @model_validator(mode="after")
    def distinct_endpoints(self):
        if self.reversal_start_index == self.reversal_end_index:
            raise ValueError("a shear reversal must use two distinct ordered sample indices")
        return self


class WangBrownReviewedExcursionParameter(Contract):
    """Compute a bounded Wang-Brown-style parameter from caller-selected reversals."""

    analysis_id: str = Field(min_length=1)
    material_condition_id: str = Field(min_length=1)
    history_source_id: str = Field(min_length=1)
    history_source_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    history_evidence: Evidence
    calibration_source_id: str = Field(min_length=1)
    calibration_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    calibration_evidence: Evidence
    normal_strain_weight_S: Nonnegative
    sample_ids: tuple[str, ...] = Field(min_length=4, max_length=10001)
    strain_tensor_components: tuple[tuple[float, ...], ...] = Field(min_length=4, max_length=10001)
    strain_shear_convention: str = Field(pattern=r"^(tensor|engineering)$")
    plane_reversals: tuple[WangBrownPlaneReversal, ...] = Field(min_length=1, max_length=20000)
    maximum_projection_work: int = Field(default=2_000_000, ge=1, le=20_000_000)
    tensor_basis_and_order_reviewed: bool
    closed_cycle_and_path_order_reviewed: bool
    shear_reversal_pairing_reviewed: bool
    material_calibration_and_scope_reviewed: bool

    @model_validator(mode="after")
    def validate_history_and_lineage(self):
        if (self.history_evidence.source_id != self.history_source_id
                or self.history_evidence.sha256 != self.history_source_sha256):
            raise ValueError("history Evidence must match the declared source and digest")
        if (self.calibration_evidence.source_id != self.calibration_source_id
                or self.calibration_evidence.sha256 != self.calibration_sha256):
            raise ValueError("calibration Evidence must match the declared source and digest")
        count = len(self.sample_ids)
        if len(set(self.sample_ids)) != count:
            raise ValueError("sample IDs must be unique and retain caller path order")
        if len(self.strain_tensor_components) != count:
            raise ValueError("sample IDs and strain tensor history must align")
        if any(len(row) != 6 for row in self.strain_tensor_components):
            raise ValueError("strain tensors use [xx, yy, zz, xy, yz, zx]")
        if any(not math.isfinite(value) for row in self.strain_tensor_components for value in row):
            raise ValueError("strain tensor components must be finite")
        if self.strain_tensor_components[0] != self.strain_tensor_components[-1]:
            raise ValueError("the tensor history must include an exact duplicate cycle endpoint")
        independent_count = count - 1
        plane_ids = [item.plane.plane_id for item in self.plane_reversals]
        if len(set(plane_ids)) != len(plane_ids):
            raise ValueError("candidate plane IDs must be unique")
        if any(index >= independent_count for item in self.plane_reversals
               for index in (item.reversal_start_index, item.reversal_end_index)):
            raise ValueError("reversal indices must refer to independent cycle samples, excluding the duplicate endpoint")
        return self


def _contract_strain(row: tuple[float, ...], convention: str):
    xx, yy, zz, xy, yz, zx = row
    shear_scale = 0.5 if convention == "engineering" else 1.0
    return (
        (xx, xy * shear_scale, zx * shear_scale),
        (xy * shear_scale, yy, yz * shear_scale),
        (zx * shear_scale, yz * shear_scale, zz),
    )


def _normal_and_shear(plane: CarpinteriSpagnoliPlane, tensor):
    normal = plane.normal
    tangent_u = plane.tangent_u
    tangent_v = plane.tangent_v
    vector = tuple(math.fsum(tensor[i][j] * normal[j] for j in range(3)) for i in range(3))
    normal_strain = math.fsum(normal[i] * vector[i] for i in range(3))
    # Engineering shear is twice tensorial shear, regardless of the input storage convention.
    shear_u = 2.0 * math.fsum(tangent_u[i] * vector[i] for i in range(3))
    shear_v = 2.0 * math.fsum(tangent_v[i] * vector[i] for i in range(3))
    return normal_strain, (shear_u, shear_v)


def _cyclic_arc_indices(start: int, end: int, count: int) -> list[int]:
    result = [start]
    index = start
    while index != end:
        index = (index + 1) % count
        result.append(index)
        if len(result) > count:
            raise ValueError("ordered reversal arc is not bounded to one cycle")
    return result


def evaluate_wang_brown_reviewed_excursion_parameter(
    request: WangBrownReviewedExcursionParameter,
) -> Calculation:
    """Calculate Δγ/2 + S ε*n* on explicit finite planes and reviewed arcs."""
    input_digest = canonical_digest(request.model_dump(mode="json"))
    knot_count = len(request.sample_ids) - 1
    work = len(request.plane_reversals) * knot_count
    base = {
        "analysis_id": request.analysis_id,
        "material_condition_id": request.material_condition_id,
        "history_source_id": request.history_source_id,
        "history_source_sha256": request.history_source_sha256,
        "input_sha256": input_digest,
        "calibration_source_id": request.calibration_source_id,
        "calibration_sha256": request.calibration_sha256,
        "normal_strain_weight_S": request.normal_strain_weight_S,
        "independent_cycle_sample_count": knot_count,
        "tensor_component_order": ["xx", "yy", "zz", "xy", "yz", "zx"],
        "strain_shear_convention": request.strain_shear_convention,
        "parameter_definition": "engineering_shear_range_over_2_plus_S_times_normal_strain_excursion_on_reviewed_reversal_arc",
    }
    if not all((request.tensor_basis_and_order_reviewed, request.closed_cycle_and_path_order_reviewed,
                request.shear_reversal_pairing_reviewed, request.material_calibration_and_scope_reviewed)):
        return Calculation(status="needs_data", values=base | {
            "reason": "tensor_basis_cycle_path_reversal_and_material_calibration_reviews_required",
            "candidate_plane_results": None,
            "governing_parameter": None,
        })
    if work > request.maximum_projection_work:
        return Calculation(status="out_of_scope", values=base | {
            "reason": "finite_plane_projection_work_budget_exceeded",
            "projection_work_units": work,
            "maximum_projection_work": request.maximum_projection_work,
            "candidate_plane_results": None,
            "governing_parameter": None,
        })
    results = []
    for item in request.plane_reversals:
        plane = item.plane
        try:
            projected = [_normal_and_shear(plane, _contract_strain(row, request.strain_shear_convention))
                         for row in request.strain_tensor_components[:-1]]
            start, end = item.reversal_start_index, item.reversal_end_index
            normal_start, shear_start = projected[start]
            normal_end, shear_end = projected[end]
            shear_range = math.hypot(shear_end[0] - shear_start[0], shear_end[1] - shear_start[1])
            arc = _cyclic_arc_indices(start, end, knot_count)
            normal_values = [projected[index][0] for index in arc]
            normal_excursion = max(normal_values) - min(normal_values)
            parameter = 0.5 * shear_range + request.normal_strain_weight_S * normal_excursion
        except (ArithmeticError, OverflowError, ValueError):
            parameter = math.inf
            shear_range = normal_excursion = math.inf
        if not all(math.isfinite(value) for value in (shear_range, normal_excursion, parameter)):
            return Calculation(status="out_of_scope", values=base | {
                "reason": "finite_samples_produce_nonfinite_wang_brown_parameter",
                "plane_id": plane.plane_id,
                "candidate_plane_results": None,
                "governing_parameter": None,
            })
        results.append({
            "plane_id": plane.plane_id,
            "reversal_start_sample_id": request.sample_ids[start],
            "reversal_end_sample_id": request.sample_ids[end],
            "engineering_shear_range": shear_range,
            "shear_strain_amplitude": 0.5 * shear_range,
            "normal_strain_excursion": normal_excursion,
            "parameter": parameter,
            "normal_strain_arc_sample_count": len(arc),
        })
    governing = max(results, key=lambda row: row["parameter"])
    return Calculation(values=base | {
        "status": "computed",
        "projection_work_units": work,
        "candidate_plane_results": results,
        "governing_plane_id": governing["plane_id"],
        "governing_parameter": governing["parameter"],
        "limitations": [
            "The caller supplies each plane's shear-reversal endpoints; this module does not count cycles or locate reversals.",
            "Normal strain excursion is the finite sampled max-minus-min value along the explicitly ordered cyclic arc from the selected start to end.",
            "Only the supplied finite planes and sample path are evaluated; there is no continuous-plane bound or interpolation between samples.",
            "S must be calibrated for the same material condition and loading regime; this parameter alone is not life, damage accumulation, acceptance or qualification.",
        ],
    })


def specifications() -> list[ModelSpec]:
    return [ModelSpec(
        "fatigue.wang_brown_reviewed_excursion_parameter",
        WangBrownReviewedExcursionParameter,
        evaluate_wang_brown_reviewed_excursion_parameter,
        {
            "candidate_plane_results[].engineering_shear_range": "1",
            "candidate_plane_results[].shear_strain_amplitude": "1",
            "candidate_plane_results[].normal_strain_excursion": "1",
            "candidate_plane_results[].parameter": "1",
            "governing_parameter": "1",
        },
        (
            "Evaluates a finite-plane Wang-Brown-style parameter using explicitly reviewed shear-reversal endpoints and the normal-strain excursion on the ordered arc.",
            "The normal-strain sensitivity S is caller-calibrated for the declared material condition; no value is inferred or transferred.",
            "Cycle counting, calibrated life, continuous-plane optimization and physical qualification are outside this API.",
        ),
        ("wang_brown_1993_path_independent_multiaxial_strain_parameter",),
        qualification="user_model",
    )]
