"""Bounded caller life mapping for an exact finite-sample Dang Van screen result."""

from __future__ import annotations

import math
from typing import Literal

from pydantic import Field, model_validator

from .contracts import AssessmentResult, Calculation, Contract, Evidence, Positive, canonical_digest
from .registry import ModelSpec

MODEL_ID = "fatigue.dang_van_finite_parameter_life"
CURVE_SOURCE_ID = "caller_dang_van_finite_parameter_life_curve"
METHOD_SOURCE_ID = "caller_finite_shear_hydrostatic_dang_van_limit_screen"
PARAMETER_DEFINITION_ID = "dang_van_finite_caller_system_time_sample_parameter_Pa.v1"
SCREEN_MODEL_ID = "fatigue.dang_van_finite_sample_limit_screen"


class DangVanFiniteParameterLifeCurve(Contract):
    """Map one pinned finite Dang Van parameter result to a same-condition life curve."""

    analysis_id: str = Field(min_length=1)
    finite_screen_result: AssessmentResult
    finite_screen_result_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    life_curve_id: str = Field(min_length=1)
    curve_material_condition_id: str = Field(min_length=1)
    curve_parameter_definition_id: Literal[PARAMETER_DEFINITION_ID]
    curve_source_id: str = Field(min_length=1)
    curve_source_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    curve_evidence: Evidence
    curve_license_id: str = Field(min_length=1)
    parameter_points_Pa: tuple[Positive, ...] = Field(min_length=2, max_length=10000)
    cycles_to_failure: tuple[Positive, ...] = Field(min_length=2, max_length=10000)
    curve_condition_descriptor_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    material_and_test_basis_reviewed: bool
    curve_rights_and_computational_use_reviewed: bool
    finite_parameter_definition_and_log_log_mapping_reviewed: bool

    @model_validator(mode="after")
    def validate_lineage_and_curve(self):
        if self.finite_screen_result.model_id != SCREEN_MODEL_ID:
            raise ValueError("the nested result must come from the registered finite Dang Van screen")
        if canonical_digest(self.finite_screen_result.model_dump(mode="json")) != self.finite_screen_result_sha256:
            raise ValueError("finite screen result digest does not match the supplied AssessmentResult")
        if self.finite_screen_result.status != "computed":
            raise ValueError("life mapping requires a computed finite screen result")
        if self.finite_screen_result.units.get("equivalent_screening_parameter_Pa") != "Pa":
            raise ValueError("finite Dang Van parameter result must declare pascal units")
        if self.finite_screen_result.values.get("method_variant") != "finite_caller_shear_systems_time_samples_Dang_Van_style":
            raise ValueError("finite screen result does not use the pinned parameter-definition variant")
        result_material = self.finite_screen_result.values.get("material_condition_id")
        input_material = self.finite_screen_result.inputs.get("calibration_material_condition_id")
        if result_material != self.curve_material_condition_id or input_material != self.curve_material_condition_id:
            raise ValueError("life curve material condition must exactly match the finite screen calibration")
        if self.curve_evidence.source_id != self.curve_source_id:
            raise ValueError("curve Evidence source ID must match the declared curve source")
        if self.curve_evidence.sha256 != self.curve_source_sha256:
            raise ValueError("curve Evidence digest must match the declared curve digest")
        if self.curve_evidence.license_id != self.curve_license_id:
            raise ValueError("curve Evidence reuse/license basis must match the declared curve license ID")
        if len(self.parameter_points_Pa) != len(self.cycles_to_failure):
            raise ValueError("parameter and cycles-to-failure vectors must have equal lengths")
        if any(right <= left for left, right in zip(self.parameter_points_Pa, self.parameter_points_Pa[1:])):
            raise ValueError("caller life curve parameter points must be strictly increasing")
        if any(right >= left for left, right in zip(self.cycles_to_failure, self.cycles_to_failure[1:])):
            raise ValueError("cycles to failure must strictly decrease as parameter increases")
        expected_digest = canonical_digest({
            "model_id": self.finite_screen_result.model_id,
            "model_version": self.finite_screen_result.model_version,
            "inputs": self.finite_screen_result.inputs,
            "context": self.finite_screen_result.context.model_dump(mode="json"),
        })
        if expected_digest != self.finite_screen_result.input_digest:
            raise ValueError("finite screen AssessmentResult input/context digest is invalid")
        return self


