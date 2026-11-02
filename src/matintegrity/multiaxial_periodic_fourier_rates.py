"""Analytic time rates of periodic stress/strain tensor Fourier interpolants."""

from __future__ import annotations

import math
from typing import Literal

from pydantic import Field, model_validator

from .contracts import Calculation, Contract, Evidence, canonical_digest
from .multiaxial_periodic_fourier_reconstruction import _real_fourier_coefficients
from .registry import ModelSpec


class PeriodicTensorFourierRates(Contract):
    analysis_id: str = Field(min_length=1)
    material_condition_id: str = Field(min_length=1)
    source_id: str = Field(min_length=1)
    source_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    evidence: Evidence
    sample_ids: list[str] = Field(min_length=4, max_length=4097)
    stress_tensor_components_Pa: list[list[float]] = Field(min_length=4, max_length=4097)
    strain_tensor_components: list[list[float]] = Field(min_length=4, max_length=4097)
    period_s: float = Field(gt=0.0)
    evaluation_ids: list[str] = Field(min_length=2, max_length=100000)
    evaluation_phase_rad: list[float] = Field(min_length=2, max_length=100000)
    strain_shear_convention: Literal["tensor", "engineering"]
    maximum_trigonometric_term_work: int = Field(default=2_000_000, ge=1, le=20_000_000)
    tensor_basis_and_order_reviewed: bool
    uniform_periodic_sampling_reviewed: bool
    closed_cycle_and_path_order_reviewed: bool
    period_and_clock_basis_reviewed: bool
    fourier_reconstruction_and_aliasing_reviewed: bool

    @model_validator(mode="after")
    def validate_inputs(self):
        if self.evidence.source_id != self.source_id or self.evidence.sha256 != self.source_sha256:
            raise ValueError("Evidence must match the declared source and digest")
        count = len(self.sample_ids)
        if len(set(self.sample_ids)) != count:
            raise ValueError("sample IDs must be unique and retain path order")
        if len(self.stress_tensor_components_Pa) != count or len(self.strain_tensor_components) != count:
            raise ValueError("sample IDs and tensor histories must align")
        if any(len(row) != 6 for row in (*self.stress_tensor_components_Pa, *self.strain_tensor_components)):
            raise ValueError("tensor rows must use [xx, yy, zz, xy, yz, zx]")
        if self.stress_tensor_components_Pa[0] != self.stress_tensor_components_Pa[-1]:
            raise ValueError("stress cycle endpoints must match exactly")
        if self.strain_tensor_components[0] != self.strain_tensor_components[-1]:
            raise ValueError("strain cycle endpoints must match exactly")
        if not all(math.isfinite(x) for row in (*self.stress_tensor_components_Pa, *self.strain_tensor_components) for x in row):
            raise ValueError("tensor samples must be finite")
        if not math.isfinite(self.period_s):
            raise ValueError("period_s must be finite")
        if len(self.evaluation_ids) != len(self.evaluation_phase_rad) or len(set(self.evaluation_ids)) != len(self.evaluation_ids):
            raise ValueError("evaluation IDs must be unique and align with phase queries")
        if any(not math.isfinite(x) or x < 0.0 or x > 2.0 * math.pi for x in self.evaluation_phase_rad):
            raise ValueError("evaluation phases must be finite radians in [0, 2*pi]")
        if any(b <= a for a, b in zip(self.evaluation_phase_rad[:-1], self.evaluation_phase_rad[1:], strict=True)):
            raise ValueError("evaluation phases must strictly increase")
        return self


def _derivative_per_phase(coefficients, phase: float) -> float:
    _, harmonics, nyquist = coefficients
    terms = [harmonic * (-cosine * math.sin(harmonic * phase) + sine * math.cos(harmonic * phase))
             for harmonic, cosine, sine in harmonics]
    if nyquist is not None:
        harmonic, cosine = nyquist
        terms.append(-harmonic * cosine * math.sin(harmonic * phase))
    try:
        return math.fsum(terms)
    except (OverflowError, ValueError):
        return math.inf


