"""Interpolate caller gasket compression curves between measured temperatures."""

from __future__ import annotations

import math
from typing import Literal

from pydantic import Field, model_validator

from ..contracts import Calculation, Contract, Evidence, Nonnegative, Positive, canonical_digest
from ..registry import ModelSpec

MODEL_ID = "fabrication.gasket_temperature_compression_curve_transfer"


class TemperatureCompressionCurve(Contract):
    specimen_id: str = Field(min_length=1)
    material_condition_id: str = Field(min_length=1)
    loading_branch_id: str = Field(min_length=1)
    temperature_K: Positive
    strain_fraction: tuple[Nonnegative, ...] = Field(min_length=2, max_length=10000)
    compressive_stress_Pa: tuple[Nonnegative, ...] = Field(min_length=2, max_length=10000)
    provider_id: str = Field(min_length=1)
    provider_revision: str = Field(min_length=1)
    record_id: str = Field(min_length=1)
    record_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    usage_license_id: str = Field(min_length=1)
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def increasing_loading_branch(self):
        if len(self.strain_fraction) != len(self.compressive_stress_Pa):
            raise ValueError("strain and stress arrays must align")
        if self.strain_fraction[0] != 0.0 or self.compressive_stress_Pa[0] != 0.0:
            raise ValueError("loading curve must start at zero strain and stress")
        if any(right <= left for left, right in zip(self.strain_fraction, self.strain_fraction[1:])):
            raise ValueError("compression strain knots must increase strictly")
        if any(right <= left for left, right in zip(self.compressive_stress_Pa, self.compressive_stress_Pa[1:])):
            raise ValueError("loading stress knots must increase strictly")
        if not all(math.isfinite(value) for value in (*self.strain_fraction, *self.compressive_stress_Pa, self.temperature_K)):
            raise ValueError("curve values must be finite")
        record = {
            "specimen_id": self.specimen_id,
            "material_condition_id": self.material_condition_id,
            "loading_branch_id": self.loading_branch_id,
            "temperature_K": self.temperature_K,
            "strain_fraction": list(self.strain_fraction),
            "compressive_stress_Pa": list(self.compressive_stress_Pa),
            "provider_id": self.provider_id,
            "provider_revision": self.provider_revision,
            "record_id": self.record_id,
        }
        if canonical_digest(record) != self.record_sha256:
            raise ValueError("temperature compression curve digest does not bind all measured values")
        if not any(
            row.source_id == self.provider_id and row.sha256 == self.record_sha256
            and row.license_id == self.usage_license_id for row in self.evidence
        ):
            raise ValueError("curve Evidence must pin measured data and usage license")
        return self


