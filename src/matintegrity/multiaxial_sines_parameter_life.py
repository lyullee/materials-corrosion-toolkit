"""Map a finite-sample Sines-style parameter to a caller-owned life curve."""

from __future__ import annotations

import math

from pydantic import Field, model_validator

from .contracts import Calculation, Contract, Evidence, Positive, canonical_digest
from .multiaxial_sines_mean_limit_screen import (
    MultiaxialSinesMeanLimitScreen,
    evaluate_multiaxial_sines_mean_limit_screen,
)
from .registry import ModelSpec


MODEL_ID = "fatigue.multiaxial_sines_parameter_life"
CURVE_SOURCE_ID = "caller_sines_parameter_constant_amplitude_life_curve"
INTERPOLATION_SOURCE_ID = "finite_sines_parameter_loglog_life_interpolation"


class SinesParameterLifePoint(Contract):
    """One supported point in a finite caller-provided Sines/life relation."""

    screening_parameter_Pa: Positive
    cycles_to_failure: Positive
    source_record_id: str = Field(min_length=1)


class MultiaxialSinesParameterLife(Contract):
    """Finite-sample Sines parameter and bounded, same-condition life mapping."""

    analysis_id: str = Field(min_length=1)
    screen: MultiaxialSinesMeanLimitScreen
    life_curve_id: str = Field(min_length=1)
    life_curve_source_id: str = CURVE_SOURCE_ID
    life_curve_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    life_curve_points: tuple[SinesParameterLifePoint, ...] = Field(min_length=2, max_length=10000)
    life_curve_evidence: Evidence
    life_curve_material_condition_id: str = Field(min_length=1)
    life_curve_interpolation_reviewed: bool
    life_curve_rights_and_condition_match_reviewed: bool

    @model_validator(mode="after")
    def validate_curve_lineage_and_order(self):
        if self.life_curve_source_id != CURVE_SOURCE_ID:
            raise ValueError("life-curve source ID must identify the caller-provided calibration basis")
        if self.life_curve_evidence.source_id != self.life_curve_source_id:
            raise ValueError("life-curve Evidence must match the declared source ID")
        if self.life_curve_evidence.sha256 != self.life_curve_sha256:
            raise ValueError("life-curve Evidence digest must match life_curve_sha256")
        if self.screen.calibration_material_condition_id != self.life_curve_material_condition_id:
            raise ValueError("Sines screen and life curve must declare the same exact material condition")
        actual_digest = canonical_digest([point.model_dump(mode="json") for point in self.life_curve_points])
        if actual_digest != self.life_curve_sha256:
            raise ValueError("life_curve_sha256 must match the ordered finite curve points")
        parameters = [point.screening_parameter_Pa for point in self.life_curve_points]
        cycles = [point.cycles_to_failure for point in self.life_curve_points]
        if not all(math.isfinite(value) and value > 0.0 for value in (*parameters, *cycles)):
            raise ValueError("life-curve parameters and cycle counts must be finite and positive")
        if any(b >= a for a, b in zip(parameters, parameters[1:])):
            raise ValueError("life-curve parameter values must strictly decrease with increasing cycle life")
        if any(b <= a for a, b in zip(cycles, cycles[1:])):
            raise ValueError("life-curve cycles_to_failure must strictly increase")
        if len({point.source_record_id for point in self.life_curve_points}) != len(self.life_curve_points):
            raise ValueError("life-curve source record identifiers must be unique")
        return self


def _interpolate_loglog(parameter: float, points: tuple[SinesParameterLifePoint, ...]) -> float | None:
    """Return bounded log-log life, or None outside the measured curve support."""
    values = [point.screening_parameter_Pa for point in points]
    if parameter < values[-1] or parameter > values[0]:
        return None
    if parameter == values[0]:
        return points[0].cycles_to_failure
    if parameter == values[-1]:
        return points[-1].cycles_to_failure
    for left, right in zip(points, points[1:]):
        if right.screening_parameter_Pa <= parameter <= left.screening_parameter_Pa:
            x0 = math.log(left.screening_parameter_Pa)
            x1 = math.log(right.screening_parameter_Pa)
            y0 = math.log(left.cycles_to_failure)
            y1 = math.log(right.cycles_to_failure)
            fraction = (math.log(parameter) - x0) / (x1 - x0)
            return math.exp(y0 + fraction * (y1 - y0))
    return None


