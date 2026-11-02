"""Area-weighted pressure distribution statistics for computed gasket contact fields."""

from __future__ import annotations

import math
from typing import Literal

from pydantic import Field, model_validator

from ..contracts import AssessmentResult, Calculation, Contract, Evidence, Nonnegative, canonical_digest
from ..registry import ModelSpec


MODEL_ID = "fabrication.gasket_contact_distribution_statistics"
SOURCE_ID = "caller_gasket_contact_distribution_statistics"
STATIC_MODELS = {"fabrication.flange_contact_field", "fabrication.flange_nonlinear_contact_field"}
HISTORY_MODELS = {
    "fabrication.flange_viscoelastic_contact_history",
    "fabrication.flange_nonlinear_viscoelastic_contact_history",
}


class GasketPressureThreshold(Contract):
    criterion_id: str = Field(min_length=1)
    minimum_pressure_Pa: Nonnegative
    provider_id: str = Field(min_length=1)
    provider_revision: str = Field(min_length=1)
    record_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    usage_license_id: str = Field(min_length=1)
    evidence: tuple[Evidence, ...] = Field(min_length=1)


class GasketContactDistributionStatistics(Contract):
    """Compute area-weighted pressure summaries without defining seal qualification."""

    schema_version: Literal["matintegrity.gasket_contact_distribution_statistics.v1"] = (
        "matintegrity.gasket_contact_distribution_statistics.v1"
    )
    assessment_id: str = Field(min_length=1)
    physical_scope_id: str = Field(min_length=1)
    contact_result: AssessmentResult
    contact_result_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    selected_time_s: Nonnegative | None = None
    quantile_levels: tuple[float, ...] = (0.05, 0.5, 0.95)
    thresholds: tuple[GasketPressureThreshold, ...] = Field(default=(), max_length=1000)
    physical_scope_and_time_reviewed: bool
    contact_area_basis_and_units_reviewed: bool
    distribution_summary_interpretation_reviewed: bool
    resolution_and_threshold_applicability_reviewed: bool
    evidence_rights_and_computational_use_reviewed: bool

    @model_validator(mode="after")
    def consistent_result_and_inputs(self):
        result = self.contact_result
        if result.status != "computed" or result.model_id not in STATIC_MODELS | HISTORY_MODELS:
            raise ValueError("a computed supported flange contact field/history is required")
        if canonical_digest(result.model_dump(mode="json")) != self.contact_result_sha256:
            raise ValueError("contact result digest does not match")
        if result.inputs.get("physical_scope_id") != self.physical_scope_id:
            raise ValueError("contact result physical scope does not match")
        if result.model_id in STATIC_MODELS and self.selected_time_s is not None:
            raise ValueError("static contact fields do not accept a selected time")
        if result.model_id in HISTORY_MODELS and self.selected_time_s is None:
            raise ValueError("contact histories require an exact selected output time")
        if any(not math.isfinite(value) or not 0.0 <= value <= 1.0 for value in self.quantile_levels):
            raise ValueError("quantile levels must be finite and lie in [0, 1]")
        if len(set(self.quantile_levels)) != len(self.quantile_levels):
            raise ValueError("quantile levels must be unique")
        if len({row.criterion_id for row in self.thresholds}) != len(self.thresholds):
            raise ValueError("threshold criterion IDs must be unique")
        for threshold in self.thresholds:
            basis = {
                "provider_id": threshold.provider_id,
                "provider_revision": threshold.provider_revision,
                "criterion_id": threshold.criterion_id,
                "physical_scope_id": self.physical_scope_id,
                "contact_result_sha256": self.contact_result_sha256,
                "selected_time_s": self.selected_time_s,
                "minimum_pressure_Pa": threshold.minimum_pressure_Pa,
            }
            if canonical_digest(basis) != threshold.record_sha256:
                raise ValueError("pressure threshold digest does not bind the scope and selected contact result")
            if not any(
                row.source_id == threshold.provider_id
                and row.sha256 == threshold.record_sha256
                and row.license_id == threshold.usage_license_id
                for row in threshold.evidence
            ):
                raise ValueError("threshold Evidence must pin the criterion record and usage license")
        return self


def _selected_output(request: GasketContactDistributionStatistics) -> tuple[dict | None, list[dict] | None]:
    result = request.contact_result
    if result.model_id in STATIC_MODELS:
        field = result.values.get("response_field")
        return result.values, field if isinstance(field, list) else None
    history = result.values.get("time_history")
    if not isinstance(history, list):
        return None, None
    selected = next((row for row in history if isinstance(row, dict) and row.get("time_s") == request.selected_time_s), None)
    field = selected.get("response_field") if selected else None
    return selected, field if isinstance(field, list) else None


