"""Optional adapter for the pinned consequence toolkit's native passive plume primitive."""

from __future__ import annotations

import json
from typing import Literal

from pydantic import Field, model_validator

from .consequence_pinned_adapter import PinnedProviderRequestEnvelope
from .contracts import Contract, Positive, canonical_digest


class CcpsNativePlumeSettings(Contract):
    schema_version: Literal["matintegrity.ccps_native_plume_settings.v1"] = (
        "matintegrity.ccps_native_plume_settings.v1"
    )
    wind_speed_m_s: Positive
    crosswind_distance_m: float
    receptor_height_m: float = Field(ge=0)
    release_height_m: float = Field(ge=0)
    sigma_y_m: Positive
    sigma_z_m: Positive
    sigma_basis: str = Field(min_length=1)
    applicability: Literal["passive_steady_open_terrain"]
    caller_reviewed: bool


class CcpsNativePlumeProviderReport(Contract):
    schema_version: Literal["matintegrity.ccps_native_plume_provider_report.v1"] = (
        "matintegrity.ccps_native_plume_provider_report.v1"
    )
    request_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    calculation_id: Literal["dispersion/plume"]
    calculation_input_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    calculation_output_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    engine_code_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    concentration_kg_m3: float = Field(ge=0)
    provider_result_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    report_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    external_native_engine_executed: Literal[True] = True
    physical_validation_claimed: Literal[False] = False
    engineering_qualification_claimed: Literal[False] = False
    limitations: tuple[str, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def bound_digest(self):
        payload = self.model_dump(mode="json", exclude={"report_digest"})
        if canonical_digest(payload) != self.report_digest:
            raise ValueError("CCPS native provider report digest mismatch")
        return self


def run_pinned_ccps_native_plume(
    envelope: PinnedProviderRequestEnvelope,
    settings: CcpsNativePlumeSettings,
) -> CcpsNativePlumeProviderReport:
    """Execute only the explicit native passive-plume calculation; never choose a fallback."""

    if not settings.caller_reviewed:
        raise ValueError("caller review of passive-plume settings is required")
    try:
        from ccps_consequence.api import calculate
        from ccps_consequence.contracts import code_digest
        from ccps_consequence.integrations import ProviderRequest, ProviderResult, evaluate_provider
    except ImportError as exc:
        raise ImportError(
            "the pinned process-risk-consequence-toolkit must be installed or on PYTHONPATH"
        ) from exc

    request = ProviderRequest.model_validate_json(json.dumps(envelope.request, allow_nan=False))
    if request.engine != "user_supplied":
        raise ValueError("native plume adapter requires the explicit user_supplied provider route")
    if request.model_id != "ccps-native-dispersion-plume-v1":
        raise ValueError("native plume adapter model identity mismatch")
    if request.quantity != "concentration_kg_m3":
        raise ValueError("native plume adapter produces concentration_kg_m3 only")
    if request.distance_m <= 0:
        raise ValueError("positive downwind distance is required")
    current_code_digest = code_digest()
    if request.expected_engine_code_digest != current_code_digest:
        raise ValueError("pinned request engine code digest differs from loaded consequence toolkit")

    receipt = calculate(
        "dispersion/plume",
        {
            "mass_rate_kg_s": request.source.mass_rate_kg_s,
            "wind_speed_m_s": settings.wind_speed_m_s,
            "downwind_distance_m": request.distance_m,
            "crosswind_distance_m": settings.crosswind_distance_m,
            "receptor_height_m": settings.receptor_height_m,
            "release_height_m": settings.release_height_m,
            "sigma_y_m": settings.sigma_y_m,
            "sigma_z_m": settings.sigma_z_m,
            "sigma_basis": settings.sigma_basis,
            "applicability": settings.applicability,
        },
        context=request.context,
    )

    class NativePlumeProvider:
        def evaluate(self, provider_request):
            return ProviderResult(
                request_digest=provider_request.digest(),
                engine=provider_request.engine,
                model_id=provider_request.model_id,
                engine_version="pinned-native-plume",
                engine_code_digest=current_code_digest,
                receptor_id=provider_request.receptor_id,
                quantity=provider_request.quantity,
                value=receipt.outputs["concentration_kg_m3"],
                evidence_ids=provider_request.source.evidence_ids,
                limitations=tuple(receipt.limitations),
            )

    provider_result = evaluate_provider(request, NativePlumeProvider())
    payload = {
        "request_digest": request.digest(),
        "calculation_id": receipt.calculation_id,
        "calculation_input_digest": receipt.input_digest,
        "calculation_output_digest": receipt.output_digest,
        "engine_code_digest": current_code_digest,
        "concentration_kg_m3": provider_result.value,
        "provider_result_digest": provider_result.digest(),
        "external_native_engine_executed": True,
        "physical_validation_claimed": False,
        "engineering_qualification_claimed": False,
        "limitations": tuple(receipt.limitations),
    }
    return CcpsNativePlumeProviderReport(
        **payload,
        report_digest=canonical_digest(
            {"schema_version": "matintegrity.ccps_native_plume_provider_report.v1", **payload}
        ),
    )
