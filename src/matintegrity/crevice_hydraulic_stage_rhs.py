"""Pure instantaneous hydraulic RHS for a caller-evidenced planar slit stage."""
from __future__ import annotations

import math
from typing import Literal

from pydantic import Field, model_validator

from .contracts import Calculation, Contract, Evidence, Positive, canonical_digest
from .registry import ModelSpec

MODEL_ID = "corrosion.crevice_hydraulic_stage_rhs"
SOURCE_ID = "caller_evidenced_planar_slit_instantaneous_hydraulic_rhs"


class CreviceHydraulicStageRHSRequest(Contract):
    """One bounded stage evaluation of pressure-driven flow with optional liquid-volume motion."""

    schema_version: Literal["matintegrity.crevice_hydraulic_stage_rhs.v1", "matintegrity.crevice_hydraulic_stage_rhs.v2"] = "matintegrity.crevice_hydraulic_stage_rhs.v1"
    assessment_id: str = Field(min_length=1)
    physical_scope_id: str = Field(min_length=1)
    time_s: float
    signed_volumetric_flow_m3_s: float
    signed_pressure_drop_Pa: float
    cell_ids: tuple[str, ...] = Field(min_length=1, max_length=2000)
    cell_lengths_m: tuple[Positive, ...] = Field(min_length=1, max_length=2000)
    aperture_by_cell_m: tuple[Positive, ...] = Field(min_length=1, max_length=2000)
    cell_volume_rate_m3_s: tuple[float, ...] = Field(default=(), max_length=2000)
    transverse_width_m: Positive
    density_kg_m3: Positive
    dynamic_viscosity_Pa_s: Positive
    resistance_correction_multiplier: Positive = 1.0
    inertance_correction_multiplier: Positive = 1.0
    geometry_provider_id: str = Field(min_length=1)
    geometry_provider_revision: str = Field(min_length=1)
    geometry_record_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    pressure_provider_id: str = Field(min_length=1)
    pressure_provider_revision: str = Field(min_length=1)
    pressure_record_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    fluid_property_provider_id: str = Field(min_length=1)
    fluid_property_provider_revision: str = Field(min_length=1)
    fluid_property_record_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    hydraulic_parameter_fit_result_sha256: str | None = Field(default=None, pattern=r"^[a-f0-9]{64}$")
    evidence: tuple[Evidence, ...] = Field(min_length=3, max_length=256)
    usage_rights_evidence: tuple[Evidence, ...] = Field(min_length=1, max_length=64)
    usage_license_id: str = Field(min_length=1)
    minimum_width_to_aperture_ratio: Positive = Field(default=20.0, ge=20.0, le=1000.0)
    maximum_reviewed_reynolds_number: Positive = Field(default=1000.0, ge=1.0, le=1000.0)
    geometry_and_stage_state_reviewed: bool
    pressure_sign_and_reference_reviewed: bool
    incompressible_newtonian_fluid_reviewed: bool
    laminar_slit_resistance_and_lumped_inertance_reviewed: bool
    correction_factor_applicability_reviewed: bool = False
    usage_rights_reviewed: bool
    computational_use_authorized: bool

    @model_validator(mode="after")
    def validate_stage_evidence_and_support(self):
        if not math.isfinite(self.time_s):
            raise ValueError("stage time must be finite")
        if not math.isfinite(self.signed_volumetric_flow_m3_s):
            raise ValueError("signed stage flow must be finite")
        if not math.isfinite(self.signed_pressure_drop_Pa):
            raise ValueError("signed pressure drop must be finite")
        n = len(self.cell_ids)
        if len(set(self.cell_ids)) != n:
            raise ValueError("ordered cell IDs must be unique")
        if len(self.cell_lengths_m) != n or len(self.aperture_by_cell_m) != n:
            raise ValueError("cell lengths and stage apertures must match cell IDs")
        if self.cell_volume_rate_m3_s and len(self.cell_volume_rate_m3_s) != n:
            raise ValueError("stage volume-rate values must match cell IDs")
        if any(not math.isfinite(value) for value in self.cell_volume_rate_m3_s):
            raise ValueError("stage cell-volume rates must be finite")
        if (self.schema_version == "matintegrity.crevice_hydraulic_stage_rhs.v1"
                and any(value != 0.0 for value in self.cell_volume_rate_m3_s)):
            raise ValueError("nonzero moving-volume rates require the digest-bound v2 schema")
        if n > 2_000:
            raise ValueError("stage cell work budget exceeded")
        geometry_payload = {
            "physical_scope_id": self.physical_scope_id,
            "time_s": float(self.time_s),
            "cell_ids": list(self.cell_ids),
            "cell_lengths_m": [float(x) for x in self.cell_lengths_m],
            "aperture_by_cell_m": [float(x) for x in self.aperture_by_cell_m],
            "transverse_width_m": float(self.transverse_width_m),
        }
        if self.schema_version == "matintegrity.crevice_hydraulic_stage_rhs.v2":
            geometry_payload["cell_volume_rate_m3_s"] = [
                float(value) for value in (self.cell_volume_rate_m3_s or (0.0,) * n)
            ]
        pressure_payload = {
            "physical_scope_id": self.physical_scope_id,
            "time_s": float(self.time_s),
            "signed_pressure_drop_Pa": float(self.signed_pressure_drop_Pa),
        }
        fluid_payload = {
            "density_kg_m3": float(self.density_kg_m3),
            "dynamic_viscosity_Pa_s": float(self.dynamic_viscosity_Pa_s),
        }
        required = (
            (self.geometry_provider_id, self.geometry_record_sha256, canonical_digest(geometry_payload)),
            (self.pressure_provider_id, self.pressure_record_sha256, canonical_digest(pressure_payload)),
            (self.fluid_property_provider_id, self.fluid_property_record_sha256, canonical_digest(fluid_payload)),
        )
        for source_id, declared_sha, actual_sha in required:
            if declared_sha != actual_sha or not any(
                row.source_id == source_id and row.sha256 == declared_sha and row.license_id
                for row in self.evidence
            ):
                raise ValueError("geometry, pressure and fluid provider digests require matching licensed Evidence")
        if not any(row.license_id == self.usage_license_id for row in self.usage_rights_evidence):
            raise ValueError("usage-rights Evidence must identify the declared license or permission basis")
        if self.hydraulic_parameter_fit_result_sha256 is None:
            if (self.resistance_correction_multiplier != 1.0
                    or self.inertance_correction_multiplier != 1.0
                    or self.correction_factor_applicability_reviewed):
                raise ValueError("non-unity correction factors require a pinned fit result")
        elif (not any(row.source_id == "calibration.crevice_slit_hydraulic_law_parameters"
                      and row.sha256 == self.hydraulic_parameter_fit_result_sha256
                      for row in self.evidence)
              or not self.correction_factor_applicability_reviewed):
            raise ValueError("fitted correction factors require matching result Evidence and applicability review")
        if not all((self.geometry_and_stage_state_reviewed,
                    self.pressure_sign_and_reference_reviewed,
                    self.incompressible_newtonian_fluid_reviewed,
                    self.laminar_slit_resistance_and_lumped_inertance_reviewed,
                    self.usage_rights_reviewed,
                    self.computational_use_authorized)):
            raise ValueError("stage geometry, pressure, fluid, law, rights and computational reviews are required")
        if any(float(self.transverse_width_m) / float(gap) < float(self.minimum_width_to_aperture_ratio)
               for gap in self.aperture_by_cell_m):
            raise ValueError("stage aperture is outside reviewed wide-slit aspect-ratio support")
        return self


