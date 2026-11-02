"""Finite-sample Itoh-style non-proportional strain parameter."""

from __future__ import annotations

import math

import numpy as np
from pydantic import Field, model_validator

from .contracts import Calculation, Contract, Evidence, Nonnegative, Positive, canonical_digest
from .registry import ModelSpec

MODEL_ID = "fatigue.itoh_nonproportional_strain_parameter"
CALIBRATION_SOURCE_ID = "caller_itoh_nonproportional_hardening_calibration"
METHOD_SOURCE_ID = "itoh_1995_nonproportional_low_cycle_fatigue_criterion"


class ItohNonproportionalStrainRequest(Contract):
    """Evaluate a caller-reviewed finite tensor cycle and material hardening factor.

    Tensor components use ``[xx, yy, zz, xy, yz, zx]`` order. Shear entries
    are explicitly declared as tensorial or engineering strain. The principal
    strain range and material coefficient are supplied and evidence-pinned by
    the caller; the evaluator computes the sampled path non-proportionality
    factor from the principal strain axes.
    """

    analysis_id: str = Field(min_length=1)
    material_condition_id: str = Field(min_length=1)
    cycle_id: str = Field(min_length=1)
    history_source_id: str = Field(min_length=1)
    history_source_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    history_evidence: Evidence
    strain_tensor_components: tuple[tuple[float, ...], ...] = Field(min_length=4, max_length=10001)
    sample_ids: tuple[str, ...] = Field(min_length=4, max_length=10001)
    time_s: tuple[Nonnegative, ...] = Field(min_length=4, max_length=10001)
    period_s: Positive
    strain_shear_convention: str = Field(pattern=r"^(tensor|engineering)$")
    tensor_component_order: tuple[str, ...] = ("xx", "yy", "zz", "xy", "yz", "zx")
    maximum_principal_strain_range: Positive
    principal_strain_range_evidence: Evidence
    hardening_coefficient_alpha: float
    calibration_source_id: str = Field(min_length=1)
    calibration_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    calibration_evidence: Evidence
    maximum_absolute_principal_strain_direction_gap_relative_tolerance: Nonnegative = 1e-10
    maximum_sample_count: int = Field(default=10001, ge=4, le=10001)
    tensor_basis_reviewed: bool
    cycle_clock_and_sample_order_reviewed: bool
    cycle_closure_reviewed: bool
    principal_strain_range_basis_reviewed: bool
    material_condition_and_alpha_calibration_reviewed: bool
    principal_axis_tie_convention_reviewed: bool

    @model_validator(mode="after")
    def validate_history_and_calibration(self):
        if self.tensor_component_order != ("xx", "yy", "zz", "xy", "yz", "zx"):
            raise ValueError("strain tensors must use [xx, yy, zz, xy, yz, zx] component order")
        n = len(self.sample_ids)
        if len(set(self.sample_ids)) != n:
            raise ValueError("sample IDs must be unique while preserving ordered cycle history")
        if len(self.strain_tensor_components) != n or len(self.time_s) != n:
            raise ValueError("strain tensors, sample IDs and clocks must have equal lengths")
        if any(len(row) != 6 for row in self.strain_tensor_components):
            raise ValueError("each symmetric strain tensor requires six components")
        if any(not math.isfinite(value) for row in self.strain_tensor_components for value in row):
            raise ValueError("strain tensor components must be finite")
        if self.time_s[0] != 0.0 or self.time_s[-1] != self.period_s:
            raise ValueError("cycle samples must begin at zero and include the declared period endpoint")
        if any(right <= left for left, right in zip(self.time_s, self.time_s[1:])):
            raise ValueError("cycle time samples must be strictly increasing")
        if self.strain_tensor_components[0] != self.strain_tensor_components[-1]:
            raise ValueError("closed tensor cycle requires an exact duplicate endpoint sample")
        if n > self.maximum_sample_count:
            raise ValueError("cycle sample count exceeds the declared work limit")
        if self.history_evidence.source_id != self.history_source_id:
            raise ValueError("history Evidence source ID must match the declared history source")
        if self.history_evidence.sha256 != self.history_source_sha256:
            raise ValueError("history Evidence digest must match the declared history digest")
        if (self.principal_strain_range_evidence.source_id != self.history_source_id
                or self.principal_strain_range_evidence.sha256 != self.history_source_sha256):
            raise ValueError("principal strain range Evidence must pin the same reviewed history")
        if (self.calibration_evidence.source_id != self.calibration_source_id
                or self.calibration_evidence.sha256 != self.calibration_sha256):
            raise ValueError("hardening calibration Evidence must match its declared source and digest")
        if self.maximum_absolute_principal_strain_direction_gap_relative_tolerance >= 1:
            raise ValueError("principal-axis gap tolerance must be below one")
        return self


