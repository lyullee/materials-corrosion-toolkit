from __future__ import annotations

import math
from typing import Literal

from pydantic import Field, model_validator

from .contracts import Calculation, Contract, Evidence, Positive, canonical_digest
from .registry import ModelSpec
from .wet_co2_cylindrical_scale_geometry import WetCo2CylindricalScaleGeometryHistory
from .wet_co2_liquid_side_mass_transfer import (
    DEFAULT_FRICTION_EXPONENT,
    WetCo2LiquidSideMassTransferRequest,
    evaluate_wet_co2_liquid_side_mass_transfer,
)

MODEL_ID = "integration.wet_co2_cylindrical_liquid_transfer_capacity_history"
HYDRAULICS_MODEL_ID = "integration.wet_co2_cylindrical_steady_hydraulics"
CORRELATION_MODEL_ID = "degradation.wet_co2_liquid_side_mass_transfer"
HYDRAULICS_SOURCE_ID = "caller_cylindrical_steady_hydraulics_result"
DIFFUSIVITY_SOURCE_ID = "caller_liquid_species_diffusivity_record"
AREA_SOURCE_ID = "caller_cylindrical_segment_wetted_area_geometry"
CORRELATION_SOURCE_ID = "registered_liquid_side_mass_transfer_correlation"


class WetCo2CylindricalLiquidDiffusivityKnot(Contract):
    time_s: float = Field(ge=0.0)
    species_id: str = Field(min_length=1, max_length=160)
    diffusivity_m2_s: Positive
    record_id: str = Field(min_length=1, max_length=160)
    record_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    evidence: tuple[Evidence, ...] = Field(min_length=1, max_length=64)

    @model_validator(mode="after")
    def bind_diffusivity_record(self):
        payload = {"time_s": self.time_s, "species_id": self.species_id,
                   "diffusivity_m2_s": self.diffusivity_m2_s}
        if canonical_digest(payload) != self.record_sha256:
            raise ValueError("diffusivity record digest must bind the exact knot/species/value")
        if not any(row.source_id == self.record_id and row.sha256 == self.record_sha256 and row.license_id
                   for row in self.evidence):
            raise ValueError("licensed Evidence must pin the declared diffusivity source record")
        return self


