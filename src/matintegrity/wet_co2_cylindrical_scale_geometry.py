"""Reconstruct cylindrical pipe geometry from caller-owned wall/scale inventories."""

from __future__ import annotations

import math
from typing import Literal

from pydantic import Field, model_validator

from .contracts import Calculation, Contract, Evidence, Nonnegative, Positive, canonical_digest
from .registry import ModelSpec

MODEL_ID = "degradation.wet_co2_cylindrical_scale_geometry_history"
GEOMETRY_SOURCE_ID = "caller_wet_co2_initial_cylindrical_pipe_geometry"
HISTORY_SOURCE_ID = "caller_wet_co2_wall_recession_and_scale_phase_inventory_history"
PHASE_SOURCE_ID = "caller_wet_co2_scale_phase_molar_volume"


class WetCo2CylindricalScalePhase(Contract):
    phase_id: str = Field(min_length=1, max_length=160)
    molar_volume_m3_mol: Positive
    provider_id: str = Field(min_length=1, max_length=160)
    provider_revision: str = Field(min_length=1, max_length=160)
    source_record_id: str = Field(min_length=1, max_length=160)
    evidence: Evidence

    @model_validator(mode="after")
    def phase_evidence_matches_provider(self):
        if self.evidence.source_id != self.provider_id or not self.evidence.sha256 or not self.evidence.license_id:
            raise ValueError("scale phase Evidence must pin its provider, content digest and usage license")
        return self


class WetCo2ScalePhaseLineInventory(Contract):
    phase_id: str = Field(min_length=1, max_length=160)
    moles_per_axial_metre_mol_m: Nonnegative


class WetCo2CylindricalGeometryKnot(Contract):
    time_s: Nonnegative
    wall_recession_m: Nonnegative
    phase_inventories: tuple[WetCo2ScalePhaseLineInventory, ...] = Field(min_length=1, max_length=32)


class WetCo2CylindricalScaleGeometryHistory(Contract):
    """Map lineal phase inventory into an axisymmetric cylindrical bore at exact knots."""

    schema_version: Literal["matintegrity.wet_co2_cylindrical_scale_geometry_history.v1"] = (
        "matintegrity.wet_co2_cylindrical_scale_geometry_history.v1"
    )
    assessment_id: str = Field(min_length=1, max_length=160)
    asset_id: str = Field(min_length=1, max_length=160)
    location_id: str = Field(min_length=1, max_length=160)
    time_basis_id: str = Field(min_length=1, max_length=160)
    outer_radius_m: Positive
    initial_inner_radius_m: Positive
    initial_wall_thickness_m: Positive
    segment_length_m: Positive
    geometry_provider_id: str = Field(min_length=1, max_length=160)
    geometry_provider_revision: str = Field(min_length=1, max_length=160)
    geometry_record_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    geometry_evidence: Evidence
    history_provider_id: str = Field(min_length=1, max_length=160)
    history_provider_revision: str = Field(min_length=1, max_length=160)
    history_record_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    history_evidence: Evidence
    phases: tuple[WetCo2CylindricalScalePhase, ...] = Field(min_length=1, max_length=32)
    history: tuple[WetCo2CylindricalGeometryKnot, ...] = Field(min_length=1, max_length=10000)
    axisymmetric_uniformity_reviewed: bool
    phase_inventory_reference_basis_reviewed: bool

    @model_validator(mode="after")
    def check_identity_and_lineage(self):
        if not math.isclose(
            self.outer_radius_m - self.initial_inner_radius_m,
            self.initial_wall_thickness_m,
            rel_tol=1e-10,
            abs_tol=1e-12,
        ):
            raise ValueError("initial inner/outer radii must agree with the declared wall thickness")
        geometry = {
            "asset_id": self.asset_id,
            "location_id": self.location_id,
            "outer_radius_m": self.outer_radius_m,
            "initial_inner_radius_m": self.initial_inner_radius_m,
            "initial_wall_thickness_m": self.initial_wall_thickness_m,
            "segment_length_m": self.segment_length_m,
            "provider_id": self.geometry_provider_id,
            "provider_revision": self.geometry_provider_revision,
        }
        if canonical_digest(geometry) != self.geometry_record_sha256:
            raise ValueError("geometry digest must bind the exact initial dimensions and provider revision")
        if (self.geometry_evidence.source_id != self.geometry_provider_id
                or self.geometry_evidence.sha256 != self.geometry_record_sha256
                or not self.geometry_evidence.license_id):
            raise ValueError("geometry Evidence must pin the dimension record and usage license")
        rows = [row.model_dump(mode="json") for row in self.history]
        if canonical_digest(rows) != self.history_record_sha256:
            raise ValueError("history digest must bind the ordered caller-provided knots")
        if (self.history_evidence.source_id != self.history_provider_id
                or self.history_evidence.sha256 != self.history_record_sha256
                or not self.history_evidence.license_id):
            raise ValueError("history Evidence must pin the ordered geometry history and usage license")
        if not self.history or self.history[0].time_s != 0.0:
            raise ValueError("geometry history must start at elapsed time zero")
        if any(right.time_s <= left.time_s for left, right in zip(self.history, self.history[1:])):
            raise ValueError("geometry history times must strictly increase")
        phase_ids = [row.phase_id for row in self.phases]
        if len(phase_ids) != len(set(phase_ids)):
            raise ValueError("scale phase IDs must be unique")
        prior_recession = -math.inf
        expected = set(phase_ids)
        for knot in self.history:
            if knot.wall_recession_m < prior_recession:
                raise ValueError("wall recession history must be nondecreasing")
            prior_recession = knot.wall_recession_m
            ids = [row.phase_id for row in knot.phase_inventories]
            if set(ids) != expected or len(ids) != len(set(ids)):
                raise ValueError("every geometry knot must provide exactly one inventory for each declared phase")
        return self