def evaluate_dang_van_finite_parameter_life(request: DangVanFiniteParameterLifeCurve) -> Calculation:
    """Interpolate cycles only on the exact same-condition caller curve."""
    curve_digest = canonical_digest({
        "life_curve_id": request.life_curve_id,
        "material_condition_id": request.curve_material_condition_id,
        "parameter_definition_id": request.curve_parameter_definition_id,
        "condition_descriptor_sha256": request.curve_condition_descriptor_sha256,
        "curve_source_id": request.curve_source_id,
        "curve_source_sha256": request.curve_source_sha256,
        "curve_license_id": request.curve_license_id,
        "parameter_points_Pa": request.parameter_points_Pa,
        "cycles_to_failure": request.cycles_to_failure,
    })
    input_digest = canonical_digest(request.model_dump(mode="json"))
    upstream = request.finite_screen_result
    base = {
        "analysis_id": request.analysis_id,
        "material_condition_id": request.curve_material_condition_id,
        "asset_id": upstream.context.asset_id,
        "location_id": upstream.context.location_id,
        "time_basis": upstream.context.time_basis,
        "screen_result_sha256": request.finite_screen_result_sha256,
        "screen_input_sha256": upstream.input_digest,
        "history_sha256": upstream.values.get("stress_history_sha256"),
        "dang_van_calibration_id": upstream.values.get("calibration_id"),
        "dang_van_calibration_sha256": upstream.values.get("calibration_sha256"),
        "parameter_definition_id": request.curve_parameter_definition_id,
        "life_curve_id": request.life_curve_id,
        "curve_source_id": request.curve_source_id,
        "curve_source_sha256": request.curve_source_sha256,
        "curve_license_id": request.curve_license_id,
        "curve_condition_descriptor_sha256": request.curve_condition_descriptor_sha256,
        "normalized_curve_sha256": curve_digest,
        "input_sha256": input_digest,
    }
    if not all((
        request.material_and_test_basis_reviewed,
        request.curve_rights_and_computational_use_reviewed,
        request.finite_parameter_definition_and_log_log_mapping_reviewed,
    )):
        return Calculation(status="needs_data", values=base | {
            "reason": "material_test_basis_curve_rights_and_parameter_definition_reviews_required",
            "dang_van_parameter_Pa": None,
            "cycles_to_failure": None,
        })

    parameter = upstream.values.get("equivalent_screening_parameter_Pa")
    if isinstance(parameter, bool) or not isinstance(parameter, (int, float)) or not math.isfinite(parameter):
        return Calculation(status="out_of_scope", values=base | {
            "reason": "finite_screen_result_does_not_contain_a_positive_finite_parameter",
            "dang_van_parameter_Pa": None,
            "cycles_to_failure": None,
        })
    parameter = float(parameter)
    if parameter <= 0.0:
        return Calculation(status="out_of_scope", values=base | {
            "reason": "nonpositive_parameter_is_outside_positive_log_curve_support",
            "dang_van_parameter_Pa": parameter,
            "cycles_to_failure": None,
        })
    x = request.parameter_points_Pa
    y = request.cycles_to_failure
    if parameter < x[0] or parameter > x[-1]:
        return Calculation(status="out_of_scope", values=base | {
            "reason": "Dang_Van_parameter_outside_caller_curve_support_no_extrapolation",
            "dang_van_parameter_Pa": parameter,
            "supported_parameter_interval_Pa": [x[0], x[-1]],
            "cycles_to_failure": None,
        })
    exact = next((index for index, value in enumerate(x) if parameter == value), None)
    if exact is not None:
        life = y[exact]
        interval_index = exact
        fraction = 0.0
        interpolation = "exact_curve_knot"
    else:
        interval_index = next(index for index in range(len(x) - 1) if x[index] < parameter < x[index + 1])
        fraction = (math.log(parameter) - math.log(x[interval_index])) / (
            math.log(x[interval_index + 1]) - math.log(x[interval_index])
        )
        log_life = math.log(y[interval_index]) + fraction * (
            math.log(y[interval_index + 1]) - math.log(y[interval_index])
        )
        life = math.exp(log_life)
        interpolation = "linear_in_log_Dang_Van_parameter_and_log_cycles"
    if not math.isfinite(life) or life <= 0.0:
        return Calculation(status="out_of_scope", values=base | {
            "reason": "interpolated_cycles_to_failure_not_positive_finite",
            "dang_van_parameter_Pa": parameter,
            "cycles_to_failure": None,
        })
    return Calculation(values=base | {
        "status": "computed",
        "dang_van_parameter_Pa": parameter,
        "cycles_to_failure": life,
        "curve_interval_index": interval_index,
        "interpolation_fraction": fraction,
        "interpolation_method": interpolation,
        "parameter_curve_support_Pa": [x[0], x[-1]],
        "life_semantics": "caller_calibrated constant-amplitude cycles for the exact finite-sample Dang Van parameter variant",
        "limitations": [
            "This is a caller empirical life mapping, not an intrinsic universal life equation of the Dang Van limit criterion.",
            "The screen and life curve must share material condition, parameter definition, test basis, environment and physical use scope.",
            "No extrapolation, scatter distribution, fatigue damage accumulation, cycle counting or sequence correction is inferred.",
            "The life is not a failure probability, code acceptance, qualified service life or material qualification.",
        ],
    })


def specifications() -> list[ModelSpec]:
    return [ModelSpec(
        model_id=MODEL_ID,
        input_type=DangVanFiniteParameterLifeCurve,
        evaluator=evaluate_dang_van_finite_parameter_life,
        units={"dang_van_parameter_Pa": "Pa", "cycles_to_failure": "cycle"},
        assumptions=(
            "Consumes only a digest-verified computed result from the named finite-sample Dang Van screen.",
            "Life is interpolated within a strictly ordered caller curve for the exact material condition and parameter definition.",
            "No extrapolation, cycle counting, damage accumulation, probability, acceptance or qualification is inferred.",
        ),
        source_ids=(CURVE_SOURCE_ID, METHOD_SOURCE_ID),
        qualification="user_model",
    )]
