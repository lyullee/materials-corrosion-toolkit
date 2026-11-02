"""Caller-quadrature finite approximation of the Papadopoulos P1 HCF screen."""

from __future__ import annotations

import math

from pydantic import Field, model_validator

from .contracts import Calculation, Contract, Evidence, Nonnegative, Positive, canonical_digest
from .registry import ModelSpec


class PapadopoulosP1ShearSystem(Contract):
    """One caller-supplied normal/shear direction and normalized quadrature weight."""

    system_id: str = Field(min_length=1)
    plane_normal: tuple[float, float, float]
    in_plane_shear_direction: tuple[float, float, float]
    normalized_orientation_weight: Positive

    @model_validator(mode="after")
    def finite_orthonormal_pair(self):
        values = (*self.plane_normal, *self.in_plane_shear_direction)
        if not all(math.isfinite(value) for value in values):
            raise ValueError("orientation vectors must be finite")
        normal_norm = math.sqrt(math.fsum(value * value for value in self.plane_normal))
        shear_norm = math.sqrt(math.fsum(value * value for value in self.in_plane_shear_direction))
        dot = math.fsum(a * b for a, b in zip(self.plane_normal, self.in_plane_shear_direction, strict=True))
        if abs(normal_norm - 1.0) > 1e-10 or abs(shear_norm - 1.0) > 1e-10 or abs(dot) > 1e-10:
            raise ValueError("plane normal and shear direction must be unit and orthogonal")
        return self


class PapadopoulosP1FiniteIntegralScreen(Contract):
    """Evaluate a caller-calibrated Papadopoulos P1 limit screen by finite quadrature."""

    analysis_id: str = Field(min_length=1)
    material_condition_id: str = Field(min_length=1)
    history_source_id: str = Field(min_length=1)
    history_source_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    history_evidence: Evidence
    calibration_id: str = Field(min_length=1)
    calibration_material_condition_id: str = Field(min_length=1)
    calibration_source_id: str = Field(min_length=1)
    calibration_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    calibration_evidence: Evidence
    sample_ids: list[str] = Field(min_length=3, max_length=10000)
    stress_tensor_components_Pa: list[list[float]] = Field(min_length=3, max_length=10000)
    shear_systems: tuple[PapadopoulosP1ShearSystem, ...] = Field(min_length=1, max_length=100000)
    hydrostatic_coefficient: Nonnegative
    fully_reversed_torsional_fatigue_limit_Pa: Positive
    maximum_shear_system_sample_work: int = Field(default=2_000_000, ge=1, le=20_000_000)
    tensor_basis_and_order_reviewed: bool
    representative_closed_cycle_reviewed: bool
    orientation_quadrature_measure_and_coverage_reviewed: bool
    calibration_and_fatigue_limit_convention_reviewed: bool
    material_scope_and_use_reviewed: bool

    @model_validator(mode="after")
    def validate_lineage_and_paths(self):
        if self.material_condition_id != self.calibration_material_condition_id:
            raise ValueError("calibration material condition must exactly match the stress history")
        if self.history_evidence.source_id != self.history_source_id or self.history_evidence.sha256 != self.history_source_sha256:
            raise ValueError("history Evidence must match its declared source and digest")
        if self.calibration_evidence.source_id != self.calibration_source_id or self.calibration_evidence.sha256 != self.calibration_sha256:
            raise ValueError("calibration Evidence must match its declared source and digest")
        if len(self.sample_ids) != len(self.stress_tensor_components_Pa):
            raise ValueError("sample IDs and stress tensors must align")
        if len(set(self.sample_ids)) != len(self.sample_ids):
            raise ValueError("sample IDs must be unique and preserve path order")
        if any(len(row) != 6 for row in self.stress_tensor_components_Pa):
            raise ValueError("stress tensors need six [xx, yy, zz, xy, yz, zx] components")
        if self.stress_tensor_components_Pa[0] != self.stress_tensor_components_Pa[-1]:
            raise ValueError("representative cycle endpoints must match exactly")
        if any(not math.isfinite(value) for row in self.stress_tensor_components_Pa for value in row):
            raise ValueError("stress tensors must be finite")
        system_ids = [item.system_id for item in self.shear_systems]
        if len(set(system_ids)) != len(system_ids):
            raise ValueError("shear-system IDs must be unique")
        weight_sum = math.fsum(item.normalized_orientation_weight for item in self.shear_systems)
        if not math.isclose(weight_sum, 1.0, rel_tol=0.0, abs_tol=1e-10):
            raise ValueError("caller quadrature weights must sum to one")
        return self


def _resolved_shear(normal: tuple[float, float, float], direction: tuple[float, float, float], tensor: list[float]) -> float:
    xx, yy, zz, xy, yz, zx = tensor
    return (
        direction[0] * (xx * normal[0] + xy * normal[1] + zx * normal[2])
        + direction[1] * (xy * normal[0] + yy * normal[1] + yz * normal[2])
        + direction[2] * (zx * normal[0] + yz * normal[1] + zz * normal[2])
    )


