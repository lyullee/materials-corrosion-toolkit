"""Caller-calibrated finite-sample Sines-style mean-invariant limit screen."""

from __future__ import annotations

import math

from pydantic import Field, model_validator

from .contracts import Calculation, Contract, Evidence, Positive, canonical_digest
from .multiaxial_stress_invariant_history import (
    SampledStressInvariantHistory,
    evaluate_sampled_stress_invariant_history,
)
from .registry import ModelSpec


class MultiaxialSinesMeanLimitScreen(Contract):
    """Finite sampled deviatoric amplitude plus time-mean hydrostatic stress."""

    analysis_id: str = Field(min_length=1)
    stress_history: SampledStressInvariantHistory
    stress_history_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    sample_time_s: list[float] = Field(min_length=3, max_length=10000)
    calibration_id: str = Field(min_length=1)
    calibration_source_id: str = Field(min_length=1)
    calibration_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    calibration_evidence: Evidence
    calibration_material_condition_id: str = Field(min_length=1)
    deviatoric_coefficient: Positive
    mean_hydrostatic_coefficient: float
    caller_limit_Pa: Positive
    coefficients_and_limit_reviewed: bool
    calibration_material_scope_reviewed: bool
    finite_sample_amplitude_and_time_weighting_reviewed: bool

    @model_validator(mode="after")
    def aligned_history_and_calibration(self):
        actual_history_digest = canonical_digest(self.stress_history.model_dump(mode="json"))
        if actual_history_digest != self.stress_history_sha256:
            raise ValueError("stress-history digest differs from the nested caller contract")
        if len(self.sample_time_s) != len(self.stress_history.sample_ids):
            raise ValueError("sample times must align with the nested stress-history samples")
        if any(not math.isfinite(value) for value in self.sample_time_s):
            raise ValueError("sample times must be finite")
        if any(right <= left for left, right in zip(self.sample_time_s[:-1], self.sample_time_s[1:], strict=True)):
            raise ValueError("sample times must strictly increase in caller path order")
        if not math.isfinite(self.mean_hydrostatic_coefficient):
            raise ValueError("mean-hydrostatic coefficient must be finite")
        if self.calibration_material_condition_id != self.stress_history.material_condition_id:
            raise ValueError("calibration material condition must exactly match the stress history")
        if (
            self.calibration_evidence.source_id != self.calibration_source_id
            or self.calibration_evidence.sha256 != self.calibration_sha256
        ):
            raise ValueError("calibration Evidence must match the declared source and digest")
        return self


def evaluate_multiaxial_sines_mean_limit_screen(request: MultiaxialSinesMeanLimitScreen) -> dict:
    """Compare a finite-sample Sines-style parameter with the caller limit.

    Mean hydrostatic stress is integrated exactly for the piecewise-linear
    hydrostatic path over the supplied, potentially nonuniform time grid. The
    deviatoric amplitude uses the separate finite-sample half-diameter contract.
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
        "finite_sample_convention": "half maximum pairwise sqrt(J2) distance; piecewise-linear time average of hydrostatic stress",
    }
    if not all((
        request.coefficients_and_limit_reviewed,
        request.calibration_material_scope_reviewed,
        request.finite_sample_amplitude_and_time_weighting_reviewed,
    )):
        return base | {
            "status": "needs_data",
            "reason": "calibration_material_scope_finite_sample_and_time_weighting_review_required",
            "screening_parameter_Pa": None,
            "mean_hydrostatic_stress_Pa": None,
            "margin_to_caller_limit_Pa": None,
            "screening_outcome": None,
        }

    history = evaluate_sampled_stress_invariant_history(request.stress_history)
    if history["status"] != "computed":
        return base | {
            "status": history["status"],
            "reason": history.get("reason", "stress_history_descriptor_unavailable"),
            "screening_parameter_Pa": None,
            "mean_hydrostatic_stress_Pa": None,
            "margin_to_caller_limit_Pa": None,
            "screening_outcome": None,
        }

    stresses = request.stress_history.stress_tensor_components_Pa
    hydrostatic = [(row[0] + row[1] + row[2]) / 3.0 for row in stresses]
    time = request.sample_time_s
    total_duration = time[-1] - time[0]
    intervals = [right - left for left, right in zip(time[:-1], time[1:], strict=True)]
    area_terms = [
        0.5 * (hydrostatic[index] + hydrostatic[index + 1]) * intervals[index]
        for index in range(len(intervals))
    ]
    if not all(math.isfinite(value) for value in (total_duration, *intervals, *area_terms)):
        return base | {
            "status": "out_of_scope",
            "reason": "finite_inputs_produce_nonfinite_time_integral",
            "screening_parameter_Pa": None,
            "mean_hydrostatic_stress_Pa": None,
            "margin_to_caller_limit_Pa": None,
            "screening_outcome": None,
        }
    try:
        mean_hydrostatic = math.fsum(area_terms) / total_duration
    except (OverflowError, ValueError, ZeroDivisionError):
        mean_hydrostatic = math.inf
    parameter = (
        request.deviatoric_coefficient * history["values"]["sampled_deviatoric_J2_half_diameter_Pa"]
        + request.mean_hydrostatic_coefficient * mean_hydrostatic
    )
    margin = request.caller_limit_Pa - parameter
    if not math.isfinite(mean_hydrostatic) or not math.isfinite(parameter) or not math.isfinite(margin):
        return base | {
            "status": "out_of_scope",
            "reason": "finite_inputs_produce_nonfinite_screening_arithmetic",
            "screening_parameter_Pa": None,
            "mean_hydrostatic_stress_Pa": None,
            "margin_to_caller_limit_Pa": None,
            "screening_outcome": None,
        }
    return base | {
        "status": "computed",
        "screening_parameter_Pa": parameter,
        "mean_hydrostatic_stress_Pa": mean_hydrostatic,
        "caller_limit_Pa": request.caller_limit_Pa,
        "margin_to_caller_limit_Pa": margin,
        "screening_outcome": "caller_limit_not_exceeded" if parameter <= request.caller_limit_Pa else "caller_limit_exceeded",
        "deviatoric_distance_witness_sample_ids": history["values"]["diameter_witness_sample_ids"],
        "meaning": "deterministic finite-sample comparison to a caller-supplied calibrated limit; not fatigue life, probability, acceptance or qualification",
    }


def _registry_evaluator(request: MultiaxialSinesMeanLimitScreen) -> Calculation:
    """Adapt the transparent value mapping to the registry Calculation contract."""
    result = evaluate_multiaxial_sines_mean_limit_screen(request)
    return Calculation(
        status=result["status"],
        values={key: value for key, value in result.items() if key != "status"},
    )


def specifications() -> list[ModelSpec]:
    return [ModelSpec(
        "fatigue.multiaxial_sines_mean_limit_screen",
        MultiaxialSinesMeanLimitScreen,
        _registry_evaluator,
        {
            "screening_parameter_Pa": "Pa",
            "mean_hydrostatic_stress_Pa": "Pa",
            "caller_limit_Pa": "Pa",
            "margin_to_caller_limit_Pa": "Pa",
        },
        (
            "Uses caller-specified coefficients, limit and same-material calibration Evidence; no constants are inferred.",
            "Mean hydrostatic stress is the trapezoidal time average on supplied sample times; deviatoric amplitude is the finite sampled half pairwise sqrt(J2) diameter.",
            "This finite-sample comparison is not a continuous-path amplitude, life prediction, failure probability, acceptance decision or material qualification.",
        ),
        ("caller_finite_sample_sines_mean_hydrostatic_limit_screen",),
        qualification="user_model",
    )]
