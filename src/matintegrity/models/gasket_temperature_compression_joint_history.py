"""Quasi-static bolt/sector equilibrium with temperature-interpolated gasket loading curves."""

from __future__ import annotations

import math
from typing import Literal

from pydantic import Field, StrictInt, model_validator

from ..contracts import Calculation, Contract, Evidence, Nonnegative, Positive, canonical_digest
from ..registry import ModelSpec
from .gasket_temperature_compression_curve import TemperatureCompressionCurve

MODEL_ID = "integration.gasket_temperature_compression_joint_history"


class TemperatureJointBolt(Contract):
    bolt_id: str = Field(min_length=1)
    initial_preload_N: Positive
    axial_stiffness_N_m: Positive
    tensile_stress_area_m2: Positive
    source_id: str = Field(min_length=1)


class TemperatureJointSector(Contract):
    sector_id: str = Field(min_length=1)
    initial_compression_m: Positive
    contact_area_m2: Positive
    source_id: str = Field(min_length=1)


class TemperatureJointLoadStep(Contract):
    step_id: str = Field(min_length=1)
    time_s: Nonnegative
    temperature_K: Positive
    external_separating_force_N: float
    bolt_free_length_change_m: tuple[float, ...]
    gasket_free_thickness_change_m: tuple[float, ...]


class GasketTemperatureCompressionJointHistory(Contract):
    """Ordered common-opening quasi-static response under caller temperature curves and thermal shifts."""

    schema_version: Literal["matintegrity.gasket_temperature_compression_joint_history.v1"] = (
        "matintegrity.gasket_temperature_compression_joint_history.v1"
    )
    assessment_id: str = Field(min_length=1)
    asset_id: str = Field(min_length=1)
    location_id: str = Field(min_length=1)
    physical_scope_id: str = Field(min_length=1)
    joint_id: str = Field(min_length=1)
    lower_temperature_curve: TemperatureCompressionCurve
    upper_temperature_curve: TemperatureCompressionCurve
    initial_gasket_thickness_m: Positive
    thickness_provider_id: str = Field(min_length=1)
    thickness_provider_revision: str = Field(min_length=1)
    thickness_record_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    thickness_usage_license_id: str = Field(min_length=1)
    thickness_evidence: tuple[Evidence, ...] = Field(min_length=1)
    bolts: tuple[TemperatureJointBolt, ...] = Field(min_length=2, max_length=256)
    sectors: tuple[TemperatureJointSector, ...] = Field(min_length=1, max_length=256)
    steps: tuple[TemperatureJointLoadStep, ...] = Field(min_length=1, max_length=10000)
    minimum_opening_m: float
    maximum_opening_m: Positive
    initial_force_balance_tolerance_N: Positive
    force_balance_tolerance_N: Positive
    opening_tolerance_m: Positive
    maximum_bisection_iterations: StrictInt = Field(default=160, ge=1, le=1000)
    common_axial_opening_reviewed: bool
    temperature_bracket_and_curve_transfer_reviewed: bool
    bolt_preload_stiffness_and_thermal_shift_reviewed: bool
    sector_area_and_gasket_free_thickness_reviewed: bool
    curve_support_and_unilateral_contact_reviewed: bool
    quasi_static_path_and_source_rights_reviewed: bool
    computational_use_authorized: bool
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def coherent_joint_path(self):
        low, high = self.lower_temperature_curve, self.upper_temperature_curve
        if low.temperature_K >= high.temperature_K:
            raise ValueError("temperature curve bracket must be strictly increasing")
        if (low.specimen_id, low.material_condition_id, low.loading_branch_id) != (
            high.specimen_id, high.material_condition_id, high.loading_branch_id
        ):
            raise ValueError("temperature curves must share specimen, condition and loading branch")
        if low.strain_fraction != high.strain_fraction:
            raise ValueError("temperature curves must share exact strain knots")
        if not math.isfinite(self.minimum_opening_m) or self.minimum_opening_m >= 0:
            raise ValueError("minimum opening must be finite and below the assembled zero-opening state")
        if self.minimum_opening_m >= self.maximum_opening_m:
            raise ValueError("opening support must bracket zero")
        for records, label in ((self.bolts, "bolt"), (self.sectors, "sector"), (self.steps, "step")):
            ids = [row.bolt_id if label == "bolt" else row.sector_id if label == "sector" else row.step_id for row in records]
            if len(ids) != len(set(ids)):
                raise ValueError(f"{label} IDs must be unique")
        for step in self.steps:
            if len(step.bolt_free_length_change_m) != len(self.bolts):
                raise ValueError("each step needs one free-length shift per bolt")
            if len(step.gasket_free_thickness_change_m) != len(self.sectors):
                raise ValueError("each step needs one free-thickness shift per sector")
            if not math.isfinite(step.external_separating_force_N) or not all(math.isfinite(value) for value in (
                *step.bolt_free_length_change_m, *step.gasket_free_thickness_change_m,
            )):
                raise ValueError("load steps and thermal shifts must be finite")
            if not low.temperature_K <= step.temperature_K <= high.temperature_K:
                raise ValueError("every step temperature must lie inside the measured gasket curve bracket")
        if self.steps[0].time_s != 0 or self.steps[0].external_separating_force_N != 0:
            raise ValueError("first reference step must be at time zero with no external separating load")
        if any(self.steps[0].bolt_free_length_change_m) or any(self.steps[0].gasket_free_thickness_change_m):
            raise ValueError("first assembled reference step must have zero free-length/thickness shifts")
        if any(right.time_s <= left.time_s for left, right in zip(self.steps, self.steps[1:])):
            raise ValueError("load-step times must strictly increase")
        required_sources = {row.source_id for row in self.bolts} | {row.source_id for row in self.sectors} | {self.thickness_provider_id}
        if not required_sources <= {row.source_id for row in self.evidence}:
            raise ValueError("joint Evidence must cover every bolt, sector and gasket-thickness source")
        thickness_record = {
            "physical_scope_id": self.physical_scope_id,
            "specimen_id": low.specimen_id,
            "material_condition_id": low.material_condition_id,
            "initial_gasket_thickness_m": self.initial_gasket_thickness_m,
            "provider_id": self.thickness_provider_id,
            "provider_revision": self.thickness_provider_revision,
        }
        if canonical_digest(thickness_record) != self.thickness_record_sha256:
            raise ValueError("initial thickness digest does not bind the joint and gasket specimen")
        if not any(row.source_id == self.thickness_provider_id and row.sha256 == self.thickness_record_sha256
                   and row.license_id == self.thickness_usage_license_id for row in self.thickness_evidence):
            raise ValueError("thickness Evidence must pin specimen geometry and usage license")
        if any(sector.initial_compression_m / self.initial_gasket_thickness_m > low.strain_fraction[-1]
               for sector in self.sectors):
            raise ValueError("initial sector compression exceeds gasket curve strain support")
        return self


