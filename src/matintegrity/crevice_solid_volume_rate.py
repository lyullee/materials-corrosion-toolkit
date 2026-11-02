"""Evidence-bound conversion of signed solid phase rates to liquid volume rates."""

from __future__ import annotations

import math
from typing import Literal

from pydantic import Field, model_validator

from .contracts import Calculation, Contract, Evidence, Positive, canonical_digest
from .registry import ModelSpec

MODEL_ID = "corrosion.crevice_solid_volume_rate"
GEOMETRY_SOURCE_ID = "caller_evidenced_crevice_phase_molar_volume_gap_occupancy_map"
RATE_SOURCE_ID = "caller_evidenced_crevice_cell_phase_molar_rate_stage"
COMPOSED_STAGE_SOURCE_ID = "composed_crevice_stage_geometry_and_phase_volume_rate"


class CreviceSolidVolumeRateRequest(Contract):
    """Convert ordered cellwise phase production rates into displaced liquid rates."""

    schema_version: Literal["matintegrity.crevice_solid_volume_rate.v1"] = "matintegrity.crevice_solid_volume_rate.v1"
    assessment_id: str = Field(min_length=1)
    physical_scope_id: str = Field(min_length=1)
    clock_id: str = Field(min_length=1)
    time_s: float
    cell_ids: tuple[str, ...] = Field(min_length=1, max_length=300)
    phase_ids_by_cell: tuple[tuple[str, ...], ...] = Field(min_length=1, max_length=300)
    phase_molar_rate_mol_s_by_cell: tuple[tuple[float, ...], ...] = Field(min_length=1, max_length=300)
    phase_molar_volume_m3_mol_by_cell: tuple[tuple[Positive, ...], ...] = Field(min_length=1, max_length=300)
    phase_occupies_gap_by_cell: tuple[tuple[bool, ...], ...] = Field(min_length=1, max_length=300)
    geometry_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    geometry_evidence: tuple[Evidence, ...] = Field(min_length=1, max_length=128)
    kinetic_rate_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    kinetic_rate_evidence: tuple[Evidence, ...] = Field(min_length=1, max_length=128)
    computational_use_authorized: bool

    @model_validator(mode="after")
    def validate_phase_rate_bindings(self):
        if not math.isfinite(self.time_s):
            raise ValueError("stage time must be finite")
        nc = len(self.cell_ids)
        if len(set(self.cell_ids)) != nc or any(not cell_id.strip() for cell_id in self.cell_ids):
            raise ValueError("cell IDs must be unique, ordered and nonblank")
        tables = (self.phase_ids_by_cell, self.phase_molar_rate_mol_s_by_cell,
                  self.phase_molar_volume_m3_mol_by_cell, self.phase_occupies_gap_by_cell)
        if any(len(table) != nc for table in tables):
            raise ValueError("phase, rate and geometry tables must have exactly one row per ordered cell")
        for cell_id, phase_ids, rates, molar_volumes, occupies in zip(
            self.cell_ids, *tables, strict=True
        ):
            if not phase_ids or len(set(phase_ids)) != len(phase_ids):
                raise ValueError(f"phase IDs for cell {cell_id!r} must be nonempty and unique")
            if len({len(rates), len(molar_volumes), len(occupies), len(phase_ids)}) != 1:
                raise ValueError(f"phase/rate/geometry shape mismatch in cell {cell_id!r}")
            if any(not math.isfinite(rate) for rate in rates):
                raise ValueError("phase molar rates must be finite and signed; positive means solid formation")
            if any(type(value) is not bool for value in occupies):
                raise ValueError("gap occupancy declarations must be explicit booleans")
        geometry_payload = {
            "physical_scope_id": self.physical_scope_id,
            "cell_ids": list(self.cell_ids),
            "phase_ids_by_cell": [list(row) for row in self.phase_ids_by_cell],
            "phase_molar_volume_m3_mol_by_cell": [
                [float(value) for value in row] for row in self.phase_molar_volume_m3_mol_by_cell
            ],
            "phase_occupies_gap_by_cell": [list(row) for row in self.phase_occupies_gap_by_cell],
        }
        rate_payload = {
            "assessment_id": self.assessment_id,
            "physical_scope_id": self.physical_scope_id,
            "clock_id": self.clock_id,
            "time_s": float(self.time_s),
            "cell_ids": list(self.cell_ids),
            "phase_ids_by_cell": [list(row) for row in self.phase_ids_by_cell],
            "phase_molar_rate_mol_s_by_cell": [
                [float(value) for value in row] for row in self.phase_molar_rate_mol_s_by_cell
            ],
        }
        for digest, expected, evidence, source, label in (
            (self.geometry_sha256, canonical_digest(geometry_payload), self.geometry_evidence,
             GEOMETRY_SOURCE_ID, "geometry"),
            (self.kinetic_rate_sha256, canonical_digest(rate_payload), self.kinetic_rate_evidence,
             RATE_SOURCE_ID, "kinetic-rate"),
        ):
            if digest != expected or not any(
                row.sha256 == digest and row.source_id == source and row.license_id
                for row in evidence
            ):
                raise ValueError(f"{label} digest requires matching licensed Evidence and exact ordered payload")
        if not self.computational_use_authorized:
            raise ValueError("computational-use authorization is required")
        return self


