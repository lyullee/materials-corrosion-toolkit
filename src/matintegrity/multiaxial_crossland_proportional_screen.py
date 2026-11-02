"""Finite-sample Crossland-style limit screen restricted to proportional stress paths."""

from __future__ import annotations

import math

from pydantic import Field, model_validator

from .contracts import Calculation, Contract, Evidence, Nonnegative, Positive, canonical_digest
from .multiaxial_stress_invariant_history import SampledStressInvariantHistory
from .registry import ModelSpec

MODEL_ID = "fatigue.multiaxial_crossland_proportional_limit_screen"
CALIBRATION_SOURCE_ID = "caller_crossland_finite_proportional_limit_calibration"
METHOD_SOURCE_ID = "crossland_1956_hydrostatic_pressure_torsional_fatigue_criterion"


class MultiaxialCrosslandProportionalLimitScreen(Contract):
    """Evaluate a finite closed proportional stress cycle against caller data."""

    analysis_id: str = Field(min_length=1)
    stress_history: SampledStressInvariantHistory
    stress_history_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    calibration_id: str = Field(min_length=1)
    calibration_source_id: str = Field(min_length=1)
    calibration_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    calibration_evidence: Evidence
    calibration_material_condition_id: str = Field(min_length=1)
    hydrostatic_coefficient_alpha: Nonnegative
    caller_limit_beta_Pa: Positive
    proportionality_tolerance_Pa: Nonnegative
    coefficients_and_limit_reviewed: bool
    calibration_material_and_scope_reviewed: bool
    proportional_path_assumption_and_tolerance_reviewed: bool
    maximum_pair_evaluations: int = Field(default=2_000_000, ge=1, le=20_000_000)

    @model_validator(mode="after")
    def validate_lineage_and_scope(self):
        actual = canonical_digest(self.stress_history.model_dump(mode="json"))
        if actual != self.stress_history_sha256:
            raise ValueError("stress-history digest differs from the nested history contract")
        if self.calibration_material_condition_id != self.stress_history.material_condition_id:
            raise ValueError("calibration material condition must exactly match the stress history")
        if (self.calibration_evidence.source_id != self.calibration_source_id
                or self.calibration_evidence.sha256 != self.calibration_sha256):
            raise ValueError("calibration Evidence must match the declared source and digest")
        return self


def _deviatoric(row: list[float]) -> tuple[float, ...]:
    mean = (row[0] + row[1] + row[2]) / 3.0
    return (row[0] - mean, row[1] - mean, row[2] - mean, row[3], row[4], row[5])


def _inner(left: tuple[float, ...], right: tuple[float, ...]) -> float:
    """J2 metric inner product; its square norm is the second deviatoric invariant."""
    return 0.5 * (left[0] * right[0] + left[1] * right[1] + left[2] * right[2]) + (
        left[3] * right[3] + left[4] * right[4] + left[5] * right[5]
    )


