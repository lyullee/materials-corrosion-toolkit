"""Couple caller thermal-expansion records to gasket/bolt assembly equilibrium."""

from __future__ import annotations

import math
from typing import Literal

from pydantic import Field, model_validator

from ..contracts import Calculation, Contract, Evidence, Positive, canonical_digest
from ..registry import ModelSpec
from .gasket_temperature_compression_joint_history import (
    GasketTemperatureCompressionJointHistory,
    TemperatureJointLoadStep,
    evaluate_gasket_temperature_compression_joint_history,
)

MODEL_ID = "integration.gasket_thermoelastic_expansion_joint_history"


class ComponentThermalExpansionRecord(Contract):
    component_id: str = Field(min_length=1)
    component_role: Literal["bolt", "gasket_sector"]
    effective_free_dimension_m: Positive
    reference_temperature_K: Positive
    temperature_knots_K: tuple[Positive, ...] = Field(min_length=2, max_length=1000)
    linear_expansion_coefficient_per_K: tuple[float, ...] = Field(min_length=2, max_length=1000)
    provider_id: str = Field(min_length=1)
    provider_revision: str = Field(min_length=1)
    record_id: str = Field(min_length=1)
    record_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    usage_license_id: str = Field(min_length=1)
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def coherent_cte_record(self):
        if len(self.temperature_knots_K) != len(self.linear_expansion_coefficient_per_K):
            raise ValueError("CTE values must align with temperature knots")
        if any(right <= left for left, right in zip(self.temperature_knots_K, self.temperature_knots_K[1:])):
            raise ValueError("CTE temperature knots must increase strictly")
        if not self.temperature_knots_K[0] <= self.reference_temperature_K <= self.temperature_knots_K[-1]:
            raise ValueError("reference temperature must lie inside the CTE table support")
        if not all(math.isfinite(value) for value in self.linear_expansion_coefficient_per_K):
            raise ValueError("CTE coefficients must be finite")
        record = {
            "component_id": self.component_id,
            "component_role": self.component_role,
            "effective_free_dimension_m": self.effective_free_dimension_m,
            "reference_temperature_K": self.reference_temperature_K,
            "temperature_knots_K": list(self.temperature_knots_K),
            "linear_expansion_coefficient_per_K": list(self.linear_expansion_coefficient_per_K),
            "provider_id": self.provider_id,
            "provider_revision": self.provider_revision,
            "record_id": self.record_id,
        }
        if canonical_digest(record) != self.record_sha256:
            raise ValueError("CTE record digest does not bind component, support and coefficients")
        if not any(row.source_id == self.provider_id and row.sha256 == self.record_sha256
                   and row.license_id == self.usage_license_id for row in self.evidence):
            raise ValueError("CTE Evidence must pin coefficients and computational-use license")
        return self


class GasketThermoelasticExpansionJointHistory(Contract):
    schema_version: Literal["matintegrity.gasket_thermoelastic_expansion_joint_history.v1"] = (
        "matintegrity.gasket_thermoelastic_expansion_joint_history.v1"
    )
    assessment_id: str = Field(min_length=1)
    joint_history: GasketTemperatureCompressionJointHistory
    component_expansion_records: tuple[ComponentThermalExpansionRecord, ...] = Field(min_length=3, max_length=512)
    cte_condition_and_dimension_applicability_reviewed: bool
    piecewise_linear_cte_integration_reviewed: bool
    common_reference_temperature_and_clock_reviewed: bool
    computational_use_authorized: bool

    @model_validator(mode="after")
    def exact_component_coverage(self):
        joint = self.joint_history
        expected = {
            **{row.bolt_id: "bolt" for row in joint.bolts},
            **{row.sector_id: "gasket_sector" for row in joint.sectors},
        }
        ids = [row.component_id for row in self.component_expansion_records]
        if len(ids) != len(set(ids)) or set(ids) != set(expected):
            raise ValueError("exactly one CTE record is required for every bolt and gasket sector")
        by_id = {row.component_id: row for row in self.component_expansion_records}
        for component_id, role in expected.items():
            record = by_id[component_id]
            if record.component_role != role:
                raise ValueError("CTE component role must match its bolt or gasket-sector identity")
            if record.reference_temperature_K != joint.steps[0].temperature_K:
                raise ValueError("every CTE reference temperature must match the initial assembly temperature")
            if any(not record.temperature_knots_K[0] <= step.temperature_K <= record.temperature_knots_K[-1]
                   for step in joint.steps):
                raise ValueError("all load-step temperatures must lie inside every component CTE table")
            if role == "gasket_sector" and not math.isclose(
                record.effective_free_dimension_m,
                joint.initial_gasket_thickness_m,
                rel_tol=1.0e-9,
                abs_tol=1.0e-12,
            ):
                raise ValueError("gasket-sector CTE dimension must match the modeled initial gasket thickness")
        if any(any(step.bolt_free_length_change_m) or any(step.gasket_free_thickness_change_m)
               for step in joint.steps):
            raise ValueError("base joint thermal shifts must be zero; this API supplies them from CTE records")
        return self