def evaluate_wet_co2_cylindrical_scale_geometry_history(
    request: WetCo2CylindricalScaleGeometryHistory,
) -> Calculation:
    """Apply exact annular geometry identities to caller-supplied recession and phase inventories."""
    digest = canonical_digest(request.model_dump(mode="json"))
    base = {
        "assessment_id": request.assessment_id,
        "asset_id": request.asset_id,
        "location_id": request.location_id,
        "time_basis_id": request.time_basis_id,
        "model_id": MODEL_ID,
        "input_sha256": digest,
        "geometry_record_sha256": request.geometry_record_sha256,
        "history_record_sha256": request.history_record_sha256,
        "geometry_basis": "axisymmetric_uniform_cylindrical_annulus_exact_volume_mapping.v1",
    }
    missing = [key for key in ("axisymmetric_uniformity_reviewed", "phase_inventory_reference_basis_reviewed")
               if not getattr(request, key)]
    if missing:
        return Calculation(status="needs_data", values=base | {
            "reason": "reviewed_axisymmetry_and_inventory_reference_basis_required",
            "missing_reviews": missing,
        })
    phases = {row.phase_id: row for row in request.phases}
    outer = request.outer_radius_m
    base_inner = request.initial_inner_radius_m
    length = request.segment_length_m
    states = []
    for index, knot in enumerate(request.history):
        steel_inner = base_inner + knot.wall_recession_m
        wall_remaining = outer - steel_inner
        inventory = {row.phase_id: row.moles_per_axial_metre_mol_m for row in knot.phase_inventories}
        phase_volume_per_length = {
            phase_id: inventory[phase_id] * phases[phase_id].molar_volume_m3_mol
            for phase_id in phases
        }
        try:
            scale_volume_per_length = math.fsum(phase_volume_per_length.values())
            bore_radius_sq = steel_inner * steel_inner - scale_volume_per_length / math.pi
            bore_radius = math.sqrt(bore_radius_sq) if bore_radius_sq > 0.0 else math.nan
        except (ArithmeticError, OverflowError, ValueError):
            bore_radius = math.nan
            scale_volume_per_length = math.inf
        if (not all(math.isfinite(value) for value in (steel_inner, wall_remaining,
                                                        scale_volume_per_length, bore_radius))
                or wall_remaining <= 0.0 or bore_radius <= 0.0 or bore_radius > steel_inner):
            return Calculation(status="out_of_scope", values=base | {
                "reason": "cylindrical_wall_or_scale_inventory_exceeds_supported_geometry",
                "completed_knot_count": len(states),
                "failed_knot_index": index,
                "failed_time_s": knot.time_s,
                "wall_remaining_m": wall_remaining if math.isfinite(wall_remaining) else None,
                "scale_volume_per_axial_metre_m2": scale_volume_per_length if math.isfinite(scale_volume_per_length) else None,
            })
        bore_area = math.pi * bore_radius * bore_radius
        steel_area = math.pi * (outer * outer - steel_inner * steel_inner)
        scale_thickness = steel_inner - bore_radius
        wetted_perimeter = 2.0 * math.pi * bore_radius
        phase_volumes = {phase_id: phase_volume_per_length[phase_id] * length for phase_id in phases}
        total_scale_volume = scale_volume_per_length * length
        if not all(math.isfinite(value) and value >= 0.0 for value in (
            bore_area, steel_area, scale_thickness, wetted_perimeter, total_scale_volume, *phase_volumes.values()
        )):
            return Calculation(status="out_of_scope", values=base | {
                "reason": "cylindrical_geometry_outputs_outside_finite_support",
                "completed_knot_count": len(states),
                "failed_knot_index": index,
            })
        states.append({
            "time_s": knot.time_s,
            "wall_recession_m": knot.wall_recession_m,
            "wall_remaining_m": wall_remaining,
            "steel_inner_radius_m": steel_inner,
            "scale_thickness_equivalent_m": scale_thickness,
            "bore_radius_m": bore_radius,
            "bore_flow_area_m2": bore_area,
            "bore_wetted_perimeter_m": wetted_perimeter,
            "steel_cross_section_area_m2": steel_area,
            "scale_volume_m3": total_scale_volume,
            "scale_volume_per_axial_metre_m2": scale_volume_per_length,
            "scale_phase_volume_m3_by_phase": {
                phase_id: phase_volumes[phase_id] for phase_id in phases
            },
            "phase_inventory_mol_m_by_phase": inventory,
        })
    return Calculation(values=base | {
        "status": "computed",
        "knot_count": len(states),
        "outer_radius_m": outer,
        "segment_length_m": length,
        "history": states,
        "limitations": [
            "The caller supplies metal recession and every solid-phase molar inventory; no wet-CO2 chemistry or electrochemistry is solved.",
            "The geometry assumes a circular tube with uniform circumferential recession and a fully dense, axisymmetric scale annulus.",
            "Phase inventories are summed by volume; radial phase ordering, porosity, cracking, spallation, roughness, flow, and pressure loss are not modeled.",
            "Only exact supplied knots are evaluated; no interpolation, time integration, corrosion rate, life, probability, acceptance, or qualification is inferred.",
        ],
    }, notes=(
        "Cylindrical scale thickness is reconstructed from the exact annular-volume balance, not a planar thickness approximation.",
        "Results are geometry handoff quantities for caller review and do not feed transport or corrosion kinetics automatically.",
    ))


