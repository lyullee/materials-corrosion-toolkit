"""Fit and apply a caller-reviewed paired power-law transfer between fatigue-life curves."""

from __future__ import annotations

import math
from typing import Literal

from pydantic import Field, model_validator

from .contracts import AssessmentResult, Calculation, Contract, Evidence, Positive, canonical_digest
from .registry import ModelSpec

MODEL_ID = "fatigue.multiaxial_power_law_life_transfer"
AUDIT_MODEL_ID = "fatigue.multiaxial_calibration_transfer_audit"


class ReferenceMultiaxialLifeCurvePoint(Contract):
    parameter_value: Positive
    reference_cycles: Positive


class MultiaxialPowerLawLifeTransfer(Contract):
    schema_version: Literal["matintegrity.multiaxial_power_law_life_transfer.v1"] = (
        "matintegrity.multiaxial_power_law_life_transfer.v1"
    )
    assessment_id: str = Field(min_length=1)
    paired_calibration_audit: AssessmentResult
    paired_calibration_audit_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    reference_curve_id: str = Field(min_length=1)
    reference_curve_revision: str = Field(min_length=1)
    parameter_definition_id: str = Field(min_length=1)
    parameter_unit: str = Field(min_length=1)
    reference_material_condition_id: str = Field(min_length=1)
    reference_curve_points: tuple[ReferenceMultiaxialLifeCurvePoint, ...] = Field(min_length=2, max_length=10000)
    reference_curve_source_id: str = Field(min_length=1)
    reference_curve_record_id: str = Field(min_length=1)
    reference_curve_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    reference_curve_usage_license_id: str = Field(min_length=1)
    reference_curve_evidence: tuple[Evidence, ...] = Field(min_length=1)
    maximum_log_reference_curve_pair_residual: Positive
    paired_points_match_reference_curve_knots_reviewed: bool
    reference_and_target_parameter_definition_match_reviewed: bool
    weighted_log_linear_transfer_form_reviewed: bool
    material_condition_and_transfer_applicability_reviewed: bool
    usage_rights_and_computational_use_authorized: bool

    @model_validator(mode="after")
    def exact_pair_support_and_lineage(self):
        if self.paired_calibration_audit.model_id != AUDIT_MODEL_ID or self.paired_calibration_audit.status != "computed":
            raise ValueError("a computed paired multiaxial calibration-transfer audit is required")
        if canonical_digest(self.paired_calibration_audit.model_dump(mode="json")) != self.paired_calibration_audit_sha256:
            raise ValueError("paired calibration-transfer audit digest mismatch")
        audit = self.paired_calibration_audit.values
        if (audit.get("parameter_definition_id"), audit.get("parameter_unit"), audit.get("reference_material_condition_id")) != (
            self.parameter_definition_id, self.parameter_unit, self.reference_material_condition_id
        ):
            raise ValueError("reference curve parameter and material condition must match the paired audit exactly")
        if audit.get("target_material_condition_id") == self.reference_material_condition_id:
            raise ValueError("paired reference and target material conditions must be distinct")
        curve_record = {
            "curve_id": self.reference_curve_id,
            "curve_revision": self.reference_curve_revision,
            "parameter_definition_id": self.parameter_definition_id,
            "parameter_unit": self.parameter_unit,
            "material_condition_id": self.reference_material_condition_id,
            "points": [row.model_dump(mode="json") for row in self.reference_curve_points],
            "source_id": self.reference_curve_source_id,
            "record_id": self.reference_curve_record_id,
        }
        if canonical_digest(curve_record) != self.reference_curve_sha256:
            raise ValueError("reference curve digest must bind condition, parameter, points and provider identity")
        if not any(row.source_id == self.reference_curve_source_id and row.sha256 == self.reference_curve_sha256
                   and row.license_id == self.reference_curve_usage_license_id
                   for row in self.reference_curve_evidence):
            raise ValueError("reference curve Evidence must bind source, exact curve digest and usage license")
        points = self.reference_curve_points
        if any(right.parameter_value <= left.parameter_value
               for left, right in zip(points[:-1], points[1:], strict=True)):
            raise ValueError("reference curve parameter values must strictly increase")
        if any(right.reference_cycles >= left.reference_cycles
               for left, right in zip(points[:-1], points[1:], strict=True)):
            raise ValueError("reference curve life must strictly decrease with increasing fatigue parameter")
        paired = audit.get("paired_points")
        if not isinstance(paired, list) or len(paired) != len(points):
            raise ValueError("paired life audit must have one observation at every exact reference curve knot")
        for curve_point, pair in zip(points, paired, strict=True):
            if pair.get("parameter_value") != curve_point.parameter_value:
                raise ValueError("paired calibration parameter levels must exactly equal reference curve knots")
        if not audit.get("reference_record_sha256") or not audit.get("target_record_sha256"):
            raise ValueError("paired calibration audit must retain both reference and target source digests")
        return self