def evaluate_periodic_tensor_fourier_rates(request: PeriodicTensorFourierRates) -> Calculation:
    """Return analytic derivatives of the full-bandwidth periodic interpolants."""
    digest = canonical_digest(request.model_dump(mode="json"))
    knots = len(request.sample_ids) - 1
    harmonics = knots // 2
    work = 12 * knots * max(1, harmonics) + 12 * len(request.evaluation_phase_rad) * max(1, harmonics)
    base = {
        "analysis_id": request.analysis_id,
        "material_condition_id": request.material_condition_id,
        "source_id": request.source_id,
        "source_sha256": request.source_sha256,
        "input_sha256": digest,
        "period_s": request.period_s,
        "independent_periodic_knot_count": knots,
        "tensor_component_order": ["xx", "yy", "zz", "xy", "yz", "zx"],
        "strain_shear_convention": request.strain_shear_convention,
        "derivative_basis": "analytic_derivative_of_full_bandwidth_real_trigonometric_interpolant",
    }
    reviews = (request.tensor_basis_and_order_reviewed, request.uniform_periodic_sampling_reviewed,
               request.closed_cycle_and_path_order_reviewed, request.period_and_clock_basis_reviewed,
               request.fourier_reconstruction_and_aliasing_reviewed)
    if not all(reviews):
        return Calculation(status="needs_data", values=base | {
            "reason": "tensor_cycle_period_clock_and_reconstruction_reviews_required",
            "evaluation_points": None,
        })
    if work > request.maximum_trigonometric_term_work:
        return Calculation(status="out_of_scope", values=base | {
            "reason": "fourier_rate_work_budget_exceeded", "trigonometric_term_work": work,
            "maximum_trigonometric_term_work": request.maximum_trigonometric_term_work,
            "evaluation_points": None,
        })
    stress = [_real_fourier_coefficients([row[j] for row in request.stress_tensor_components_Pa[:-1]]) for j in range(6)]
    strain = [_real_fourier_coefficients([row[j] for row in request.strain_tensor_components[:-1]]) for j in range(6)]
    scale = 2.0 * math.pi / request.period_s
    rows = []
    for index, phase in enumerate(request.evaluation_phase_rad):
        stress_rate = [_derivative_per_phase(c, phase) * scale for c in stress]
        strain_rate = [_derivative_per_phase(c, phase) * scale for c in strain]
        if not all(math.isfinite(x) for x in (*stress_rate, *strain_rate)):
            return Calculation(status="out_of_scope", values=base | {
                "reason": "finite_samples_produce_nonfinite_interpolant_rate",
                "evaluation_id": request.evaluation_ids[index], "evaluation_points": None,
            })
        rows.append({
            "evaluation_id": request.evaluation_ids[index], "phase_rad": phase,
            "stress_rate_tensor_components_Pa_s": stress_rate,
            "strain_rate_tensor_components_s_inv": strain_rate,
        })
    coefficients = {"stress": stress, "strain": strain}
    return Calculation(values=base | {
        "status": "computed", "trigonometric_term_work": work,
        "coefficient_sha256": canonical_digest(coefficients), "evaluation_points": rows,
        "limitations": [
            "Rates are derivatives of the finite-sample full-bandwidth periodic interpolant, not measured derivatives.",
            "Uniform sampling, cycle closure and a physically meaningful period must be reviewed by the caller.",
            "High-frequency noise and aliasing are retained; no smoothing or derivative uncertainty is provided.",
            "This API does not infer constitutive state, plasticity, damage, fatigue life or material qualification.",
        ],
    })


def specifications() -> list[ModelSpec]:
    return [ModelSpec(
        "fatigue.periodic_tensor_fourier_rates", PeriodicTensorFourierRates,
        evaluate_periodic_tensor_fourier_rates,
        {"evaluation_points[].stress_rate_tensor_components_Pa_s": "Pa/s",
         "evaluation_points[].strain_rate_tensor_components_s_inv": "1/s"},
        ("Returns analytic derivatives with respect to physical time of the full-bandwidth real Fourier interpolants.",
         "Requires a reviewed period and uniformly spaced closed-cycle samples.",
         "Derivative output is a kinematic input bridge only; it is not a constitutive or fatigue-life result."),
        ("trefethen_spectral_methods_in_matlab_fourier_differentiation",), qualification="user_model",
    )]