def evaluate_multiaxial_sines_parameter_life(request: MultiaxialSinesParameterLife) -> Calculation:
    """Evaluate the finite-sample Sines screen, then map within a supplied life curve."""
    digest = canonical_digest(request.model_dump(mode="json"))
    base = {
        "analysis_id": request.analysis_id,
        "life_curve_id": request.life_curve_id,
        "life_curve_source_id": request.life_curve_source_id,
        "life_curve_sha256": request.life_curve_sha256,
        "life_curve_material_condition_id": request.life_curve_material_condition_id,
        "screen_input_sha256": canonical_digest(request.screen.model_dump(mode="json")),
        "input_sha256": digest,
    }
    if not (
        request.life_curve_interpolation_reviewed
        and request.life_curve_rights_and_condition_match_reviewed
    ):
        return Calculation(
            status="needs_data",
            values=base | {
                "reason": "caller_life_curve_interpolation_rights_and_condition_review_required",
                "screening_parameter_Pa": None,
                "cycles_to_failure": None,
                "life_curve_support_status": None,
            },
        )

    screen = evaluate_multiaxial_sines_mean_limit_screen(request.screen)
    if screen["status"] != "computed":
        return Calculation(
            status=screen["status"],
            values=base | {
                "reason": screen.get("reason", "sines_screen_not_computed"),
                "screening_parameter_Pa": screen.get("screening_parameter_Pa"),
                "cycles_to_failure": None,
                "life_curve_support_status": "not_evaluated",
                "sines_screen": screen,
            },
        )

    parameter = screen["screening_parameter_Pa"]
    if not math.isfinite(parameter) or parameter <= 0.0:
        return Calculation(
            status="out_of_scope",
            values=base | {
                "reason": "sines_parameter_must_be_positive_for_loglog_life_mapping",
                "screening_parameter_Pa": parameter,
                "cycles_to_failure": None,
                "life_curve_support_status": "not_evaluated",
                "sines_screen": screen,
            },
        )

    cycles = _interpolate_loglog(parameter, request.life_curve_points)
    if cycles is None or not math.isfinite(cycles):
        return Calculation(
            status="out_of_scope",
            values=base | {
                "reason": "sines_parameter_outside_caller_life_curve_support",
                "screening_parameter_Pa": parameter,
                "curve_parameter_support_Pa": [
                    request.life_curve_points[-1].screening_parameter_Pa,
                    request.life_curve_points[0].screening_parameter_Pa,
                ],
                "cycles_to_failure": None,
                "life_curve_support_status": "outside_support",
                "sines_screen": screen,
            },
        )
    return Calculation(
        status="computed",
        values=base | {
            "screening_parameter_Pa": parameter,
            "cycles_to_failure": cycles,
            "life_curve_support_status": "inside_support",
            "interpolation": "piecewise_loglog_between_adjacent_caller_points",
            "interpolation_bracket_source_record_ids": _bracket_record_ids(
                parameter, request.life_curve_points
            ),
            "sines_screen": screen,
            "meaning": "bounded life estimate conditional on caller-supplied same-condition curve and finite-sample Sines descriptor",
        },
        notes=(
            "The finite-sample half-diameter and time-average hydrostatic convention are inherited from the nested Sines screen.",
            "The life relation is caller supplied and is interpolated only within its observed parameter support.",
            "No cycle counting, variable-amplitude damage, sequence effect, probability, acceptance or material qualification is inferred.",
        ),
    )


def _bracket_record_ids(
    parameter: float, points: tuple[SinesParameterLifePoint, ...]
) -> list[str]:
    for left, right in zip(points, points[1:]):
        if right.screening_parameter_Pa <= parameter <= left.screening_parameter_Pa:
            return [left.source_record_id, right.source_record_id]
    if parameter == points[0].screening_parameter_Pa:
        return [points[0].source_record_id]
    if parameter == points[-1].screening_parameter_Pa:
        return [points[-1].source_record_id]
    return []


def specifications() -> list[ModelSpec]:
    return [ModelSpec(
        model_id=MODEL_ID,
        input_type=MultiaxialSinesParameterLife,
        evaluator=evaluate_multiaxial_sines_parameter_life,
        units={
            "screening_parameter_Pa": "Pa",
            "cycles_to_failure": "cycle",
            "curve_parameter_support_Pa[]": "Pa",
        },
        assumptions=(
            "Uses a caller Sines-style finite-sample parameter screen and a same-material-condition caller life curve.",
            "Life is mapped by piecewise log-log interpolation strictly inside the observed parameter support.",
            "The nested parameter convention uses finite sampled deviatoric half-diameter and piecewise-linear time-average hydrostatic stress.",
            "No cycle counting, variable-amplitude damage, sequence effect, probability, acceptance or qualification is inferred.",
        ),
        source_ids=(
            "caller_finite_sample_sines_mean_hydrostatic_limit_screen",
            CURVE_SOURCE_ID,
            INTERPOLATION_SOURCE_ID,
        ),
        qualification="user_model",
    )]
