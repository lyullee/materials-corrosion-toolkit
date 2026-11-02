"""Caller-data implementation of a generalized strain-amplitude plane parameter."""

from __future__ import annotations

import math

from pydantic import Field, model_validator

from ..contracts import Calculation, Contract, Evidence, Nonnegative, Positive, canonical_digest
from ..registry import ModelSpec
from .fatigue import CriticalPlaneCandidate


Tensor6 = list[float]  # [xx, yy, zz, xy, yz, zx]; shear entries are tensor components.


class InceGlinkaGSACalculation(Contract):
    """One closed tensor cycle and caller-declared elastic/plastic strain split."""

    assessment_id: str = Field(min_length=1)
    physical_scope_id: str = Field(min_length=1)
    material_condition_id: str = Field(min_length=1)
    location_id: str = Field(min_length=1)
    source_provider_id: str = Field(min_length=1)
    source_provider_revision: str = Field(min_length=1)
    configuration_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    sample_ids: tuple[str, ...] = Field(min_length=3, max_length=100000)
    stress_tensor_components_Pa: tuple[Tensor6, ...] = Field(min_length=3, max_length=100000)
    elastic_strain_tensor_components: tuple[Tensor6, ...] = Field(min_length=3, max_length=100000)
    plastic_strain_tensor_components: tuple[Tensor6, ...] = Field(min_length=3, max_length=100000)
    candidate_planes: tuple[CriticalPlaneCandidate, ...] = Field(min_length=1, max_length=100000)
    shear_fatigue_strength_coefficient_Pa: Positive
    axial_fatigue_strength_coefficient_Pa: Positive
    maximum_stress_closure_error_Pa: Nonnegative
    maximum_elastic_strain_closure_error: Nonnegative
    maximum_plastic_strain_closure_error: Nonnegative
    maximum_plane_sample_evaluations: int = Field(default=2_000_000, ge=1, le=50_000_000)
    representative_cycle_and_tensor_convention_reviewed: bool
    elastic_plastic_decomposition_reviewed: bool
    plane_grid_support_reviewed: bool
    material_parameter_basis_and_units_reviewed: bool
    source_use_rights_reviewed: bool
    computational_use_authorized: bool
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def aligned_closed_cycle(self):
        n = len(self.sample_ids)
        if len(set(self.sample_ids)) != n:
            raise ValueError("sample IDs must be unique and retain the input path order")
        histories = (
            self.stress_tensor_components_Pa,
            self.elastic_strain_tensor_components,
            self.plastic_strain_tensor_components,
        )
        if any(len(history) != n for history in histories):
            raise ValueError("stress and both strain histories must align with sample IDs")
        if any(len(tensor) != 6 for history in histories for tensor in history):
            raise ValueError("each symmetric tensor must use [xx, yy, zz, xy, yz, zx]")
        if len({plane.plane_id for plane in self.candidate_planes}) != len(self.candidate_planes):
            raise ValueError("candidate plane IDs must be unique")
        if len(self.candidate_planes) * n > self.maximum_plane_sample_evaluations:
            raise ValueError("finite-plane history work budget exceeded")
        if self.source_provider_id not in {item.source_id for item in self.evidence}:
            raise ValueError("the history provider must be identified in Evidence")
        return self


def _tensor_product(a: list[float], tensor: Tensor6, b: list[float]) -> float:
    xx, yy, zz, xy, yz, zx = tensor
    matrix = ((xx, xy, zx), (xy, yy, yz), (zx, yz, zz))
    return sum(a[i] * matrix[i][j] * b[j] for i in range(3) for j in range(3))


def _range_amplitude(values: list[float]) -> float:
    return (max(values) - min(values)) / 2.0


