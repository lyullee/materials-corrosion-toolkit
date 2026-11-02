"""Finite-quadrature Papadopoulos P2-style multiaxial fatigue limit screen."""

from __future__ import annotations

import math

from pydantic import Field, model_validator

from .contracts import Calculation, Contract, Evidence, Nonnegative, Positive, canonical_digest
from .multiaxial_stress_invariant_history import SampledStressInvariantHistory
from .registry import ModelSpec


class PapadopoulosPlaneShearQuadrature(Contract):
    """Caller finite quadrature of in-plane resolved-shear directions."""

    plane_id: str = Field(min_length=1)
    normal: tuple[float, float, float]
    tangent_u: tuple[float, float, float]
    tangent_v: tuple[float, float, float]
    chi_radians: tuple[float, ...] = Field(min_length=2, max_length=360)
    normalized_direction_weights: tuple[Positive, ...] = Field(min_length=2, max_length=360)

    @model_validator(mode="after")
    def valid_basis_and_quadrature(self):
        if len(self.chi_radians) != len(self.normalized_direction_weights):
            raise ValueError("each in-plane shear direction requires one quadrature weight")
        vectors = (self.normal, self.tangent_u, self.tangent_v)
        if any(not math.isfinite(value) for vector in vectors for value in vector):
            raise ValueError("plane basis vectors must be finite")

        def dot(left, right):
            return math.fsum(a * b for a, b in zip(left, right, strict=True))

        tolerance = 1e-9
        if any(abs(dot(vector, vector) - 1.0) > tolerance for vector in vectors):
            raise ValueError("plane normal and tangent basis vectors must be unit length")
        if any(abs(dot(left, right)) > tolerance for left, right in (
            (self.normal, self.tangent_u),
            (self.normal, self.tangent_v),
            (self.tangent_u, self.tangent_v),
        )):
            raise ValueError("plane normal and tangent directions must be mutually orthogonal")
        if any(not math.isfinite(angle) or not 0.0 <= angle < 2.0 * math.pi for angle in self.chi_radians):
            raise ValueError("chi angles must be finite radians in [0, 2*pi)")
        if len(set(self.chi_radians)) != len(self.chi_radians):
            raise ValueError("chi angles must be unique within each plane")
        weight_sum = math.fsum(self.normalized_direction_weights)
        if not math.isclose(weight_sum, 1.0, rel_tol=0.0, abs_tol=1e-10):
            raise ValueError("direction quadrature weights must sum to one")
        return self


class PapadopoulosP2FiniteSampleScreen(Contract):
    """Compute one finite-plane/direction P2-style limit comparison."""

    analysis_id: str = Field(min_length=1)
    stress_history: SampledStressInvariantHistory
    stress_history_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    plane_quadratures: tuple[PapadopoulosPlaneShearQuadrature, ...] = Field(min_length=1, max_length=1000)
    calibration_id: str = Field(min_length=1)
    calibration_source_id: str = Field(min_length=1)
    calibration_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    calibration_evidence: Evidence
    calibration_material_condition_id: str = Field(min_length=1)
    hydrostatic_coefficient: Nonnegative
    caller_limit_Pa: Positive
    plane_population_and_direction_quadrature_reviewed: bool
    stress_basis_and_sampled_cycle_reviewed: bool
    calibration_material_scope_reviewed: bool
    caller_limit_use_reviewed: bool
    maximum_shear_evaluations: int = Field(default=2_000_000, ge=1, le=20_000_000)

    @model_validator(mode="after")
    def coherent_history_and_calibration(self):
        actual_history_digest = canonical_digest(self.stress_history.model_dump(mode="json"))
        if actual_history_digest != self.stress_history_sha256:
            raise ValueError("stress-history digest differs from the nested caller contract")
        plane_ids = [item.plane_id for item in self.plane_quadratures]
        if len(set(plane_ids)) != len(plane_ids):
            raise ValueError("plane IDs must be unique")
        if self.calibration_material_condition_id != self.stress_history.material_condition_id:
            raise ValueError("calibration material condition must exactly match the stress history")
        if (
            self.calibration_evidence.source_id != self.calibration_source_id
            or self.calibration_evidence.sha256 != self.calibration_sha256
        ):
            raise ValueError("calibration Evidence must match the declared source and digest")
        return self


