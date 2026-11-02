"""Exact-knot uniform equivalent remaining-thickness adapter.

This adapter consumes a previously computed and digest-verified AssessmentResult.
It never restores thickness from negative signed penetration.
"""

from __future__ import annotations

import json
from typing import Literal

from pydantic import Field

from .contracts import AssessmentResult, Calculation, Contract, Evidence, Positive, RunContext, canonical_digest
from .registry import ModelSpec
from .ti12mo5zr_mass_balance import (
    Ti12Mo5ZrMassBalanceResult,
    Ti12Mo5ZrPenetrationPoint,
)

SOURCE_MODEL_ID = "corrosion.ti12mo5zr_aesec_signed_equivalent_penetration"
ADAPTER_MODEL_ID = "corrosion.ti12mo5zr_uniform_equivalent_remaining_thickness"
DATASET_ID = "zenodo-ti12mo5zr-aqueous-corrosion"
PROVIDER_ARCHIVE_SHA256 = "caf53855e78ff7162c361ba73435892759926f2d60513f5d42220239ce21f537"
PROVIDER_MEMBER_SHA256 = "52aef79a7284b88296f00ade100756efbdd60893028fe302a1e29fee4c9ae024"


class RemainingThicknessRequest(Contract):
    schema_version: Literal["matintegrity.ti12mo5zr_remaining_thickness_request.v1"] = (
        "matintegrity.ti12mo5zr_remaining_thickness_request.v1"
    )
    assessment: AssessmentResult
    expected_assessment_input_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    expected_assessment_result_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    expected_mass_balance_result_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    expected_run_context: RunContext
    baseline_thickness_m: Positive
    baseline_thickness_evidence: Evidence
    uniform_area_basis_authorized: Literal[True]
    density_material_applicability_authorized: Literal[True]
    computational_use_authorized: Literal[True]
    local_only_authorized: Literal[True]


class RemainingThicknessKnot(Contract):
    schema_version: Literal["matintegrity.ti12mo5zr_remaining_thickness_knot.v1"] = (
        "matintegrity.ti12mo5zr_remaining_thickness_knot.v1"
    )
    source_row_number: int = Field(ge=2)
    source_row_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    source_member_sha256: Literal[PROVIDER_MEMBER_SHA256] = PROVIDER_MEMBER_SHA256
    source_archive_sha256: Literal[PROVIDER_ARCHIVE_SHA256] = PROVIDER_ARCHIVE_SHA256
    provider_time_s: float = Field(ge=0)
    signed_net_mass_flux_kg_m2_s: float
    signed_equivalent_penetration_velocity_m_s: float
    cumulative_positive_penetration_m: float = Field(ge=0)
    cumulative_negative_penetration_m: float = Field(le=0)
    cumulative_signed_net_penetration_m: float
    remaining_thickness_m: float = Field(ge=0)


class RemainingThicknessHistory(Contract):
    schema_version: Literal["matintegrity.ti12mo5zr_remaining_thickness_history.v1"] = (
        "matintegrity.ti12mo5zr_remaining_thickness_history.v1"
    )
    model_id: Literal[ADAPTER_MODEL_ID] = ADAPTER_MODEL_ID
    source_model_id: Literal[SOURCE_MODEL_ID] = SOURCE_MODEL_ID
    dataset_id: Literal[DATASET_ID] = DATASET_ID
    source_archive_sha256: Literal[PROVIDER_ARCHIVE_SHA256] = PROVIDER_ARCHIVE_SHA256
    source_member_sha256: Literal[PROVIDER_MEMBER_SHA256] = PROVIDER_MEMBER_SHA256
    assessment_input_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    assessment_result_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    mass_balance_result_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    expected_run_context: RunContext
    baseline_thickness_m: Positive
    baseline_thickness_evidence: Evidence
    baseline_evidence_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    density_kg_m3: Positive
    density_evidence: Evidence
    density_evidence_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    provider_time_basis: Literal["provider_time_s_exact_knots"] = "provider_time_s_exact_knots"
    remaining_thickness_basis: Literal["baseline_minus_positive_cumulative_penetration_only"] = (
        "baseline_minus_positive_cumulative_penetration_only"
    )
    signed_ledger_preserved: Literal[True] = True
    negative_penetration_restores_thickness: Literal[False] = False
    knots: tuple[RemainingThicknessKnot, ...] = Field(min_length=2, max_length=20_000)
    scope_limit: Literal["uniform_equivalent_area_average_no_localized_wall_claim"] = (
        "uniform_equivalent_area_average_no_localized_wall_claim"
    )


