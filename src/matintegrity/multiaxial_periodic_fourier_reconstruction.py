"""Finite trigonometric interpolation for one uniformly sampled closed tensor cycle."""

from __future__ import annotations

import math
from typing import Literal

from pydantic import Field, model_validator

from .contracts import Calculation, Contract, Evidence, canonical_digest
from .registry import ModelSpec


class PeriodicTensorFourierReconstruction(Contract):
    analysis_id: str = Field(min_length=1)
    material_condition_id: str = Field(min_length=1)
    source_id: str = Field(min_length=1)
    source_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    evidence: Evidence
    sample_ids: list[str] = Field(min_length=4, max_length=4097)
    stress_tensor_components_Pa: list[list[float]] = Field(min_length=4, max_length=4097)
    strain_tensor_components: list[list[float]] = Field(min_length=4, max_length=4097)
    evaluation_ids: list[str] = Field(min_length=2, max_length=100000)
    evaluation_phase_rad: list[float] = Field(min_length=2, max_length=100000)
    input_strain_shear_convention: Literal["tensor", "engineering"]
    maximum_trigonometric_term_work: int = Field(default=2_000_000, ge=1, le=20_000_000)
    tensor_basis_and_order_reviewed: bool
    uniform_periodic_sampling_reviewed: bool
    closed_cycle_and_path_order_reviewed: bool
    fourier_reconstruction_and_aliasing_reviewed: bool

    @model_validator(mode="after")
    def validate_cycle_and_queries(self):
        if self.evidence.source_id != self.source_id or self.evidence.sha256 != self.source_sha256:
            raise ValueError("Evidence must match the declared source and digest")
        count = len(self.sample_ids)
        if len(self.stress_tensor_components_Pa) != count or len(self.strain_tensor_components) != count:
            raise ValueError("sample IDs and both tensor histories must align")
        if len(set(self.sample_ids)) != count:
            raise ValueError("sample IDs must be unique and retain path order")
        if any(len(row) != 6 for row in (*self.stress_tensor_components_Pa, *self.strain_tensor_components)):
            raise ValueError("stress and strain tensors must use six [xx, yy, zz, xy, yz, zx] components")
        if self.stress_tensor_components_Pa[0] != self.stress_tensor_components_Pa[-1]:
            raise ValueError("stress cycle endpoints must match exactly")
        if self.strain_tensor_components[0] != self.strain_tensor_components[-1]:
            raise ValueError("strain cycle endpoints must match exactly")
        if not all(math.isfinite(value) for row in (*self.stress_tensor_components_Pa, *self.strain_tensor_components) for value in row):
            raise ValueError("tensor samples must be finite")
        if len(self.evaluation_ids) != len(self.evaluation_phase_rad):
            raise ValueError("evaluation IDs and phase coordinates must align")
        if len(set(self.evaluation_ids)) != len(self.evaluation_ids):
            raise ValueError("evaluation IDs must be unique")
        if any(not math.isfinite(value) or value < 0.0 or value > 2.0 * math.pi for value in self.evaluation_phase_rad):
            raise ValueError("evaluation phases must be finite radians in [0, 2*pi]")
        if any(right <= left for left, right in zip(self.evaluation_phase_rad[:-1], self.evaluation_phase_rad[1:], strict=True)):
            raise ValueError("evaluation phases must strictly increase")
        return self


def _real_fourier_coefficients(values: list[float]) -> tuple[float, list[tuple[int, float, float]], tuple[int, float] | None]:
    count = len(values)
    mean = _safe_fsum(values) / count
    harmonics = []
    highest_nyquist = None
    max_regular = (count - 1) // 2
    for harmonic in range(1, max_regular + 1):
        cosine = _safe_fsum(values[index] * math.cos(2.0 * math.pi * harmonic * index / count) for index in range(count))
        sine = _safe_fsum(values[index] * math.sin(2.0 * math.pi * harmonic * index / count) for index in range(count))
        harmonics.append((harmonic, 2.0 * cosine / count, 2.0 * sine / count))
    if count % 2 == 0:
        harmonic = count // 2
        cosine = _safe_fsum(values[index] * math.cos(math.pi * index) for index in range(count))
        highest_nyquist = (harmonic, cosine / count)
    return mean, harmonics, highest_nyquist


def _evaluate_fourier(coefficients, phase: float) -> float:
    mean, harmonics, nyquist = coefficients
    terms = [mean]
    terms.extend(cosine * math.cos(harmonic * phase) + sine * math.sin(harmonic * phase)
                 for harmonic, cosine, sine in harmonics)
    if nyquist is not None:
        harmonic, cosine = nyquist
        terms.append(cosine * math.cos(harmonic * phase))
    return _safe_fsum(terms)


def _safe_fsum(values) -> float:
    try:
        return math.fsum(values)
    except (OverflowError, ValueError):
        return math.inf