def specifications() -> list[ModelSpec]:
    return [ModelSpec(
        model_id=MODEL_ID,
        input_type=WetCo2CylindricalScaleGeometryHistory,
        evaluator=evaluate_wet_co2_cylindrical_scale_geometry_history,
        units={
            "history[].time_s": "s",
            "history[].wall_recession_m": "m",
            "history[].wall_remaining_m": "m",
            "history[].steel_inner_radius_m": "m",
            "history[].scale_thickness_equivalent_m": "m",
            "history[].bore_radius_m": "m",
            "history[].bore_flow_area_m2": "m^2",
            "history[].bore_wetted_perimeter_m": "m",
            "history[].steel_cross_section_area_m2": "m^2",
            "history[].scale_volume_m3": "m^3",
            "history[].scale_volume_per_axial_metre_m2": "m^2",
        },
        assumptions=(
            "Caller-supplied lineal phase inventories and molar volumes map to an annular cylindrical scale volume.",
            "Initial tube outer radius is fixed; metal loss moves the inner steel interface radially outward.",
            "Uniform axisymmetric geometry is required and independently reviewed by the caller.",
            "This model computes geometry only; it does not solve chemistry, kinetics, transport, corrosion or pressure loss.",
        ),
        source_ids=(GEOMETRY_SOURCE_ID, HISTORY_SOURCE_ID, PHASE_SOURCE_ID),
        qualification="user_model",
    )]
