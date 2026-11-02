"""Descriptive audit of caller-paired multiaxial fatigue calibration transfer."""

from __future__ import annotations

import math
from typing import Literal

from pydantic import Field, model_validator

from .contracts import Calculation, Contract, Evidence, Positive, canonical_digest
from .registry import ModelSpec

MODEL_ID = "fatigue.multiaxial_calibration_transfer_audit"
SOURCE_IDS = (
    "caller_paired_reference_target_multiaxial_life_observations",
    "independent_weighted_log_life_ratio_summary",
)


class PairedLifeCalibrationPoint(Contract):
    """Two life observations at one identical caller-defined fatigue parameter."""

    pair_id: str = Field(min_length=1, max_length=160)
    parameter_value: Positive
    reference_cycles: Positive
    target_cycles: Positive
    weight: Positive


class MultiaxialCalibrationTransferAudit(Contract):
    """Summarize paired life ratios without transferring a calibration curve."""

    schema_version: Literal["matintegrity.multiaxial_calibration_transfer_audit.v1"] = "matintegrity.multiaxial_calibration_transfer_audit.v1"
    assessment_id: str = Field(min_length=1, max_length=160)
    physical_scope_id: str = Field(min_length=1, max_length=160)
    location_id: str = Field(min_length=1, max_length=160)
    parameter_definition_id: str = Field(min_length=1, max_length=160)
    parameter_unit: str = Field(min_length=1, max_length=40)
    reference_material_condition_id: str = Field(min_length=1, max_length=160)
    target_material_condition_id: str = Field(min_length=1, max_length=160)
    reference_test_context_id: str = Field(min_length=1, max_length=160)
    target_test_context_id: str = Field(min_length=1, max_length=160)
    reference_record_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    target_record_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    reference_evidence: tuple[Evidence, ...] = Field(min_length=1)
    target_evidence: tuple[Evidence, ...] = Field(min_length=1)
    paired_points: tuple[PairedLifeCalibrationPoint, ...] = Field(min_length=2, max_length=10000)
    paired_parameter_and_protocol_reviewed: bool
    rights_and_condition_scope_reviewed: bool

    @model_validator(mode="after")
    def verify_pairs_and_provenance(self):
        if self.reference_material_condition_id == self.target_material_condition_id:
            raise ValueError("reference and target must identify distinct material conditions")
        for name, evidence_rows, expected_digest in (
            ("reference", self.reference_evidence, self.reference_record_sha256),
            ("target", self.target_evidence, self.target_record_sha256),
        ):
            if not any(row.sha256 == expected_digest and row.license_id for row in evidence_rows):
                raise ValueError(f"{name} Evidence must pin its record digest and declare a usage license")
        ids = [row.pair_id for row in self.paired_points]
        levels = [row.parameter_value for row in self.paired_points]
        weights = [row.weight for row in self.paired_points]
        if len(ids) != len(set(ids)):
            raise ValueError("paired point IDs must be unique")
        if any(right <= left for left, right in zip(levels, levels[1:])):
            raise ValueError("paired parameter levels must be unique and strictly increasing")
        if not math.isclose(math.fsum(weights), 1.0, rel_tol=1e-12, abs_tol=1e-12):
            raise ValueError("caller weights must sum to one; the audit will not normalize them")
        return self