def _weighted_quantile(values_and_weights: list[tuple[float, float]], level: float, total_weight: float) -> float:
    """Left-continuous weighted empirical quantile; no interpolation across nodes."""
    ordered = sorted(values_and_weights, key=lambda item: item[0])
    if level <= 0.0:
        return ordered[0][0]
    target = level * total_weight
    cumulative = 0.0
    for value, weight in ordered:
        cumulative += weight
        if cumulative >= target:
            return value
    return ordered[-1][0]


def summarize_gasket_contact_distribution(request: GasketContactDistributionStatistics) -> Calculation:
    """Compute force-closing, area-weighted pressure moments, quantiles and threshold areas."""
    digest = canonical_digest(request.model_dump(mode="json"))
    result = request.contact_result
    base = {
        "assessment_id": request.assessment_id,
        "physical_scope_id": request.physical_scope_id,
        "contact_result_model_id": result.model_id,
        "contact_result_sha256": request.contact_result_sha256,
        "selected_time_s": request.selected_time_s,
        "input_sha256": digest,
    }
    reviews = (
        request.physical_scope_and_time_reviewed,
        request.contact_area_basis_and_units_reviewed,
        request.distribution_summary_interpretation_reviewed,
        request.resolution_and_threshold_applicability_reviewed,
        request.evidence_rights_and_computational_use_reviewed,
    )
    if not all(reviews):
        return Calculation(status="needs_data", values=base | {"missing_review_count": sum(not row for row in reviews)})
    unit_key = (
        "response_field.mean_contact_pressure_Pa"
        if result.model_id in STATIC_MODELS
        else "time_history[].response_field[].mean_contact_pressure_Pa"
    )
    if result.units.get(unit_key) != "Pa":
        return Calculation(status="out_of_scope", values=base, notes=("Upstream contact pressure must explicitly use Pa.",))
    selected_output, field = _selected_output(request)
    if not field:
        return Calculation(status="out_of_scope", values=base, notes=("Selected computed contact field is missing.",))
    inputs = result.inputs
    node_ids = inputs.get("node_ids", inputs.get("contact_node_ids"))
    areas = inputs.get("gasket_contact_area_m2", inputs.get("contact_area_m2"))
    if not isinstance(node_ids, list) or not isinstance(areas, list) or len(node_ids) != len(areas):
        return Calculation(status="out_of_scope", values=base, notes=("Pinned contact input must provide aligned node IDs and gasket areas.",))
    if [row.get("node_id") for row in field if isinstance(row, dict)] != node_ids or len(field) != len(node_ids):
        return Calculation(status="out_of_scope", values=base, notes=("Selected field node order must match its pinned contact input.",))
    if any(isinstance(area, bool) or not isinstance(area, (int, float)) or not math.isfinite(area) or area <= 0 for area in areas):
        return Calculation(status="out_of_scope", values=base, notes=("Nodal contact areas must be finite and positive.",))
    pressures: list[float] = []
    force_sum_values = []
    for row, area in zip(field, areas, strict=True):
        pressure = row.get("mean_contact_pressure_Pa")
        force = row.get("contact_force_N")
        if isinstance(pressure, bool) or not isinstance(pressure, (int, float)) or not math.isfinite(pressure) or pressure < 0:
            return Calculation(status="out_of_scope", values=base | {"invalid_node_id": row["node_id"]}, notes=("Contact pressures must be finite and nonnegative.",))
        if isinstance(force, bool) or not isinstance(force, (int, float)) or not math.isfinite(force) or force < 0:
            return Calculation(status="out_of_scope", values=base | {"invalid_node_id": row["node_id"]}, notes=("Contact forces must be finite and nonnegative.",))
        reconstructed = float(area) * float(pressure)
        tolerance = max(1e-8, 1e-10 * max(abs(reconstructed), abs(float(force))))
        if abs(reconstructed - float(force)) > tolerance:
            return Calculation(status="out_of_scope", values=base | {"invalid_node_id": row["node_id"]}, notes=("Pressure, area and contact force do not close at a node.",))
        pressures.append(float(pressure))
        force_sum_values.append(float(force))
    try:
        total_area = math.fsum(float(value) for value in areas)
        total_force = math.fsum(force_sum_values)
        mean = total_force / total_area
        variance = math.fsum(
            float(area) * (pressure - mean) ** 2
            for area, pressure in zip(areas, pressures, strict=True)
        ) / total_area
    except (OverflowError, ZeroDivisionError):
        return Calculation(status="out_of_scope", values=base, notes=("Area-weighted totals exceeded finite numeric support.",))
    if not math.isfinite(variance) or variance < 0.0:
        return Calculation(status="out_of_scope", values=base, notes=("Weighted pressure variance is outside finite numeric support.",))
    std = math.sqrt(variance)
    weighted = list(zip(pressures, [float(area) for area in areas], strict=True))
    try:
        quantiles = {f"{level:g}": _weighted_quantile(weighted, level, total_area) for level in request.quantile_levels}
    except (OverflowError, ZeroDivisionError):
        return Calculation(status="out_of_scope", values=base, notes=("Weighted empirical quantile calculation failed.",))
    threshold_results = []
    for threshold in request.thresholds:
        deficient_area = math.fsum(
            float(area) for area, pressure in zip(areas, pressures, strict=True)
            if pressure < threshold.minimum_pressure_Pa
        )
        threshold_results.append({
            "criterion_id": threshold.criterion_id,
            "minimum_pressure_Pa": threshold.minimum_pressure_Pa,
            "criterion_record_sha256": threshold.record_sha256,
            "area_below_threshold_m2": deficient_area,
            "area_fraction_below_threshold": deficient_area / total_area,
        })
    expected_sum = selected_output.get("contact_force_sum_N") if selected_output is not None else None
    if isinstance(expected_sum, (int, float)) and not isinstance(expected_sum, bool) and math.isfinite(expected_sum):
        total_closure_residual = total_force - float(expected_sum)
    else:
        total_closure_residual = None
    outputs = {
        "node_count": len(field),
        "finite_node_total_area_m2": total_area,
        "contact_force_resultant_N": total_force,
        "area_weighted_mean_contact_pressure_Pa": mean,
        "area_weighted_pressure_standard_deviation_Pa": std,
        "area_weighted_pressure_coefficient_of_variation": std / mean if mean > 0 else None,
        "area_weighted_empirical_quantiles_Pa": quantiles,
        "area_with_positive_contact_force_m2": math.fsum(float(area) for area, force in zip(areas, force_sum_values, strict=True) if force > 0),
        "area_fraction_with_positive_contact_force": math.fsum(float(area) for area, force in zip(areas, force_sum_values, strict=True) if force > 0) / total_area,
        "caller_threshold_area_summaries": threshold_results,
        "upstream_total_force_closure_residual_N": total_closure_residual,
        "quantile_definition": "left_continuous_area_weighted_empirical_quantile_without_inter_node_interpolation",
        "interpretation": "finite_mesh_area_weighted_pressure_distribution_summary_only",
    }
    if any(isinstance(value, float) and not math.isfinite(value) for value in outputs.values()):
        return Calculation(status="out_of_scope", values=base, notes=("Distribution summary exceeded finite numeric range.",))
    return Calculation(values=base | outputs, notes=(
        "Area-weighted distribution summaries are computed over the caller's finite nodal partition and declared nodal areas.",
        "Threshold area fractions compare to caller criteria only; no leakage, seal acceptance, qualification, local stress, life or probability is inferred.",
    ))


