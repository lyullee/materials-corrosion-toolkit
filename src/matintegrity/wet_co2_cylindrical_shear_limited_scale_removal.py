from __future__ import annotations

import math
from typing import Literal

from pydantic import Field, model_validator

from .contracts import Calculation, Contract, Evidence, Nonnegative, Positive, canonical_digest
from .registry import ModelSpec
from .wet_co2_cylindrical_scale_geometry import WetCo2CylindricalScaleGeometryHistory

MODEL_ID = "integration.wet_co2_cylindrical_shear_limited_scale_removal"
GROWTH_SOURCE_ID = "caller_cylindrical_diffusion_limited_scale_growth_ledger"
SHEAR_SOURCE_ID = "caller_wall_shear_history"
DETACHMENT_LAW_SOURCE_ID = "caller_calibrated_shear_scale_detachment_law"


class WetCo2ScaleShearKnot(Contract):
    time_s: Nonnegative
    wall_shear_stress_Pa: Nonnegative
    record_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    evidence: tuple[Evidence, ...] = Field(min_length=1, max_length=64)

    @model_validator(mode="after")
    def bind_shear_record(self):
        payload = {"time_s": self.time_s, "wall_shear_stress_Pa": self.wall_shear_stress_Pa}
        if canonical_digest(payload) != self.record_sha256:
            raise ValueError("shear record digest must bind exact knot time and stress")
        if not any(row.sha256 == self.record_sha256 and row.license_id for row in self.evidence):
            raise ValueError("licensed Evidence must pin each caller wall-shear knot")
        return self


class WetCo2CylindricalShearLimitedScaleRemoval(Contract):
    """Apply caller-calibrated threshold stripping to one selected scale growth ledger."""

    schema_version: Literal["matintegrity.wet_co2_cylindrical_shear_limited_scale_removal.v1"] = (
        "matintegrity.wet_co2_cylindrical_shear_limited_scale_removal.v1"
    )
    assessment_id: str = Field(min_length=1, max_length=160)
    solid_id: str = Field(min_length=1, max_length=160)
    geometry: WetCo2CylindricalScaleGeometryHistory
    geometry_result: Calculation
    growth_ledger: Calculation
    shear_history: tuple[WetCo2ScaleShearKnot, ...] = Field(min_length=2, max_length=5000)
    critical_shear_stress_Pa: Positive
    detachment_velocity_scale_m_s: Positive
    stress_exponent: Positive
    detachment_law_record_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    detachment_law_evidence: tuple[Evidence, ...] = Field(min_length=1, max_length=64)
    detached_layer_and_inner_area_basis_reviewed: bool

    @model_validator(mode="after")
    def bind_law_and_inputs(self):
        payload = {
            "solid_id": self.solid_id,
            "critical_shear_stress_Pa": self.critical_shear_stress_Pa,
            "detachment_velocity_scale_m_s": self.detachment_velocity_scale_m_s,
            "stress_exponent": self.stress_exponent,
        }
        if canonical_digest(payload) != self.detachment_law_record_sha256:
            raise ValueError("detachment-law digest must bind solid, threshold, coefficient and exponent")
        if not any(row.sha256 == self.detachment_law_record_sha256 and row.license_id
                   for row in self.detachment_law_evidence):
            raise ValueError("licensed Evidence must pin the caller-calibrated shear detachment law")
        if self.geometry_result.status != "computed" or self.growth_ledger.status != "computed":
            raise ValueError("geometry and diffusion-limited growth ledger inputs must be computed")
        times = tuple(row.time_s for row in self.geometry.history)
        if times != tuple(row.time_s for row in self.shear_history):
            raise ValueError("shear knots must exactly match geometry knot times")
        if self.geometry_result.values.get("model_id") != "degradation.wet_co2_cylindrical_scale_geometry_history":
            raise ValueError("geometry result must come from the cylindrical scale geometry evaluator")
        if self.growth_ledger.values.get("model_id") != "integration.wet_co2_cylindrical_diffusion_limited_scale_growth":
            raise ValueError("growth result must come from the diffusion-limited scale growth evaluator")
        if self.geometry_result.values.get("input_sha256") != canonical_digest(self.geometry.model_dump(mode="json")):
            raise ValueError("geometry result was not calculated from the supplied geometry request")
        geometry_digest = canonical_digest(self.geometry_result.model_dump(mode="json"))
        if self.growth_ledger.values.get("geometry_result_sha256") != geometry_digest:
            raise ValueError("growth ledger geometry lineage does not match supplied geometry result")
        if self.growth_ledger.values.get("solid_id") != self.solid_id:
            raise ValueError("selected scale solid must match growth ledger phase")
        if tuple(float(row["time_s"]) for row in self.geometry_result.values.get("history", [])) != times:
            raise ValueError("geometry result history must match the geometry request knots")
        if tuple(float(row["time_s"]) for row in self.growth_ledger.values.get("history", [])) != times:
            raise ValueError("growth ledger history must match geometry knots")
        return self