def ince_glinka_gsa_parameter(x: InceGlinkaGSACalculation) -> Calculation:
    """Evaluate a finite-plane GSA parameter for one supplied closed cycle.

    No cycle counting, life mapping, interpolation between sample knots or
    continuous plane maximization is performed here.
    """
    digest = canonical_digest(x.model_dump(mode="json"))
    common = {
        "assessment_id": x.assessment_id,
        "physical_scope_id": x.physical_scope_id,
        "material_condition_id": x.material_condition_id,
        "location_id": x.location_id,
        "source_provider_id": x.source_provider_id,
        "source_provider_revision": x.source_provider_revision,
        "configuration_sha256": x.configuration_sha256,
        "input_sha256": digest,
        "sample_count": len(x.sample_ids),
        "candidate_plane_count": len(x.candidate_planes),
        "parameter": "generalized_strain_amplitude",
        "cycle_counting": "not_performed_single_closed_cycle_only",
    }
    reviews = {
        "representative_cycle_and_tensor_convention_reviewed": x.representative_cycle_and_tensor_convention_reviewed,
        "elastic_plastic_decomposition_reviewed": x.elastic_plastic_decomposition_reviewed,
        "plane_grid_support_reviewed": x.plane_grid_support_reviewed,
        "material_parameter_basis_and_units_reviewed": x.material_parameter_basis_and_units_reviewed,
        "source_use_rights_reviewed": x.source_use_rights_reviewed,
        "computational_use_authorized": x.computational_use_authorized,
    }
    missing = [name for name, accepted in reviews.items() if not accepted]
    if missing:
        return Calculation(status="needs_data", values=common | {"missing_reviews": missing})

    histories = (
        x.stress_tensor_components_Pa,
        x.elastic_strain_tensor_components,
        x.plastic_strain_tensor_components,
    )
    closure_errors = [
        math.dist(first, last)
        for history in histories
        for first, last in ((history[0], history[-1]),)
    ]
    stress_error, elastic_error, plastic_error = closure_errors
    if not all(math.isfinite(value) for value in closure_errors):
        return Calculation(status="out_of_scope", values=common | {
            "reason": "cycle_closure_metric_exceeds_finite_numeric_support",
        })
    closure_ok = (
        stress_error <= x.maximum_stress_closure_error_Pa
        and elastic_error <= x.maximum_elastic_strain_closure_error
        and plastic_error <= x.maximum_plastic_strain_closure_error
    )
    if not closure_ok:
        return Calculation(
            status="needs_data",
            values=common | {
                "stress_closure_error_Pa": stress_error,
                "elastic_strain_closure_error": elastic_error,
                "plastic_strain_closure_error": plastic_error,
                "candidate_planes": [],
            },
            notes=("The supplied first and last tensor states exceed one or more declared cycle-closure tolerances.",),
        )

    candidates: list[dict[str, float | str]] = []
    try:
        for plane in x.candidate_planes:
            normal = plane.normal
            direction = plane.in_plane_direction
            resolved_stress_n = [
                _tensor_product(normal, tensor, normal) for tensor in x.stress_tensor_components_Pa
            ]
            resolved_stress_shear = [
                _tensor_product(direction, tensor, normal) for tensor in x.stress_tensor_components_Pa
            ]
            resolved_elastic_n = [
                _tensor_product(normal, tensor, normal) for tensor in x.elastic_strain_tensor_components
            ]
            resolved_plastic_n = [
                _tensor_product(normal, tensor, normal) for tensor in x.plastic_strain_tensor_components
            ]
            resolved_elastic_shear = [
                2.0 * _tensor_product(direction, tensor, normal)
                for tensor in x.elastic_strain_tensor_components
            ]
            resolved_plastic_shear = [
                2.0 * _tensor_product(direction, tensor, normal)
                for tensor in x.plastic_strain_tensor_components
            ]
            tau_max = max(abs(value) for value in resolved_stress_shear)
            sigma_n_max = max(resolved_stress_n)
            gamma_e_amp = _range_amplitude(resolved_elastic_shear)
            gamma_p_amp = _range_amplitude(resolved_plastic_shear)
            epsilon_e_amp = _range_amplitude(resolved_elastic_n)
            epsilon_p_amp = _range_amplitude(resolved_plastic_n)
            gsa = (
                (tau_max / x.shear_fatigue_strength_coefficient_Pa) * gamma_e_amp
                + gamma_p_amp
                + (sigma_n_max / x.axial_fatigue_strength_coefficient_Pa) * epsilon_e_amp
                + epsilon_p_amp
            )
            if not math.isfinite(gsa):
                raise ArithmeticError("nonfinite generalized strain-amplitude parameter")
            candidates.append({
                "plane_id": plane.plane_id,
                "maximum_absolute_resolved_shear_stress_Pa": tau_max,
                "maximum_resolved_normal_stress_Pa": sigma_n_max,
                "elastic_shear_strain_amplitude": gamma_e_amp,
                "plastic_shear_strain_amplitude": gamma_p_amp,
                "elastic_normal_strain_amplitude": epsilon_e_amp,
                "plastic_normal_strain_amplitude": epsilon_p_amp,
                "gsa_parameter": gsa,
            })
    except (ArithmeticError, OverflowError, ValueError):
        return Calculation(status="out_of_scope", values=common | {
            "reason": "nonfinite_or_unrepresentable_plane_parameter",
            "candidate_planes": [],
        })

    critical = max(candidates, key=lambda row: (float(row["gsa_parameter"]), str(row["plane_id"])))
    return Calculation(values=common | {
        "stress_closure_error_Pa": stress_error,
        "elastic_strain_closure_error": elastic_error,
        "plastic_strain_closure_error": plastic_error,
        "maximum_gsa_parameter": critical["gsa_parameter"],
        "critical_plane_id": critical["plane_id"],
        "candidate_planes": candidates,
        "fatigue_life_or_acceptance_inferred": False,
    }, notes=(
        "The caller-supplied elastic/plastic tensor split and strength coefficients determine this finite-plane parameter.",
        "This implementation is an independent coding of a published mathematical criterion; it does not reproduce the paper text or experimental tables.",
        "Only caller-listed planes and supplied knots are evaluated; the result is not life, damage accumulation, acceptance, calibration transfer or material qualification.",
    ))


def specifications() -> list[ModelSpec]:
    return [ModelSpec(
        "fatigue.ince_glinka_generalized_strain_amplitude",
        InceGlinkaGSACalculation,
        ince_glinka_gsa_parameter,
        {
            "maximum_gsa_parameter": "1",
            "candidate_planes[].gsa_parameter": "1",
        },
        (
            "One caller-declared closed stress/elastic-strain/plastic-strain tensor cycle.",
            "The caller supplies material fatigue-strength coefficients and a finite reviewed plane set.",
            "No rainflow, cycle accumulation, life mapping, unsampled-path correction or physical qualification.",
        ),
        ("ince_glinka_generalized_strain_amplitude",),
        qualification="user_model",
    )]