def _temperature_stress_points(
    low: TemperatureCompressionCurve,
    high: TemperatureCompressionCurve,
    temperature_K: float,
) -> tuple[float, ...]:
    fraction = (temperature_K - low.temperature_K) / (high.temperature_K - low.temperature_K)
    values = tuple(a + fraction * (b - a) for a, b in zip(low.compressive_stress_Pa, high.compressive_stress_Pa))
    if not all(math.isfinite(value) and value >= 0.0 for value in values):
        raise OverflowError("temperature-interpolated gasket stress curve is outside finite support")
    return values


def _gasket_force_and_tangent(
    strain_knots: tuple[float, ...], stress_knots: tuple[float, ...],
    compression_m: float, thickness_m: float, area_m2: float,
) -> tuple[float, float]:
    if compression_m <= 0.0:
        return 0.0, 0.0
    strain = compression_m / thickness_m
    if not math.isfinite(strain) or strain > strain_knots[-1]:
        raise ValueError("sector compression is outside the measured gasket curve support")
    low = 0
    high = len(strain_knots) - 1
    while low + 1 < high:
        middle = (low + high) // 2
        if strain_knots[middle] <= strain:
            low = middle
        else:
            high = middle
    slope = (stress_knots[low + 1] - stress_knots[low]) / (strain_knots[low + 1] - strain_knots[low])
    stress = stress_knots[low] + slope * (strain - strain_knots[low])
    force = stress * area_m2
    tangent = slope * area_m2 / thickness_m
    if not all(math.isfinite(value) and value >= 0.0 for value in (force, tangent)):
        raise OverflowError("gasket sector force or tangent exceeds finite support")
    return force, tangent