def evaluate_crevice_solid_volume_rate(request: CreviceSolidVolumeRateRequest) -> Calculation:
    """Calculate solid and liquid volume rates without clipping dissolution or growth."""
    input_sha = canonical_digest(request.model_dump(mode="json"))
    try:
        solid_rates = []
        liquid_rates = []
        for rates, molar_volumes, occupies in zip(
            request.phase_molar_rate_mol_s_by_cell,
            request.phase_molar_volume_m3_mol_by_cell,
            request.phase_occupies_gap_by_cell,
            strict=True,
        ):
            volume_terms = tuple(
                float(rate) * float(volume)
                for rate, volume, occupies_gap in zip(rates, molar_volumes, occupies, strict=True)
                if occupies_gap
            )
            if any(not math.isfinite(value) or (rate != 0.0 and value == 0.0)
                   for value, rate in zip(volume_terms,
                       (rate for rate, occupies_gap in zip(rates, occupies, strict=True) if occupies_gap),
                       strict=True)):
                raise ArithmeticError("a gap-solid volume-rate term exceeds numeric representation")
            solid_rate = math.fsum(volume_terms)
            if not math.isfinite(solid_rate):
                raise ArithmeticError("solid volume rate exceeds finite numeric support")
            solid_rates.append(solid_rate)
            liquid_rates.append(-solid_rate)
        return Calculation(values={
            "model_id": MODEL_ID,
            "assessment_id": request.assessment_id,
            "physical_scope_id": request.physical_scope_id,
            "clock_id": request.clock_id,
            "time_s": float(request.time_s),
            "input_sha256": input_sha,
            "geometry_sha256": request.geometry_sha256,
            "kinetic_rate_sha256": request.kinetic_rate_sha256,
            "cell_ids": list(request.cell_ids),
            "solid_volume_rate_m3_s_by_cell": solid_rates,
            "liquid_volume_rate_m3_s_by_cell": liquid_rates,
            "volume_rate_closure_residual_m3_s_by_cell": [
                solid + liquid for solid, liquid in zip(solid_rates, liquid_rates, strict=True)
            ],
            "positive_solid_rate_means_precipitation": True,
            "computed_from_gap_occupying_phases_only": True,
            "committed": True,
            "qualification_claimed": False,
        }, notes=(
            "Liquid displacement is minus the signed volume rate of phases explicitly declared to occupy the gap.",
            "This adapter does not calculate phase kinetics, transport, an aperture state or pressure-driven flow; its output is suitable as a separately reviewed stage input to the hydraulic RHS.",
        ))
    except (ArithmeticError, OverflowError, ValueError) as error:
        return Calculation(status="out_of_scope", values={
            "model_id": MODEL_ID,
            "assessment_id": request.assessment_id,
            "input_sha256": input_sha,
            "reason": str(error),
            "committed": False,
            "qualification_claimed": False,
        })