def evaluate_periodic_tensor_fourier_reconstruction(request: PeriodicTensorFourierReconstruction) -> Calculation:
    """Interpolate tensor samples with the full real trigonometric interpolant."""
    input_digest = canonical_digest(request.model_dump(mode="json"))
    knot_count = len(request.sample_ids) - 1
    harmonic_count = knot_count // 2
    work = 12 * knot_count * max(1, harmonic_count) + 12 * len(request.evaluation_phase_rad) * max(1, harmonic_count)
    base = {
        "analysis_id": request.analysis_id,
        "material_condition_id": request.material_condition_id,
        "source_id": request.source_id,
        "source_sha256": request.source_sha256,
        "input_sha256": input_digest,
        "sample_count_including_duplicate_endpoint": len(request.sample_ids),
        "independent_periodic_knot_count": knot_count,
        "evaluation_count": len(request.evaluation_phase_rad),
        "tensor_component_order": ["xx", "yy", "zz", "xy", "yz", "zx"],
        "input_strain_shear_convention": request.input_strain_shear_convention,
        "time_reconstruction": "full_bandwidth_real_trigonometric_interpolant_on_uniform_periodic_knots",
    }
    if not all((
        request.tensor_basis_and_order_reviewed,
        request.uniform_periodic_sampling_reviewed,
        request.closed_cycle_and_path_order_reviewed,
        request.fourier_reconstruction_and_aliasing_reviewed,
    )):
        return Calculation(status="needs_data", values=base | {
            "reason": "tensor_sampling_closure_periodicity_and_fourier_aliasing_reviews_required",
            "stress_tensor_components_at_evaluation_phases": None,
            "strain_tensor_components_at_evaluation_phases": None,
        })
    if work > request.maximum_trigonometric_term_work:
        return Calculation(status="out_of_scope", values=base | {
            "reason": "trigonometric_interpolation_work_budget_exceeded",
            "trigonometric_term_work": work,
            "maximum_trigonometric_term_work": request.maximum_trigonometric_term_work,
            "stress_tensor_components_at_evaluation_phases": None,
            "strain_tensor_components_at_evaluation_phases": None,
        })
    stress_unique = request.stress_tensor_components_Pa[:-1]
    strain_unique = request.strain_tensor_components[:-1]
    stress_coefficients = [_real_fourier_coefficients([row[component] for row in stress_unique]) for component in range(6)]
    strain_coefficients = [_real_fourier_coefficients([row[component] for row in strain_unique]) for component in range(6)]
    coefficient_values = []
    for collection in (stress_coefficients, strain_coefficients):
        for mean, harmonics, nyquist in collection:
            coefficient_values.append(mean)
            for _, cosine, sine in harmonics:
                coefficient_values.extend((cosine, sine))
            if nyquist is not None:
                coefficient_values.append(nyquist[1])
    if not all(math.isfinite(value) for value in coefficient_values):
        return Calculation(status="out_of_scope", values=base | {
            "reason": "finite_samples_produce_nonfinite_fourier_coefficients",
            "stress_tensor_components_at_evaluation_phases": None,
            "strain_tensor_components_at_evaluation_phases": None,
        })
    stress_output = []
    strain_output = []
    for phase in request.evaluation_phase_rad:
        stress_row = [_evaluate_fourier(coefficient, phase) for coefficient in stress_coefficients]
        strain_row = [_evaluate_fourier(coefficient, phase) for coefficient in strain_coefficients]
        if not all(math.isfinite(value) for value in (*stress_row, *strain_row)):
            return Calculation(status="out_of_scope", values=base | {
                "reason": "finite_samples_produce_nonfinite_trigonometric_interpolant",
                "evaluation_id": request.evaluation_ids[len(stress_output)],
                "stress_tensor_components_at_evaluation_phases": None,
                "strain_tensor_components_at_evaluation_phases": None,
            })
        stress_output.append(stress_row)
        strain_output.append(strain_row)
    coefficient_payload = {
        "stress": [[mean, harmonics, nyquist] for mean, harmonics, nyquist in stress_coefficients],
        "strain": [[mean, harmonics, nyquist] for mean, harmonics, nyquist in strain_coefficients],
    }
    return Calculation(values=base | {
        "status": "computed",
        "trigonometric_term_work": work,
        "fourier_coefficient_sha256": canonical_digest(coefficient_payload),
        "evaluation_points": [
            {
                "evaluation_id": request.evaluation_ids[index],
                "phase_rad": phase,
                "stress_tensor_components_Pa": stress_output[index],
                "strain_tensor_components": strain_output[index],
            }
            for index, phase in enumerate(request.evaluation_phase_rad)
        ],
        "limitations": [
            "Input knots are assumed uniformly spaced over one periodic cycle; nonuniform clocks are unsupported.",
            "All resolvable harmonics are retained; there is no smoothing, low-pass filtering or anti-aliasing, and no interpolation error bound is returned.",
            "Discontinuities, sharp corners or noisy records can create global oscillation/Gibbs behavior; reconstruction suitability must be reviewed by the caller.",
            "This module only reconstructs stress and strain tensors; it does not calculate work, damage, fatigue life or qualification.",
        ],
    })


def specifications() -> list[ModelSpec]:
    return [ModelSpec(
        "fatigue.periodic_tensor_fourier_reconstruction",
        PeriodicTensorFourierReconstruction,
        evaluate_periodic_tensor_fourier_reconstruction,
        {
            "evaluation_points[].stress_tensor_components_Pa": "Pa",
            "evaluation_points[].strain_tensor_components": "1",
            "evaluation_points[].phase_rad": "rad",
        },
        (
            "Uses full-bandwidth trigonometric interpolation on a uniformly sampled, exactly closed periodic tensor cycle.",
            "All harmonic coefficients are derived from the caller's finite samples without filtering or extrapolating beyond the period.",
            "Interpolation is a path reconstruction option only and does not by itself establish stress-strain damage, life or qualification.",
        ),
        ("caller_uniform_periodic_real_trigonometric_tensor_interpolation", "trefethen_spectral_methods_fourier_interpolation"),
        qualification="user_model",
    )]