def _strain_matrix(row: tuple[float, ...], shear_convention: str) -> np.ndarray:
    xx, yy, zz, xy, yz, zx = row
    shear_scale = 0.5 if shear_convention == "engineering" else 1.0
    return np.asarray(
        (
            (xx, shear_scale * xy, shear_scale * zx),
            (shear_scale * xy, yy, shear_scale * yz),
            (shear_scale * zx, shear_scale * yz, zz),
        ),
        dtype=float,
    )


def evaluate_itoh_nonproportional_strain_parameter(
    request: ItohNonproportionalStrainRequest,
) -> Calculation:
    """Return the sampled Itoh non-proportionality factor and strain parameter.

    The integral is evaluated by the trapezoidal rule on caller time knots.
    Principal strain axes are unoriented lines, so the angle between an axis
    and the reference axis is computed with the absolute eigenvector dot
    product. No unobserved temporal extrema or cycle count is inferred.
    """
    payload = request.model_dump(mode="json")
    digest = canonical_digest(payload)
    base = {
        "analysis_id": request.analysis_id,
        "material_condition_id": request.material_condition_id,
        "cycle_id": request.cycle_id,
        "history_source_id": request.history_source_id,
        "history_source_sha256": request.history_source_sha256,
        "calibration_source_id": request.calibration_source_id,
        "calibration_sha256": request.calibration_sha256,
        "input_sha256": digest,
        "sample_count": len(request.sample_ids),
    }
    reviews = (
        request.tensor_basis_reviewed,
        request.cycle_clock_and_sample_order_reviewed,
        request.cycle_closure_reviewed,
        request.principal_strain_range_basis_reviewed,
        request.material_condition_and_alpha_calibration_reviewed,
    )
    if not all(reviews):
        return Calculation(
            status="needs_data",
            values=base | {"reason": "tensor_cycle_range_and_material_calibration_reviews_required"},
        )

    eigenvalues_and_vectors = [np.linalg.eigh(_strain_matrix(row, request.strain_shear_convention))
                               for row in request.strain_tensor_components]
    amplitudes: list[float] = []
    axes: list[np.ndarray] = []
    axis_ties: list[str] = []
    tolerance = request.maximum_absolute_principal_strain_direction_gap_relative_tolerance

    for index, (eigenvalues, eigenvectors) in enumerate(eigenvalues_and_vectors):
        minimum = float(eigenvalues[0])
        maximum = float(eigenvalues[2])
        minimum_magnitude = abs(minimum)
        maximum_magnitude = abs(maximum)
        amplitude = max(minimum_magnitude, maximum_magnitude)
        amplitudes.append(amplitude)
        if amplitude == 0.0:
            # The associated integral weight is zero, so the arbitrary
            # eigenbasis at an all-zero sample cannot affect the result.
            axes.append(np.asarray((1.0, 0.0, 0.0)))
            continue
        choose_maximum = maximum_magnitude >= minimum_magnitude
        selected = 2 if choose_maximum else 0
        gap = abs(float(eigenvalues[selected] - eigenvalues[1]))
        if gap <= tolerance * amplitude:
            axis_ties.append(request.sample_ids[index])
        if math.isclose(maximum_magnitude, minimum_magnitude, rel_tol=tolerance, abs_tol=0.0):
            # Resolve equal-magnitude tensile/compressive extremes by a
            # declared deterministic convention; report all such samples.
            axis_ties.append(request.sample_ids[index])
            selected = 2
        amplitudes[-1] = amplitude
        axes.append(eigenvectors[:, selected].astype(float, copy=False))

    maximum_amplitude = max(amplitudes)
    if maximum_amplitude <= 0.0:
        return Calculation(
            status="out_of_scope",
            values=base | {"reason": "zero_maximum_absolute_principal_strain"},
        )
    if axis_ties and not request.principal_axis_tie_convention_reviewed:
        return Calculation(
            status="needs_data",
            values=base | {
                "reason": "principal_strain_axis_not_unique_at_some_samples",
                "axis_tie_sample_ids": list(dict.fromkeys(axis_ties)),
            },
        )

    reference_index = max(range(len(amplitudes)), key=amplitudes.__getitem__)
    reference_axis = axes[reference_index]
    weighted_rotation = []
    for amplitude, axis in zip(amplitudes, axes, strict=True):
        cosine = min(1.0, max(0.0, abs(float(np.dot(reference_axis, axis)))))
        sine_rotation = math.sqrt(max(0.0, 1.0 - cosine * cosine))
        weighted_rotation.append(amplitude * sine_rotation)

    integral = math.fsum(
        0.5 * (weighted_rotation[index] + weighted_rotation[index + 1])
        * (request.time_s[index + 1] - request.time_s[index])
        for index in range(len(weighted_rotation) - 1)
    )
    nonproportional_factor = (math.pi / 2.0) * integral / (request.period_s * maximum_amplitude)
    if not math.isfinite(nonproportional_factor) or nonproportional_factor < 0.0:
        return Calculation(
            status="out_of_scope",
            values=base | {"reason": "nonfinite_or_negative_nonproportionality_factor"},
        )

    parameter_range = (1.0 + request.hardening_coefficient_alpha * nonproportional_factor)
    parameter_range *= request.maximum_principal_strain_range
    if not math.isfinite(parameter_range) or parameter_range <= 0.0:
        return Calculation(
            status="out_of_scope",
            values=base | {"reason": "nonpositive_or_nonfinite_adjusted_strain_range"},
        )
    return Calculation(
        status="computed",
        values=base | {
            "nonproportional_factor_sampled_trapezoid": nonproportional_factor,
            "hardening_coefficient_alpha": request.hardening_coefficient_alpha,
            "maximum_principal_strain_range": request.maximum_principal_strain_range,
            "itoh_adjusted_nonproportional_strain_range": parameter_range,
            "maximum_absolute_principal_strain_reference_sample_id": request.sample_ids[reference_index],
            "principal_axis_tie_samples_resolved_by_positive_extreme": list(dict.fromkeys(axis_ties)),
            "integration_method": "trapezoidal quadrature over supplied time samples",
            "scope": "one caller-reviewed closed finite cycle; no cycle counting, life mapping, damage accumulation, extrapolation or material qualification",
        },
    )


def specifications() -> list[ModelSpec]:
    return [
        ModelSpec(
            model_id=MODEL_ID,
            input_type=ItohNonproportionalStrainRequest,
            evaluator=evaluate_itoh_nonproportional_strain_parameter,
            units={
                "nonproportional_factor_sampled_trapezoid": "1",
                "hardening_coefficient_alpha": "1",
                "maximum_principal_strain_range": "1",
                "itoh_adjusted_nonproportional_strain_range": "1",
            },
            assumptions=(
                "The evaluated factor is a trapezoidal approximation over the caller-provided samples and clocks for one exactly closed cycle.",
                "The maximum-principal-strain range and non-proportional hardening coefficient are caller-supplied, evidence-pinned and specific to the declared material condition.",
                "A non-unique principal axis requires an explicit review; equal tensile/compressive magnitudes use the positive extreme only as a declared computational tie convention.",
                "The result is a strain parameter only; no cycle counting, strain-life mapping, damage accumulation or qualification is inferred.",
            ),
            source_ids=(CALIBRATION_SOURCE_ID, METHOD_SOURCE_ID),
            qualification="engineering_screening",
        )
    ]