def evaluate_crevice_hydraulic_stage_rhs(request: CreviceHydraulicStageRHSRequest) -> Calculation:
    """Evaluate pressure-driven flow acceleration with optional moving-volume continuity."""
    digest = canonical_digest(request.model_dump(mode="json"))
    width = float(request.transverse_width_m)
    lengths = tuple(float(x) for x in request.cell_lengths_m)
    apertures = tuple(float(x) for x in request.aperture_by_cell_m)
    try:
        resistance_terms = tuple(
            12.0 * float(request.dynamic_viscosity_Pa_s) * length / (width * gap**3)
            for length, gap in zip(lengths, apertures, strict=True)
        )
        inertance_terms = tuple(
            float(request.density_kg_m3) * length / (width * gap)
            for length, gap in zip(lengths, apertures, strict=True)
        )
        resistance = math.fsum(resistance_terms) * float(request.resistance_correction_multiplier)
        inertance = math.fsum(inertance_terms) * float(request.inertance_correction_multiplier)
        flow = float(request.signed_volumetric_flow_m3_s)
        pressure_drop = float(request.signed_pressure_drop_Pa)
        volume_rates = tuple(float(value) for value in (request.cell_volume_rate_m3_s or (0.0,) * len(apertures)))
        face_flows = [flow]
        for volume_rate in volume_rates:
            face_flows.append(face_flows[-1] - volume_rate)
        cell_mean_flows = tuple(0.5 * (left + right) for left, right in zip(face_flows[:-1], face_flows[1:], strict=True))
        continuity_residuals = tuple(
            face_flows[index] - face_flows[index + 1] - volume_rates[index]
            for index in range(len(volume_rates))
        )
        pressure_resistance = math.fsum(
            resistance_terms[index] * cell_mean_flows[index] for index in range(len(apertures))
        ) * float(request.resistance_correction_multiplier)
        pressure_force = pressure_drop - pressure_resistance
        flow_derivative = (pressure_drop - pressure_resistance) / inertance
        pressure_drop_by_cell = tuple(
            inertance_terms[index] * float(request.inertance_correction_multiplier) * flow_derivative
            + float(request.resistance_correction_multiplier) * resistance_terms[index] * cell_mean_flows[index]
            for index in range(len(apertures))
        )
        pressure_closure_residual = math.fsum(pressure_drop_by_cell) - pressure_drop
        pressure_closure_scale = max(
            abs(pressure_drop), math.fsum(abs(value) for value in pressure_drop_by_cell), 1e-300
        )
        pressure_closure_roundoff_limit = 64.0 * math.ulp(pressure_closure_scale)
        relaxation_rate = resistance / inertance
        zero_inlet_face_flows = [0.0]
        for volume_rate in volume_rates:
            zero_inlet_face_flows.append(zero_inlet_face_flows[-1] - volume_rate)
        zero_inlet_cell_flows = [0.5 * (left + right) for left, right in zip(
            zero_inlet_face_flows[:-1], zero_inlet_face_flows[1:], strict=True
        )]
        resistance_offset = math.fsum(
            resistance_terms[index] * zero_inlet_cell_flows[index] for index in range(len(apertures))
        ) * float(request.resistance_correction_multiplier)
        equilibrium_flow = (pressure_drop - resistance_offset) / resistance
        reynolds_by_cell = tuple(
            2.0 * float(request.density_kg_m3) * abs(cell_flow)
            / (width * float(request.dynamic_viscosity_Pa_s))
            for cell_flow in cell_mean_flows
        )
        reynolds = max(reynolds_by_cell, default=0.0)
        aspect_ratios = tuple(width / aperture for aperture in apertures)
        outputs = (resistance, inertance, pressure_force, flow_derivative, pressure_closure_residual,
                   pressure_closure_roundoff_limit,
                   relaxation_rate, equilibrium_flow, reynolds)
        if any(not math.isfinite(value) for value in outputs):
            raise ArithmeticError("hydraulic stage RHS exceeded finite numeric support")
        if resistance <= 0.0 or inertance <= 0.0:
            raise ArithmeticError("stage resistance and inertance must remain positive")
        if abs(pressure_closure_residual) > pressure_closure_roundoff_limit:
            raise ArithmeticError("stage_series_pressure_closure_failed")
        if reynolds > float(request.maximum_reviewed_reynolds_number):
            return Calculation(status="out_of_scope", values={
                "model_id": MODEL_ID,
                "assessment_id": request.assessment_id,
                "input_sha256": digest,
                "reason": "stage_reynolds_support_exceeded",
                "reynolds_number": reynolds,
                "maximum_reviewed_reynolds_number": float(request.maximum_reviewed_reynolds_number),
                "committed": False,
                "qualification_claimed": False,
            })
        return Calculation(values={
            "model_id": MODEL_ID,
            "assessment_id": request.assessment_id,
            "physical_scope_id": request.physical_scope_id,
            "input_sha256": digest,
            "source_id": SOURCE_ID,
            "time_s": float(request.time_s),
            "signed_volumetric_flow_m3_s": flow,
            "signed_pressure_drop_Pa": pressure_drop,
            "series_resistance_Pa_s_m3": resistance,
            "series_inertance_Pa_s2_m3": inertance,
            "pressure_force_Pa": pressure_force,
            "volumetric_flow_derivative_m3_s2": flow_derivative,
            "momentum_relaxation_rate_s_inv": relaxation_rate,
            "instantaneous_equilibrium_flow_m3_s": equilibrium_flow,
            "cell_resistance_terms_Pa_s_m3": list(resistance_terms),
            "cell_inertance_terms_Pa_s2_m3": list(inertance_terms),
            "cell_volume_rate_m3_s": list(volume_rates),
            "volumetric_flow_by_face_m3_s": face_flows,
            "cell_mean_volumetric_flow_m3_s": list(cell_mean_flows),
            "cell_continuity_residual_m3_s": list(continuity_residuals),
            "cell_pressure_drop_Pa": list(pressure_drop_by_cell),
            "pressure_closure_residual_Pa": pressure_closure_residual,
            "pressure_closure_roundoff_limit_Pa": pressure_closure_roundoff_limit,
            "pressure_closure_closed": abs(pressure_closure_residual) <= pressure_closure_roundoff_limit,
            "stage_aperture_by_cell_m": list(apertures),
            "width_to_aperture_ratio_by_cell": list(aspect_ratios),
            "stage_reynolds_number": reynolds,
            "stage_reynolds_number_by_cell": list(reynolds_by_cell),
            "maximum_reviewed_reynolds_number": float(request.maximum_reviewed_reynolds_number),
            "resistance_correction_multiplier": float(request.resistance_correction_multiplier),
            "inertance_correction_multiplier": float(request.inertance_correction_multiplier),
            "geometry_record_sha256": request.geometry_record_sha256,
            "pressure_record_sha256": request.pressure_record_sha256,
            "fluid_property_record_sha256": request.fluid_property_record_sha256,
            "hydraulic_parameter_fit_result_sha256": request.hydraulic_parameter_fit_result_sha256,
            "evidence_sha256": canonical_digest([row.model_dump(mode="json") for row in request.evidence]),
            "committed": True,
            "qualification_claimed": False,
        }, notes=(
            "The pure stage evaluator returns inlet dQ/dt from the series pressure balance. In schema v2, caller stage volume rates define face-flow differences through incompressible cell continuity.",
            "Dynamic cell volume rates are stage inputs and are not derived here from solid inventory. The evaluator does not integrate flow or couple to a reactive BDF state.",
            "Resistance is the caller-selected wide-slit laminar relation and inertance is a lumped one-dimensional fluid-column approximation, not a Navier-Stokes solution.",
        ))
    except (ArithmeticError, OverflowError, ValueError, ZeroDivisionError) as error:
        return Calculation(status="out_of_scope", values={
            "model_id": MODEL_ID,
            "assessment_id": request.assessment_id,
            "input_sha256": digest,
            "reason": str(error),
            "committed": False,
            "qualification_claimed": False,
        })


