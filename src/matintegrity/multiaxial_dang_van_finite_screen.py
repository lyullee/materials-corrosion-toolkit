"""Finite-system, finite-sample Dang Van-style multiaxial fatigue limit screen."""

from __future__ import annotations

import math

from pydantic import Field, model_validator

from .contracts import Calculation, Contract, Evidence, Nonnegative, Positive, canonical_digest
from .multiaxial_stress_invariant_history import SampledStressInvariantHistory
from .registry import ModelSpec


class DangVanShearSystem(Contract):
    """One caller-declared oriented material plane and in-plane shear direction."""

    system_id: str = Field(min_length=1)
    plane_normal: tuple[float, float, float]
    shear_direction: tuple[float, float, float]

    @model_validator(mode="after")
    def unit_orthogonal_basis(self):
        if any(not math.isfinite(value) for vector in (self.plane_normal, self.shear_direction) for value in vector):
            raise ValueError("shear-system vectors must be finite")
        normal_norm = math.sqrt(math.fsum(value * value for value in self.plane_normal))
        direction_norm = math.sqrt(math.fsum(value * value for value in self.shear_direction))
        if not math.isclose(normal_norm, 1.0, rel_tol=0.0, abs_tol=1e-9):
            raise ValueError("plane normal must be unit length")
        if not math.isclose(direction_norm, 1.0, rel_tol=0.0, abs_tol=1e-9):
            raise ValueError("shear direction must be unit length")
        dot = math.fsum(a * b for a, b in zip(self.plane_normal, self.shear_direction, strict=True))
        if abs(dot) > 1e-9:
            raise ValueError("shear direction must lie in the declared material plane")
        return self


class DangVanFiniteSampleScreen(Contract):
    """Caller-calibrated high-cycle screen on explicit planes and sample times."""

    analysis_id: str = Field(min_length=1)
    stress_history: SampledStressInvariantHistory
    stress_history_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    sample_time_s: tuple[float, ...] = Field(min_length=3, max_length=10000)
    shear_systems: tuple[DangVanShearSystem, ...] = Field(min_length=1, max_length=2000)
    calibration_id: str = Field(min_length=1)
    calibration_source_id: str = Field(min_length=1)
    calibration_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    calibration_evidence: Evidence
    calibration_material_condition_id: str = Field(min_length=1)
    hydrostatic_coefficient: Nonnegative
    caller_limit_Pa: Positive
    candidate_system_population_reviewed: bool
    time_weighted_shear_mean_reviewed: bool
    stress_sign_and_basis_reviewed: bool
    calibration_material_scope_reviewed: bool
    caller_limit_use_reviewed: bool
    maximum_shear_evaluations: int = Field(default=2_000_000, ge=1, le=20_000_000)

    @model_validator(mode="after")
    def aligned_history_and_calibration(self):
        actual_history_digest = canonical_digest(self.stress_history.model_dump(mode="json"))
        if actual_history_digest != self.stress_history_sha256:
            raise ValueError("stress-history digest differs from the nested caller contract")
        if len(self.sample_time_s) != len(self.stress_history.sample_ids):
            raise ValueError("sample times must align with the nested stress history")
        if any(not math.isfinite(value) for value in self.sample_time_s):
            raise ValueError("sample times must be finite")
        if any(right <= left for left, right in zip(self.sample_time_s[:-1], self.sample_time_s[1:], strict=True)):
            raise ValueError("sample times must strictly increase in caller path order")
        system_ids = [row.system_id for row in self.shear_systems]
        if len(set(system_ids)) != len(system_ids):
            raise ValueError("shear-system IDs must be unique")
        if self.calibration_material_condition_id != self.stress_history.material_condition_id:
            raise ValueError("calibration material condition must exactly match the stress history")
        if (
            self.calibration_evidence.source_id != self.calibration_source_id
            or self.calibration_evidence.sha256 != self.calibration_sha256
        ):
            raise ValueError("calibration Evidence must match the declared source and digest")
        return self


