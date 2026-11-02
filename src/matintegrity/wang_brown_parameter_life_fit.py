"""Bounded empirical life fit for a finite sampled Wang–Brown-style parameter."""

from __future__ import annotations

import math
from typing import Literal

from pydantic import Field, model_validator

from .contracts import AssessmentResult, Calculation, Contract, Evidence, Positive, canonical_digest
from .registry import ModelSpec

MODEL_ID = "fatigue.wang_brown_parameter_life_fit"
PARAMETER_MODEL_ID = "fatigue.wang_brown_reviewed_excursion_parameter"
CALIBRATION_SOURCE_ID = "caller_wang_brown_parameter_constant_amplitude_life_data"
METHOD_SOURCE_ID = "wang_brown_1993_path_independent_multiaxial_strain_parameter"
PARAMETER_DEFINITION_ID = "wang_brown_finite_reviewed_shear_reversal_plus_normal_excursion.v1"
PARAMETER_DEFINITION = "engineering_shear_range_over_2_plus_S_times_normal_strain_excursion_on_reviewed_reversal_arc"


class WangBrownParameterLifeFit(Contract):
    """Fit and apply a same-condition power law to independent failure tests."""

    analysis_id: str = Field(min_length=1)
    parameter_result: AssessmentResult
    parameter_result_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    material_condition_id: str = Field(min_length=1)
    calibration_id: str = Field(min_length=1)
    calibration_source_id: Literal[CALIBRATION_SOURCE_ID]
    calibration_source_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    calibration_evidence: Evidence
    calibration_license_id: str = Field(min_length=1)
    calibration_condition_descriptor_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    parameter_definition_id: Literal[PARAMETER_DEFINITION_ID]
    calibration_parameter_values: tuple[Positive, ...] = Field(min_length=3, max_length=10000)
    observed_cycles_to_failure: tuple[Positive, ...] = Field(min_length=3, max_length=10000)
    calibration_material_test_scope_reviewed: bool
    calibration_rights_and_computational_use_reviewed: bool
    fit_and_prediction_scope_reviewed: bool

    @model_validator(mode="after")
    def validate_lineage_and_inputs(self):
        result = self.parameter_result
        if result.model_id != PARAMETER_MODEL_ID or result.status != "computed":
            raise ValueError("parameter result must be a computed Wang-Brown reviewed-excursion result")
        if canonical_digest(result.model_dump(mode="json")) != self.parameter_result_sha256:
            raise ValueError("parameter result digest does not match the supplied result")
        if result.values.get("parameter_definition") != PARAMETER_DEFINITION:
            raise ValueError("parameter result uses a different parameter definition")
        if result.values.get("material_condition_id") != self.material_condition_id:
            raise ValueError("calibration and parameter result material conditions must match exactly")
        if result.inputs.get("material_condition_id") != self.material_condition_id:
            raise ValueError("parameter input material condition must match the calibration condition")
        expected_input_digest = canonical_digest({
            "model_id": result.model_id,
            "model_version": result.model_version,
            "inputs": result.inputs,
            "context": result.context.model_dump(mode="json"),
        })
        if expected_input_digest != result.input_digest:
            raise ValueError("parameter result input/context digest is invalid")
        if self.calibration_evidence.source_id != self.calibration_source_id:
            raise ValueError("calibration Evidence source ID must match the declared source")
        if self.calibration_evidence.sha256 != self.calibration_source_sha256:
            raise ValueError("calibration Evidence digest must match the declared source digest")
        if self.calibration_evidence.license_id != self.calibration_license_id:
            raise ValueError("calibration Evidence reuse basis must match the declared license ID")
        if len(self.calibration_parameter_values) != len(self.observed_cycles_to_failure):
            raise ValueError("calibration parameter and failure-cycle arrays must have equal lengths")
        if len(set(self.calibration_parameter_values)) < 3:
            raise ValueError("at least three distinct parameter levels are required for the log-linear fit")
        return self