def specifications() -> tuple[ModelSpec, ...]:
    return (ModelSpec(
        model_id=MODEL_ID,
        input_type=CreviceHydraulicStageRHSRequest,
        evaluator=evaluate_crevice_hydraulic_stage_rhs,
        units={
            "time_s": "s",
            "signed_volumetric_flow_m3_s": "m^3/s",
            "signed_pressure_drop_Pa": "Pa",
            "series_resistance_Pa_s_m3": "Pa s/m^3",
            "series_inertance_Pa_s2_m3": "Pa s^2/m^3",
            "pressure_force_Pa": "Pa",
            "volumetric_flow_derivative_m3_s2": "m^3/s^2",
            "momentum_relaxation_rate_s_inv": "1/s",
            "instantaneous_equilibrium_flow_m3_s": "m^3/s",
            "cell_resistance_terms_Pa_s_m3[]": "Pa s/m^3",
            "cell_inertance_terms_Pa_s2_m3[]": "Pa s^2/m^3",
            "cell_volume_rate_m3_s[]": "m^3/s",
            "volumetric_flow_by_face_m3_s[]": "m^3/s",
            "cell_mean_volumetric_flow_m3_s[]": "m^3/s",
            "cell_continuity_residual_m3_s[]": "m^3/s",
            "cell_pressure_drop_Pa[]": "Pa",
            "pressure_closure_residual_Pa": "Pa",
            "pressure_closure_roundoff_limit_Pa": "Pa",
            "pressure_closure_closed": "1",
            "stage_aperture_by_cell_m[]": "m",
            "width_to_aperture_ratio_by_cell[]": "1",
            "stage_reynolds_number": "1",
            "stage_reynolds_number_by_cell[]": "1",
        },
        assumptions=(
            "The API evaluates one instantaneous series-slit momentum RHS. Schema v1 retains fixed-volume flow; v2 applies caller digest-bound cell volume rates to incompressible face-flow continuity.",
            "Cell pressure losses use the declared parallel-plate resistance and lumped fluid inertance relations, with cellwise pressure closure returned for inspection.",
            "Stage aperture, volume rate, pressure forcing and fluid properties are caller-provided digest-pinned records; flow integration and reactive BDF coupling remain external.",
            "The declared wide-slit and laminar/Reynolds support must hold in every cell; no pressure-flow law qualification or general flow solution is inferred.",
        ),
        source_ids=(SOURCE_ID,),
        version="0.1.0",
        qualification="user_model",
    ),)
