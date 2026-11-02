"""Registered composition of phase-derived volume rates and one hydraulic stage."""

from __future__ import annotations

from typing import Literal

from pydantic import Field, model_validator

from .contracts import Calculation, Contract, Evidence
from .crevice_hydraulic_stage_rhs import (
    MODEL_ID as HYDRAULIC_MODEL_ID,
    CreviceHydraulicStageRHSRequest,
    evaluate_crevice_hydraulic_stage_rhs,
)
from .crevice_solid_volume_rate import (
    COMPOSED_STAGE_SOURCE_ID,
    MODEL_ID as VOLUME_RATE_MODEL_ID,
    CreviceSolidVolumeRateRequest,
    bind_solid_volume_rates_to_hydraulic_stage,
    evaluate_crevice_solid_volume_rate,
)
from .registry import ModelSpec

MODEL_ID = "integration.crevice_solid_volume_hydraulic_stage"


class CreviceSolidVolumeHydraulicStageRequest(Contract):
    """Run a licensed phase-volume calculation through one digest-bound hydraulic RHS."""

    schema_version: Literal["matintegrity.crevice_solid_volume_hydraulic_stage.v1"] = (
        "matintegrity.crevice_solid_volume_hydraulic_stage.v1"
    )
    volume_rate_request: CreviceSolidVolumeRateRequest
    volume_rate_result: Calculation
    hydraulic_stage_request: CreviceHydraulicStageRHSRequest
    composition_authorization: Evidence
    composition_authorization_reviewed: bool
    computational_use_authorized: bool

    @model_validator(mode="after")
    def validate_composition_policy(self):
        if self.volume_rate_result.model_id != VOLUME_RATE_MODEL_ID:
            raise ValueError("volume-rate result must come from corrosion.crevice_solid_volume_rate")
        if self.composition_authorization.source_id != COMPOSED_STAGE_SOURCE_ID:
            raise ValueError("composition authorization must use the registered composition source ID")
        if not self.composition_authorization.license_id:
            raise ValueError("composition authorization must declare its license or permission basis")
        if not self.composition_authorization_reviewed or not self.computational_use_authorized:
            raise ValueError("composition-use review and computational authorization are required")
        return self


def evaluate_crevice_solid_volume_hydraulic_stage(
    request: CreviceSolidVolumeHydraulicStageRequest,
) -> Calculation:
    """Validate phase-rate lineage, compose hydraulic v2 input, and evaluate its RHS."""
    from .contracts import canonical_digest

    input_sha = canonical_digest(request.model_dump(mode="json"))
    try:
        stage_request = bind_solid_volume_rates_to_hydraulic_stage(
            request.hydraulic_stage_request,
            request.volume_rate_request,
            request.volume_rate_result,
            composition_authorization=request.composition_authorization,
        )
        hydraulic_result = evaluate_crevice_hydraulic_stage_rhs(stage_request)
        return Calculation(
            status=hydraulic_result.status,
            values={
                "model_id": MODEL_ID,
                "assessment_id": request.hydraulic_stage_request.assessment_id,
                "physical_scope_id": request.hydraulic_stage_request.physical_scope_id,
                "time_s": float(request.hydraulic_stage_request.time_s),
                "input_sha256": input_sha,
                "volume_rate_result_sha256": canonical_digest(
                    request.volume_rate_result.model_dump(mode="json")
                ),
                "composed_hydraulic_request": stage_request.model_dump(mode="json"),
                "hydraulic_stage_result": hydraulic_result.model_dump(mode="json"),
                "committed": bool(hydraulic_result.values.get("committed", False)),
                "qualification_claimed": False,
            },
            notes=(
                "This registered adapter composes two exact-stage APIs and returns the hydraulic RHS result.",
                "It does not solve phase kinetics and hydraulics in one BDF trial or integrate flow, chemistry, transport or moving geometry.",
            ) + hydraulic_result.notes,
        )
    except (ArithmeticError, OverflowError, ValueError) as error:
        return Calculation(status="out_of_scope", values={
            "model_id": MODEL_ID,
            "input_sha256": input_sha,
            "reason": str(error),
            "committed": False,
            "qualification_claimed": False,
        })


def specifications() -> tuple[ModelSpec, ...]:
    return (ModelSpec(
        model_id=MODEL_ID,
        input_type=CreviceSolidVolumeHydraulicStageRequest,
        evaluator=evaluate_crevice_solid_volume_hydraulic_stage,
        units={
            "time_s": "s",
            "hydraulic_stage_result.values.volumetric_flow_derivative_m3_s2": "m^3/s^2",
            "hydraulic_stage_result.values.volumetric_flow_by_face_m3_s[]": "m^3/s",
            "hydraulic_stage_result.values.cell_volume_rate_m3_s[]": "m^3/s",
            "committed": "1",
            "qualification_claimed": "1",
        },
        assumptions=(
            "The adapter requires a committed, digest-matched signed phase-volume result and matching assessment, scope, stage time and ordered cells.",
            "The caller must explicitly authorize the exact combined geometry/volume-rate/full-result digest; component licenses are not assumed to transfer.",
            "The adapter composes a stage result only; it does not couple the two calculations inside a shared BDF nonlinear solve or claim physical qualification.",
        ),
        source_ids=(
            "caller_evidenced_crevice_phase_molar_volume_gap_occupancy_map",
            "caller_evidenced_crevice_cell_phase_molar_rate_stage",
            COMPOSED_STAGE_SOURCE_ID,
            "caller_evidenced_planar_slit_instantaneous_hydraulic_rhs",
        ),
        version="0.1.0",
        qualification="user_model",
    ),)
