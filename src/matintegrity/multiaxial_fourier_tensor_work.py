"""Exact signed tensor work over the full-bandwidth periodic Fourier interpolant."""

from __future__ import annotations

import math
from typing import Literal

from pydantic import Field, model_validator

from .contracts import Calculation, Contract, Evidence, canonical_digest
from .multiaxial_periodic_fourier_reconstruction import _real_fourier_coefficients
from .registry import ModelSpec


class PeriodicFourierTensorWork(Contract):
    analysis_id: str = Field(min_length=1)
    material_condition_id: str = Field(min_length=1)
    source_id: str = Field(min_length=1)
    source_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    evidence: Evidence
    sample_ids: list[str] = Field(min_length=4, max_length=4097)
    stress_tensor_components_Pa: list[list[float]] = Field(min_length=4, max_length=4097)
    strain_tensor_components: list[list[float]] = Field(min_length=4, max_length=4097)
    strain_shear_convention: Literal["tensor", "engineering"]
    maximum_trigonometric_term_work: int = Field(default=2_000_000, ge=1, le=20_000_000)
    tensor_basis_and_order_reviewed: bool
    uniform_periodic_sampling_reviewed: bool
    closed_cycle_and_path_order_reviewed: bool
    stress_strain_conjugacy_and_work_sign_reviewed: bool
    fourier_reconstruction_suitability_reviewed: bool

    @model_validator(mode="after")
    def aligned_closed_histories(self):
        if self.evidence.source_id != self.source_id or self.evidence.sha256 != self.source_sha256:
            raise ValueError("Evidence must match the declared source and digest")
        count = len(self.sample_ids)
        if len(set(self.sample_ids)) != count:
            raise ValueError("sample IDs must be unique and ordered")
        if len(self.stress_tensor_components_Pa) != count or len(self.strain_tensor_components) != count:
            raise ValueError("sample IDs and stress/strain histories must align")
        if any(len(row) != 6 for row in (*self.stress_tensor_components_Pa, *self.strain_tensor_components)):
            raise ValueError("tensor rows use [xx, yy, zz, xy, yz, zx]")
        if self.stress_tensor_components_Pa[0] != self.stress_tensor_components_Pa[-1]:
            raise ValueError("stress cycle endpoints must match exactly")
        if self.strain_tensor_components[0] != self.strain_tensor_components[-1]:
            raise ValueError("strain cycle endpoints must match exactly")
        if not all(math.isfinite(value) for row in (*self.stress_tensor_components_Pa, *self.strain_tensor_components) for value in row):
            raise ValueError("stress and strain tensor samples must be finite")
        return self


