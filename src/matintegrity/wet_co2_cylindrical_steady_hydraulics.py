from __future__ import annotations

import math
import sys
from typing import Literal

from pydantic import Field, model_validator

from .contracts import Calculation, Contract, Evidence, Nonnegative, Positive, canonical_digest
from .registry import ModelSpec
from .wet_co2_cylindrical_scale_geometry import WetCo2CylindricalScaleGeometryHistory

MODEL_ID = "integration.wet_co2_cylindrical_steady_hydraulics"
GEOMETRY_SOURCE_ID = "caller_wet_co2_cylindrical_geometry_result"
FLUID_SOURCE_ID = "caller_single_phase_density_viscosity_roughness_flow_record"
HYDRAULIC_SOURCE_ID = "darcy_weisbach_laminar_colebrook_pipe_flow"
RE_LAMINAR_MAX = 2300.0
RE_TURBULENT_MIN = 4000.0
RELATIVE_ROUGHNESS_MAX = 0.05


class WetCo2CylindricalHydraulicKnot(Contract):
    time_s: Nonnegative
    signed_flow_rate_m3_s: float
    fluid_density_kg_m3: Positive
    dynamic_viscosity_Pa_s: Positive
    absolute_roughness_m: Nonnegative
    record_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    evidence: tuple[Evidence, ...] = Field(min_length=1, max_length=64)

    @model_validator(mode="after")
    def bind_knot_record(self):
        payload = {
            "time_s": self.time_s,
            "signed_flow_rate_m3_s": self.signed_flow_rate_m3_s,
            "fluid_density_kg_m3": self.fluid_density_kg_m3,
            "dynamic_viscosity_Pa_s": self.dynamic_viscosity_Pa_s,
            "absolute_roughness_m": self.absolute_roughness_m,
        }
        if not math.isfinite(self.signed_flow_rate_m3_s):
            raise ValueError("signed flow rate must be finite")
        if canonical_digest(payload) != self.record_sha256:
            raise ValueError("hydraulic input digest must bind exact knot flow and fluid/roughness properties")
        if not any(row.sha256 == self.record_sha256 and row.license_id for row in self.evidence):
            raise ValueError("licensed Evidence must pin each caller hydraulic property record")
        return self


class WetCo2CylindricalSteadyHydraulics(Contract):
    """Single-phase pipe-flow screening at exact evolving cylindrical bore knots."""

    schema_version: Literal["matintegrity.wet_co2_cylindrical_steady_hydraulics.v1"] = (
        "matintegrity.wet_co2_cylindrical_steady_hydraulics.v1"
    )
    assessment_id: str = Field(min_length=1, max_length=160)
    geometry: WetCo2CylindricalScaleGeometryHistory
    geometry_result: Calculation
    knots: tuple[WetCo2CylindricalHydraulicKnot, ...] = Field(min_length=1, max_length=5000)
    laminar_regime_and_single_phase_reviewed: bool
    straight_pipe_and_fully_developed_flow_reviewed: bool
    colebrook_maximum_iterations: int = Field(default=200, ge=10, le=1000)
    colebrook_relative_tolerance: Positive = 1e-10

    @model_validator(mode="after")
    def verify_geometry_binding(self):
        if self.geometry_result.status != "computed":
            raise ValueError("cylindrical geometry result must be computed")
        if self.geometry_result.values.get("model_id") != "degradation.wet_co2_cylindrical_scale_geometry_history":
            raise ValueError("geometry result must come from the cylindrical annular geometry evaluator")
        if self.geometry_result.values.get("input_sha256") != canonical_digest(self.geometry.model_dump(mode="json")):
            raise ValueError("geometry result digest does not bind the supplied geometry request")
        times = tuple(row.time_s for row in self.geometry.history)
        if tuple(row.time_s for row in self.knots) != times:
            raise ValueError("hydraulic knot times must exactly match the geometry history")
        if tuple(float(row["time_s"]) for row in self.geometry_result.values.get("history", [])) != times:
            raise ValueError("computed geometry knots must exactly match the supplied hydraulic records")
        return self