def specifications() -> list[ModelSpec]:
    return [ModelSpec(
        MODEL_ID,
        GasketContactDistributionStatistics,
        summarize_gasket_contact_distribution,
        {
            "finite_node_total_area_m2": "m^2",
            "contact_force_resultant_N": "N",
            "area_weighted_mean_contact_pressure_Pa": "Pa",
            "area_weighted_pressure_standard_deviation_Pa": "Pa",
            "area_weighted_pressure_coefficient_of_variation": "1",
            "area_weighted_empirical_quantiles_Pa": "Pa",
            "area_with_positive_contact_force_m2": "m^2",
            "area_fraction_with_positive_contact_force": "1",
            "caller_threshold_area_summaries[].minimum_pressure_Pa": "Pa",
            "caller_threshold_area_summaries[].area_below_threshold_m2": "m^2",
            "caller_threshold_area_summaries[].area_fraction_below_threshold": "1",
            "upstream_total_force_closure_residual_N": "N",
        },
        (
            "Summarize a digest-pinned computed flange gasket pressure field using its own declared finite nodal contact areas.",
            "Report area-weighted mean, variance, coefficient of variation, left-continuous empirical quantiles, positive-force coverage and optional caller-threshold area fractions.",
            "Statistics describe only the finite caller discretization and do not establish a leak/seal criterion or qualification.",
        ),
        (SOURCE_ID, "caller_finite_area_weighted_empirical_statistics"),
        qualification="engineering_screening",
    )]