def assessment_input_digest(result: AssessmentResult) -> str:
    """Recreate the registry's input digest payload for independent verification."""
    return canonical_digest({
        "model_id": result.model_id,
        "model_version": result.model_version,
        "inputs": result.inputs,
        "context": result.context.model_dump(mode="json"),
    })


def assessment_result_digest(result: AssessmentResult) -> str:
    """Digest the complete serialized assessment, including values and context."""
    return canonical_digest(result.model_dump(mode="json"))


def mass_balance_result_digest(result: Ti12Mo5ZrMassBalanceResult) -> str:
    return canonical_digest(result.model_dump(mode="json"))


def _check_outer_context(request: RemainingThicknessRequest, context: RunContext) -> None:
    if canonical_digest(context.model_dump(mode="json")) != canonical_digest(
        request.expected_run_context.model_dump(mode="json")
    ):
        raise ValueError("Adapter RunContext does not match the caller-pinned context")


def build_remaining_thickness_history(
    request: RemainingThicknessRequest,
) -> RemainingThicknessHistory:
    """Verify assessment provenance, then subtract positive loss at exact knots."""
    if not request.uniform_area_basis_authorized or not request.density_material_applicability_authorized:
        raise PermissionError("Uniform-area and density/material applicability authorization is required")
    assessment = request.assessment
    if assessment.model_id != SOURCE_MODEL_ID or assessment.status != "computed":
        raise ValueError("A computed assessment from the required signed mass-balance model is required")
    if not {DATASET_ID, "caller-density-evidence"}.issubset(set(assessment.source_ids)):
        raise ValueError("Source assessment does not declare the expected dataset and density evidence IDs")
    if assessment.context.model_dump(mode="json") != request.expected_run_context.model_dump(mode="json"):
        raise ValueError("Expected RunContext does not match the source assessment")
    actual_input_digest = assessment_input_digest(assessment)
    if (assessment.input_digest != actual_input_digest
            or request.expected_assessment_input_digest != assessment.input_digest):
        raise ValueError("Assessment input digest is invalid or differs from the caller-pinned digest")
    actual_result_digest = assessment_result_digest(assessment)
    if request.expected_assessment_result_digest != actual_result_digest:
        raise ValueError("Assessment result digest differs from the caller-pinned digest")

    raw_mass_balance = assessment.values.get("mass_balance")
    if not isinstance(raw_mass_balance, dict):
        raise ValueError("Assessment does not contain the expected mass_balance result")
    # AssessmentResult values are JSON-native; strict tuple contracts must be
    # reconstructed from JSON rather than Python list/dict coercion.
    mass_balance = Ti12Mo5ZrMassBalanceResult.model_validate_json(
        json.dumps(raw_mass_balance, ensure_ascii=False, allow_nan=False)
    )
    actual_mass_digest = mass_balance_result_digest(mass_balance)
    if request.expected_mass_balance_result_digest != actual_mass_digest:
        raise ValueError("Nested mass-balance digest differs from the caller-pinned digest")
    if (mass_balance.model_id != SOURCE_MODEL_ID
            or mass_balance.source_archive_sha256 != PROVIDER_ARCHIVE_SHA256
            or mass_balance.source_member_sha256 != PROVIDER_MEMBER_SHA256
            or mass_balance.analyzed_elements != ("Ti", "Mo", "Zr")):
        raise ValueError("Source model, pinned files, or analyzed-element coverage does not match")

    assessment_inputs = assessment.inputs
    if assessment_inputs.get("density_kg_m3") != mass_balance.density_kg_m3:
        raise ValueError("Assessment input density does not match the mass-balance result")
    expected_density_evidence = assessment_inputs.get("density_evidence")
    if not isinstance(expected_density_evidence, dict):
        raise ValueError("Assessment inputs omit density Evidence")
    density_digest = canonical_digest(mass_balance.density_evidence.model_dump(mode="json"))
    if (canonical_digest(expected_density_evidence) != density_digest
            or mass_balance.density_evidence_sha256 != density_digest):
        raise ValueError("Density Evidence does not reconcile to the source assessment")

    knots: list[RemainingThicknessKnot] = []
    previous_time: float | None = None
    last_cumulative_positive = -1.0
    for point in mass_balance.points:
        if previous_time is not None and point.provider_time_s <= previous_time:
            raise ValueError("Source assessment knots are not strictly ordered in provider time")
        if point.cumulative_positive_penetration_m < last_cumulative_positive:
            raise ValueError("Positive cumulative penetration must not decrease")
        remaining = request.baseline_thickness_m - point.cumulative_positive_penetration_m
        if remaining < 0:
            raise ValueError("Positive cumulative penetration exceeds the caller-approved baseline thickness")
        knots.append(RemainingThicknessKnot(
            source_row_number=point.source_row_number,
            source_row_sha256=point.source_row_sha256,
            source_member_sha256=point.source_member_sha256,
            source_archive_sha256=point.source_archive_sha256,
            provider_time_s=point.provider_time_s,
            signed_net_mass_flux_kg_m2_s=point.signed_net_mass_flux_kg_m2_s,
            signed_equivalent_penetration_velocity_m_s=point.signed_equivalent_penetration_velocity_m_s,
            cumulative_positive_penetration_m=point.cumulative_positive_penetration_m,
            cumulative_negative_penetration_m=point.cumulative_negative_penetration_m,
            cumulative_signed_net_penetration_m=point.cumulative_signed_net_penetration_m,
            remaining_thickness_m=remaining,
        ))
        previous_time = point.provider_time_s
        last_cumulative_positive = point.cumulative_positive_penetration_m
    if len(knots) != mass_balance.input_row_count or len(knots) < 2:
        raise ValueError("Knot count is inconsistent with the pinned source assessment")

    baseline_digest = canonical_digest(request.baseline_thickness_evidence.model_dump(mode="json"))
    return RemainingThicknessHistory(
        assessment_input_digest=assessment.input_digest,
        assessment_result_digest=actual_result_digest,
        mass_balance_result_digest=actual_mass_digest,
        expected_run_context=assessment.context,
        baseline_thickness_m=request.baseline_thickness_m,
        baseline_thickness_evidence=request.baseline_thickness_evidence,
        baseline_evidence_sha256=baseline_digest,
        density_kg_m3=mass_balance.density_kg_m3,
        density_evidence=mass_balance.density_evidence,
        density_evidence_sha256=density_digest,
        knots=tuple(knots),
    )


