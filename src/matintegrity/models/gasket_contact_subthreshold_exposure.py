"""Area-time exposure of gasket contact pressure below a caller-defined threshold."""

from __future__ import annotations

import math
from typing import Literal

from pydantic import Field, model_validator

from ..contracts import AssessmentResult, Calculation, Contract, Evidence, Nonnegative, canonical_digest
from ..registry import ModelSpec


MODEL_ID = "fabrication.gasket_contact_subthreshold_exposure"
SOURCE_ID = "caller_gasket_contact_subthreshold_exposure_threshold"
HISTORY_MODELS = {
    "fabrication.flange_viscoelastic_contact_history",
    "fabrication.flange_nonlinear_viscoelastic_contact_history",
}


class GasketContactSubthresholdExposure(Contract):
    """Integrate area and pressure deficit over time using piecewise-linear nodal histories."""

    schema_version: Literal["matintegrity.gasket_contact_subthreshold_exposure.v1"] = (
        "matintegrity.gasket_contact_subthreshold_exposure.v1"
    )
    assessment_id: str = Field(min_length=1)
    physical_scope_id: str = Field(min_length=1)
    contact_history: AssessmentResult
    contact_history_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    minimum_contact_pressure_Pa: Nonnegative
    threshold_provider_id: str = Field(min_length=1)
    threshold_provider_revision: str = Field(min_length=1)
    threshold_record_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    threshold_usage_license_id: str = Field(min_length=1)
    threshold_evidence: tuple[Evidence, ...] = Field(min_length=1)
    physical_scope_time_and_history_basis_reviewed: bool
    pressure_threshold_applicability_reviewed: bool
    nodal_area_partition_and_resolution_reviewed: bool
    piecewise_linear_interpolation_and_exposure_interpretation_reviewed: bool
    lineage_license_and_computational_use_reviewed: bool

    @model_validator(mode="after")
    def coherent_history_and_threshold(self):
        result = self.contact_history
        if result.status != "computed" or result.model_id not in HISTORY_MODELS:
            raise ValueError("a computed supported viscoelastic contact history is required")
        if canonical_digest(result.model_dump(mode="json")) != self.contact_history_sha256:
            raise ValueError("contact history digest does not match")
        if result.inputs.get("physical_scope_id") != self.physical_scope_id:
            raise ValueError("contact history physical scope does not match")
        basis = {
            "provider_id": self.threshold_provider_id,
            "provider_revision": self.threshold_provider_revision,
            "physical_scope_id": self.physical_scope_id,
            "contact_history_sha256": self.contact_history_sha256,
            "minimum_contact_pressure_Pa": self.minimum_contact_pressure_Pa,
        }
        if canonical_digest(basis) != self.threshold_record_sha256:
            raise ValueError("threshold digest must bind provider, scope, history and pressure threshold")
        if not any(
            row.source_id == self.threshold_provider_id
            and row.sha256 == self.threshold_record_sha256
            and row.license_id == self.threshold_usage_license_id
            for row in self.threshold_evidence
        ):
            raise ValueError("threshold Evidence must pin its record digest and license")
        return self


def _below_fraction(p0: float, p1: float, threshold: float) -> float:
    """Fraction of a linearly interpolated interval strictly below threshold."""
    low0, low1 = p0 < threshold, p1 < threshold
    if low0 and low1:
        return 1.0
    if not low0 and not low1:
        return 0.0
    if low0:
        below_distance = threshold - p0
        above_distance = p1 - threshold
    else:
        below_distance = threshold - p1
        above_distance = p0 - threshold
    if above_distance <= 0.0:
        return 1.0
    if below_distance >= above_distance:
        return 1.0 / (1.0 + above_distance / below_distance)
    ratio = below_distance / above_distance
    return ratio / (1.0 + ratio)