class GasketTemperatureCompressionCurveTransfer(Contract):
    schema_version: Literal["matintegrity.gasket_temperature_compression_curve_transfer.v1"] = (
        "matintegrity.gasket_temperature_compression_curve_transfer.v1"
    )
    assessment_id: str = Field(min_length=1)
    physical_scope_id: str = Field(min_length=1)
    material_condition_id: str = Field(min_length=1)
    specimen_id: str = Field(min_length=1)
    lower_temperature_curve: TemperatureCompressionCurve
    upper_temperature_curve: TemperatureCompressionCurve
    target_temperature_K: Positive
    loaded_area_m2: Positive
    initial_gasket_thickness_m: Positive
    specimen_geometry_provider_id: str = Field(min_length=1)
    specimen_geometry_provider_revision: str = Field(min_length=1)
    specimen_geometry_record_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    geometry_usage_license_id: str = Field(min_length=1)
    geometry_evidence: tuple[Evidence, ...] = Field(min_length=1)
    same_specimen_and_condition_transfer_reviewed: bool
    same_loading_path_and_strain_grid_reviewed: bool
    linear_temperature_interpolation_reviewed: bool
    no_extrapolation_and_no_time_history_reviewed: bool
    computational_use_authorized: bool

    @model_validator(mode="after")
    def coherent_temperature_bracket(self):
        low, high = self.lower_temperature_curve, self.upper_temperature_curve
        if not low.temperature_K < high.temperature_K:
            raise ValueError("lower and upper curve temperatures must strictly increase")
        if not low.temperature_K <= self.target_temperature_K <= high.temperature_K:
            raise ValueError("target temperature must lie inside the measured temperature bracket")
        if len(low.strain_fraction) != len(high.strain_fraction) or low.strain_fraction != high.strain_fraction:
            raise ValueError("temperature curves must use identical strain knots; regridding is not implicit")
        if (low.specimen_id, low.material_condition_id, low.loading_branch_id) != (
            high.specimen_id, high.material_condition_id, high.loading_branch_id
        ):
            raise ValueError("temperature curves must share specimen, material condition and loading branch")
        if (self.specimen_id, self.material_condition_id) != (low.specimen_id, low.material_condition_id):
            raise ValueError("request specimen/material condition must match both curves")
        if low.provider_id == high.provider_id and low.record_id == high.record_id:
            raise ValueError("temperature endpoints must identify separate measurement records")
        geometry_record = {
            "physical_scope_id": self.physical_scope_id,
            "specimen_id": self.specimen_id,
            "material_condition_id": self.material_condition_id,
            "loaded_area_m2": self.loaded_area_m2,
            "initial_gasket_thickness_m": self.initial_gasket_thickness_m,
            "provider_id": self.specimen_geometry_provider_id,
            "provider_revision": self.specimen_geometry_provider_revision,
        }
        if canonical_digest(geometry_record) != self.specimen_geometry_record_sha256:
            raise ValueError("specimen geometry digest does not bind scope and dimensions")
        if not any(
            row.source_id == self.specimen_geometry_provider_id
            and row.sha256 == self.specimen_geometry_record_sha256
            and row.license_id == self.geometry_usage_license_id
            for row in self.geometry_evidence
        ):
            raise ValueError("geometry Evidence must pin dimensions and their use license")
        return self