def _resolved_shear(stress: list[float], normal: tuple[float, float, float], shear_direction: tuple[float, float, float]) -> float:
    """Return m·sigma·n for [xx, yy, zz, xy, yz, zx] symmetric stress."""
    nx, ny, nz = normal
    xx, yy, zz, xy, yz, zx = stress
    traction = (
        xx * nx + xy * ny + zx * nz,
        xy * nx + yy * ny + yz * nz,
        zx * nx + yz * ny + zz * nz,
    )
    try:
        return math.fsum(value * direction for value, direction in zip(traction, shear_direction, strict=True))
    except (OverflowError, ValueError):
        return math.inf


def evaluate_papadopoulos_p2_finite_sample_screen(request: PapadopoulosP2FiniteSampleScreen) -> dict:
    """Evaluate finite shear-direction quadrature and compare to caller limit.

    For each candidate plane, the generalized shear amplitude is the square
    root of twice the direction-weighted mean of squared half-ranges. The factor
    two makes equally weighted uniform directions approximate the published
    circle integral convention; this finite sum is caller-declared quadrature.
    """
    input_digest = canonical_digest(request.model_dump(mode="json"))
    base = {
        "analysis_id": request.analysis_id,
        "material_condition_id": request.calibration_material_condition_id,
        "stress_history_sha256": request.stress_history_sha256,
        "calibration_id": request.calibration_id,
        "calibration_source_id": request.calibration_source_id,
        "calibration_sha256": request.calibration_sha256,
        "input_sha256": input_digest,
        "method_variant": "finite-plane_and_finite_in-plane-direction_Papadopoulos_P2_style",
    }
    if not all((
        request.plane_population_and_direction_quadrature_reviewed,
        request.stress_basis_and_sampled_cycle_reviewed,
        request.calibration_material_scope_reviewed,
        request.caller_limit_use_reviewed,
        request.stress_history.closed_cycle_and_sample_order_reviewed,
        request.stress_history.stress_tensor_basis_reviewed,
    )):
        return base | {
            "status": "needs_data",
            "reason": "plane_quadrature_stress_cycle_calibration_and_limit_reviews_required",
            "equivalent_screening_parameter_Pa": None,
            "margin_to_caller_limit_Pa": None,
            "screening_outcome": None,
        }

    history = request.stress_history
    evaluation_count = len(history.sample_ids) * sum(len(item.chi_radians) for item in request.plane_quadratures)
    if evaluation_count > request.maximum_shear_evaluations:
        return base | {
            "status": "out_of_scope",
            "reason": "finite_plane_direction_sample_work_limit_exceeded",
            "shear_evaluations_required": evaluation_count,
            "shear_evaluations_allowed": request.maximum_shear_evaluations,
            "equivalent_screening_parameter_Pa": None,
            "margin_to_caller_limit_Pa": None,
            "screening_outcome": None,
        }

    stress_rows = history.stress_tensor_components_Pa
    hydrostatic = [(row[0] / 3.0 + row[1] / 3.0 + row[2] / 3.0) for row in stress_rows]
    if any(not math.isfinite(value) for value in hydrostatic):
        return base | {
            "status": "out_of_scope",
            "reason": "finite_stress_samples_produce_nonfinite_hydrostatic_stress",
            "equivalent_screening_parameter_Pa": None,
            "margin_to_caller_limit_Pa": None,
            "screening_outcome": None,
        }
    hydrostatic_max_index = max(range(len(hydrostatic)), key=hydrostatic.__getitem__)
    plane_results = []
    for plane in request.plane_quadratures:
        weighted_squares = []
        maximum_direction_amplitude = -1.0
        maximum_direction_witness = None
        for angle, weight in zip(plane.chi_radians, plane.normalized_direction_weights, strict=True):
            direction = tuple(
                math.cos(angle) * u + math.sin(angle) * v
                for u, v in zip(plane.tangent_u, plane.tangent_v, strict=True)
            )
            shear_samples = [
                _resolved_shear(stress, plane.normal, direction)
                for stress in stress_rows
            ]
            if any(not math.isfinite(value) for value in shear_samples):
                return base | {
                    "status": "out_of_scope",
                    "reason": "finite_stress_samples_produce_nonfinite_resolved_shear",
                    "equivalent_screening_parameter_Pa": None,
                    "margin_to_caller_limit_Pa": None,
                    "screening_outcome": None,
                }
            minimum_index = min(range(len(shear_samples)), key=shear_samples.__getitem__)
            maximum_index = max(range(len(shear_samples)), key=shear_samples.__getitem__)
            amplitude = 0.5 * shear_samples[maximum_index] - 0.5 * shear_samples[minimum_index]
            square_term = weight * amplitude * amplitude
            if not math.isfinite(square_term):
                return base | {
                    "status": "out_of_scope",
                    "reason": "finite_resolved_shear_produces_nonfinite_amplitude_square",
                    "equivalent_screening_parameter_Pa": None,
                    "margin_to_caller_limit_Pa": None,
                    "screening_outcome": None,
                }
            weighted_squares.append(square_term)
            if amplitude > maximum_direction_amplitude:
                maximum_direction_amplitude = amplitude
                maximum_direction_witness = {
                    "chi_radians": angle,
                    "minimum_sample_id": history.sample_ids[minimum_index],
                    "maximum_sample_id": history.sample_ids[maximum_index],
                }
        try:
            generalized_shear_amplitude = math.sqrt(2.0 * math.fsum(weighted_squares))
        except (OverflowError, ValueError):
            generalized_shear_amplitude = math.inf
        if not math.isfinite(generalized_shear_amplitude):
            return base | {
                "status": "out_of_scope",
                "reason": "finite_direction_quadrature_produces_nonfinite_generalized_amplitude",
                "equivalent_screening_parameter_Pa": None,
                "margin_to_caller_limit_Pa": None,
                "screening_outcome": None,
            }
        plane_results.append({
            "plane_id": plane.plane_id,
            "generalized_shear_amplitude_Pa": generalized_shear_amplitude,
            "direction_count": len(plane.chi_radians),
            "direction_weight_sum": math.fsum(plane.normalized_direction_weights),
            "maximum_single_direction_half_range_Pa": maximum_direction_amplitude,
            "maximum_direction_witness": maximum_direction_witness,
        })

    governing = max(plane_results, key=lambda row: row["generalized_shear_amplitude_Pa"])
    parameter = governing["generalized_shear_amplitude_Pa"] + request.hydrostatic_coefficient * hydrostatic[hydrostatic_max_index]
    margin = request.caller_limit_Pa - parameter
    if not math.isfinite(parameter) or not math.isfinite(margin):
        return base | {
            "status": "out_of_scope",
            "reason": "finite_inputs_produce_nonfinite_limit_combination",
            "equivalent_screening_parameter_Pa": None,
            "margin_to_caller_limit_Pa": None,
            "screening_outcome": None,
        }
    return base | {
        "status": "computed",
        "hydrostatic_maximum_Pa": hydrostatic[hydrostatic_max_index],
        "hydrostatic_maximum_witness_sample_id": history.sample_ids[hydrostatic_max_index],
        "governing_plane_id": governing["plane_id"],
        "plane_results": plane_results,
        "hydrostatic_coefficient": request.hydrostatic_coefficient,
        "caller_limit_Pa": request.caller_limit_Pa,
        "equivalent_screening_parameter_Pa": parameter,
        "margin_to_caller_limit_Pa": margin,
        "screening_outcome": "caller_limit_not_exceeded" if parameter <= request.caller_limit_Pa else "caller_limit_exceeded",
        "meaning": "finite caller plane/direction/sample comparison; not a continuous optimum, fatigue life, probability, acceptance or qualification",
    }