def evaluate_gasket_contact_subthreshold_exposure(
    request: GasketContactSubthresholdExposure,
) -> Calculation:
    """Integrate below-threshold area-time and pressure-deficit dose on the supplied mesh."""
    result = request.contact_history
    digest = canonical_digest(request.model_dump(mode="json"))
    base = {
        "assessment_id": request.assessment_id,
        "physical_scope_id": request.physical_scope_id,
        "contact_history_model_id": result.model_id,
        "contact_history_sha256": request.contact_history_sha256,
        "threshold_provider_id": request.threshold_provider_id,
        "threshold_record_sha256": request.threshold_record_sha256,
        "input_sha256": digest,
    }
    reviews = (
        request.physical_scope_time_and_history_basis_reviewed,
        request.pressure_threshold_applicability_reviewed,
        request.nodal_area_partition_and_resolution_reviewed,
        request.piecewise_linear_interpolation_and_exposure_interpretation_reviewed,
        request.lineage_license_and_computational_use_reviewed,
    )
    if not all(reviews):
        return Calculation(status="needs_data", values=base | {"missing_review_count": sum(not row for row in reviews)})
    if result.units.get("time_history[].time_s") != "s" or result.units.get("time_history[].response_field[].mean_contact_pressure_Pa") != "Pa":
        return Calculation(status="out_of_scope", values=base, notes=("History time and pressure units must explicitly be seconds and pascals.",))
    node_ids = result.inputs.get("node_ids", result.inputs.get("contact_node_ids"))
    areas = result.inputs.get("gasket_contact_area_m2", result.inputs.get("contact_area_m2"))
    history = result.values.get("time_history")
    if not isinstance(node_ids, list) or not isinstance(areas, list) or len(node_ids) != len(areas):
        return Calculation(status="out_of_scope", values=base, notes=("Contact history must retain aligned node IDs and contact areas in its pinned inputs.",))
    if len(set(node_ids)) != len(node_ids) or any(
        isinstance(area, bool) or not isinstance(area, (int, float)) or not math.isfinite(area) or area <= 0
        for area in areas
    ):
        return Calculation(status="out_of_scope", values=base, notes=("Contact node IDs and areas must be unique, finite and positive.",))
    if not isinstance(history, list) or len(history) < 2:
        return Calculation(status="out_of_scope", values=base, notes=("At least two computed history knots are required.",))
    times: list[float] = []
    pressure_rows: list[list[float]] = []
    for knot_index, knot in enumerate(history):
        if not isinstance(knot, dict) or knot.get("status", "computed") != "computed":
            return Calculation(status="needs_data", values=base | {"incomplete_knot_index": knot_index}, notes=("Incomplete history knots are not extrapolated.",))
        time_s, field = knot.get("time_s"), knot.get("response_field")
        if isinstance(time_s, bool) or not isinstance(time_s, (int, float)) or not math.isfinite(time_s) or time_s < 0:
            return Calculation(status="out_of_scope", values=base | {"invalid_knot_index": knot_index}, notes=("History times must be finite and nonnegative.",))
        if not isinstance(field, list) or len(field) != len(node_ids):
            return Calculation(status="out_of_scope", values=base | {"invalid_knot_index": knot_index}, notes=("Every knot must contain the complete contact node field.",))
        if [row.get("node_id") for row in field if isinstance(row, dict)] != node_ids:
            return Calculation(status="out_of_scope", values=base | {"invalid_knot_index": knot_index}, notes=("Nodal pressure order must exactly match the source input order.",))
        pressures = []
        for row in field:
            value = row.get("mean_contact_pressure_Pa")
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value < 0:
                return Calculation(status="out_of_scope", values=base | {"invalid_knot_index": knot_index, "node_id": row["node_id"]}, notes=("Nodal pressure must be finite and nonnegative.",))
            pressures.append(float(value))
        times.append(float(time_s))
        pressure_rows.append(pressures)
    if any(right <= left for left, right in zip(times, times[1:])):
        return Calculation(status="out_of_scope", values=base, notes=("History times must strictly increase.",))

    try:
        total_area = math.fsum(float(area) for area in areas)
        interval_area_time = []
        interval_deficit_dose = []
        for index, (t0, t1) in enumerate(zip(times[:-1], times[1:], strict=True)):
            dt = t1 - t0
            below_area_time = 0.0
            deficit_dose = 0.0
            for node_index, area_value in enumerate(areas):
                p0 = pressure_rows[index][node_index]
                p1 = pressure_rows[index + 1][node_index]
                fraction = _below_fraction(p0, p1, request.minimum_contact_pressure_Pa)
                below_area_time += float(area_value) * dt * fraction
                deficit0 = max(request.minimum_contact_pressure_Pa - p0, 0.0)
                deficit1 = max(request.minimum_contact_pressure_Pa - p1, 0.0)
                if p0 < request.minimum_contact_pressure_Pa and p1 < request.minimum_contact_pressure_Pa:
                    deficit_integral = dt * 0.5 * (deficit0 + deficit1)
                elif p0 < request.minimum_contact_pressure_Pa:
                    deficit_integral = dt * fraction * 0.5 * deficit0
                elif p1 < request.minimum_contact_pressure_Pa:
                    deficit_integral = dt * fraction * 0.5 * deficit1
                else:
                    deficit_integral = 0.0
                deficit_dose += float(area_value) * deficit_integral
            interval_area_time.append(below_area_time)
            interval_deficit_dose.append(deficit_dose)
        total_below_area_time = math.fsum(interval_area_time)
        total_deficit_dose = math.fsum(interval_deficit_dose)
        duration = times[-1] - times[0]
    except (OverflowError, ZeroDivisionError):
        return Calculation(status="out_of_scope", values=base, notes=("Area-time exposure integration exceeded finite numeric support.",))
    if not all(math.isfinite(value) for value in (total_area, total_below_area_time, total_deficit_dose, duration)) or total_area <= 0:
        return Calculation(status="out_of_scope", values=base, notes=("Exposure totals are outside finite numeric support.",))

    knot_summaries = []
    for time_s, pressures in zip(times, pressure_rows, strict=True):
        area_below = math.fsum(float(area) for area, pressure in zip(areas, pressures, strict=True) if pressure < request.minimum_contact_pressure_Pa)
        knot_summaries.append({
            "time_s": time_s,
            "area_below_threshold_m2": area_below,
            "area_fraction_below_threshold": area_below / total_area,
        })
    peak_knot = max(knot_summaries, key=lambda row: row["area_fraction_below_threshold"])
    return Calculation(values=base | {
        "minimum_contact_pressure_Pa": request.minimum_contact_pressure_Pa,
        "history_start_time_s": times[0],
        "history_end_time_s": times[-1],
        "history_duration_s": duration,
        "finite_node_total_area_m2": total_area,
        "below_threshold_area_time_m2_s": total_below_area_time,
        "below_threshold_time_averaged_area_fraction": total_below_area_time / total_area / duration,
        "integrated_pressure_deficit_area_time_Pa_m2_s": total_deficit_dose,
        "maximum_knot_area_fraction_below_threshold": peak_knot["area_fraction_below_threshold"],
        "time_of_maximum_knot_area_fraction_below_threshold_s": peak_knot["time_s"],
        "area_fraction_time_history": knot_summaries,
        "interval_below_threshold_area_time_m2_s": interval_area_time,
        "interval_pressure_deficit_area_time_Pa_m2_s": interval_deficit_dose,
        "interpolation": "piecewise_linear_nodal_pressure_between_computed_knots_with_exact_threshold_crossing_area_time",
        "interpretation": "caller_thresholded_finite_mesh_area_time_exposure_only",
    }, notes=(
        "Nodal pressures are linearly interpolated between computed knots; below-threshold area-time uses exact segment crossing fractions for that interpolation.",
        "Pressure-deficit dose integrates the positive part of threshold minus linearly interpolated pressure per node; it is a descriptive exposure measure, not a leak-rate model.",
        "No hidden contact events between knots, seal acceptance, leakage, failure probability, local stress or qualification is inferred.",
    ))