def evaluate_gasket_temperature_compression_joint_history(
    request: GasketTemperatureCompressionJointHistory,
) -> Calculation:
    """Solve force equilibrium at each exact knot using temperature-specific gasket curves."""
    digest = canonical_digest(request.model_dump(mode="json"))
    base = {
        "assessment_id": request.assessment_id,
        "asset_id": request.asset_id,
        "location_id": request.location_id,
        "joint_id": request.joint_id,
        "physical_scope_id": request.physical_scope_id,
        "gasket_specimen_id": request.lower_temperature_curve.specimen_id,
        "material_condition_id": request.lower_temperature_curve.material_condition_id,
        "input_sha256": digest,
        "model_id": MODEL_ID,
    }
    reviews = {
        "common_axial_opening_reviewed": request.common_axial_opening_reviewed,
        "temperature_bracket_and_curve_transfer_reviewed": request.temperature_bracket_and_curve_transfer_reviewed,
        "bolt_preload_stiffness_and_thermal_shift_reviewed": request.bolt_preload_stiffness_and_thermal_shift_reviewed,
        "sector_area_and_gasket_free_thickness_reviewed": request.sector_area_and_gasket_free_thickness_reviewed,
        "curve_support_and_unilateral_contact_reviewed": request.curve_support_and_unilateral_contact_reviewed,
        "quasi_static_path_and_source_rights_reviewed": request.quasi_static_path_and_source_rights_reviewed,
        "computational_use_authorized": request.computational_use_authorized,
    }
    missing = [name for name, value in reviews.items() if not value]
    if missing:
        return Calculation(status="needs_data", values=base | {"missing_reviews": missing})
    low_curve, high_curve = request.lower_temperature_curve, request.upper_temperature_curve
    strain_knots = low_curve.strain_fraction
    first_step = request.steps[0]
    initial_stress = _temperature_stress_points(low_curve, high_curve, first_step.temperature_K)
    initial_gasket_force = math.fsum(
        _gasket_force_and_tangent(
            strain_knots, initial_stress, sector.initial_compression_m,
            request.initial_gasket_thickness_m, sector.contact_area_m2,
        )[0]
        for sector in request.sectors
    )
    initial_bolt_force = math.fsum(row.initial_preload_N for row in request.bolts)
    initial_residual = initial_bolt_force - initial_gasket_force
    if not math.isfinite(initial_residual):
        return Calculation(status="out_of_scope", values=base | {"reason": "initial_force_balance_exceeded_finite_support"})
    if abs(initial_residual) > request.initial_force_balance_tolerance_N:
        return Calculation(status="needs_data", values=base | {
            "initial_bolt_force_sum_N": initial_bolt_force,
            "initial_gasket_force_sum_N": initial_gasket_force,
            "initial_force_balance_residual_N": initial_residual,
        })
    history = []
    for step in request.steps:
        try:
            stress_knots = _temperature_stress_points(low_curve, high_curve, step.temperature_K)

            def state(opening: float):
                bolt_rows = []
                for bolt, free_shift in zip(request.bolts, step.bolt_free_length_change_m):
                    extension = opening - free_shift
                    force = max(0.0, bolt.initial_preload_N + bolt.axial_stiffness_N_m * extension)
                    stress = force / bolt.tensile_stress_area_m2
                    if not all(math.isfinite(value) for value in (extension, force, stress)):
                        raise OverflowError("bolt response exceeds finite support")
                    bolt_rows.append({
                        "bolt_id": bolt.bolt_id,
                        "extension_m": extension,
                        "tensile_force_N": force,
                        "nominal_tensile_stress_Pa": stress,
                    })
                sector_rows = []
                for sector, free_shift in zip(request.sectors, step.gasket_free_thickness_change_m):
                    compression = sector.initial_compression_m + free_shift - opening
                    force, tangent = _gasket_force_and_tangent(
                        strain_knots, stress_knots, compression,
                        request.initial_gasket_thickness_m, sector.contact_area_m2,
                    )
                    pressure = force / sector.contact_area_m2
                    sector_rows.append({
                        "sector_id": sector.sector_id,
                        "compression_m": max(0.0, compression),
                        "contact_gap_m": max(0.0, -compression),
                        "compressive_force_N": force,
                        "mean_contact_pressure_Pa": pressure,
                        "tangent_stiffness_N_m": tangent,
                    })
                bolt_sum = math.fsum(row["tensile_force_N"] for row in bolt_rows)
                gasket_sum = math.fsum(row["compressive_force_N"] for row in sector_rows)
                residual = bolt_sum - gasket_sum - step.external_separating_force_N
                tangent = math.fsum(
                    bolt.axial_stiffness_N_m for bolt, row in zip(request.bolts, bolt_rows)
                    if row["tensile_force_N"] > 0.0
                ) + math.fsum(row["tangent_stiffness_N_m"] for row in sector_rows)
                if not all(math.isfinite(value) for value in (bolt_sum, gasket_sum, residual, tangent)):
                    raise OverflowError("equilibrium balance exceeds finite support")
                return residual, bolt_rows, sector_rows, bolt_sum, gasket_sum, tangent

            lower = request.minimum_opening_m
            for bolt, free_shift in zip(request.bolts, step.bolt_free_length_change_m):
                lower = max(lower, free_shift - bolt.initial_preload_N / bolt.axial_stiffness_N_m)
            if lower >= request.maximum_opening_m:
                return Calculation(status="out_of_scope", values=base | {
                    "failed_step_id": step.step_id,
                    "reason": "bolt_tension_support_does_not_overlap_opening_bracket",
                    "effective_lower_opening_m": lower,
                    "maximum_opening_m": request.maximum_opening_m,
                    "completed_step_count": len(history),
                })
            low_state = state(lower)
            high_state = state(request.maximum_opening_m)
            if low_state[0] > request.force_balance_tolerance_N or high_state[0] < -request.force_balance_tolerance_N:
                return Calculation(status="out_of_scope", values=base | {
                    "failed_step_id": step.step_id,
                    "lower_bound_residual_N": low_state[0],
                    "upper_bound_residual_N": high_state[0],
                    "completed_step_count": len(history),
                    "reason": "equilibrium_root_not_bracketed_in_caller_support",
                })
            lo, hi = lower, request.maximum_opening_m
            opening = lo + 0.5 * (hi - lo)
            current = state(opening)
            for _ in range(request.maximum_bisection_iterations):
                if abs(current[0]) <= request.force_balance_tolerance_N or hi - lo <= request.opening_tolerance_m:
                    break
                if current[0] < 0.0:
                    lo = opening
                else:
                    hi = opening
                opening = lo + 0.5 * (hi - lo)
                current = state(opening)
            if current[5] <= 0.0 or abs(current[0]) > request.force_balance_tolerance_N:
                return Calculation(status="out_of_scope", values=base | {
                    "failed_step_id": step.step_id,
                    "completed_step_count": len(history),
                    "reason": "equilibrium_not_unique_or_force_tolerance_not_met",
                })
        except (ArithmeticError, OverflowError, ValueError):
            return Calculation(status="out_of_scope", values=base | {
                "failed_step_id": step.step_id,
                "completed_step_count": len(history),
                "reason": "temperature_dependent_joint_state_left_curve_or_numeric_support",
            })
        residual, bolt_rows, sector_rows, bolt_sum, gasket_sum, tangent = current
        history.append({
            "step_id": step.step_id,
            "time_s": step.time_s,
            "temperature_K": step.temperature_K,
            "temperature_interpolation_fraction": (step.temperature_K - low_curve.temperature_K) / (
                high_curve.temperature_K - low_curve.temperature_K
            ),
            "opening_m": opening,
            "bolt_tensile_force_sum_N": bolt_sum,
            "gasket_compressive_force_sum_N": gasket_sum,
            "external_separating_force_N": step.external_separating_force_N,
            "force_balance_residual_N": residual,
            "equilibrium_tangent_N_m": tangent,
            "bolts": bolt_rows,
            "gasket_sectors": sector_rows,
        })
    return Calculation(values=base | {
        "step_count": len(history),
        "initial_force_balance_residual_N": initial_residual,
        "history": history,
        "limitations": [
            "One common axial opening couples the caller tension-only bolt springs and compression-only gasket sectors.",
            "Gasket stress-strain values interpolate linearly in temperature only between the two measured loading curves, which share exact strain knots.",
            "The response is quasi-static and uses caller thermal free-length/free-thickness changes; no hysteresis, stress relaxation, flange FE bending, seal acceptance, leakage or qualification is inferred.",
        ],
    })