class WetCo2CylindricalLiquidTransferCapacityHistory(Contract):
    """Compose cylindrical single-phase hydraulics with an existing pointwise liquid transfer correlation."""

    schema_version: Literal["matintegrity.wet_co2_cylindrical_liquid_transfer_capacity_history.v1"] = (
        "matintegrity.wet_co2_cylindrical_liquid_transfer_capacity_history.v1"
    )
    assessment_id: str = Field(min_length=1, max_length=160)
    physical_scope_id: str = Field(min_length=1, max_length=160)
    condition_id: str = Field(min_length=1, max_length=160)
    species_id: str = Field(min_length=1, max_length=160)
    geometry: WetCo2CylindricalScaleGeometryHistory
    geometry_result: Calculation
    hydraulics_result: Calculation
    hydraulics_evidence: Evidence
    diffusivity_history: tuple[WetCo2CylindricalLiquidDiffusivityKnot, ...] = Field(min_length=1, max_length=5000)
    friction_exponent: float = Field(default=DEFAULT_FRICTION_EXPONENT, ge=0.5, le=1.0)
    single_phase_pipe_region_reviewed: bool
    provider_state_and_time_alignment_reviewed: bool
    turbulent_flow_and_local_shear_reviewed: bool
    property_species_temperature_solvent_match_reviewed: bool
    area_basis_and_left_held_integration_reviewed: bool
    correlation_scope_and_exponent_reviewed: bool
    schmidt_extrapolation_reviewed: bool = False

    @model_validator(mode="after")
    def bind_history_sources(self):
        if self.geometry_result.status != "computed" or self.hydraulics_result.status != "computed":
            raise ValueError("geometry and cylindrical hydraulics results must be computed")
        if self.geometry_result.values.get("model_id") != "degradation.wet_co2_cylindrical_scale_geometry_history":
            raise ValueError("geometry result must come from the cylindrical geometry evaluator")
        if self.hydraulics_result.values.get("model_id") != HYDRAULICS_MODEL_ID:
            raise ValueError("hydraulics result must come from the cylindrical steady hydraulics evaluator")
        if self.geometry_result.values.get("input_sha256") != canonical_digest(self.geometry.model_dump(mode="json")):
            raise ValueError("geometry result must bind the supplied geometry input")
        hydraulic_digest = canonical_digest(self.hydraulics_result.model_dump(mode="json"))
        if (self.hydraulics_evidence.source_id != HYDRAULICS_MODEL_ID
                or self.hydraulics_evidence.sha256 != hydraulic_digest or not self.hydraulics_evidence.license_id):
            raise ValueError("licensed Evidence must bind the exact hydraulic result")
        if self.hydraulics_result.values.get("geometry_result_sha256") != canonical_digest(
            self.geometry_result.model_dump(mode="json")
        ):
            raise ValueError("hydraulics and transfer request must use the same geometry result")
        if (self.hydraulics_result.values.get("assessment_id") != self.assessment_id
                or self.hydraulics_result.values.get("asset_id") != self.geometry.asset_id
                or self.hydraulics_result.values.get("location_id") != self.geometry.location_id):
            raise ValueError("hydraulic, geometry, assessment and asset/location scopes must match")
        geometry_times = tuple(row.time_s for row in self.geometry.history)
        hydraulic_rows = self.hydraulics_result.values.get("history", [])
        if tuple(float(row["time_s"]) for row in hydraulic_rows) != geometry_times:
            raise ValueError("hydraulic and geometry knots must match exactly")
        if tuple(float(row["time_s"]) for row in self.geometry_result.values.get("history", [])) != geometry_times:
            raise ValueError("geometry result knots must match exactly")
        if tuple(row.time_s for row in self.diffusivity_history) != geometry_times:
            raise ValueError("species diffusivity records must cover every exact knot in geometry order")
        if any(row.species_id != self.species_id for row in self.diffusivity_history):
            raise ValueError("diffusivity history must contain only the requested corrosive species")
        return self