def evaluate_papadopoulos_p1_finite_integral_screen(request: PapadopoulosP1FiniteIntegralScreen) -> Calculation:
    """Compute a finite orientation-quadrature P1-style shear RMS and limit margin."""
    input_digest = canonical_digest(request.model_dump(mode="json"))
    base = {
        "analysis_id": request.analysis_id,
        "material_condition_id": request.material_condition_id,
        "history_source_id": request.history_source_id,
        "history_source_sha256": request.history_source_sha256,
        "calibration_id": request.calibration_id,
        "calibration_source_id": request.calibration_source_id,
        "calibration_sha256": request.calibration_sha256,
        "input_sha256": input_digest,
        "sample_count": len(request.sample_ids),
        "orientation_system_count": len(request.shear_systems),
        "fatigue_criterion": "Papadopoulos_P1_integral_high_cycle_fatigue_limit_form",
        "quadrature_convention": "caller weights normalized to one; P1 shear term is sqrt(5 times weighted mean squared resolved shear amplitude)",
    }
    if not all((
        request.tensor_basis_and_order_reviewed,
        request.representative_closed_cycle_reviewed,
        request.orientation_quadrature_measure_and_coverage_reviewed,
        request.calibration_and_fatigue_limit_convention_reviewed,
        request.material_scope_and_use_reviewed,
    )):
        return Calculation(status="needs_data", values=base | {
            "reason": "history_quadrature_calibration_and_use_reviews_required",
            "criterion_parameter_Pa": None,
            "margin_to_torsional_limit_Pa": None,
            "screening_outcome": None,
            "shear_system_results": None,
        })
    work = len(request.sample_ids) * len(request.shear_systems)
    if work > request.maximum_shear_system_sample_work:
        return Calculation(status="out_of_scope", values=base | {
            "reason": "finite_orientation_sample_work_budget_exceeded",
            "shear_system_sample_work": work,
            "maximum_shear_system_sample_work": request.maximum_shear_system_sample_work,
            "criterion_parameter_Pa": None,
            "margin_to_torsional_limit_Pa": None,
            "screening_outcome": None,
            "shear_system_results": None,
        })
    hydro = [(row[0] + row[1] + row[2]) / 3.0 for row in request.stress_tensor_components_Pa]
    maximum_hydro = max(hydro)
    squared_amplitude_terms = []
    system_results = []
    for system in request.shear_systems:
        resolved = [
            _resolved_shear(system.plane_normal, system.in_plane_shear_direction, tensor)
            for tensor in request.stress_tensor_components_Pa
        ]
        amplitude = 0.5 * (max(resolved) - min(resolved))
        weighted_term = system.normalized_orientation_weight * amplitude * amplitude
        if not all(math.isfinite(value) for value in (amplitude, weighted_term)):
            return Calculation(status="out_of_scope", values=base | {
                "reason": "finite_stress_values_produce_nonfinite_shear_amplitude",
                "system_id": system.system_id,
                "criterion_parameter_Pa": None,
                "margin_to_torsional_limit_Pa": None,
                "screening_outcome": None,
                "shear_system_results": None,
            })
        squared_amplitude_terms.append(weighted_term)
        system_results.append({
            "system_id": system.system_id,
            "normalized_orientation_weight": system.normalized_orientation_weight,
            "sampled_resolved_shear_stress_amplitude_Pa": amplitude,
            "weighted_squared_amplitude_Pa2": weighted_term,
        })
    try:
        shear_rms = math.sqrt(5.0 * math.fsum(squared_amplitude_terms))
        parameter = shear_rms + request.hydrostatic_coefficient * maximum_hydro
        margin = request.fully_reversed_torsional_fatigue_limit_Pa - parameter
    except (OverflowError, ValueError):
        shear_rms = parameter = margin = math.inf
    if not all(math.isfinite(value) for value in (maximum_hydro, shear_rms, parameter, margin)):
        return Calculation(status="out_of_scope", values=base | {
            "reason": "finite_inputs_produce_nonfinite_p1_arithmetic",
            "criterion_parameter_Pa": None,
            "margin_to_torsional_limit_Pa": None,
            "screening_outcome": None,
            "shear_system_results": None,
        })
    return Calculation(values=base | {
        "status": "computed",
        "weighted_generalized_shear_amplitude_Pa": shear_rms,
        "maximum_sampled_hydrostatic_stress_Pa": maximum_hydro,
        "hydrostatic_coefficient": request.hydrostatic_coefficient,
        "criterion_parameter_Pa": parameter,
        "fully_reversed_torsional_fatigue_limit_Pa": request.fully_reversed_torsional_fatigue_limit_Pa,
        "margin_to_torsional_limit_Pa": margin,
        "screening_outcome": "caller_limit_not_exceeded" if parameter <= request.fully_reversed_torsional_fatigue_limit_Pa else "caller_limit_exceeded",
        "shear_system_results": system_results,
        "limitations": [
            "Orientation integral is approximated only by caller-supplied finite systems and normalized weights; no continuous orientation error bound is computed.",
            "Each shear amplitude is the half-range over the supplied closed-cycle samples; no unsampled temporal extrema or cycle decomposition is inferred.",
            "Calibration coefficient, torsional fatigue limit and material applicability are caller-owned; no curve transfer, finite-life prediction, damage accumulation or qualification is implied.",
            "This is a high-cycle fatigue-limit screening form, not a low-cycle plasticity model.",
        ],
    })


def specifications() -> list[ModelSpec]:
    return [ModelSpec(
        "fatigue.papadopoulos_p1_finite_integral_screen",
        PapadopoulosP1FiniteIntegralScreen,
        evaluate_papadopoulos_p1_finite_integral_screen,
        {
            "weighted_generalized_shear_amplitude_Pa": "Pa",
            "maximum_sampled_hydrostatic_stress_Pa": "Pa",
            "criterion_parameter_Pa": "Pa",
            "margin_to_torsional_limit_Pa": "Pa",
        },
        (
            "The integral criterion is approximated by caller-declared finite orientation quadrature; weights must sum to one.",
            "The caller supplies the material-matched hydrostatic coefficient and fully reversed torsional limit with Evidence provenance.",
            "The result is a finite-sample high-cycle limit screen, not a finite-life prediction or material qualification.",
        ),
        ("papadopoulos_1995_high_cycle_integral_multiaxial_criterion", "papadopoulos_long_life_multiaxial_2001"),
        qualification="user_model",
    )]