def evaluate_gasket_temperature_compression_curve_transfer(
    request: GasketTemperatureCompressionCurveTransfer,
) -> Calculation:
    """Interpolate matched measured loading curves in temperature and report assembly-ready points."""
    digest = canonical_digest(request.model_dump(mode="json"))
    base = {
        "assessment_id": request.assessment_id,
        "physical_scope_id": request.physical_scope_id,
        "material_condition_id": request.material_condition_id,
        "specimen_id": request.specimen_id,
        "target_temperature_K": request.target_temperature_K,
        "lower_curve_sha256": request.lower_temperature_curve.record_sha256,
        "upper_curve_sha256": request.upper_temperature_curve.record_sha256,
        "input_sha256": digest,
        "model_id": MODEL_ID,
    }
    reviews = {
        "same_specimen_and_condition_transfer_reviewed": request.same_specimen_and_condition_transfer_reviewed,
        "same_loading_path_and_strain_grid_reviewed": request.same_loading_path_and_strain_grid_reviewed,
        "linear_temperature_interpolation_reviewed": request.linear_temperature_interpolation_reviewed,
        "no_extrapolation_and_no_time_history_reviewed": request.no_extrapolation_and_no_time_history_reviewed,
        "computational_use_authorized": request.computational_use_authorized,
    }
    missing = [name for name, value in reviews.items() if not value]
    if missing:
        return Calculation(status="needs_data", values=base | {"missing_reviews": missing})
    low, high = request.lower_temperature_curve, request.upper_temperature_curve
    fraction = (request.target_temperature_K - low.temperature_K) / (high.temperature_K - low.temperature_K)
    strains = low.strain_fraction
    stresses = tuple(a + fraction * (b - a) for a, b in zip(low.compressive_stress_Pa, high.compressive_stress_Pa))
    volume = request.loaded_area_m2 * request.initial_gasket_thickness_m
    if not math.isfinite(volume) or volume <= 0 or any(not math.isfinite(value) or value < 0 for value in stresses):
        return Calculation(status="out_of_scope", values=base | {"reason": "interpolated_response_outside_finite_support"})
    points = []
    accumulated_energy_density = 0.0
    for index, (strain, stress) in enumerate(zip(strains, stresses)):
        if index:
            energy_increment = 0.5 * (stresses[index - 1] + stress) * (strain - strains[index - 1])
            accumulated_energy_density += energy_increment
        tangent = None
        if index:
            tangent = (stress - stresses[index - 1]) / (strain - strains[index - 1])
        secant = stress / strain if strain > 0 else None
        force = stress * request.loaded_area_m2
        displacement = strain * request.initial_gasket_thickness_m
        if not all(math.isfinite(value) for value in (
            accumulated_energy_density, force, displacement,
            *(value for value in (tangent, secant) if value is not None),
        )):
            return Calculation(status="out_of_scope", values=base | {
                "reason": "curve_response_or_work_integral_exceeded_finite_support",
                "completed_point_count": len(points),
            })
        points.append({
            "compression_strain_fraction": strain,
            "compressive_stress_Pa": stress,
            "compression_displacement_m": displacement,
            "compression_force_N": force,
            "interval_tangent_modulus_Pa": tangent,
            "secant_modulus_Pa": secant,
            "loading_energy_density_to_point_J_m3": accumulated_energy_density,
        })
    return Calculation(values=base | {
        "temperature_interpolation_fraction": fraction,
        "lower_temperature_K": low.temperature_K,
        "upper_temperature_K": high.temperature_K,
        "strain_point_count": len(points),
        "loading_curve": points,
        "maximum_supported_strain_fraction": strains[-1],
        "maximum_supported_compressive_stress_Pa": stresses[-1],
        "maximum_supported_compression_force_N": points[-1]["compression_force_N"],
        "geometry_record_sha256": request.specimen_geometry_record_sha256,
        "interpolation_basis": "linear_stress_interpolation_at_identical_strain_knots_inside_temperature_bracket",
        "constitutive_law_fitted": False,
    }, notes=(
        "Stress values are linearly interpolated between two caller-measured curves at identical strain knots; no temperature extrapolation is performed.",
        "The resulting force-compression points may be supplied to an assembly solver only after that solver's geometry and curve interpretation checks.",
        "The output is a transferred quasi-static loading branch; unloading, hysteresis, time dependence, thermal expansion, stress relaxation and qualification are not inferred.",
    ))


def specifications() -> list[ModelSpec]:
    return [ModelSpec(
        MODEL_ID,
        GasketTemperatureCompressionCurveTransfer,
        evaluate_gasket_temperature_compression_curve_transfer,
        {
            "loading_curve[].compression_strain_fraction": "1",
            "loading_curve[].compressive_stress_Pa": "Pa",
            "loading_curve[].compression_displacement_m": "m",
            "loading_curve[].compression_force_N": "N",
            "loading_curve[].interval_tangent_modulus_Pa": "Pa",
            "loading_curve[].secant_modulus_Pa": "Pa",
            "loading_curve[].loading_energy_density_to_point_J_m3": "J/m^3",
            "maximum_supported_strain_fraction": "1",
            "maximum_supported_compressive_stress_Pa": "Pa",
            "maximum_supported_compression_force_N": "N",
        },
        (
            "Only caller-supplied monotone loading curves at two temperatures are used, and they must share specimen, material condition, branch and strain knots.",
            "Linear interpolation applies to stress at fixed compression strain inside the measured temperature bracket only.",
            "Area and initial thickness convert target stress-strain points into nominal force-compression points; no temperature-dependent geometry is inferred.",
        ),
        (
            "caller_gasket_temperature_bracket_loading_curves",
            "caller_gasket_specimen_geometry_and_condition",
            "linear_temperature_interpolation_at_fixed_compression_strain",
            "quasi_static_gasket_force_compression_curve_transfer",
        ),
        qualification="user_model",
    )]