def evaluate_wet_co2_cylindrical_liquid_transfer_capacity_history(
    request: WetCo2CylindricalLiquidTransferCapacityHistory,
) -> Calculation:
    """Calculate per-knot kL and integrate segment transfer conductance on left-held intervals."""
    hydraulic_rows = request.hydraulics_result.values["history"]
    geometry_rows = request.geometry_result.values["history"]
    hydraulic_digest = canonical_digest(request.hydraulics_result.model_dump(mode="json"))
    geometry_digest = canonical_digest(request.geometry_result.model_dump(mode="json"))
    base = {
        "assessment_id": request.assessment_id,
        "asset_id": request.geometry.asset_id,
        "location_id": request.geometry.location_id,
        "physical_scope_id": request.physical_scope_id,
        "condition_id": request.condition_id,
        "model_id": MODEL_ID,
        "geometry_result_sha256": geometry_digest,
        "hydraulics_result_sha256": hydraulic_digest,
        "input_sha256": canonical_digest(request.model_dump(mode="json")),
        "source_ids": [HYDRAULICS_SOURCE_ID, DIFFUSIVITY_SOURCE_ID, AREA_SOURCE_ID, CORRELATION_SOURCE_ID],
    }
    reviews = (
        "single_phase_pipe_region_reviewed", "provider_state_and_time_alignment_reviewed",
        "turbulent_flow_and_local_shear_reviewed", "property_species_temperature_solvent_match_reviewed",
        "area_basis_and_left_held_integration_reviewed", "correlation_scope_and_exponent_reviewed",
    )
    missing = [name for name in reviews if not getattr(request, name)]
    if missing:
        return Calculation(status="needs_data", values=base | {
            "reason": "liquid_transfer_mapping_and_integration_review_required",
            "missing_reviews": missing,
        })
    output = []
    cumulative_exposure = 0.0
    segment_length = request.geometry.segment_length_m
    for index, (hydraulic, geom, diffusivity) in enumerate(zip(
        hydraulic_rows, geometry_rows, request.diffusivity_history, strict=True
    )):
        velocity = float(hydraulic["signed_mean_velocity_m_s"])
        shear = float(hydraulic["wall_shear_stress_magnitude_Pa"])
        if velocity <= 0.0 or shear <= 0.0:
            return Calculation(status="out_of_scope", values=base | {
                "reason": "liquid_side_correlation_requires_positive_forward_turbulent_pipe_flow",
                "failed_knot_index": index,
                "signed_mean_velocity_m_s": velocity,
                "wall_shear_stress_magnitude_Pa": shear,
                "completed_prefix_knot_count": len(output),
            })
        density = float(hydraulic["fluid_density_kg_m3"])
        viscosity = float(hydraulic["dynamic_viscosity_Pa_s"])
        diameter = float(hydraulic["bore_diameter_m"])
        area = float(geom["bore_wetted_perimeter_m"]) * segment_length
        hydro_config_digest = str(request.hydraulics_result.values["input_sha256"])
        hydro_record = hydraulic.get("hydraulic_parameter_record_sha256")
        if not hydro_record:
            return Calculation(status="needs_data", values=base | {
                "reason": "hydraulic_knot_source_record_digest_missing",
                "failed_knot_index": index,
                "completed_prefix_knot_count": len(output),
            })
        evidence = (
            request.hydraulics_evidence,
            diffusivity.evidence[0],
        )
        corr_request = WetCo2LiquidSideMassTransferRequest(
            assessment_id=request.assessment_id,
            asset_id=request.geometry.asset_id,
            location_id=request.geometry.location_id,
            physical_scope_id=request.physical_scope_id,
            condition_id=request.condition_id,
            time_s=diffusivity.time_s,
            liquid_flow_region="single_phase_pipe",
            liquid_mean_velocity_m_s=velocity,
            liquid_wall_shear_stress_Pa=shear,
            liquid_density_kg_m3=density,
            liquid_dynamic_viscosity_Pa_s=viscosity,
            corrosive_species_diffusivity_m2_s=diffusivity.diffusivity_m2_s,
            hydraulic_diameter_m=diameter,
            friction_exponent=request.friction_exponent,
            hydrodynamic_provider_id=HYDRAULICS_MODEL_ID,
            hydrodynamic_provider_revision="caller_result_bound",
            hydrodynamic_configuration_sha256=hydro_config_digest,
            hydrodynamic_result_sha256=hydraulic_digest,
            diffusivity_record_id=diffusivity.record_id,
            diffusivity_record_sha256=diffusivity.record_sha256,
            evidence=evidence,
            provider_state_and_time_alignment_reviewed=request.provider_state_and_time_alignment_reviewed,
            liquid_wetting_and_wall_area_basis_reviewed=request.area_basis_and_left_held_integration_reviewed,
            turbulent_flow_and_local_shear_reviewed=request.turbulent_flow_and_local_shear_reviewed,
            diffusivity_species_temperature_and_solvent_match_reviewed=request.property_species_temperature_solvent_match_reviewed,
            friction_exponent_and_scope_reviewed=request.correlation_scope_and_exponent_reviewed,
            outside_published_schmidt_range_reviewed=request.schmidt_extrapolation_reviewed,
        )
        correlation = evaluate_wet_co2_liquid_side_mass_transfer(corr_request)
        if correlation.status != "computed":
            return Calculation(status=correlation.status, values=base | {
                "reason": "registered_pointwise_liquid_transfer_correlation_not_computed",
                "failed_knot_index": index,
                "completed_prefix_knot_count": len(output),
                "correlation_result": correlation.model_dump(mode="json"),
            })
        km = float(correlation.values["liquid_side_mass_transfer_coefficient_m_s"])
        conductance = km * area
        exposure = 0.0
        if index < len(hydraulic_rows) - 1:
            dt = float(hydraulic_rows[index + 1]["time_s"]) - float(hydraulic["time_s"])
            exposure = conductance * dt
            if not math.isfinite(exposure) or exposure < 0.0:
                return Calculation(status="out_of_scope", values=base | {
                    "reason": "integrated_segment_transfer_exposure_outside_finite_support",
                    "failed_knot_index": index,
                    "completed_prefix_knot_count": len(output),
                })
            cumulative_exposure += exposure
        output.append({
            "time_s": float(hydraulic["time_s"]),
            "species_id": request.species_id,
            "bore_diameter_m": diameter,
            "segment_wall_area_m2": area,
            "liquid_side_mass_transfer_coefficient_m_s": km,
            "segment_transfer_conductance_m3_s": conductance,
            "interval_left_held_duration_s": (float(hydraulic_rows[index + 1]["time_s"]) - float(hydraulic["time_s"]))
                                               if index < len(hydraulic_rows) - 1 else 0.0,
            "interval_transfer_exposure_m3": exposure,
            "cumulative_transfer_exposure_m3": cumulative_exposure,
            "correlation_result_sha256": canonical_digest(correlation.model_dump(mode="json")),
            "hydraulic_parameter_record_sha256": hydro_record,
            "diffusivity_record_sha256": diffusivity.record_sha256,
        })
    return Calculation(values=base | {
        "status": "computed",
        "species_id": request.species_id,
        "knot_count": len(output),
        "interval_integration": "left_held_kL_times_exact_bore_wetted_area.v1",
        "history": output,
        "interpretation_boundary": "The integrated value is conductance exposure with units of volume; concentration driving force is not supplied, so mass transfer is not integrated.",
        "limitations": [
            "The registered pointwise liquid-side correlation remains the sole correlation; this adapter adds exact geometry history and segment area integration only.",
            "The correlation requires positive forward turbulent single-phase pipe flow and its own Reynolds/Schmidt support; no extrapolation is introduced.",
            "Liquid density and viscosity are reused from the caller hydraulic record; species diffusivity is caller supplied at every exact knot with Evidence.",
            "The segment is treated as fully wetted over its entire cylindrical perimeter. Gas/liquid flow pattern, partial wetting, reactive consumption, speciation and corrosion rate are not inferred.",
            "Interval kL and area are held at the left knot. No temporal interpolation or within-interval hydraulic feedback is performed.",
        ],
    })


def specifications() -> list[ModelSpec]:
    return [ModelSpec(
        model_id=MODEL_ID,
        input_type=WetCo2CylindricalLiquidTransferCapacityHistory,
        evaluator=evaluate_wet_co2_cylindrical_liquid_transfer_capacity_history,
        units={
            "history[].segment_wall_area_m2": "m^2",
            "history[].liquid_side_mass_transfer_coefficient_m_s": "m/s",
            "history[].segment_transfer_conductance_m3_s": "m^3/s",
            "history[].interval_transfer_exposure_m3": "m^3",
            "history[].cumulative_transfer_exposure_m3": "m^3",
        },
        assumptions=(
            "The existing pointwise liquid-side mass-transfer correlation is evaluated at each exact cylindrical hydraulics knot.",
            "The entire bore perimeter and segment length are treated as wetted area.",
            "The interval conductance exposure uses left-held transfer coefficient and area; no concentration driving force is assumed.",
        ),
        source_ids=(HYDRAULICS_SOURCE_ID, DIFFUSIVITY_SOURCE_ID, AREA_SOURCE_ID, CORRELATION_SOURCE_ID),
        qualification="user_model",
    )]