def bind_solid_volume_rates_to_hydraulic_stage(
    hydraulic_request,
    volume_rate_request: CreviceSolidVolumeRateRequest,
    volume_rate_result: Calculation,
    *,
    composition_authorization: Evidence,
):
    """Bind a committed phase-volume result into a digest-checked hydraulic stage request.

    The derived geometry evidence binds the hydraulic mesh together with the
    kinetic volume-rate result. This function composes two stage APIs; it does
    not integrate either state or couple them to the component BDF solver.
    """
    from .crevice_hydraulic_stage_rhs import CreviceHydraulicStageRHSRequest

    hydraulic = (
        hydraulic_request if isinstance(hydraulic_request, CreviceHydraulicStageRHSRequest)
        else CreviceHydraulicStageRHSRequest.model_validate(hydraulic_request)
    )
    rate_request = (
        volume_rate_request if isinstance(volume_rate_request, CreviceSolidVolumeRateRequest)
        else CreviceSolidVolumeRateRequest.model_validate(volume_rate_request)
    )
    if (volume_rate_result.status != "computed"
            or volume_rate_result.model_id != MODEL_ID
            or not volume_rate_result.values.get("committed", False)):
        raise ValueError("a committed crevice solid-volume-rate result is required")
    if volume_rate_result.values.get("input_sha256") != canonical_digest(rate_request.model_dump(mode="json")):
        raise ValueError("phase-volume result does not match its request digest")
    rate = volume_rate_result.values
    if (rate_request.assessment_id != hydraulic.assessment_id
            or rate_request.physical_scope_id != hydraulic.physical_scope_id
            or rate_request.time_s != hydraulic.time_s
            or tuple(rate.get("cell_ids", ())) != tuple(hydraulic.cell_ids)):
        raise ValueError("phase-volume result assessment, scope, stage time and ordered cells must match hydraulics")
    volume_rates = tuple(float(value) for value in rate.get("liquid_volume_rate_m3_s_by_cell", ()))
    if len(volume_rates) != len(hydraulic.cell_ids) or any(not math.isfinite(value) for value in volume_rates):
        raise ValueError("phase-volume result must contain one finite liquid-volume rate per hydraulic cell")

    volume_result_sha = canonical_digest(volume_rate_result.model_dump(mode="json"))
    derived_sha = composed_crevice_stage_geometry_digest(
        hydraulic,
        volume_rates,
        volume_rate_result_sha256=volume_result_sha,
    )
    if (composition_authorization.source_id != COMPOSED_STAGE_SOURCE_ID
            or composition_authorization.sha256 != derived_sha
            or not composition_authorization.license_id):
        raise ValueError("explicit composition authorization must bind the exact derived stage digest and license")
    request_data = hydraulic.model_dump(mode="python")
    request_data.update(
        schema_version="matintegrity.crevice_hydraulic_stage_rhs.v2",
        cell_volume_rate_m3_s=volume_rates,
        geometry_provider_id=COMPOSED_STAGE_SOURCE_ID,
        geometry_provider_revision="phase-volume-stage-composition.v1",
        geometry_record_sha256=derived_sha,
        evidence=tuple(hydraulic.evidence) + (composition_authorization,),
    )
    return CreviceHydraulicStageRHSRequest.model_validate(request_data)


def composed_crevice_stage_geometry_digest(
    hydraulic_request,
    liquid_volume_rates_m3_s,
    *,
    volume_rate_result_sha256: str,
) -> str:
    """Return the geometry/rate digest a caller must authorize for one composed stage."""
    from .crevice_hydraulic_stage_rhs import CreviceHydraulicStageRHSRequest

    hydraulic = (
        hydraulic_request if isinstance(hydraulic_request, CreviceHydraulicStageRHSRequest)
        else CreviceHydraulicStageRHSRequest.model_validate(hydraulic_request)
    )
    rates = tuple(float(value) for value in liquid_volume_rates_m3_s)
    if len(rates) != len(hydraulic.cell_ids) or any(not math.isfinite(value) for value in rates):
        raise ValueError("one finite liquid-volume rate is required per ordered hydraulic cell")
    if (not isinstance(volume_rate_result_sha256, str)
            or len(volume_rate_result_sha256) != 64
            or any(character not in "0123456789abcdef" for character in volume_rate_result_sha256)):
        raise ValueError("phase-volume result digest is required for stage composition authorization")
    payload = {
        "physical_scope_id": hydraulic.physical_scope_id,
        "time_s": float(hydraulic.time_s),
        "cell_ids": list(hydraulic.cell_ids),
        "cell_lengths_m": [float(value) for value in hydraulic.cell_lengths_m],
        "aperture_by_cell_m": [float(value) for value in hydraulic.aperture_by_cell_m],
        "transverse_width_m": float(hydraulic.transverse_width_m),
        "cell_volume_rate_m3_s": list(rates),
        "volume_rate_result_sha256": volume_rate_result_sha256,
    }
    return canonical_digest(payload)


def specifications() -> tuple[ModelSpec, ...]:
    return (ModelSpec(
        model_id=MODEL_ID,
        input_type=CreviceSolidVolumeRateRequest,
        evaluator=evaluate_crevice_solid_volume_rate,
        units={
            "time_s": "s",
            "phase_molar_rate_mol_s_by_cell[][]": "mol/s",
            "phase_molar_volume_m3_mol_by_cell[][]": "m^3/mol",
            "solid_volume_rate_m3_s_by_cell[]": "m^3/s",
            "liquid_volume_rate_m3_s_by_cell[]": "m^3/s",
            "volume_rate_closure_residual_m3_s_by_cell[]": "m^3/s",
        },
        assumptions=(
            "Positive phase molar rate denotes precipitation and negative rate denotes dissolution.",
            "Only phases explicitly marked as gap occupying contribute to solid volume change; the liquid volume rate is the equal-and-opposite signed result.",
            "Phase rate and molar-volume geometry maps are separately digest bound by licensed Evidence; this conversion does not qualify the rates or the molar volumes.",
            "The output is a stage quantity and does not integrate a coupled chemistry, solid, hydraulic or moving-boundary system.",
        ),
        source_ids=(GEOMETRY_SOURCE_ID, RATE_SOURCE_ID, COMPOSED_STAGE_SOURCE_ID),
        version="0.1.0",
        qualification="user_model",
    ),)