def evaluate_multiaxial_crossland_proportional_limit_screen(
    request: MultiaxialCrosslandProportionalLimitScreen,
) -> Calculation:
    """Compute sqrt(J2)_a + alpha * max(sigma_H) for collinear deviatoric paths.

    The stress history is sampled and closed. Proportionality is checked by
    testing all finite deviatoric samples against the affine line through the
    farthest sampled pair in the J2 metric. Non-collinear histories are refused.
    """
    history = request.stress_history
    rows = history.stress_tensor_components_Pa
    count = len(rows)
    pair_count = count * (count - 1) // 2
    digest = canonical_digest(request.model_dump(mode="json"))
    base = {
        "analysis_id": request.analysis_id,
        "material_condition_id": request.calibration_material_condition_id,
        "history_source_id": history.source_id,
        "history_source_sha256": history.source_sha256,
        "stress_history_sha256": request.stress_history_sha256,
        "calibration_id": request.calibration_id,
        "calibration_source_id": request.calibration_source_id,
        "calibration_sha256": request.calibration_sha256,
        "hydrostatic_coefficient_alpha": request.hydrostatic_coefficient_alpha,
        "caller_limit_beta_Pa": request.caller_limit_beta_Pa,
        "proportionality_tolerance_Pa": request.proportionality_tolerance_Pa,
        "input_sha256": digest,
        "finite_path_convention": "half_range_of_J2_metric_coordinate_for_a_collinear_deviatoric_stress_path",
    }
    if not all((history.closed_cycle_and_sample_order_reviewed, history.stress_tensor_basis_reviewed,
                request.coefficients_and_limit_reviewed, request.calibration_material_and_scope_reviewed,
                request.proportional_path_assumption_and_tolerance_reviewed)):
        return Calculation(status="needs_data", values=base | {
            "reason": "stress_basis_cycle_material_calibration_and_proportionality_reviews_required",
            "crossland_parameter_Pa": None,
            "screening_outcome": None,
        })
    if pair_count > request.maximum_pair_evaluations:
        return Calculation(status="out_of_scope", values=base | {
            "reason": "finite_path_pair_search_work_limit_exceeded",
            "pair_evaluations_required": pair_count,
            "pair_evaluations_allowed": request.maximum_pair_evaluations,
            "crossland_parameter_Pa": None,
            "screening_outcome": None,
        })

    dev = [_deviatoric(row) for row in rows]
    farthest_sq = -1.0
    witness = (0, 0)
    for i in range(count - 1):
        for j in range(i + 1, count):
            delta = tuple(b - a for a, b in zip(dev[i], dev[j], strict=True))
            squared = _inner(delta, delta)
            if not math.isfinite(squared) or squared < 0:
                return Calculation(status="out_of_scope", values=base | {
                    "reason": "finite_path_produces_invalid_deviatoric_distance",
                    "crossland_parameter_Pa": None,
                    "screening_outcome": None,
                })
            if squared > farthest_sq:
                farthest_sq, witness = squared, (i, j)

    if farthest_sq == 0.0:
        amplitude = 0.0
        maximum_line_residual = 0.0
        coordinate_min = coordinate_max = 0.0
    else:
        origin = dev[witness[0]]
        endpoint = dev[witness[1]]
        direction = tuple(b - a for a, b in zip(origin, endpoint, strict=True))
        distance = math.sqrt(farthest_sq)
        unit = tuple(value / distance for value in direction)
        coordinates = []
        residuals = []
        for point in dev:
            relative = tuple(value - start for value, start in zip(point, origin, strict=True))
            coordinate = _inner(relative, unit)
            residual = tuple(value - coordinate * axis for value, axis in zip(relative, unit, strict=True))
            residual_sq = _inner(residual, residual)
            if not math.isfinite(coordinate) or not math.isfinite(residual_sq) or residual_sq < 0:
                return Calculation(status="out_of_scope", values=base | {
                    "reason": "proportionality_projection_produced_nonfinite_value",
                    "crossland_parameter_Pa": None,
                    "screening_outcome": None,
                })
            coordinates.append(coordinate)
            residuals.append(math.sqrt(residual_sq))
        maximum_line_residual = max(residuals)
        if maximum_line_residual > request.proportionality_tolerance_Pa:
            return Calculation(status="out_of_scope", values=base | {
                "reason": "deviatoric_stress_path_exceeds_declared_proportionality_tolerance",
                "maximum_deviatoric_line_residual_Pa": maximum_line_residual,
                "proportionality_tolerance_Pa": request.proportionality_tolerance_Pa,
                "crossland_parameter_Pa": None,
                "screening_outcome": None,
            })
        coordinate_min, coordinate_max = min(coordinates), max(coordinates)
        amplitude = 0.5 * (coordinate_max - coordinate_min)

    hydrostatic = [(row[0] + row[1] + row[2]) / 3.0 for row in rows]
    peak_hydrostatic = max(hydrostatic)
    parameter = amplitude + request.hydrostatic_coefficient_alpha * peak_hydrostatic
    margin = request.caller_limit_beta_Pa - parameter
    if not all(math.isfinite(value) for value in (amplitude, maximum_line_residual, peak_hydrostatic, parameter, margin)):
        return Calculation(status="out_of_scope", values=base | {
            "reason": "finite_sample_crossland_arithmetic_nonfinite",
            "crossland_parameter_Pa": None,
            "screening_outcome": None,
        })
    return Calculation(values=base | {
        "status": "computed",
        "sqrt_J2_stress_amplitude_Pa": amplitude,
        "maximum_hydrostatic_stress_Pa": peak_hydrostatic,
        "maximum_deviatoric_line_residual_Pa": maximum_line_residual,
        "proportionality_witness_sample_ids": [history.sample_ids[witness[0]], history.sample_ids[witness[1]]],
        "crossland_parameter_Pa": parameter,
        "margin_to_caller_limit_Pa": margin,
        "screening_outcome": "caller_limit_not_exceeded" if parameter <= request.caller_limit_beta_Pa else "caller_limit_exceeded",
        "interpretation": "finite sampled Crossland-style high-cycle limit screen for a stress path passing the declared proportionality check",
        "limitations": [
            "Only finite samples of a closed cycle are evaluated; unsampled extrema and continuous-time behavior are not reconstructed.",
            "The deviatoric path must fit one affine line within the caller-declared absolute tolerance; non-proportional paths are rejected.",
            "Alpha, beta, and material applicability are caller supplied and require same-condition calibration; no calibration transfer is inferred.",
            "The output is a deterministic limit screen, not cycle life, variable-amplitude damage, probability, code acceptance, or qualification.",
        ],
    })


def specifications() -> list[ModelSpec]:
    return [ModelSpec(
        model_id=MODEL_ID,
        input_type=MultiaxialCrosslandProportionalLimitScreen,
        evaluator=evaluate_multiaxial_crossland_proportional_limit_screen,
        units={
            "sqrt_J2_stress_amplitude_Pa": "Pa",
            "maximum_hydrostatic_stress_Pa": "Pa",
            "crossland_parameter_Pa": "Pa",
            "caller_limit_beta_Pa": "Pa",
            "margin_to_caller_limit_Pa": "Pa",
        },
        assumptions=(
            "Uses the maximum sampled hydrostatic stress and half-range of the collinear deviatoric path coordinate.",
            "Requires a finite closed proportional stress cycle within the caller-declared absolute residual tolerance.",
            "Uses caller-supplied same-condition Crossland coefficients and limit; no life, probability, acceptance, or qualification is inferred.",
        ),
        source_ids=(CALIBRATION_SOURCE_ID, METHOD_SOURCE_ID),
        qualification="user_model",
    )]