def evaluate_multiaxial_calibration_transfer_audit(
    request: MultiaxialCalibrationTransferAudit,
) -> Calculation:
    """Compute weighted paired life ratios at exact shared parameter levels."""
    digest = canonical_digest(request.model_dump(mode="json"))
    base = {
        "assessment_id": request.assessment_id,
        "physical_scope_id": request.physical_scope_id,
        "location_id": request.location_id,
        "reference_material_condition_id": request.reference_material_condition_id,
        "target_material_condition_id": request.target_material_condition_id,
        "parameter_definition_id": request.parameter_definition_id,
        "parameter_unit": request.parameter_unit,
        "reference_test_context_id": request.reference_test_context_id,
        "target_test_context_id": request.target_test_context_id,
        "reference_record_sha256": request.reference_record_sha256,
        "target_record_sha256": request.target_record_sha256,
        "input_sha256": digest,
        "model_id": MODEL_ID,
        "basis": "caller_paired_exact_parameter_level_life_ratio_audit.v1",
    }
    if not request.paired_parameter_and_protocol_reviewed or not request.rights_and_condition_scope_reviewed:
        missing = []
        if not request.paired_parameter_and_protocol_reviewed:
            missing.append("paired_parameter_and_protocol_reviewed")
        if not request.rights_and_condition_scope_reviewed:
            missing.append("rights_and_condition_scope_reviewed")
        return Calculation(status="needs_data", values=base | {
            "reason": "reviewed_pairing_and_source_scope_required",
            "missing_reviews": missing,
        })

    rows = []
    log_ratios = []
    try:
        for point in request.paired_points:
            log_ratio = math.log(point.target_cycles) - math.log(point.reference_cycles)
            ratio = math.exp(log_ratio)
            if not math.isfinite(ratio) or ratio <= 0.0:
                raise ArithmeticError("paired life ratio is outside finite numeric support")
            rows.append({
                "pair_id": point.pair_id,
                "parameter_value": point.parameter_value,
                "reference_cycles": point.reference_cycles,
                "target_cycles": point.target_cycles,
                "target_to_reference_life_ratio": ratio,
                "log_target_to_reference_life_ratio": log_ratio,
                "weight": point.weight,
            })
            log_ratios.append(log_ratio)
        weighted_log_mean = math.fsum(
            point.weight * log_ratio for point, log_ratio in zip(request.paired_points, log_ratios, strict=True)
        )
        weighted_log_variance = math.fsum(
            point.weight * (log_ratio - weighted_log_mean) ** 2
            for point, log_ratio in zip(request.paired_points, log_ratios, strict=True)
        )
        geometric_mean_ratio = math.exp(weighted_log_mean)
        weighted_log_sd = math.sqrt(weighted_log_variance)
    except (ArithmeticError, OverflowError, ValueError):
        return Calculation(status="out_of_scope", values=base | {
            "reason": "paired_life_ratio_arithmetic_outside_finite_support",
            "completed_pair_count": len(rows),
        })
    if not all(math.isfinite(value) for value in (weighted_log_mean, weighted_log_variance,
                                                    geometric_mean_ratio, weighted_log_sd)) or geometric_mean_ratio <= 0.0:
        return Calculation(status="out_of_scope", values=base | {
            "reason": "weighted_transfer_summary_outside_finite_support",
            "completed_pair_count": len(rows),
        })
    return Calculation(values=base | {
        "status": "computed",
        "pair_count": len(rows),
        "paired_points": rows,
        "weighted_geometric_mean_target_to_reference_life_ratio": geometric_mean_ratio,
        "weighted_mean_log_life_ratio": weighted_log_mean,
        "weighted_population_sd_log_life_ratio": weighted_log_sd,
        "minimum_paired_life_ratio": min(row["target_to_reference_life_ratio"] for row in rows),
        "maximum_paired_life_ratio": max(row["target_to_reference_life_ratio"] for row in rows),
        "interpretation": "descriptive paired finite calibration-transfer diagnostic only",
        "limitations": [
            "Only exact caller-paired parameter levels are compared; no interpolation or extrapolation is performed.",
            "Weights are caller supplied and summarize only the declared finite points.",
            "The life ratio is not a transfer function, design-life estimate, probability, confidence interval or material qualification.",
            "Different test contexts remain explicitly labeled and require an engineering judgment before comparison.",
        ],
    }, notes=(
        "The calculation uses only caller-supplied reference and target lives at the same declared parameter values.",
        "No curve is fitted or transferred; results are descriptive and conditional on caller-reviewed pairing, rights and context.",
    ))


def specifications() -> list[ModelSpec]:
    return [ModelSpec(
        model_id=MODEL_ID,
        input_type=MultiaxialCalibrationTransferAudit,
        evaluator=evaluate_multiaxial_calibration_transfer_audit,
        units={
            "paired_points[].parameter_value": "caller_declared_parameter_unit",
            "paired_points[].reference_cycles": "cycles",
            "paired_points[].target_cycles": "cycles",
            "paired_points[].target_to_reference_life_ratio": "1",
            "weighted_geometric_mean_target_to_reference_life_ratio": "1",
            "weighted_mean_log_life_ratio": "1",
            "weighted_population_sd_log_life_ratio": "1",
        },
        assumptions=(
            "Only exact caller-paired parameter levels and caller-normalized positive weights are summarized.",
            "No calibration curve is fit, transferred, or extrapolated.",
            "The result is descriptive finite-data evidence and does not qualify a material or establish probability.",
        ),
        source_ids=SOURCE_IDS,
        qualification="data_import",
    )]
