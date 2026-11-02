"""Life-dependent Carpinteri-Spagnoli plane life from caller axial/torsion S-N curves."""

from __future__ import annotations

import math

from pydantic import Field, model_validator

from .carpinteri_spagnoli_finite_screen import CarpinteriSpagnoliPlane, _safe_fsum, _traction
from .contracts import Calculation, Contract, Evidence, Positive, canonical_digest
from .registry import ModelSpec


class CarpinteriSpagnoliLife(Contract):
    analysis_id: str = Field(min_length=1)
    material_condition_id: str = Field(min_length=1)
    history_source_id: str = Field(min_length=1)
    history_source_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    history_evidence: Evidence
    axial_curve_source_id: str = Field(min_length=1)
    axial_curve_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    axial_curve_evidence: Evidence
    torsion_curve_source_id: str = Field(min_length=1)
    torsion_curve_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    torsion_curve_evidence: Evidence
    sample_ids: list[str] = Field(min_length=3, max_length=10000)
    stress_tensor_components_Pa: list[list[float]] = Field(min_length=3, max_length=10000)
    candidate_planes: tuple[CarpinteriSpagnoliPlane, ...] = Field(min_length=1, max_length=10000)
    axial_curve_cycles: list[Positive] = Field(min_length=2, max_length=10000)
    axial_stress_amplitudes_Pa: list[Positive] = Field(min_length=2, max_length=10000)
    torsion_curve_cycles: list[Positive] = Field(min_length=2, max_length=10000)
    torsion_shear_amplitudes_Pa: list[Positive] = Field(min_length=2, max_length=10000)
    logarithmic_life_tolerance: Positive = 1e-10
    maximum_root_iterations: int = Field(default=100, ge=10, le=1000)
    maximum_plane_pair_evaluations: int = Field(default=2_000_000, ge=1, le=20_000_000)
    maximum_curve_root_work: int = Field(default=2_000_000, ge=1, le=20_000_000)
    material_curve_match_and_smooth_specimen_basis_reviewed: bool
    representative_closed_cycle_and_stress_basis_reviewed: bool
    plane_population_and_hard_metal_scope_reviewed: bool
    life_dependent_model_and_root_reviewed: bool
    curve_rights_and_engineering_use_reviewed: bool

    @model_validator(mode="after")
    def validate_inputs(self):
        for evidence, source_id, sha256, label in (
            (self.history_evidence, self.history_source_id, self.history_source_sha256, "history"),
            (self.axial_curve_evidence, self.axial_curve_source_id, self.axial_curve_sha256, "axial curve"),
            (self.torsion_curve_evidence, self.torsion_curve_source_id, self.torsion_curve_sha256, "torsion curve"),
        ):
            if evidence.source_id != source_id or evidence.sha256 != sha256:
                raise ValueError(f"{label} Evidence must match the declared source and digest")
        if len(self.sample_ids) != len(self.stress_tensor_components_Pa):
            raise ValueError("sample IDs and stress tensors must align")
        if len(set(self.sample_ids)) != len(self.sample_ids):
            raise ValueError("sample IDs must be unique and retain caller path order")
        if any(len(row) != 6 for row in self.stress_tensor_components_Pa):
            raise ValueError("stress tensors require [xx, yy, zz, xy, yz, zx]")
        if self.stress_tensor_components_Pa[0] != self.stress_tensor_components_Pa[-1]:
            raise ValueError("the representative stress cycle must close exactly")
        if any(not math.isfinite(value) for row in self.stress_tensor_components_Pa for value in row):
            raise ValueError("stress components must be finite")
        for cycles, amplitudes, label in (
            (self.axial_curve_cycles, self.axial_stress_amplitudes_Pa, "axial"),
            (self.torsion_curve_cycles, self.torsion_shear_amplitudes_Pa, "torsion"),
        ):
            if len(cycles) != len(amplitudes):
                raise ValueError(f"{label} curve cycle and strength arrays must align")
            if any(right <= left for left, right in zip(cycles[:-1], cycles[1:], strict=True)):
                raise ValueError(f"{label} curve cycles must strictly increase")
            if any(right >= left for left, right in zip(amplitudes[:-1], amplitudes[1:], strict=True)):
                raise ValueError(f"{label} fatigue strengths must strictly decrease with life")
        if max(self.axial_curve_cycles[0], self.torsion_curve_cycles[0]) >= min(self.axial_curve_cycles[-1], self.torsion_curve_cycles[-1]):
            raise ValueError("axial and torsion curves must have a nonempty common life interval")
        if len({plane.plane_id for plane in self.candidate_planes}) != len(self.candidate_planes):
            raise ValueError("candidate plane IDs must be unique")
        return self