def _interpolate_cte(record: ComponentThermalExpansionRecord, temperature_K: float) -> float:
    knots = record.temperature_knots_K
    values = record.linear_expansion_coefficient_per_K
    if not knots[0] <= temperature_K <= knots[-1]:
        raise ValueError("temperature is outside caller CTE support")
    if temperature_K == knots[-1]:
        return values[-1]
    low, high = 0, len(knots) - 1
    while low + 1 < high:
        middle = (low + high) // 2
        if knots[middle] <= temperature_K:
            low = middle
        else:
            high = middle
    fraction = (temperature_K - knots[low]) / (knots[low + 1] - knots[low])
    value = values[low] + fraction * (values[low + 1] - values[low])
    if not math.isfinite(value):
        raise OverflowError("interpolated CTE is outside finite numeric support")
    return value


def _integrated_log_strain(record: ComponentThermalExpansionRecord, target_temperature_K: float) -> float:
    reference = record.reference_temperature_K
    if target_temperature_K == reference:
        return 0.0
    sign = 1.0 if target_temperature_K > reference else -1.0
    left, right = (reference, target_temperature_K) if sign > 0 else (target_temperature_K, reference)
    interior = [value for value in record.temperature_knots_K if left < value < right]
    breakpoints = [left, *interior, right]
    terms = []
    for start, end in zip(breakpoints, breakpoints[1:]):
        alpha_start = _interpolate_cte(record, start)
        alpha_end = _interpolate_cte(record, end)
        terms.append(0.5 * (alpha_start + alpha_end) * (end - start))
    result = sign * math.fsum(terms)
    if not math.isfinite(result):
        raise OverflowError("integrated free thermal strain is outside finite numeric support")
    return result