def evaluate_wang_brown_parameter_life_fit(request: WangBrownParameterLifeFit) -> Calculation:
    """Fit log(Nf)=a+b log(P) by OLS and predict only inside calibration support."""
    result = request.parameter_result
    fit_digest = canonical_digest({
        "calibration_id": request.calibration_id,
        "material_condition_id": request.material_condition_id,
        "parameter_definition_id": request.parameter_definition_id,
        "condition_descriptor_sha256": request.calibration_condition_descriptor_sha256,
        "source_id": request.calibration_source_id,
        "source_sha256": request.calibration_source_sha256,
        "license_id": request.calibration_license_id,
        "parameter_values": request.calibration_parameter_values,
        "observed_cycles_to_failure": request.observed_cycles_to_failure,
    })
    base = {
        "analysis_id": request.analysis_id,
        "material_condition_id": request.material_condition_id,
        "parameter_definition_id": request.parameter_definition_id,
        "parameter_result_sha256": request.parameter_result_sha256,
        "parameter_input_sha256": result.input_digest,
        "parameter_history_sha256": result.values.get("history_source_sha256"),
        "parameter_calibration_sha256": result.values.get("calibration_sha256"),
        "life_calibration_id": request.calibration_id,
        "life_calibration_source_id": request.calibration_source_id,
        "life_calibration_source_sha256": request.calibration_source_sha256,
        "life_calibration_license_id": request.calibration_license_id,
        "condition_descriptor_sha256": request.calibration_condition_descriptor_sha256,
        "normalized_life_calibration_sha256": fit_digest,
        "input_sha256": canonical_digest(request.model_dump(mode="json")),
    }
    if not all((request.calibration_material_test_scope_reviewed,
                request.calibration_rights_and_computational_use_reviewed,
                request.fit_and_prediction_scope_reviewed)):
        return Calculation(status="needs_data", values=base | {
            "reason": "material_test_scope_data_rights_and_fit_scope_reviews_required",
            "cycles_to_failure": None,
        })

    x_values = request.calibration_parameter_values
    y_values = request.observed_cycles_to_failure
    target = result.values.get("governing_parameter")
    if isinstance(target, bool) or not isinstance(target, (float, int)) or not math.isfinite(target) or target <= 0:
        return Calculation(status="out_of_scope", values=base | {
            "reason": "upstream_parameter_not_positive_and_finite",
            "parameter_value": target if isinstance(target, (int, float)) and math.isfinite(target) else None,
            "cycles_to_failure": None,
        })
    if target < min(x_values) or target > max(x_values):
        return Calculation(status="out_of_scope", values=base | {
            "reason": "parameter_outside_caller_calibration_support_no_extrapolation",
            "parameter_value": target,
            "calibration_parameter_support": [min(x_values), max(x_values)],
            "cycles_to_failure": None,
        })

    lx = [math.log(v) for v in x_values]
    ly = [math.log(v) for v in y_values]
    mean_x = math.fsum(lx) / len(lx)
    mean_y = math.fsum(ly) / len(ly)
    sxx = math.fsum((v - mean_x) ** 2 for v in lx)
    if not math.isfinite(sxx) or sxx <= 0:
        return Calculation(status="out_of_scope", values=base | {
            "reason": "calibration_parameter_variance_is_not_positive",
            "cycles_to_failure": None,
        })
    slope = math.fsum((x - mean_x) * (y - mean_y) for x, y in zip(lx, ly, strict=True)) / sxx
    intercept = mean_y - slope * mean_x
    if not math.isfinite(slope) or not math.isfinite(intercept) or slope >= 0:
        return Calculation(status="out_of_scope", values=base | {
            "reason": "fitted_life_must_decrease_with_increasing_parameter",
            "fitted_log_life_slope": slope if math.isfinite(slope) else None,
            "cycles_to_failure": None,
        })
    residuals = [y - (intercept + slope * x) for x, y in zip(lx, ly, strict=True)]
    ss_res = math.fsum(value * value for value in residuals)
    ss_tot = math.fsum((value - mean_y) ** 2 for value in ly)
    r_squared = 1.0 - ss_res / ss_tot if ss_tot > 0 else 1.0
    prediction = math.exp(intercept + slope * math.log(float(target)))
    if not math.isfinite(prediction) or prediction <= 0:
        return Calculation(status="out_of_scope", values=base | {
            "reason": "fitted_life_prediction_not_positive_and_finite",
            "cycles_to_failure": None,
        })
    return Calculation(values=base | {
        "status": "computed",
        "parameter_value": float(target),
        "parameter_units": "1",
        "cycles_to_failure": prediction,
        "fitted_log_life_intercept": intercept,
        "fitted_log_life_slope": slope,
        "log_life_r_squared_descriptive_only": r_squared,
        "log_life_residual_rms_descriptive_only": math.sqrt(ss_res / len(residuals)),
        "calibration_observation_count": len(lx),
        "calibration_parameter_support": [min(x_values), max(x_values)],
        "life_semantics": "caller constant-amplitude failure-cycle data fitted for this exact finite Wang-Brown-style parameter and material condition",
        "limitations": [
            "The power law is fitted only from caller-supplied constant-amplitude test observations; it is not asserted as a universal Wang-Brown life equation.",
            "The fitted value is returned only within the observed calibration parameter range; no extrapolation or transfer between materials, environments or strain definitions is performed.",
            "This API neither counts field cycles nor accumulates variable-amplitude damage, models sequence effects, estimates a failure probability, nor qualifies service life.",
            "Fit diagnostics describe the supplied observations and do not independently validate the test program or model form.",
        ],
    })


def specifications() -> list[ModelSpec]:
    return [ModelSpec(
        model_id=MODEL_ID,
        input_type=WangBrownParameterLifeFit,
        evaluator=evaluate_wang_brown_parameter_life_fit,
        units={"parameter_value": "1", "cycles_to_failure": "cycle"},
        assumptions=(
            "A log-log power law is estimated by ordinary least squares from at least three distinct caller test levels.",
            "Prediction requires exact material-condition and parameter-definition identity and lies within data support.",
            "No extrapolation, variable-amplitude damage rule, probability, acceptance or qualification is inferred.",
        ),
        source_ids=(CALIBRATION_SOURCE_ID, METHOD_SOURCE_ID),
        qualification="user_model",
    )]