def specifications() -> list[ModelSpec]:
    return [ModelSpec(
        MODEL_ID,
        GasketContactSubthresholdExposure,
        evaluate_gasket_contact_subthreshold_exposure,
        {
            "minimum_contact_pressure_Pa": "Pa",
            "history_start_time_s": "s",
            "history_end_time_s": "s",
            "history_duration_s": "s",
            "finite_node_total_area_m2": "m^2",
            "below_threshold_area_time_m2_s": "m^2*s",
            "below_threshold_time_averaged_area_fraction": "1",
            "integrated_pressure_deficit_area_time_Pa_m2_s": "Pa*m^2*s",
            "maximum_knot_area_fraction_below_threshold": "1",
            "time_of_maximum_knot_area_fraction_below_threshold_s": "s",
            "area_fraction_time_history[].time_s": "s",
            "area_fraction_time_history[].area_below_threshold_m2": "m^2",
            "area_fraction_time_history[].area_fraction_below_threshold": "1",
            "interval_below_threshold_area_time_m2_s[]": "m^2*s",
            "interval_pressure_deficit_area_time_Pa_m2_s[]": "Pa*m^2*s",
        },
        (
            "Integrate a caller-evidenced thresholded pressure exposure over a computed viscoelastic gasket contact history and its finite nodal area partition.",
            "Within each time interval, pressure is linearly interpolated and threshold crossing fractions are integrated per node; no between-knot solver result is claimed.",
            "Area-time and pressure-deficit exposure are not leakage, sealing acceptance, life, probability or qualification outputs.",
        ),
        (SOURCE_ID, "piecewise_linear_threshold_area_time_integral"),
        qualification="engineering_screening",
    )]