def evaluate_gasket_thermoelastic_expansion_joint_history(
    request: GasketThermoelasticExpansionJointHistory,
) -> Calculation:
    """Calculate bolt/gasket free thermal changes, then solve the coupled assembly history."""
    joint = request.joint_history
    digest = canonical_digest(request.model_dump(mode="json"))
    base = {
        "assessment_id": request.assessment_id,
        "asset_id": joint.asset_id,
        "location_id": joint.location_id,
        "joint_id": joint.joint_id,
        "physical_scope_id": joint.physical_scope_id,
        "cte_record_sha256_by_component": {
            row.component_id: row.record_sha256 for row in request.component_expansion_records
        },
        "input_sha256": digest,
        "model_id": MODEL_ID,
    }
    reviews = {
        "cte_condition_and_dimension_applicability_reviewed": request.cte_condition_and_dimension_applicability_reviewed,
        "piecewise_linear_cte_integration_reviewed": request.piecewise_linear_cte_integration_reviewed,
        "common_reference_temperature_and_clock_reviewed": request.common_reference_temperature_and_clock_reviewed,
        "computational_use_authorized": request.computational_use_authorized,
    }
    missing = [name for name, value in reviews.items() if not value]
    if missing:
        return Calculation(status="needs_data", values=base | {"missing_reviews": missing})
    records = {row.component_id: row for row in request.component_expansion_records}
    computed_steps = []
    thermal_rows = []
    try:
        for step in joint.steps:
            bolt_changes = []
            gasket_changes = []
            detail = []
            for bolt in joint.bolts:
                record = records[bolt.bolt_id]
                integrated_log_strain = _integrated_log_strain(record, step.temperature_K)
                free_strain = math.expm1(integrated_log_strain)
                change = record.effective_free_dimension_m * free_strain
                if not math.isfinite(change):
                    raise OverflowError("bolt free thermal-length change is nonfinite")
                bolt_changes.append(change)
                detail.append({"component_id": bolt.bolt_id, "role": "bolt", "free_thermal_strain": free_strain,
                               "integrated_log_strain": integrated_log_strain, "free_length_change_m": change})
            for sector in joint.sectors:
                record = records[sector.sector_id]
                integrated_log_strain = _integrated_log_strain(record, step.temperature_K)
                free_strain = math.expm1(integrated_log_strain)
                change = record.effective_free_dimension_m * free_strain
                if not math.isfinite(change):
                    raise OverflowError("gasket free thermal-thickness change is nonfinite")
                gasket_changes.append(change)
                detail.append({"component_id": sector.sector_id, "role": "gasket_sector", "free_thermal_strain": free_strain,
                               "integrated_log_strain": integrated_log_strain, "free_thickness_change_m": change})
            computed_steps.append(TemperatureJointLoadStep(
                step_id=step.step_id,
                time_s=step.time_s,
                temperature_K=step.temperature_K,
                external_separating_force_N=step.external_separating_force_N,
                bolt_free_length_change_m=tuple(bolt_changes),
                gasket_free_thickness_change_m=tuple(gasket_changes),
            ))
            thermal_rows.append({"step_id": step.step_id, "time_s": step.time_s, "temperature_K": step.temperature_K,
                                 "component_expansion": detail})
    except (ArithmeticError, OverflowError, ValueError) as error:
        return Calculation(status="out_of_scope", values=base | {
            "reason": "thermal_expansion_integration_outside_caller_support",
            "detail": str(error),
            "completed_step_count": len(thermal_rows),
        })
    coupled_request = joint.model_copy(update={"steps": tuple(computed_steps)})
    joint_result = evaluate_gasket_temperature_compression_joint_history(coupled_request)
    return Calculation(status=joint_result.status, values={
        **joint_result.values,
        **base,
        "joint_history_model_id": joint_result.values.get("model_id"),
        "history": joint_result.values.get("history", []),
        "thermal_expansion_history": thermal_rows,
        "cte_integration_method": "piecewise_linear_alpha_exact_integral_to_log_strain_then_expm1_length_change",
        "limitations": [
            "Bolt and gasket free expansion are integrated from caller piecewise-linear CTE tables relative to the initial assembly temperature.",
            "The coupled joint remains a common-opening quasi-static model and does not include thermal gradients, flange bending, stress relaxation, hysteresis or contact FE response.",
            "CTE table support, component effective dimensions and applicability to the assembled material condition require caller evidence and review.",
        ],
    })


def specifications() -> list[ModelSpec]:
    return [ModelSpec(
        MODEL_ID,
        GasketThermoelasticExpansionJointHistory,
        evaluate_gasket_thermoelastic_expansion_joint_history,
        {
            "thermal_expansion_history[].time_s": "s",
            "thermal_expansion_history[].temperature_K": "K",
            "thermal_expansion_history[].component_expansion[].free_thermal_strain": "1",
            "thermal_expansion_history[].component_expansion[].integrated_log_strain": "1",
            "thermal_expansion_history[].component_expansion[].free_length_change_m": "m",
            "thermal_expansion_history[].component_expansion[].free_thickness_change_m": "m",
            "history[].opening_m": "m",
            "history[].bolt_tensile_force_sum_N": "N",
            "history[].gasket_compressive_force_sum_N": "N",
            "history[].force_balance_residual_N": "N",
            "history[].bolts[].tensile_force_N": "N",
            "history[].gasket_sectors[].mean_contact_pressure_Pa": "Pa",
        },
        (
            "Each component's free thermal change is its reference dimension times expm1 of the exact piecewise-linear integral of instantaneous alpha(T), interpreted as logarithmic strain.",
            "The calculated thermal shifts are passed into the existing temperature-interpolated quasi-static joint equilibrium at matching exact time/temperature knots.",
            "No thermal gradient, residual thermal stress, temperature extrapolation, hysteresis or material qualification is inferred.",
        ),
        (
            "caller_bolt_and_gasket_sector_cte_temperature_tables",
            "caller_component_effective_free_dimensions_and_reference_temperature",
            "piecewise_linear_cte_thermal_strain_integral",
            "temperature_dependent_bolt_gasket_joint_equilibrium",
        ),
        qualification="user_model",
    )]