def _colebrook_darcy_friction_factor(reynolds: float, relative_roughness: float,
                                     maximum_iterations: int, tolerance: float) -> tuple[float, int]:
    """Bisection solution of Colebrook-White in Darcy friction-factor form."""
    def residual(factor: float) -> float:
        root = math.sqrt(factor)
        return 1.0 / root + 2.0 * math.log10(relative_roughness / 3.7 + 2.51 / (reynolds * root))

    low, high = 0.004, 0.25
    f_low, f_high = residual(low), residual(high)
    if not math.isfinite(f_low) or not math.isfinite(f_high) or f_low * f_high >= 0.0:
        raise ArithmeticError("Colebrook root is not bracketed in the supported friction-factor interval")
    for iteration in range(1, maximum_iterations + 1):
        middle = 0.5 * (low + high)
        f_middle = residual(middle)
        if not math.isfinite(f_middle):
            raise ArithmeticError("Colebrook residual left finite numeric support")
        if abs(f_middle) <= tolerance or (high - low) <= tolerance * max(middle, 1e-12):
            return middle, iteration
        if f_low * f_middle > 0.0:
            low, f_low = middle, f_middle
        else:
            high, f_high = middle, f_middle
    raise ArithmeticError("Colebrook solver exceeded the caller iteration budget")