def _log_strength(cycles: list[float], strengths: list[float], log_life: float) -> float:
    log_cycles = [math.log(value) for value in cycles]
    if log_life < log_cycles[0] or log_life > log_cycles[-1]:
        raise ValueError("life outside curve support")
    if log_life == log_cycles[-1]:
        return strengths[-1]
    index = next(i for i in range(len(log_cycles) - 1) if log_cycles[i] <= log_life < log_cycles[i + 1])
    fraction = (log_life - log_cycles[index]) / (log_cycles[index + 1] - log_cycles[index])
    log_strength = math.log(strengths[index]) + fraction * (
        math.log(strengths[index + 1]) - math.log(strengths[index])
    )
    return math.exp(log_strength)


def evaluate_carpinteri_spagnoli_life(request: CarpinteriSpagnoliLife) -> Calculation:
    """Solve the life-dependent quadratic C-S utilization on finite planes."""
    digest = canonical_digest(request.model_dump(mode="json"))
    lower_life = max(request.axial_curve_cycles[0], request.torsion_curve_cycles[0])
    upper_life = min(request.axial_curve_cycles[-1], request.torsion_curve_cycles[-1])
    base = {
        "analysis_id": request.analysis_id,
        "material_condition_id": request.material_condition_id,
        "history_source_id": request.history_source_id,
        "history_source_sha256": request.history_source_sha256,
        "axial_curve_source_id": request.axial_curve_source_id,
        "axial_curve_sha256": request.axial_curve_sha256,
        "torsion_curve_source_id": request.torsion_curve_source_id,
        "torsion_curve_sha256": request.torsion_curve_sha256,
        "input_sha256": digest,
        "common_life_support_cycles": [lower_life, upper_life],
        "candidate_plane_count": len(request.candidate_planes),
    }
    if not all((
        request.material_curve_match_and_smooth_specimen_basis_reviewed,
        request.representative_closed_cycle_and_stress_basis_reviewed,
        request.plane_population_and_hard_metal_scope_reviewed,
        request.life_dependent_model_and_root_reviewed,
        request.curve_rights_and_engineering_use_reviewed,
    )):
        return Calculation(status="needs_data", values=base | {
            "reason": "material_curves_cycle_plane_scope_root_and_rights_reviews_required",
            "cycles_to_failure": None,
            "plane_life_results": None,
        })
    pair_work = len(request.sample_ids) * (len(request.sample_ids) - 1) // 2 * len(request.candidate_planes)
    if pair_work > request.maximum_plane_pair_evaluations:
        return Calculation(status="out_of_scope", values=base | {
            "reason": "finite_plane_sample_pair_work_budget_exceeded",
            "plane_pair_evaluations_required": pair_work,
            "maximum_plane_pair_evaluations": request.maximum_plane_pair_evaluations,
            "cycles_to_failure": None,
            "plane_life_results": None,
        })
    curve_work = len(request.candidate_planes) * request.maximum_root_iterations * (
        len(request.axial_curve_cycles) + len(request.torsion_curve_cycles)
    )
    if curve_work > request.maximum_curve_root_work:
        return Calculation(status="out_of_scope", values=base | {
            "reason": "curve_interpolation_root_work_budget_exceeded",
            "curve_root_work_required": curve_work,
            "maximum_curve_root_work": request.maximum_curve_root_work,
            "cycles_to_failure": None,
            "plane_life_results": None,
        })
    plane_features = []
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
        maximum_normal = max(normal_stress)
        max_distance_sq = -1.0
        witness = (0, 0)
        for left in range(len(shear_vectors) - 1):
            for right in range(left + 1, len(shear_vectors)):
                distance_sq = _safe_fsum((shear_vectors[right][axis] - shear_vectors[left][axis]) ** 2 for axis in range(2))
                if distance_sq > max_distance_sq:
                    max_distance_sq = distance_sq
                    witness = (left, right)
        tau_amplitude = 0.5 * math.sqrt(max(0.0, max_distance_sq))
        if not all(math.isfinite(value) for value in (maximum_normal, tau_amplitude)):
            return Calculation(status="out_of_scope", values=base | {
                "reason": "finite_plane_projection_produced_nonfinite_stress_feature",
                "plane_id": plane.plane_id,
                "cycles_to_failure": None,
                "plane_life_results": None,
            })
        plane_features.append({
            "plane_id": plane.plane_id,
            "maximum_normal_stress_Pa": maximum_normal,
            "finite_sample_shear_vector_amplitude_Pa": tau_amplitude,
            "shear_witness_sample_ids": [request.sample_ids[witness[0]], request.sample_ids[witness[1]]],
        })

    log_lower, log_upper = math.log(lower_life), math.log(upper_life)
    plane_results = []
    for feature in plane_features:
        sigma_n = feature["maximum_normal_stress_Pa"]
        tau_a = feature["finite_sample_shear_vector_amplitude_Pa"]

        def residual(log_life: float) -> float:
            sigma_f = _log_strength(request.axial_curve_cycles, request.axial_stress_amplitudes_Pa, log_life)
            tau_f = _log_strength(request.torsion_curve_cycles, request.torsion_shear_amplitudes_Pa, log_life)
            return (sigma_n / sigma_f) ** 2 + (tau_a / tau_f) ** 2 - 1.0

        try:
            low_residual, high_residual = residual(log_lower), residual(log_upper)
        except (OverflowError, ValueError, ZeroDivisionError):
            low_residual = high_residual = math.nan
        if not math.isfinite(low_residual) or not math.isfinite(high_residual):
            return Calculation(status="out_of_scope", values=base | {
                "reason": "life_curve_ratio_evaluation_outside_finite_support",
                "plane_id": feature["plane_id"],
                "cycles_to_failure": None,
                "plane_life_results": None,
            })
        if low_residual > 0.0 or high_residual < 0.0:
            return Calculation(status="out_of_scope", values=base | {
                "reason": "plane_failure_root_not_bracketed_inside_common_curve_support",
                "plane_id": feature["plane_id"],
                "utilization_residual_at_support": [low_residual, high_residual],
                "cycles_to_failure": None,
                "plane_life_results": None,
            })
        if low_residual == 0.0:
            log_life = log_lower
            iterations = 0
        elif high_residual == 0.0:
            log_life = log_upper
            iterations = 0
        else:
            lo, hi = log_lower, log_upper
            iterations = 0
            for iterations in range(1, request.maximum_root_iterations + 1):
                mid = 0.5 * (lo + hi)
                mid_residual = residual(mid)
                if not math.isfinite(mid_residual):
                    return Calculation(status="out_of_scope", values=base | {
                        "reason": "nonfinite_life_root_residual",
                        "plane_id": feature["plane_id"],
                        "cycles_to_failure": None,
                        "plane_life_results": None,
                    })
                if mid_residual >= 0.0:
                    hi = mid
                else:
                    lo = mid
                if hi - lo <= request.logarithmic_life_tolerance:
                    break
            log_life = 0.5 * (lo + hi)
            if hi - lo > request.logarithmic_life_tolerance:
                return Calculation(status="out_of_scope", values=base | {
                    "reason": "life_root_iteration_budget_exhausted",
                    "plane_id": feature["plane_id"],
                    "cycles_to_failure": None,
                    "plane_life_results": None,
                })
        life = math.exp(log_life)
        plane_results.append(feature | {
            "cycles_to_failure": life,
            "root_iterations": iterations,
            "residual_at_solution": residual(log_life),
        })
    governing = min(plane_results, key=lambda row: row["cycles_to_failure"])
    if not math.isfinite(governing["cycles_to_failure"]):
        return Calculation(status="out_of_scope", values=base | {
            "reason": "nonfinite_governing_plane_life",
            "cycles_to_failure": None,
            "plane_life_results": plane_results,
        })
    return Calculation(values=base | {
        "status": "computed",
        "cycles_to_failure": governing["cycles_to_failure"],
        "governing_plane_id_on_finite_candidate_set": governing["plane_id"],
        "plane_life_results": plane_results,
        "life_dependent_coefficient_definition": "k_CS(N) = axial_stress_amplitude(N) / torsion_shear_amplitude(N)",
        "interpolation": "linear in log stress amplitude versus log cycles within each caller curve segment",
        "limitations": [
            "Life is solved only inside the common support of caller axial and torsion S-N curves; no extrapolation is permitted.",
            "Utilization is monotone under the validated strictly decreasing positive curves; the scalar life root is solved in logarithmic cycle coordinates.",
            "Critical plane is the minimum life over caller finite candidates, not the original continuous averaged-principal-direction plane rule.",
            "The caller must qualify curve material match, HCF/hard-metal applicability, stress measures, cycle decomposition and the life-dependent C-S assumption.",
            "No variable-amplitude accumulation, scatter, probability, transfer, code acceptance or material qualification is inferred.",
        ],
    })


def specifications() -> list[ModelSpec]:
    return [ModelSpec(
        "fatigue.carpinteri_spagnoli_life_dependent_curve",
        CarpinteriSpagnoliLife,
        evaluate_carpinteri_spagnoli_life,
        {"cycles_to_failure": "cycle", "plane_life_results[].cycles_to_failure": "cycle"},
        (
            "Uses finite caller planes and same-condition axial/torsion S-N curves; curve strengths define the life-dependent shear weighting.",
            "The scalar utilization root is restricted to the shared curve life interval and uses bounded logarithmic bisection.",
            "No continuous plane orientation, variable-amplitude accumulation or material qualification is implied.",
        ),
        ("carpinteri_spagnoli_life_dependent_material_parameter_sn_curve_method",),
        qualification="user_model",
    )]