def evaluate_remaining_thickness(
    request: RemainingThicknessRequest,
) -> Calculation:
    result = build_remaining_thickness_history(request)
    return Calculation(
        values={"remaining_thickness_history": result.model_dump(mode="json")},
        notes=(
            "Remaining thickness is baseline thickness minus positive cumulative equivalent penetration only.",
            "Negative signed penetration is retained in the ledger and never restores thickness.",
            "This exact-knot uniform area-average history cannot support localized wall-loss claims, life, or risk probability.",
        ),
    )


def specifications() -> list[ModelSpec]:
    return [
        ModelSpec(
            model_id=ADAPTER_MODEL_ID,
            input_type=RemainingThicknessRequest,
            evaluator=evaluate_remaining_thickness,
            units={
                "remaining_thickness_history.knots[].remaining_thickness_m": "m",
                "remaining_thickness_history.knots[].provider_time_s": "s",
                "remaining_thickness_history.knots[].signed_net_mass_flux_kg_m2_s": "kg/m^2/s",
                "remaining_thickness_history.knots[].signed_equivalent_penetration_velocity_m_s": "m/s",
            },
            assumptions=(
                "The embedded source assessment, its registry input digest, complete result digest, and nested mass-balance digest are caller-pinned and independently verified.",
                "The caller supplies baseline-thickness Evidence and approves uniform area basis and density/material applicability.",
                "Remaining thickness equals baseline minus positive cumulative penetration only; negative source ledger values do not restore thickness.",
                "Only exact source observation knots are reported; no interpolation, localization, life, or risk inference is performed.",
            ),
            source_ids=(DATASET_ID, "caller-baseline-thickness-evidence", "caller-density-evidence"),
            qualification="engineering_screening",
            context_validator=_check_outer_context,
        )
    ]
