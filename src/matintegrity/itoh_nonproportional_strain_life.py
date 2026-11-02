"""Bounded life mapping for the caller-calibrated Itoh non-proportional parameter."""

from __future__ import annotations

import math
from typing import Literal

from pydantic import Field, model_validator

from .contracts import Calculation, Contract, Evidence, Positive, canonical_digest
from .itoh_nonproportional_strain_parameter import (
    CALIBRATION_SOURCE_ID,
    ItohNonproportionalStrainRequest,
    evaluate_itoh_nonproportional_strain_parameter,
)
from .registry import ModelSpec

MODEL_ID = "fatigue.itoh_nonproportional_strain_life"
CURVE_SOURCE_ID = "caller_itoh_nonproportional_strain_life_curve"
METHOD_SOURCE_ID = "itoh_1995_nonproportional_low_cycle_fatigue_criterion"
STRAIN_DEFINITION_ID = "itoh_1995_adjusted_nonproportional_principal_strain_range.v1"


class ItohNonproportionalStrainLife(Contract):
    """Apply one digest-pinned, same-condition strain-range/life calibration curve."""

    analysis_id: str = Field(min_length=1)
    parameter_request: ItohNonproportionalStrainRequest
    life_curve_id: str = Field(min_length=1)
    curve_material_condition_id: str = Field(min_length=1)
    curve_strain_definition_id: Literal[STRAIN_DEFINITION_ID]
    curve_source_id: str = Field(min_length=1)
    curve_source_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    curve_evidence: Evidence
    curve_license_id: str = Field(min_length=1)
    nonproportional_strain_range_points: tuple[Positive, ...] = Field(min_length=2, max_length=10000)
    cycles_to_failure: tuple[Positive, ...] = Field(min_length=2, max_length=10000)
    curve_condition_descriptor_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    curve_material_match_and_test_basis_reviewed: bool
    curve_rights_and_engineering_use_reviewed: bool
    log_log_interpolation_and_constant_amplitude_scope_reviewed: bool

    @model_validator(mode="after")
    def validate_curve_and_condition(self):
        if self.curve_material_condition_id != self.parameter_request.material_condition_id:
            raise ValueError("life curve material condition must exactly match the Itoh parameter request")
        if self.curve_evidence.source_id != self.curve_source_id:
            raise ValueError("curve Evidence source ID must match the declared curve source")
        if self.curve_evidence.sha256 != self.curve_source_sha256:
            raise ValueError("curve Evidence digest must match the declared curve digest")
        if self.curve_evidence.license_id != self.curve_license_id:
            raise ValueError("curve Evidence license/reuse basis must match the declared curve license ID")
        if len(self.nonproportional_strain_range_points) != len(self.cycles_to_failure):
            raise ValueError("strain-range and cycles-to-failure vectors must have equal lengths")
        if any(right <= left for left, right in zip(
            self.nonproportional_strain_range_points[:-1],
            self.nonproportional_strain_range_points[1:],
            strict=True,
        )):
            raise ValueError("calibration strain ranges must be strictly increasing")
        if any(right >= left for left, right in zip(
            self.cycles_to_failure[:-1], self.cycles_to_failure[1:], strict=True
        )):
            raise ValueError("cycles to failure must strictly decrease with increasing strain range")
        return self