def evaluate_multiaxial_power_law_life_transfer(request: MultiaxialPowerLawLifeTransfer) -> Calculation:
    """Fit log(target life)=intercept+slope*log(reference life) at exact paired parameter knots."""
    audit_result = request.paired_calibration_audit
    audit = audit_result.values
    digest = canonical_digest(request.model_dump(mode="json"))
    base = {
        "assessment_id": request.assessment_id,
        "model_id": MODEL_ID,
        "input_sha256": digest,
        "paired_calibration_audit_sha256": request.paired_calibration_audit_sha256,
        "reference_curve_sha256": request.reference_curve_sha256,
        "physical_scope_id": audit.get("physical_scope_id"),
        "location_id": audit.get("location_id"),
        "reference_material_condition_id": request.reference_material_condition_id,
        "target_material_condition_id": audit.get("target_material_condition_id"),
        "parameter_definition_id": request.parameter_definition_id,
        "parameter_unit": request.parameter_unit,
    }
    reviews = {
        "paired_points_match_reference_curve_knots_reviewed": request.paired_points_match_reference_curve_knots_reviewed,
        "reference_and_target_parameter_definition_match_reviewed": request.reference_and_target_parameter_definition_match_reviewed,
        "weighted_log_linear_transfer_form_reviewed": request.weighted_log_linear_transfer_form_reviewed,
        "material_condition_and_transfer_applicability_reviewed": request.material_condition_and_transfer_applicability_reviewed,
        "usage_rights_and_computational_use_authorized": request.usage_rights_and_computational_use_authorized,
    }
    missing = [name for name, accepted in reviews.items() if not accepted]
    if missing:
        return Calculation(status="needs_data", values=base | {"missing_reviews": missing})

    paired = audit["paired_points"]
    calibration_parameters = [row["parameter_value"] for row in paired]
    if calibration_parameters[0] != request.reference_curve_points[0].parameter_value or calibration_parameters[-1] != request.reference_curve_points[-1].parameter_value:
        return Calculation(status="out_of_scope", values=base | {
            "reason": "paired_transfer_support_does_not_cover_reference_curve_knots",
        })
    weights = [float(row["weight"]) for row in paired]
    curve_pair_log_residuals = [
        math.log(float(pair["reference_cycles"])) - math.log(float(point.reference_cycles))
        for pair, point in zip(paired, request.reference_curve_points, strict=True)
    ]
    maximum_curve_pair_log_residual = max(abs(value) for value in curve_pair_log_residuals)
    if maximum_curve_pair_log_residual > request.maximum_log_reference_curve_pair_residual:
        return Calculation(status="out_of_scope", values=base | {
            "reason": "reference_curve_inconsistent_with_paired_reference_lives",
            "maximum_log_residual": maximum_curve_pair_log_residual,
            "caller_maximum_log_residual": request.maximum_log_reference_curve_pair_residual,
        })
    x = [math.log(float(row["reference_cycles"])) for row in paired]
    y = [math.log(float(row["target_cycles"])) for row in paired]
    try:
        mean_x = math.fsum(weight * value for weight, value in zip(weights, x, strict=True))
        mean_y = math.fsum(weight * value for weight, value in zip(weights, y, strict=True))
        variance_x = math.fsum(weight * (value - mean_x) ** 2 for weight, value in zip(weights, x, strict=True))
        covariance_xy = math.fsum(weight * (x_value - mean_x) * (y_value - mean_y)
                                   for weight, x_value, y_value in zip(weights, x, y, strict=True))
        if variance_x <= 1e-14 * max(1.0, math.fsum(weight * value * value for weight, value in zip(weights, x, strict=True))):
            return Calculation(status="out_of_scope", values=base | {
                "reason": "paired_reference_lives_do_not_identify_a_power_law_slope",
            })
        slope = covariance_xy / variance_x
        intercept = mean_y - slope * mean_x
        if not math.isfinite(slope) or not math.isfinite(intercept) or slope <= 0:
            return Calculation(status="out_of_scope", values=base | {
                "reason": "fitted_transfer_slope_is_nonpositive_or_nonfinite",
                "fitted_slope": slope,
            })
        residuals = [target - (intercept + slope * reference)
                     for reference, target in zip(x, y, strict=True)]
        weighted_log_rmse = math.sqrt(math.fsum(weight * residual * residual
                                                  for weight, residual in zip(weights, residuals, strict=True)))
        maximum_absolute_log_residual = max(abs(value) for value in residuals)
        curve = []
        for point in request.reference_curve_points:
            target_life = math.exp(intercept + slope * math.log(point.reference_cycles))
            if not math.isfinite(target_life) or target_life <= 0:
                raise OverflowError("transferred life is outside finite positive support")
            curve.append({
                "parameter_value": point.parameter_value,
                "reference_cycles": point.reference_cycles,
                "transferred_target_cycles": target_life,
                "parameter_unit": request.parameter_unit,
            })
    except (ArithmeticError, OverflowError, ValueError) as error:
        return Calculation(status="out_of_scope", values=base | {
            "reason": "power_law_transfer_arithmetic_outside_finite_support",
            "detail": str(error),
        })
    if not math.isfinite(weighted_log_rmse) or not math.isfinite(maximum_absolute_log_residual):
        return Calculation(status="out_of_scope", values=base | {"reason": "transfer_residual_summary_nonfinite"})
    if any(right["transferred_target_cycles"] >= left["transferred_target_cycles"]
           for left, right in zip(curve[:-1], curve[1:], strict=True)):
        return Calculation(status="out_of_scope", values=base | {"reason": "transferred_curve_not_monotone_decreasing"})
    try:
        pair_fit = [{
            "pair_id": row["pair_id"],
            "parameter_value": row["parameter_value"],
            "reference_cycles": row["reference_cycles"],
            "target_cycles": row["target_cycles"],
            "weight": row["weight"],
            "fitted_target_cycles": math.exp(intercept + slope * x[index]),
            "log_life_residual": residuals[index],
        } for index, row in enumerate(paired)]
    except (ArithmeticError, OverflowError, ValueError) as error:
        return Calculation(status="out_of_scope", values=base | {
            "reason": "paired_fit_prediction_outside_finite_support",
            "detail": str(error),
        })
    return Calculation(status="computed", values=base | {
        "reference_curve_id": request.reference_curve_id,
        "reference_curve_revision": request.reference_curve_revision,
        "target_test_context_id": audit.get("target_test_context_id"),
        "reference_test_context_id": audit.get("reference_test_context_id"),
        "transfer_model": "weighted_log_linear_paired_life_relation",
        "log_target_life_intercept": intercept,
        "target_life_power_exponent": slope,
        "weighted_log_fit_rmse": weighted_log_rmse,
        "maximum_absolute_log_fit_residual": maximum_absolute_log_residual,
        "maximum_log_reference_curve_pair_residual": request.maximum_log_reference_curve_pair_residual,
        "observed_maximum_log_reference_curve_pair_residual": maximum_curve_pair_log_residual,
        "paired_fit_diagnostics": pair_fit,
        "transferred_target_curve": curve,
        "limitations": [
            "The target curve is a two-parameter empirical log-life relation fitted only to the exact paired parameter knots in the nested audit result.",
            "The full reference curve must be covered by those paired parameter knots; no parameter-level or life extrapolation is performed.",
            "Caller weights and a constant power-law transfer form are assumptions. Residuals are descriptive and do not quantify parameter uncertainty or prediction intervals.",
            "The transfer applies only to the declared reference/target material conditions, test contexts and source evidence; it does not qualify other materials, geometries or loading populations.",
            "No fatigue criterion is selected, no damage is accumulated, and no code acceptance, probability, reliability or material qualification is inferred.",
        ],
    })