def _resolved_shear(stress: list[float], normal: tuple[float, float, float], direction: tuple[float, float, float]) -> float:
    xx, yy, zz, xy, yz, zx = stress
    nx, ny, nz = normal
    traction = (
        xx * nx + xy * ny + zx * nz,
        xy * nx + yy * ny + yz * nz,
        zx * nx + yz * ny + zz * nz,
    )
    try:
        return math.fsum(value * component for value, component in zip(traction, direction, strict=True))
    except (OverflowError, ValueError):
        return math.inf


def evaluate_dang_van_finite_sample_screen(request: DangVanFiniteSampleScreen) -> dict:
    """Evaluate finite sampled |tau - mean(tau)| + a*sigma_H against caller limit."""
    input_digest = canonical_digest(request.model_dump(mode="json"))
    base = {
        "analysis_id": request.analysis_id,
        "material_condition_id": request.calibration_material_condition_id,
        "stress_history_sha256": request.stress_history_sha256,
        "calibration_id": request.calibration_id,
        "calibration_source_id": request.calibration_source_id,
        "calibration_sha256": request.calibration_sha256,
        "input_sha256": input_digest,
        "method_variant": "finite_caller_shear_systems_time_samples_Dang_Van_style",
    }
    if not all((
        request.candidate_system_population_reviewed,
        request.time_weighted_shear_mean_reviewed,
        request.stress_sign_and_basis_reviewed,
        request.calibration_material_scope_reviewed,
        request.caller_limit_use_reviewed,
        request.stress_history.closed_cycle_and_sample_order_reviewed,
        request.stress_history.stress_tensor_basis_reviewed,
    )):
        return base | {
            "status": "needs_data",
            "reason": "candidate_systems_sample_clock_stress_calibration_and_limit_reviews_required",
            "equivalent_screening_parameter_Pa": None,
            "margin_to_caller_limit_Pa": None,
            "screening_outcome": None,
        }

    history = request.stress_history
    sample_count = len(history.sample_ids)
    evaluation_count = sample_count * len(request.shear_systems)
    if evaluation_count > request.maximum_shear_evaluations:
        return base | {
            "status": "out_of_scope",
            "reason": "finite_shear_system_sample_work_limit_exceeded",
            "shear_evaluations_required": evaluation_count,
            "shear_evaluations_allowed": request.maximum_shear_evaluations,
            "equivalent_screening_parameter_Pa": None,
            "margin_to_caller_limit_Pa": None,
            "screening_outcome": None,
        }

    stresses = history.stress_tensor_components_Pa
    hydrostatic = [row[0] / 3.0 + row[1] / 3.0 + row[2] / 3.0 for row in stresses]
    if any(not math.isfinite(value) for value in hydrostatic):
        return base | {
            "status": "out_of_scope",
            "reason": "finite_stress_samples_produce_nonfinite_hydrostatic_stress",
            "equivalent_screening_parameter_Pa": None,
            "margin_to_caller_limit_Pa": None,
            "screening_outcome": None,
        }

    times = request.sample_time_s
    duration = times[-1] - times[0]
    intervals = [right - left for left, right in zip(times[:-1], times[1:], strict=True)]
    if not math.isfinite(duration) or duration <= 0.0 or any(not math.isfinite(dt) for dt in intervals):
        return base | {
            "status": "out_of_scope",
            "reason": "sample_clock_duration_outside_finite_numeric_support",
            "equivalent_screening_parameter_Pa": None,
            "margin_to_caller_limit_Pa": None,
            "screening_outcome": None,
        }

    candidate_results = []
    for system in request.shear_systems:
        shear = [_resolved_shear(row, system.plane_normal, system.shear_direction) for row in stresses]
        if any(not math.isfinite(value) for value in shear):
            return base | {
                "status": "out_of_scope",
                "reason": "finite_stress_samples_produce_nonfinite_resolved_shear",
                "equivalent_screening_parameter_Pa": None,
                "margin_to_caller_limit_Pa": None,
                "screening_outcome": None,
            }
        shear_integral = [
            (0.5 * shear[index] + 0.5 * shear[index + 1]) * intervals[index]
            for index in range(sample_count - 1)
        ]
        if any(not math.isfinite(value) for value in shear_integral):
            return base | {
                "status": "out_of_scope",
                "reason": "sampled_shear_mean_integral_nonfinite",
                "equivalent_screening_parameter_Pa": None,
                "margin_to_caller_limit_Pa": None,
                "screening_outcome": None,
            }
        try:
            mean_shear = math.fsum(shear_integral) / duration
        except (OverflowError, ValueError, ZeroDivisionError):
            mean_shear = math.inf
        if not math.isfinite(mean_shear):
            return base | {
                "status": "out_of_scope",
                "reason": "sampled_shear_mean_nonfinite",
                "equivalent_screening_parameter_Pa": None,
                "margin_to_caller_limit_Pa": None,
                "screening_outcome": None,
            }
        criterion_samples = [
            abs(shear[index] - mean_shear) + request.hydrostatic_coefficient * hydrostatic[index]
            for index in range(sample_count)
        ]
        if any(not math.isfinite(value) for value in criterion_samples):
            return base | {
                "status": "out_of_scope",
                "reason": "finite_inputs_produce_nonfinite_criterion_sample",
                "equivalent_screening_parameter_Pa": None,
                "margin_to_caller_limit_Pa": None,
                "screening_outcome": None,
            }
        peak_index = max(range(sample_count), key=criterion_samples.__getitem__)
        candidate_results.append({
            "system_id": system.system_id,
            "time_weighted_mean_resolved_shear_Pa": mean_shear,
            "maximum_dang_van_parameter_Pa": criterion_samples[peak_index],
            "governing_sample_id": history.sample_ids[peak_index],
        })

    governing = max(candidate_results, key=lambda row: row["maximum_dang_van_parameter_Pa"])
    parameter = governing["maximum_dang_van_parameter_Pa"]
    margin = request.caller_limit_Pa - parameter
    if not math.isfinite(margin):
        return base | {
            "status": "out_of_scope",
            "reason": "finite_parameter_and_limit_produce_nonfinite_margin",
            "equivalent_screening_parameter_Pa": None,
            "margin_to_caller_limit_Pa": None,
            "screening_outcome": None,
        }
    return base | {
        "status": "computed",
        "hydrostatic_peak_Pa": max(hydrostatic),
        "caller_limit_Pa": request.caller_limit_Pa,
        "hydrostatic_coefficient": request.hydrostatic_coefficient,
        "equivalent_screening_parameter_Pa": parameter,
        "margin_to_caller_limit_Pa": margin,
        "governing_system_id": governing["system_id"],
        "governing_sample_id": governing["governing_sample_id"],
        "candidate_system_results": candidate_results,
        "screening_outcome": "caller_limit_not_exceeded" if margin >= 0.0 else "caller_limit_exceeded",
        "meaning": "finite caller-system/time-sample high-cycle limit screen; no life, probability, acceptance or qualification is inferred",
    }