def specifications() -> list[ModelSpec]:
    return [ModelSpec(
        MODEL_ID,
        GasketTemperatureCompressionJointHistory,
        evaluate_gasket_temperature_compression_joint_history,
        {
            "history[].time_s": "s",
            "history[].temperature_K": "K",
            "history[].opening_m": "m",
            "history[].bolt_tensile_force_sum_N": "N",
            "history[].gasket_compressive_force_sum_N": "N",
            "history[].external_separating_force_N": "N",
            "history[].force_balance_residual_N": "N",
            "history[].equilibrium_tangent_N_m": "N/m",
            "history[].bolts[].extension_m": "m",
            "history[].bolts[].tensile_force_N": "N",
            "history[].bolts[].nominal_tensile_stress_Pa": "Pa",
            "history[].gasket_sectors[].compression_m": "m",
            "history[].gasket_sectors[].contact_gap_m": "m",
            "history[].gasket_sectors[].compressive_force_N": "N",
            "history[].gasket_sectors[].mean_contact_pressure_Pa": "Pa",
            "history[].gasket_sectors[].tangent_stiffness_N_m": "N/m",
        },
        (
            "Every load step uses the same caller bolt preloads/stiffnesses and sector data with its exact temperature-specific interpolated gasket curve.",
            "A single axial opening balances tension-only bolt springs, compression-only gasket sectors and caller separating load at each knot.",
            "The first step must balance initial preload against gasket force at initial compression; thermal shifts and external separating force are caller inputs thereafter.",
        ),
        (
            "caller_gasket_temperature_bracket_loading_curves",
            "caller_bolt_preload_stiffness_and_thermal_free_length",
            "caller_gasket_sector_area_compression_and_thermal_free_thickness",
            "quasi_static_parallel_bolt_gasket_force_equilibrium_with_temperature_curve_transfer",
        ),
        qualification="user_model",
    )]