def specifications() -> list[ModelSpec]:
    return [ModelSpec(
        MODEL_ID,
        MultiaxialPowerLawLifeTransfer,
        evaluate_multiaxial_power_law_life_transfer,
        {
            "reference_curve_points[].parameter_value": "caller_declared_parameter_unit",
            "reference_curve_points[].reference_cycles": "cycles",
            "paired_calibration_audit.values.paired_points[].reference_cycles": "cycles",
            "paired_calibration_audit.values.paired_points[].target_cycles": "cycles",
            "transferred_target_curve[].parameter_value": "caller_declared_parameter_unit",
            "transferred_target_curve[].reference_cycles": "cycles",
            "transferred_target_curve[].transferred_target_cycles": "cycles",
            "target_life_power_exponent": "1",
            "weighted_log_fit_rmse": "1",
        },
        (
            "A positive weighted log-linear relation between paired target and reference lives is fit at the exact fatigue parameter knots in a digest-pinned calibration audit.",
            "The reference curve is mapped only over the exact parameter support represented by the paired observations and must match their reference lives within a caller tolerance.",
            "The empirical transfer is specific to the declared material conditions and test contexts; it does not establish a material law or qualification.",
        ),
        (
            "computed_digest_pinned_multiaxial_paired_life_audit",
            "caller_reference_condition_multiaxial_parameter_life_curve",
            "weighted_log_linear_paired_life_transfer",
        ),
        qualification="user_model",
    )]