def _registry_calculation(request):
    result = evaluate_dang_van_finite_sample_screen(request)
    return Calculation(status=result["status"], values=result)

def specifications() -> list[ModelSpec]:
    return [ModelSpec(
        "fatigue.dang_van_finite_sample_limit_screen",
        DangVanFiniteSampleScreen,
        _registry_calculation,
        {
            "candidate_system_results[].time_weighted_mean_resolved_shear_Pa": "Pa",
            "candidate_system_results[].maximum_dang_van_parameter_Pa": "Pa",
            "hydrostatic_peak_Pa": "Pa",
            "caller_limit_Pa": "Pa",
            "equivalent_screening_parameter_Pa": "Pa",
            "margin_to_caller_limit_Pa": "Pa",
        },
        (
            "Uses the published Dang Van high-cycle form combining centered shear stress history and instantaneous hydrostatic stress, restricted to caller-declared finite shear systems and time samples.",
            "Shear mean is a trapezoidal time average on the caller clock; material coefficient and limit, plane population and applicability are caller supplied with matching Evidence.",
            "The deterministic finite-set comparison is not a continuous plane search, fatigue-life estimate, probability, code acceptance or qualification.",
        ),
        ("caller_finite_shear_hydrostatic_dang_van_limit_screen",),
        qualification="user_model",
    )]