def evaluate_itoh_nonproportional_strain_life(
    request: ItohNonproportionalStrainLife,
) -> Calculation:
    """Map the computed Itoh strain range to bounded caller calibration data.

    Interpolation is linear in log strain range and log cycles. Exact knots
    are returned directly. No cycle decomposition, extrapolation or material
    transfer is performed.
    """
    curve_payload = {
        "life_curve_id": request.life_curve_id,
        "material_condition_id": request.curve_material_condition_id,
        "strain_definition_id": request.curve_strain_definition_id,
        "curve_condition_descriptor_sha256": request.curve_condition_descriptor_sha256,
        "source_id": request.curve_source_id,
        "source_sha256": request.curve_source_sha256,
        "curve_license_id": request.curve_license_id,
        "nonproportional_strain_range_points": request.nonproportional_strain_range_points,
        "cycles_to_failure": request.cycles_to_failure,
    }
    curve_digest = canonical_digest(curve_payload)
    input_digest = canonical_digest(request.model_dump(mode="json"))
    base = {
        "analysis_id": request.analysis_id,
        "material_condition_id": request.curve_material_condition_id,
        "life_curve_id": request.life_curve_id,
        "strain_definition_id": request.curve_strain_definition_id,
        "curve_source_id": request.curve_source_id,
        "curve_source_sha256": request.curve_source_sha256,
        "curve_license_id": request.curve_license_id,
        "curve_condition_descriptor_sha256": request.curve_condition_descriptor_sha256,
        "normalized_curve_sha256": curve_digest,
        "input_sha256": input_digest,
        "history_source_id": request.parameter_request.history_source_id,
        "strain_history_source_sha256": request.parameter_request.history_source_sha256,
        "principal_strain_range_source_id": request.parameter_request.principal_strain_range_evidence.source_id,
        "alpha_calibration_source_id": request.parameter_request.calibration_source_id,
        "hardening_calibration_sha256": request.parameter_request.calibration_sha256,
    }
    if not all((
        request.curve_material_match_and_test_basis_reviewed,
        request.curve_rights_and_engineering_use_reviewed,
        request.log_log_interpolation_and_constant_amplitude_scope_reviewed,
    )):
        return Calculation(status="needs_data", values=base | {
            "reason": "curve_material_rights_test_basis_and_interpolation_reviews_required",
            "itoh_strain_range": None,
            "cycles_to_failure": None,
        })

    parameter = evaluate_itoh_nonproportional_strain_parameter(request.parameter_request)
    if parameter.status != "computed":
        return Calculation(status=parameter.status, values=base | {
            "reason": "underlying_itoh_nonproportional_parameter_unavailable",
            "underlying_status": parameter.status,
            "underlying_input_sha256": parameter.values.get("input_sha256"),
            "underlying_reason": parameter.values.get("reason"),
            "itoh_strain_range": None,
            "cycles_to_failure": None,
        })
    strain_range = parameter.values["itoh_adjusted_nonproportional_strain_range"]
    base["parameter_input_sha256"] = parameter.values["input_sha256"]
    base["nonproportional_factor_sampled_trapezoid"] = parameter.values[
        "nonproportional_factor_sampled_trapezoid"
    ]
    if not math.isfinite(strain_range) or strain_range <= 0.0:
        return Calculation(status="out_of_scope", values=base | {
            "reason": "computed_Itoh_strain_range_not_positive_finite",
            "itoh_strain_range": None,
            "cycles_to_failure": None,
        })
    x = request.nonproportional_strain_range_points
    y = request.cycles_to_failure
    if strain_range < x[0] or strain_range > x[-1]:
        return Calculation(status="out_of_scope", values=base | {
            "reason": "Itoh_strain_range_outside_curve_support_no_extrapolation",
            "itoh_strain_range": strain_range,
            "supported_strain_range": [x[0], x[-1]],
            "cycles_to_failure": None,
        })

    exact = next((index for index, value in enumerate(x) if strain_range == value), None)
    if exact is not None:
        life = y[exact]
        interval_index = exact
        fraction = 0.0
        interpolation = "exact_curve_knot"
    else:
        interval_index = next(index for index in range(len(x) - 1)
                              if x[index] < strain_range < x[index + 1])
        fraction = (math.log(strain_range) - math.log(x[interval_index])) / (
            math.log(x[interval_index + 1]) - math.log(x[interval_index])
        )
        log_life = math.log(y[interval_index]) + fraction * (
            math.log(y[interval_index + 1]) - math.log(y[interval_index])
        )
        life = math.exp(log_life)
        interpolation = "linear_in_log_strain_range_and_log_cycles"
    if not math.isfinite(life) or life <= 0.0:
        return Calculation(status="out_of_scope", values=base | {
            "reason": "interpolated_life_not_positive_finite",
            "itoh_strain_range": strain_range,
            "cycles_to_failure": None,
        })
    return Calculation(values=base | {
        "status": "computed",
        "itoh_strain_range": strain_range,
        "cycles_to_failure": life,
        "curve_interval_index": interval_index,
        "interpolation_fraction": fraction,
        "interpolation_method": interpolation,
        "curve_strain_range_support": [x[0], x[-1]],
        "life_semantics": "caller-calibrated constant-amplitude cycles to failure for the exact Itoh strain definition and material condition",
        "limitations": [
            "The curve must represent the declared material condition, strain-range definition, test mode, environment and valid life interval.",
            "Interpolation is bounded; no extrapolation, scatter model, uncertainty or transfer to another material condition is estimated.",
            "A single constant-amplitude cycle parameter is mapped; variable-amplitude cycle counting and damage accumulation are not performed.",
            "A computed life is a caller-model output, not an acceptance, remaining-life qualification or failure probability.",
        ],
    })


def specifications() -> list[ModelSpec]:
    return [ModelSpec(
        model_id=MODEL_ID,
        input_type=ItohNonproportionalStrainLife,
        evaluator=evaluate_itoh_nonproportional_strain_life,
        units={"itoh_strain_range": "1", "cycles_to_failure": "cycle"},
        assumptions=(
            "A finite sampled Itoh non-proportional strain parameter is recomputed from the nested pinned history.",
            "Life calibration must match the exact material condition and strain-definition identifier and is interpolated only inside its supplied support.",
            "No extrapolation, cycle counting, variable-amplitude damage accumulation, uncertainty or material qualification is performed.",
        ),
        source_ids=(CURVE_SOURCE_ID, CALIBRATION_SOURCE_ID, METHOD_SOURCE_ID),
        qualification="user_model",
    )]
