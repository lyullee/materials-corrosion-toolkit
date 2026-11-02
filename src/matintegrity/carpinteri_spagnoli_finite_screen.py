"""Finite-plane Carpinteri-Spagnoli-style high-cycle fatigue limit screen."""

from __future__ import annotations

import math

from pydantic import Field, model_validator

from .contracts import Calculation, Contract, Evidence, Positive, canonical_digest
from .registry import ModelSpec


class CarpinteriSpagnoliPlane(Contract):
    plane_id: str = Field(min_length=1)
    normal: tuple[float, float, float]
    tangent_u: tuple[float, float, float]
    tangent_v: tuple[float, float, float]

    @model_validator(mode="after")
    def orthonormal_frame(self):
        vectors = (self.normal, self.tangent_u, self.tangent_v)
        if any(not math.isfinite(value) for vector in vectors for value in vector):
            raise ValueError("plane frame must contain finite coordinates")
        dots = [math.fsum(a * b for a, b in zip(left, right, strict=True)) for left, right in (
            (self.normal, self.normal), (self.tangent_u, self.tangent_u), (self.tangent_v, self.tangent_v),
            (self.normal, self.tangent_u), (self.normal, self.tangent_v), (self.tangent_u, self.tangent_v),
        )]
        if any(abs(value - target) > 1e-9 for value, target in zip(dots, (1, 1, 1, 0, 0, 0), strict=True)):
            raise ValueError("plane normal and tangents must form an orthonormal frame")
        return self


class CarpinteriSpagnoliFiniteScreen(Contract):
    analysis_id: str = Field(min_length=1)
    material_condition_id: str = Field(min_length=1)
    history_source_id: str = Field(min_length=1)
    history_source_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    history_evidence: Evidence
    axial_limit_source_id: str = Field(min_length=1)
    axial_limit_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    axial_limit_evidence: Evidence
    fully_reversed_axial_limit_Pa: Positive
    torsion_limit_source_id: str = Field(min_length=1)
    torsion_limit_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    torsion_limit_evidence: Evidence
    fully_reversed_torsion_limit_Pa: Positive
    sample_ids: list[str] = Field(min_length=3, max_length=10000)
    stress_tensor_components_Pa: list[list[float]] = Field(min_length=3, max_length=10000)
    candidate_planes: tuple[CarpinteriSpagnoliPlane, ...] = Field(min_length=1, max_length=10000)
    maximum_plane_pair_evaluations: int = Field(default=2_000_000, ge=1, le=20_000_000)
    matched_material_endurance_data_reviewed: bool
    fully_reversed_smooth_specimen_basis_reviewed: bool
    closed_cycle_tensor_order_and_sign_reviewed: bool
    finite_plane_population_and_basis_reviewed: bool
    hard_metal_hcf_scope_and_use_reviewed: bool

    @model_validator(mode="after")
    def validate_lineage_and_samples(self):
        for evidence, source_id, sha256, label in (
            (self.history_evidence, self.history_source_id, self.history_source_sha256, "history"),
            (self.axial_limit_evidence, self.axial_limit_source_id, self.axial_limit_sha256, "axial limit"),
            (self.torsion_limit_evidence, self.torsion_limit_source_id, self.torsion_limit_sha256, "torsion limit"),
        ):
            if evidence.source_id != source_id or evidence.sha256 != sha256:
                raise ValueError(f"{label} Evidence must match its declared source and digest")
        if len(self.sample_ids) != len(self.stress_tensor_components_Pa):
            raise ValueError("sample IDs and stress tensor history must align")
        if len(set(self.sample_ids)) != len(self.sample_ids):
            raise ValueError("sample IDs must be unique and ordered")
        if any(len(row) != 6 for row in self.stress_tensor_components_Pa):
            raise ValueError("stress tensors use [xx, yy, zz, xy, yz, zx]")
        if self.stress_tensor_components_Pa[0] != self.stress_tensor_components_Pa[-1]:
            raise ValueError("the representative stress cycle must close exactly")
        if any(not math.isfinite(value) for row in self.stress_tensor_components_Pa for value in row):
            raise ValueError("stress tensor components must be finite")
        plane_ids = [plane.plane_id for plane in self.candidate_planes]
        if len(set(plane_ids)) != len(plane_ids):
            raise ValueError("plane IDs must be unique")
        return self


