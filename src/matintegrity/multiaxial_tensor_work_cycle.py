"""Signed tensor work per volume along a finite, caller-supplied closed path."""

from __future__ import annotations

import math

from pydantic import Field, model_validator

from .contracts import Calculation, Contract, canonical_digest
from .registry import ModelSpec

MODEL_ID = "fatigue.sampled_tensor_stress_strain_work_cycle"
SOURCE_ID = "caller_multiaxial_tensor_work_cycle"


class MultiaxialTensorWorkCycle(Contract):
    """Aligned sampled Cauchy-stress and infinitesimal-strain tensor history.

    Stress components are always physical symmetric-tensor components in Pa.
    Strain shear components follow the explicit ``strain_shear_convention``.
    The path between adjacent samples is interpreted as a straight segment in
    the joint stress/strain sample space.
    """

    analysis_id: str = Field(min_length=1)
    material_condition_id: str = Field(min_length=1)
    location_id: str = Field(min_length=1)
    stress_history_source_id: str = Field(min_length=1)
    stress_history_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    strain_history_source_id: str = Field(min_length=1)
    strain_history_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    sample_ids: list[str] = Field(min_length=3, max_length=50000)
    stress_tensor_components_Pa: list[list[float]] = Field(min_length=3, max_length=50000)
    strain_tensor_components: list[list[float]] = Field(min_length=3, max_length=50000)
    tensor_component_order: tuple[str, ...] = ("xx", "yy", "zz", "xy", "yz", "zx")
    strain_shear_convention: str = Field(pattern=r"^(tensor|engineering)$")
    cycle_closure_and_sample_order_reviewed: bool
    stress_basis_and_sign_reviewed: bool
    strain_basis_and_sign_reviewed: bool
    stress_strain_conjugacy_reviewed: bool

    @model_validator(mode="after")
    def aligned_finite_closed_path(self):
        if self.tensor_component_order != ("xx", "yy", "zz", "xy", "yz", "zx"):
            raise ValueError("stress and strain components must use [xx, yy, zz, xy, yz, zx] order")
        count = len(self.sample_ids)
        if len(self.stress_tensor_components_Pa) != count or len(self.strain_tensor_components) != count:
            raise ValueError("sample IDs, stress tensors and strain tensors must have equal lengths")
        if len(set(self.sample_ids)) != count:
            raise ValueError("sample IDs must be unique while retaining caller path order")
        if any(len(row) != 6 for row in (*self.stress_tensor_components_Pa, *self.strain_tensor_components)):
            raise ValueError("each symmetric stress and strain tensor requires six components")
        if self.stress_tensor_components_Pa[0] != self.stress_tensor_components_Pa[-1]:
            raise ValueError("closed stress history requires exactly matching endpoint tensors")
        if self.strain_tensor_components[0] != self.strain_tensor_components[-1]:
            raise ValueError("closed strain history requires exactly matching endpoint tensors")
        if any(
            not math.isfinite(value)
            for history in (self.stress_tensor_components_Pa, self.strain_tensor_components)
            for row in history
            for value in row
        ):
            raise ValueError("stress and strain samples must be finite")
        return self


def _incremental_tensor_contraction(
    stress_average: list[float], strain_increment: list[float], shear_convention: str
) -> float:
    """Contract symmetric tensors with the selected shear component meaning."""
    normal = math.fsum(stress_average[index] * strain_increment[index] for index in range(3))
    shear_weight = 2.0 if shear_convention == "tensor" else 1.0
    shear = math.fsum(
        stress_average[index] * strain_increment[index]
        for index in range(3, 6)
    )
    return normal + shear_weight * shear


def evaluate_multiaxial_tensor_work_cycle(request: MultiaxialTensorWorkCycle) -> dict:
    """Integrate signed ``stress : d(strain)`` over the supplied polygonal cycle.

    The trapezoidal stress average is exact for each straight segment when both
    stress and strain are linearly interpolated between adjacent knots. This is
    a path integral; no time interpolation or additional samples are invented.
    """
    input_digest = canonical_digest(request.model_dump(mode="json"))
    base = {
        "analysis_id": request.analysis_id,
        "material_condition_id": request.material_condition_id,
        "location_id": request.location_id,
        "stress_history_source_id": request.stress_history_source_id,
        "stress_history_sha256": request.stress_history_sha256,
        "strain_history_source_id": request.strain_history_source_id,
        "strain_history_sha256": request.strain_history_sha256,
        "input_sha256": input_digest,
        "sample_count": len(request.sample_ids),
        "segment_count": len(request.sample_ids) - 1,
        "strain_shear_convention": request.strain_shear_convention,
    }
    if not all((
        request.cycle_closure_and_sample_order_reviewed,
        request.stress_basis_and_sign_reviewed,
        request.strain_basis_and_sign_reviewed,
        request.stress_strain_conjugacy_reviewed,
    )):
        return base | {
            "status": "needs_data",
            "reason": "reviewed_cycle_order_tensor_bases_signs_and_conjugacy_required",
            "signed_net_work_density_J_m3": None,
        }

    segment_terms: list[float] = []
    stress_rows = request.stress_tensor_components_Pa
    strain_rows = request.strain_tensor_components
    for index in range(len(request.sample_ids) - 1):
        average_stress = [
            0.5 * left + 0.5 * right
            for left, right in zip(stress_rows[index], stress_rows[index + 1], strict=True)
        ]
        strain_increment = [
            right - left
            for left, right in zip(strain_rows[index], strain_rows[index + 1], strict=True)
        ]
        try:
            segment_work = _incremental_tensor_contraction(
                average_stress, strain_increment, request.strain_shear_convention
            )
        except (OverflowError, ValueError):
            segment_work = math.inf
        segment_terms.append(segment_work)
        if not math.isfinite(segment_terms[-1]):
            return base | {
                "status": "out_of_scope",
                "reason": "finite_inputs_produce_nonfinite_segment_work",
                "signed_net_work_density_J_m3": None,
            }

    try:
        net_work = math.fsum(segment_terms)
    except (OverflowError, ValueError):
        net_work = math.inf
    if not math.isfinite(net_work):
        return base | {
            "status": "out_of_scope",
            "reason": "finite_segment_works_overflow_net_sum",
            "signed_net_work_density_J_m3": None,
        }
    return base | {
        "status": "computed",
        "signed_net_work_density_J_m3": net_work,
        "integration_basis": "piecewise-linear stress and strain between caller knots; exact trapezoidal segment integral",
        "meaning": "signed net tensor work per volume only; not irreversible dissipation, fatigue damage, life, probability, acceptance or qualification",
    }


def _registered_evaluator(request: MultiaxialTensorWorkCycle) -> Calculation:
    result = evaluate_multiaxial_tensor_work_cycle(request)
    status = result.pop("status")
    return Calculation(status=status, values=result)


def specifications() -> list[ModelSpec]:
    return [ModelSpec(
        model_id=MODEL_ID,
        input_type=MultiaxialTensorWorkCycle,
        evaluator=_registered_evaluator,
        units={"signed_net_work_density_J_m3": "J/m3"},
        assumptions=(
            "Stress and strain tensors must share a caller-reviewed conjugate basis, sign convention and exactly closed sample order.",
            "The result is signed work over piecewise-linear segments between supplied knots; it is not necessarily irreversible dissipation.",
            "No fatigue damage, life, probability, acceptance or qualification is inferred.",
        ),
        source_ids=(SOURCE_ID,),
        qualification="user_model",
    )]