def _registry_calculation(request):
    result = evaluate_papadopoulos_p2_finite_sample_screen(request)
    return Calculation(status=result["status"], values=result)

def specifications() -> list[ModelSpec]:
    return [ModelSpec(
        "fatigue.papadopoulos_p2_finite_sample_limit_screen",
        PapadopoulosP2FiniteSampleScreen,
        _registry_calculation,
        {
            "hydrostatic_maximum_Pa": "Pa",
            "plane_results[].generalized_shear_amplitude_Pa": "Pa",
            "plane_results[].maximum_single_direction_half_range_Pa": "Pa",
            "caller_limit_Pa": "Pa",
            "equivalent_screening_parameter_Pa": "Pa",
            "margin_to_caller_limit_Pa": "Pa",
        },
        (
            "The Papadopoulos P2 structure combines a critical-plane generalized shear amplitude with maximum hydrostatic stress; the implementation uses only caller-supplied finite planes and finite direction quadrature.",
            "Material coefficient, limit, plane population, angular weights and application scope are caller supplied and reviewed; no material data or continuous search is inferred.",
            "The finite sample/plane/direction result is a deterministic screen, not life, probability, code acceptance or qualification.",
        ),
        ("caller_finite_quadrature_papadopoulos_p2_limit_screen",),
        qualification="user_model",
    )]