def evaluate_wet_co2_cylindrical_steady_hydraulics(
    request: WetCo2CylindricalSteadyHydraulics,
) -> Calculation:
    """Calculate pressure-loss, regime and wall-shear descriptors for single-phase pipe flow."""
    geometry_values = request.geometry_result.values
    geometry_rows = geometry_values["history"]
    base = {
        "assessment_id": request.assessment_id,
        "asset_id": request.geometry.asset_id,
        "location_id": request.geometry.location_id,
        "model_id": MODEL_ID,
        "geometry_result_sha256": canonical_digest(request.geometry_result.model_dump(mode="json")),
        "input_sha256": canonical_digest(request.model_dump(mode="json")),
        "source_ids": [GEOMETRY_SOURCE_ID, FLUID_SOURCE_ID, HYDRAULIC_SOURCE_ID],
    }
    missing_reviews = [name for name in (
        "laminar_regime_and_single_phase_reviewed", "straight_pipe_and_fully_developed_flow_reviewed",
    ) if not getattr(request, name)]
    if missing_reviews:
        return Calculation(status="needs_data", values=base | {
            "reason": "single_phase_and_fully_developed_pipe_flow_review_required",
            "missing_reviews": missing_reviews,
        })
    length = request.geometry.segment_length_m
    output = []
    for index, (geometry_row, knot) in enumerate(zip(geometry_rows, request.knots, strict=True)):
        radius = float(geometry_row["bore_radius_m"])
        diameter = 2.0 * radius
        area = math.pi * radius * radius
        velocity = knot.signed_flow_rate_m3_s / area
        reynolds = knot.fluid_density_kg_m3 * abs(velocity) * diameter / knot.dynamic_viscosity_Pa_s
        if not all(math.isfinite(value) for value in (radius, diameter, area, velocity, reynolds)) or radius <= 0.0:
            return Calculation(status="out_of_scope", values=base | {
                "reason": "bore_flow_state_outside_finite_support",
                "failed_knot_index": index,
            })
        relative_roughness = knot.absolute_roughness_m / diameter
        if relative_roughness > RELATIVE_ROUGHNESS_MAX:
            return Calculation(status="out_of_scope", values=base | {
                "reason": "relative_roughness_exceeds_declared_colebrook_support",
                "failed_knot_index": index,
                "relative_roughness": relative_roughness,
                "supported_maximum": RELATIVE_ROUGHNESS_MAX,
                "completed_prefix_knot_count": len(output),
            })
        if reynolds == 0.0:
            regime = "zero_flow"
            friction = 0.0
            iterations = 0
        elif reynolds <= RE_LAMINAR_MAX:
            regime = "laminar"
            friction = 64.0 / reynolds
            iterations = 0
        elif reynolds < RE_TURBULENT_MIN:
            return Calculation(status="out_of_scope", values=base | {
                "reason": "transitional_reynolds_regime_not_modeled",
                "failed_knot_index": index,
                "completed_prefix_knot_count": len(output),
                "reynolds_number": reynolds,
                "transition_interval": [RE_LAMINAR_MAX, RE_TURBULENT_MIN],
            })
        else:
            regime = "turbulent_colebrook_white"
            try:
                friction, iterations = _colebrook_darcy_friction_factor(
                    reynolds, relative_roughness, request.colebrook_maximum_iterations,
                    request.colebrook_relative_tolerance,
                )
            except ArithmeticError as exc:
                return Calculation(status="out_of_scope", values=base | {
                    "reason": "colebrook_white_solution_failed_closed",
                    "failed_knot_index": index,
                    "completed_prefix_knot_count": len(output),
                    "detail": str(exc),
                })
        pressure_drop_magnitude = friction * (length / diameter) * knot.fluid_density_kg_m3 * velocity * velocity / 2.0
        sign = 0.0 if knot.signed_flow_rate_m3_s == 0.0 else math.copysign(1.0, knot.signed_flow_rate_m3_s)
        signed_pressure_drop = sign * pressure_drop_magnitude
        signed_wall_shear = sign * friction * knot.fluid_density_kg_m3 * velocity * velocity / 8.0
        values = (friction, pressure_drop_magnitude, signed_pressure_drop, signed_wall_shear)
        if not all(math.isfinite(value) for value in values):
            return Calculation(status="out_of_scope", values=base | {
                "reason": "hydraulic_output_outside_finite_support",
                "failed_knot_index": index,
                "completed_prefix_knot_count": len(output),
            })
        output.append({
            "time_s": knot.time_s,
            "bore_radius_m": radius,
            "bore_diameter_m": diameter,
            "flow_area_m2": area,
            "signed_flow_rate_m3_s": knot.signed_flow_rate_m3_s,
            "signed_mean_velocity_m_s": velocity,
            "fluid_density_kg_m3": knot.fluid_density_kg_m3,
            "dynamic_viscosity_Pa_s": knot.dynamic_viscosity_Pa_s,
            "absolute_roughness_m": knot.absolute_roughness_m,
            "relative_roughness": relative_roughness,
            "reynolds_number": reynolds,
            "flow_regime": regime,
            "darcy_friction_factor": friction,
            "colebrook_iterations": iterations,
            "signed_pressure_drop_Pa": signed_pressure_drop,
            "signed_wall_shear_stress_Pa": signed_wall_shear,
            "wall_shear_stress_magnitude_Pa": abs(signed_wall_shear),
            "hydraulic_parameter_record_sha256": knot.record_sha256,
        })
    return Calculation(values=base | {
        "status": "computed",
        "knot_count": len(output),
        "flow_model": "single_phase_fully_developed_darcy_weisbach.v1",
        "history": output,
        "limitations": [
            "Density, viscosity, roughness and signed volumetric flow are caller-supplied at each geometry knot.",
            "Laminar flow uses Darcy f=64/Re; turbulent flow uses the implicit Colebrook-White equation for the declared roughness.",
            "The transition interval 2300<Re<4000 is unsupported and fails closed; multiphase CO2/water/gas flow is not represented.",
            "Straight fully developed single-phase flow is assumed; fittings, elevation, acceleration, compressibility, heat transfer and transient momentum are omitted.",
            "Wall shear is a section-average descriptor, not a scale adhesion or corrosion law. No roughness evolution or hydraulic feedback is performed.",
        ],
    })


def specifications() -> list[ModelSpec]:
    return [ModelSpec(
        model_id=MODEL_ID,
        input_type=WetCo2CylindricalSteadyHydraulics,
        evaluator=evaluate_wet_co2_cylindrical_steady_hydraulics,
        units={
            "history[].signed_flow_rate_m3_s": "m^3/s",
            "history[].signed_mean_velocity_m_s": "m/s",
            "history[].reynolds_number": "1",
            "history[].darcy_friction_factor": "1",
            "history[].signed_pressure_drop_Pa": "Pa",
            "history[].signed_wall_shear_stress_Pa": "Pa",
        },
        assumptions=(
            "The circular bore is represented by the exact area and wetted perimeter of the supplied geometry history.",
            "Flow is single phase, steady at each exact geometry knot and fully developed along a straight segment.",
            "Colebrook-White is solved only in turbulent support; the transitional regime is not interpolated.",
        ),
        source_ids=(GEOMETRY_SOURCE_ID, FLUID_SOURCE_ID, HYDRAULIC_SOURCE_ID),
        qualification="user_model",
    )]