def evaluate_wet_co2_cylindrical_shear_limited_scale_removal(
    request: WetCo2CylindricalShearLimitedScaleRemoval,
) -> Calculation:
    """Compute threshold-triggered stripping flux and finite phase removal per axial metre."""
    geometry_rows = request.geometry_result.values["history"]
    growth_rows = request.growth_ledger.values["history"]
    phase = next((row for row in request.geometry.phases if row.phase_id == request.solid_id), None)
    base = {
        "assessment_id": request.assessment_id,
        "asset_id": request.geometry.asset_id,
        "location_id": request.geometry.location_id,
        "model_id": MODEL_ID,
        "solid_id": request.solid_id,
        "input_sha256": canonical_digest(request.model_dump(mode="json")),
        "geometry_result_sha256": canonical_digest(request.geometry_result.model_dump(mode="json")),
        "growth_ledger_sha256": canonical_digest(request.growth_ledger.model_dump(mode="json")),
        "detachment_law_record_sha256": request.detachment_law_record_sha256,
        "source_ids": [GROWTH_SOURCE_ID, SHEAR_SOURCE_ID, DETACHMENT_LAW_SOURCE_ID],
    }
    if phase is None:
        return Calculation(status="needs_data", values=base | {"reason": "selected_scale_phase_missing_from_geometry"})
    if not request.detached_layer_and_inner_area_basis_reviewed:
        return Calculation(status="needs_data", values=base | {
            "reason": "detached_phase_identity_and_inner_area_basis_review_required",
        })
    start_inventory = float(geometry_rows[0].get("phase_inventory_mol_m_by_phase", {}).get(request.solid_id, 0.0))
    inventory = start_inventory
    states = []
    for index, (geom, growth, shear) in enumerate(zip(
        geometry_rows, growth_rows, request.shear_history, strict=True
    )):
        time_s = float(geom["time_s"])
        radius = float(geom["bore_radius_m"])
        tau = shear.wall_shear_stress_Pa
        ratio_excess = max(0.0, tau / request.critical_shear_stress_Pa - 1.0)
        try:
            detach_velocity = request.detachment_velocity_scale_m_s * ratio_excess ** request.stress_exponent
        except OverflowError:
            return Calculation(status="out_of_scope", values=base | {"reason": "shear_detachment_law_overflow", "failed_knot_index": index})
        if not math.isfinite(detach_velocity):
            return Calculation(status="out_of_scope", values=base | {"reason": "shear_detachment_velocity_nonfinite", "failed_knot_index": index})
        detach_flux_requested = detach_velocity / phase.molar_volume_m3_mol
        growth_increment = float(growth["interval_left_held_net_phase_increment_mol_m"])
        pre_detach_inventory = inventory
        if index < len(geometry_rows) - 1:
            dt = float(geometry_rows[index + 1]["time_s"]) - time_s
            pre_detach_inventory += growth_increment
            if pre_detach_inventory < -1e-12:
                return Calculation(status="out_of_scope", values=base | {
                    "reason": "growth_ledger_dissolution_depletes_phase_before_shear_removal",
                    "failed_interval_index": index,
                    "pre_detachment_inventory_mol_m": pre_detach_inventory,
                })
            pre_detach_inventory = max(0.0, pre_detach_inventory)
            detach_requested_mol_m = detach_flux_requested * (2.0 * math.pi * radius) * dt
            detach_actual_mol_m = min(pre_detach_inventory, detach_requested_mol_m)
            inventory = pre_detach_inventory - detach_actual_mol_m
        else:
            dt = 0.0
            detach_requested_mol_m = 0.0
            detach_actual_mol_m = 0.0
        geometry_inventory = float(geom.get("phase_inventory_mol_m_by_phase", {}).get(request.solid_id, 0.0))
        states.append({
            "time_s": time_s,
            "wall_shear_stress_Pa": tau,
            "critical_shear_stress_Pa": request.critical_shear_stress_Pa,
            "detachment_velocity_m_s": detach_velocity,
            "requested_detachment_flux_mol_m2_s": detach_flux_requested,
            "growth_ledger_interval_increment_mol_m": growth_increment,
            "pre_detachment_phase_inventory_mol_m": pre_detach_inventory if index < len(geometry_rows) - 1 else inventory,
            "requested_detachment_mol_m": detach_requested_mol_m,
            "actual_detachment_mol_m": detach_actual_mol_m,
            "phase_inventory_after_interval_mol_m": inventory,
            "geometry_phase_inventory_mol_m": geometry_inventory,
            "inventory_difference_from_geometry_mol_m": inventory - geometry_inventory,
            "interval_duration_s": dt,
        })
    return Calculation(values=base | {
        "status": "computed",
        "knot_count": len(states),
        "detachment_law": "caller_calibrated_threshold_power_law.v1",
        "history": states,
        "limitations": [
            "The threshold and power law are caller calibration inputs; no universal scale adhesion or shear threshold is asserted.",
            "The law treats the caller coefficient as a local scale-recession velocity and converts it with the selected phase molar volume.",
            "Rates are left-held to the next geometry knot and applied to inner wetted area per axial metre.",
            "Removal is capped by currently available phase inventory, but detached material fate and chemistry are not modeled.",
            "This post-process does not update transport, saturation, diffusion limitation, layer ordering, or geometry and is not a qualified erosion/spallation prediction.",
        ],
    })


def specifications() -> list[ModelSpec]:
    return [ModelSpec(
        model_id=MODEL_ID,
        input_type=WetCo2CylindricalShearLimitedScaleRemoval,
        evaluator=evaluate_wet_co2_cylindrical_shear_limited_scale_removal,
        units={
            "history[].wall_shear_stress_Pa": "Pa",
            "history[].detachment_velocity_m_s": "m/s",
            "history[].requested_detachment_flux_mol_m2_s": "mol/m^2/s",
            "history[].actual_detachment_mol_m": "mol/m",
            "history[].phase_inventory_after_interval_mol_m": "mol/m",
        },
        assumptions=(
            "Scale removal begins above a caller-declared critical wall shear stress and follows a caller-calibrated power law.",
            "The scale flux and geometry use the same exact knot sequence and inner wetted-area basis.",
            "A finite phase inventory limits the removable amount in each interval.",
        ),
        source_ids=(GROWTH_SOURCE_ID, SHEAR_SOURCE_ID, DETACHMENT_LAW_SOURCE_ID),
        qualification="user_model",
    )]



