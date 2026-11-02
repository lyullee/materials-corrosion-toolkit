"""Caller-calibrated finite-sample invariant fatigue-limit screening."""

from __future__ import annotations

import math

from pydantic import Field, model_validator

from .contracts import Calculation, Contract, Evidence, Nonnegative, Positive, canonical_digest
from .registry import ModelSpec
from .multiaxial_stress_invariant_history import (
    SampledStressInvariantHistory,
    evaluate_sampled_stress_invariant_history,
)


class MultiaxialInvariantLimitScreen(Contract):
    """Linear invariant limit screen over one reviewed finite stress cycle.

    The finite half-diameter convention is explicitly tied to the sampled
    deviatoric path. The scalar coefficients and comparison limit are supplied
    and calibrated by the caller for the exact material condition.
    """

    analysis_id: str = Field(min_length=1)
    stress_history: SampledStressInvariantHistory
    stress_history_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    calibration_id: str = Field(min_length=1)
    calibration_source_id: str = Field(min_length=1)
    calibration_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    calibration_evidence: Evidence
    calibration_material_condition_id: str = Field(min_length=1)
    deviatoric_coefficient: Positive
    hydrostatic_coefficient: Nonnegative
    caller_limit_Pa: Positive
    coefficients_and_limit_reviewed: bool
    calibration_material_scope_reviewed: bool
    use_for_finite_sample_screen_reviewed: bool

    @model_validator(mode="after")
    def digest_and_calibration_lineage(self):
        actual_history_digest = canonical_digest(self.stress_history.model_dump(mode="json"))
        if actual_history_digest != self.stress_history_sha256:
            raise ValueError("stress-history digest differs from the nested caller contract")
        if self.calibration_material_condition_id != self.stress_history.material_condition_id:
            raise ValueError("calibration material condition must exactly match the stress history")
        if (
            self.calibration_evidence.source_id != self.calibration_source_id
            or self.calibration_evidence.sha256 != self.calibration_sha256
        ):
            raise ValueError("calibration Evidence must match the declared source and calibration digest")
        return self


def evaluate_multiaxial_invariant_limit_screen(request: MultiaxialInvariantLimitScreen) -> dict:
    """Compare caller-calibrated linear invariant parameter with a caller limit."""
    input_digest = canonical_digest(request.model_dump(mode="json"))
    base = {
        "analysis_id": request.analysis_id,
        "material_condition_id": request.calibration_material_condition_id,
        "stress_history_sha256": request.stress_history_sha256,
        "calibration_id": request.calibration_id,
        "calibration_source_id": request.calibration_source_id,
        "calibration_sha256": request.calibration_sha256,
        "input_sha256": input_digest,
        "finite_sample_convention": "half maximum pairwise sqrt(J2) distance on supplied deviatoric stress samples",
    }
    if not all((
        request.coefficients_and_limit_reviewed,
        request.calibration_material_scope_reviewed,
        request.use_for_finite_sample_screen_reviewed,
    )):
        return base | {
            "status": "needs_data",
            "reason": "caller_calibration_limit_material_scope_and_finite_sample_use_review_required",
            "screening_parameter_Pa": None,
            "margin_to_caller_limit_Pa": None,
            "screening_outcome": None,
        }

    history = evaluate_sampled_stress_invariant_history(request.stress_history)
    if history["status"] != "computed":
        return base | {
            "status": history["status"],
            "reason": history.get("reason", "stress_history_descriptor_unavailable"),
            "screening_parameter_Pa": None,
            "margin_to_caller_limit_Pa": None,
            "screening_outcome": None,
        }

    values = history["values"]
    parameter = (
        request.deviatoric_coefficient * values["sampled_deviatoric_J2_half_diameter_Pa"]
        + request.hydrostatic_coefficient * values["maximum_sampled_hydrostatic_stress_Pa"]
    )
    margin = request.caller_limit_Pa - parameter
    if not math.isfinite(parameter) or not math.isfinite(margin):
        return base | {
            "status": "out_of_scope",
            "reason": "finite_inputs_produce_nonfinite_screening_arithmetic",
            "screening_parameter_Pa": None,
            "margin_to_caller_limit_Pa": None,
            "screening_outcome": None,
        }
    return base | {
        "status": "computed",
        "screening_parameter_Pa": parameter,
        "margin_to_caller_limit_Pa": margin,
        "screening_outcome": "caller_limit_not_exceeded" if parameter <= request.caller_limit_Pa else "caller_limit_exceeded",
        "hydrostatic_peak_witness_sample_id": values["maximum_hydrostatic_sample_id"],
        "deviatoric_distance_witness_sample_ids": values["diameter_witness_sample_ids"],
        "meaning": "deterministic finite-sample comparison to a caller-supplied calibrated limit; not fatigue life, probability, acceptance or qualification",
    }



def _registry_calculation(request):
    result = evaluate_multiaxial_invariant_limit_screen(request)
    return Calculation(status=result["status"], values=result)

def specifications() -> list[ModelSpec]:
    return [ModelSpec(
        "fatigue.multiaxial_invariant_limit_screen",
        MultiaxialInvariantLimitScreen,
        _registry_calculation,
        {
            "screening_parameter_Pa": "Pa",
            "margin_to_caller_limit_Pa": "Pa",
        },
        (
            "Requires caller-reviewed coefficients, reference limit, calibration lineage and exact material-condition match; it does not estimate calibration parameters.",
            "Uses only the nested finite-sample maximum hydrostatic stress and half maximum pairwise deviatoric sqrt(J2) distance; no interpolation or unsampled-path correction is applied.",
            "The outcome is a deterministic comparison to a caller limit, not fatigue life, probability, code acceptance or material qualification.",
        ),
        ("caller_finite_sample_multiaxial_invariant_limit_screen",),
        qualification="user_model",
    )]