def _traction(normal: tuple[float, float, float], tensor: list[float]) -> tuple[float, float, float]:
    xx, yy, zz, xy, yz, zx = tensor
    nx, ny, nz = normal
    return (
        _safe_fsum((xx * nx, xy * ny, zx * nz)),
        _safe_fsum((xy * nx, yy * ny, yz * nz)),
        _safe_fsum((zx * nx, yz * ny, zz * nz)),
    )


def _safe_fsum(values) -> float:
    try:
        return math.fsum(values)
    except (OverflowError, ValueError):
        return math.inf


def evaluate_carpinteri_spagnoli_finite_screen(request: CarpinteriSpagnoliFiniteScreen) -> Calculation:
    """Evaluate max-plane sqrt(sigma_n,max² + k²*tau_a²) on finite samples."""
    input_digest = canonical_digest(request.model_dump(mode="json"))
    ratio = request.fully_reversed_torsion_limit_Pa / request.fully_reversed_axial_limit_Pa
    coefficient = request.fully_reversed_axial_limit_Pa / request.fully_reversed_torsion_limit_Pa
    base = {
        "analysis_id": request.analysis_id,
        "material_condition_id": request.material_condition_id,
        "history_source_id": request.history_source_id,
        "history_source_sha256": request.history_source_sha256,
        "axial_limit_source_id": request.axial_limit_source_id,
        "axial_limit_sha256": request.axial_limit_sha256,
        "torsion_limit_source_id": request.torsion_limit_source_id,
        "torsion_limit_sha256": request.torsion_limit_sha256,
        "input_sha256": input_digest,
        "cycle_sample_count": len(request.sample_ids),
        "candidate_plane_count": len(request.candidate_planes),
        "criterion": "Carpinteri_Spagnoli_finite_plane_quadratic_equivalent_stress",
    }
    if not all((
        request.matched_material_endurance_data_reviewed,
        request.fully_reversed_smooth_specimen_basis_reviewed,
        request.closed_cycle_tensor_order_and_sign_reviewed,
        request.finite_plane_population_and_basis_reviewed,
        request.hard_metal_hcf_scope_and_use_reviewed,
    )):
        return Calculation(status="needs_data", values=base | {
            "reason": "endurance_history_plane_population_and_scope_reviews_required",
            "critical_plane_parameter_Pa": None,
            "margin_to_axial_endurance_limit_Pa": None,
        })
    if not math.isfinite(ratio) or not math.isfinite(coefficient):
        return Calculation(status="out_of_scope", values=base | {
            "reason": "endurance_limit_ratio_outside_finite_numeric_support",
            "critical_plane_parameter_Pa": None,
            "margin_to_axial_endurance_limit_Pa": None,
        })
    work = len(request.sample_ids) * (len(request.sample_ids) - 1) // 2 * len(request.candidate_planes)
    if work > request.maximum_plane_pair_evaluations:
        return Calculation(status="out_of_scope", values=base | {
            "reason": "finite_plane_pair_sample_work_budget_exceeded",
            "plane_pair_evaluations_required": work,
            "maximum_plane_pair_evaluations": request.maximum_plane_pair_evaluations,
            "critical_plane_parameter_Pa": None,
            "margin_to_axial_endurance_limit_Pa": None,
        })
    plane_results = []
    for plane in request.candidate_planes:
        normal_stress = []
        shear_vectors = []
        for tensor in request.stress_tensor_components_Pa:
            traction = _traction(plane.normal, tensor)
            normal_stress.append(_safe_fsum(plane.normal[j] * traction[j] for j in range(3)))
            shear_vectors.append((
                _safe_fsum(plane.tangent_u[j] * traction[j] for j in range(3)),
                _safe_fsum(plane.tangent_v[j] * traction[j] for j in range(3)),
            ))
        max_normal_index = max(range(len(normal_stress)), key=normal_stress.__getitem__)
        max_distance_sq = -1.0
        witness = (0, 0)
        for left in range(len(shear_vectors) - 1):
            for right in range(left + 1, len(shear_vectors)):
                distance_sq = _safe_fsum((shear_vectors[right][axis] - shear_vectors[left][axis]) ** 2 for axis in range(2))
                if distance_sq > max_distance_sq:
                    max_distance_sq = distance_sq
                    witness = (left, right)
        shear_amplitude = 0.5 * math.sqrt(max(0.0, max_distance_sq))
        maximum_normal = normal_stress[max_normal_index]
        parameter = math.hypot(maximum_normal, coefficient * shear_amplitude)
        if not all(math.isfinite(value) for value in (maximum_normal, shear_amplitude, parameter)):
            return Calculation(status="out_of_scope", values=base | {
                "reason": "finite_tensor_samples_produce_nonfinite_plane_parameter",
                "plane_id": plane.plane_id,
                "critical_plane_parameter_Pa": None,
                "margin_to_axial_endurance_limit_Pa": None,
            })
        plane_results.append({
            "plane_id": plane.plane_id,
            "maximum_normal_stress_Pa": maximum_normal,
            "maximum_normal_stress_sample_id": request.sample_ids[max_normal_index],
            "finite_sample_shear_vector_half_diameter_Pa": shear_amplitude,
            "shear_diameter_witness_sample_ids": [request.sample_ids[witness[0]], request.sample_ids[witness[1]]],
            "equivalent_stress_parameter_Pa": parameter,
        })
    governing = max(plane_results, key=lambda row: row["equivalent_stress_parameter_Pa"])
    parameter = governing["equivalent_stress_parameter_Pa"]
    margin = request.fully_reversed_axial_limit_Pa - parameter
    if not math.isfinite(margin):
        return Calculation(status="out_of_scope", values=base | {
            "reason": "finite_screening_parameter_produces_nonfinite_margin",
            "critical_plane_parameter_Pa": None,
            "margin_to_axial_endurance_limit_Pa": None,
        })
    return Calculation(values=base | {
        "status": "computed",
        "axial_to_torsion_endurance_ratio": ratio,
        "shear_weight_coefficient": coefficient,
        "axial_fully_reversed_endurance_limit_Pa": request.fully_reversed_axial_limit_Pa,
        "torsional_fully_reversed_endurance_limit_Pa": request.fully_reversed_torsion_limit_Pa,
        "critical_plane_id_on_finite_candidate_set": governing["plane_id"],
        "critical_plane_parameter_Pa": parameter,
        "margin_to_axial_endurance_limit_Pa": margin,
        "screening_outcome": "caller_limit_not_exceeded" if margin >= 0.0 else "caller_limit_exceeded",
        "plane_results": plane_results,
        "limitations": [
            "Critical plane is the maximum over the caller's finite candidate set; the original averaged-principal-direction orientation rule is not solved or bounded here.",
            "Shear amplitude is half the largest pairwise distance of finite sampled in-plane shear-traction vectors.",
            "The normal component is the signed maximum over the supplied cycle and enters quadratically as written; no compressive correction is added.",
            "Applicability is restricted to caller-reviewed hard-metal high-cycle conditions with matched smooth-specimen R=-1 limits; no finite life, probability, acceptance or qualification is inferred.",
        ],
    })


def specifications() -> list[ModelSpec]:
    return [ModelSpec(
        "fatigue.carpinteri_spagnoli_finite_limit_screen",
        CarpinteriSpagnoliFiniteScreen,
        evaluate_carpinteri_spagnoli_finite_screen,
        {
            "critical_plane_parameter_Pa": "Pa",
            "margin_to_axial_endurance_limit_Pa": "Pa",
            "plane_results[].maximum_normal_stress_Pa": "Pa",
            "plane_results[].finite_sample_shear_vector_half_diameter_Pa": "Pa",
        },
        (
            "Uses the quadratic combination of maximum plane-normal stress and weighted shear-vector amplitude on caller-supplied finite planes.",
            "The shear coefficient is derived from matched fully reversed axial and torsional endurance limits for the caller-reviewed hard-metal HCF scope.",
            "Finite plane selection and sampled vector amplitude do not reproduce or qualify a continuous original Carpinteri-Spagnoli procedure.",
        ),
        ("carpinteri_spagnoli_2001_hard_metal_high_cycle_fatigue_criterion",),
        qualification="user_model",
    )]