def evaluate_periodic_fourier_tensor_work(request: PeriodicFourierTensorWork) -> Calculation:
    """Integrate sigma:d-epsilon over one trigonometric-interpolant cycle exactly."""
    input_digest = canonical_digest(request.model_dump(mode="json"))
    knot_count = len(request.sample_ids) - 1
    harmonic_count = knot_count // 2
    work_budget = 12 * knot_count * max(1, harmonic_count)
    base = {
        "analysis_id": request.analysis_id,
        "material_condition_id": request.material_condition_id,
        "source_id": request.source_id,
        "source_sha256": request.source_sha256,
        "input_sha256": input_digest,
        "independent_periodic_knot_count": knot_count,
        "tensor_component_order": ["xx", "yy", "zz", "xy", "yz", "zx"],
        "strain_shear_convention": request.strain_shear_convention,
        "time_reconstruction": "full_bandwidth_real_trigonometric_interpolant",
        "integration": "exact_orthogonality_integral_of_interpolant_sigma: d_epsilon over phase 0..2pi",
    }
    if not all((
        request.tensor_basis_and_order_reviewed,
        request.uniform_periodic_sampling_reviewed,
        request.closed_cycle_and_path_order_reviewed,
        request.stress_strain_conjugacy_and_work_sign_reviewed,
        request.fourier_reconstruction_suitability_reviewed,
    )):
        return Calculation(status="needs_data", values=base | {
            "reason": "tensor_sampling_closure_conjugacy_work_sign_and_fourier_suitability_reviews_required",
            "signed_work_density_J_m3": None,
            "component_work_density_J_m3": None,
        })
    if work_budget > request.maximum_trigonometric_term_work:
        return Calculation(status="out_of_scope", values=base | {
            "reason": "fourier_coefficient_work_budget_exceeded",
            "trigonometric_term_work": work_budget,
            "maximum_trigonometric_term_work": request.maximum_trigonometric_term_work,
            "signed_work_density_J_m3": None,
            "component_work_density_J_m3": None,
        })
    stress_unique = request.stress_tensor_components_Pa[:-1]
    strain_unique = request.strain_tensor_components[:-1]
    component_results = []
    coefficient_payload = []
    shear_weights = (1.0, 1.0, 1.0, 2.0, 2.0, 2.0) if request.strain_shear_convention == "tensor" else (1.0,) * 6
    for component in range(6):
        stress_coeff = _real_fourier_coefficients([row[component] for row in stress_unique])
        strain_coeff = _real_fourier_coefficients([row[component] for row in strain_unique])
        stress_mean, stress_harmonics, stress_nyquist = stress_coeff
        strain_mean, strain_harmonics, strain_nyquist = strain_coeff
        if len(stress_harmonics) != len(strain_harmonics):
            return Calculation(status="out_of_scope", values=base | {
                "reason": "stress_and_strain_fourier_basis_mismatch",
                "signed_work_density_J_m3": None,
                "component_work_density_J_m3": None,
            })
        terms = []
        for stress_item, strain_item in zip(stress_harmonics, strain_harmonics, strict=True):
            harmonic, stress_cos, stress_sin = stress_item
            strain_harmonic, strain_cos, strain_sin = strain_item
            if harmonic != strain_harmonic:
                return Calculation(status="out_of_scope", values=base | {
                    "reason": "stress_and_strain_harmonic_indices_mismatch",
                    "signed_work_density_J_m3": None,
                    "component_work_density_J_m3": None,
                })
            terms.append(math.pi * harmonic * shear_weights[component] * (
                stress_cos * strain_sin - stress_sin * strain_cos
            ))
        try:
            work = math.fsum(terms)
        except (OverflowError, ValueError):
            work = math.inf
        component_results.append(work)
        coefficient_payload.append({
            "stress_mean": stress_mean,
            "strain_mean": strain_mean,
            "stress_harmonics": stress_harmonics,
            "strain_harmonics": strain_harmonics,
            "stress_nyquist": stress_nyquist,
            "strain_nyquist": strain_nyquist,
        })
    if not all(math.isfinite(value) for value in component_results):
        return Calculation(status="out_of_scope", values=base | {
            "reason": "finite_inputs_produce_nonfinite_fourier_work_terms",
            "signed_work_density_J_m3": None,
            "component_work_density_J_m3": None,
        })
    try:
        total_work = math.fsum(component_results)
    except (OverflowError, ValueError):
        total_work = math.inf
    if not math.isfinite(total_work):
        return Calculation(status="out_of_scope", values=base | {
            "reason": "nonfinite_total_fourier_tensor_work",
            "signed_work_density_J_m3": None,
            "component_work_density_J_m3": component_results,
        })
    return Calculation(values=base | {
        "status": "computed",
        "trigonometric_term_work": work_budget,
        "coefficient_sha256": canonical_digest(coefficient_payload),
        "component_work_density_J_m3": component_results,
        "signed_work_density_J_m3": total_work,
        "limitations": [
            "The result is exact for the unique full-bandwidth trigonometric interpolant of the supplied uniformly spaced knots, not necessarily for the physical unsampled path.",
            "Even-sample Nyquist terms have cosine-only representation and do not contribute a closed-cycle cross-harmonic work term.",
            "This is signed net work density; it is not automatically irreversible plastic dissipation, fatigue damage, life, acceptance or qualification.",
            "Nonuniform sampling, smoothing, alias rejection and interpolation uncertainty are not handled.",
        ],
    })


def specifications() -> list[ModelSpec]:
    return [ModelSpec(
        "fatigue.periodic_fourier_tensor_work",
        PeriodicFourierTensorWork,
        evaluate_periodic_fourier_tensor_work,
        {"signed_work_density_J_m3": "J/m^3", "component_work_density_J_m3": "J/m^3"},
        (
            "Stress and strain use the same ordered closed tensor cycle and a caller-declared tensor or engineering shear convention.",
            "The signed closed-cycle integral is exact only for the full-bandwidth periodic trigonometric interpolant of the uniform samples.",
            "Net work is not identified as plastic dissipation or mapped to fatigue damage or life.",
        ),
        ("caller_exact_closed_tensor_work_fourier_orthogonality_integral",),
        qualification="user_model",
    )]
