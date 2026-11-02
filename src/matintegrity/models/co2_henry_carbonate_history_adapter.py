"""Exact-knot history handoff from corrected Henry records to carbonate equilibrium."""

from __future__ import annotations

from pydantic import Field, model_validator

from ..contracts import Calculation, Contract, RunContext, canonical_digest
from ..registry import ModelSpec
from .co2_fixed_fugacity_equilibrium import SOURCE_IDS as CARBONATE_SOURCE_IDS
from .co2_henry_carbonate_adapter import (
    SOURCE_ID as POINT_ADAPTER_SOURCE_ID,
    Co2HenryCarbonateAdapterRequest,
    co2_henry_temperature_to_fixed_fugacity_carbonate,
)
from .co2_henry_vant_hoff import (
    GAS_CONSTANT_SOURCE_ID,
    METHOD_SOURCE_ID as HENRY_METHOD_SOURCE_ID,
    SOURCE_ID as HENRY_CORRECTION_SOURCE_ID,
)

MODEL_ID = "integration.co2_henry_temperature_to_fixed_fugacity_carbonate_history"
SOURCE_ID = "caller_ordered_co2_henry_carbonate_history"


class Co2HenryCarbonateHistoryAdapterRequest(Contract):
    history_id: str = Field(min_length=1)
    asset_id: str = Field(min_length=1)
    location_id: str = Field(min_length=1)
    physical_scope_id: str = Field(min_length=1)
    time_basis: str = Field(min_length=1)
    time_s: tuple[float, ...] = Field(min_length=1, max_length=20000)
    knot_requests: tuple[Co2HenryCarbonateAdapterRequest, ...] = Field(min_length=1, max_length=20000)
    history_clock_and_sample_alignment_reviewed: bool
    all_points_must_compute_before_commit: bool = True
    maximum_point_evaluations: int = Field(default=20000, ge=1, le=20000)

    @model_validator(mode="after")
    def aligned_exact_knots(self):
        if len(self.time_s) != len(self.knot_requests):
            raise ValueError("one Henry-result/carbonate adapter request is required per exact time knot")
        if any(time < 0.0 for time in self.time_s):
            raise ValueError("history times must be nonnegative")
        if any(right <= left for left, right in zip(self.time_s[:-1], self.time_s[1:], strict=True)):
            raise ValueError("history times must increase strictly")
        if not self.all_points_must_compute_before_commit:
            raise ValueError("history output uses a complete-only policy; partial prefixes are returned only on failure")
        sample_ids = [row.carbonate_equilibrium.sample_id for row in self.knot_requests]
        correction_assessment_ids = [
            row.henry_temperature_correction_request.assessment_id for row in self.knot_requests
        ]
        if len(set(sample_ids)) != len(sample_ids):
            raise ValueError("carbonate sample identifiers must be unique across exact knots")
        if len(set(correction_assessment_ids)) != len(correction_assessment_ids):
            raise ValueError("Henry correction assessment identifiers must be unique across exact knots")
        for row in self.knot_requests:
            equilibrium = row.carbonate_equilibrium
            if (equilibrium.asset_id, equilibrium.location_id) != (self.asset_id, self.location_id):
                raise ValueError("every carbonate knot must match the history asset and location")
        return self


def co2_henry_carbonate_equilibrium_history(
    request: Co2HenryCarbonateHistoryAdapterRequest,
    *,
    context: RunContext | None = None,
) -> Calculation:
    """Evaluate each digest-bound exact knot, stopping at the first failed point."""
    history_digest = canonical_digest(request.model_dump(mode="json"))
    base = {
        "model_id": MODEL_ID,
        "history_id": request.history_id,
        "asset_id": request.asset_id,
        "location_id": request.location_id,
        "physical_scope_id": request.physical_scope_id,
        "time_basis": request.time_basis,
        "time_s": list(request.time_s),
        "point_count": len(request.knot_requests),
        "input_sha256": history_digest,
        "temperature_interpolation_performed": False,
        "henry_coefficient_extrapolation_performed": False,
        "solvent_composition_interpolation_performed": False,
        "full_aqueous_composition_solved": False,
        "carbonate_only_speciation_performed": True,
    }
    if len(request.knot_requests) > request.maximum_point_evaluations:
        return Calculation(
            status="out_of_scope",
            values=base | {
                "reason": "point_evaluation_budget_exceeded",
                "maximum_point_evaluations": request.maximum_point_evaluations,
            },
        )
    if not request.history_clock_and_sample_alignment_reviewed:
        return Calculation(
            status="needs_data",
            values=base | {"missing_reviews": ["history_clock_and_sample_alignment_reviewed"]},
        )
    if context is not None and (context.asset_id, context.location_id, context.time_basis) != (
        request.asset_id,
        request.location_id,
        request.time_basis,
    ):
        return Calculation(
            status="needs_data",
            values=base | {
                "reason": "run_context_does_not_match_history_asset_location_or_time_basis",
                "run_context": context.model_dump(mode="json"),
            },
        )

    rows = []
    for index, (time_s, knot_request) in enumerate(zip(request.time_s, request.knot_requests, strict=True)):
        correction_result = knot_request.henry_temperature_correction_result
        if (
            correction_result.context.asset_id != request.asset_id
            or correction_result.context.location_id != request.location_id
            or correction_result.context.time_basis != request.time_basis
        ):
            point = Calculation(
                status="needs_data",
                values={
                    "reason": "henry_correction_assessment_context_mismatch",
                    "assessment_input_digest": correction_result.input_digest,
                    "assessment_asset_id": correction_result.context.asset_id,
                    "assessment_location_id": correction_result.context.location_id,
                    "assessment_time_basis": correction_result.context.time_basis,
                },
            )
        else:
            point = co2_henry_temperature_to_fixed_fugacity_carbonate(knot_request)
        row = {
            "index": index,
            "time_s": time_s,
            "sample_id": knot_request.carbonate_equilibrium.sample_id,
            "assessment_id": knot_request.henry_temperature_correction_request.assessment_id,
            "target_temperature_K": knot_request.henry_temperature_correction_request.target_temperature_K,
            "solvent_composition_sha256": knot_request.henry_temperature_correction_request.sample_solvent_composition_sha256,
            "henry_reference_record_sha256": knot_request.henry_temperature_correction_request.reference.record_sha256,
            "henry_correction_input_digest": correction_result.input_digest,
            "status": point.status,
            "values": point.values,
            "notes": list(point.notes),
        }
        if point.status != "computed":
            return Calculation(
                status=point.status,
                values=base
                | {
                    "commit_policy": "complete_history_only",
                    "completed_sample_count": len(rows),
                    "completed_prefix": rows,
                    "failed_sample_index": index,
                    "failed_sample_time_s": time_s,
                    "failed_sample_id": row["sample_id"],
                    "failed_sample_status": point.status,
                    "failed_sample_values": point.values,
                },
                notes=point.notes
                + (
                    "The failed knot is reported with the computed prefix; no complete-history aggregate is committed.",
                ),
            )
        rows.append(row)

    return Calculation(
        values=base
        | {
            "commit_policy": "complete_history_only",
            "sample_results": rows,
            "sample_ids": [row["sample_id"] for row in rows],
            "temperature_K_history": [row["values"]["temperature_K"] for row in rows],
            "henry_coefficient_mol_L_Pa_history": [
                row["values"]["henry_coefficient_mol_L_Pa"] for row in rows
            ],
            "ph_activity_history": [row["values"]["ph_activity"] for row in rows],
            "co2star_mol_L_history": [row["values"]["co2star_mol_L"] for row in rows],
            "hco3_mol_L_history": [row["values"]["hco3_mol_L"] for row in rows],
            "co3_mol_L_history": [row["values"]["co3_mol_L"] for row in rows],
            "all_points_computed": True,
            "point_count_computed": len(rows),
        },
        notes=(
            "Every exact caller knot uses its own digest-verified Henry correction result and matching temperature and solvent-composition digest.",
            "No temperature or solvent-composition interpolation, between-knot evaluation, or Henry extrapolation is performed.",
            "The downstream calculation solves carbonate-only species and alkalinity closure, not full aqueous solution composition.",
        ),
    )


def specifications() -> list[ModelSpec]:
    return [
        ModelSpec(
            MODEL_ID,
            Co2HenryCarbonateHistoryAdapterRequest,
            co2_henry_carbonate_equilibrium_history,
            {
                "time_s[]": "s",
                "temperature_K_history[]": "K",
                "henry_coefficient_mol_L_Pa_history[]": "mol/L/Pa",
                "ph_activity_history[]": "1",
                "co2star_mol_L_history[]": "mol/L",
                "hco3_mol_L_history[]": "mol/L",
                "co3_mol_L_history[]": "mol/L",
                "point_count_computed": "count",
            },
            (
                "Each point requires one computed and digest-verified Henry temperature-correction AssessmentResult and one aligned carbonate-equilibrium input.",
                "Target temperature, mol/L/Pa convention, solvent digest, upstream provider/revision/configuration and reference/result digests are checked at every exact knot.",
                "The history uses exact caller order and complete-only aggregate semantics; it stops at the first failure and returns only the successful prefix plus the failure.",
                "No inter-knot temperature or solvent interpolation, Henry extrapolation, full aqueous composition, general reaction-network speciation, corrosion rate, scale or acceptance is inferred.",
            ),
            (
                SOURCE_ID,
                POINT_ADAPTER_SOURCE_ID,
                HENRY_CORRECTION_SOURCE_ID,
                HENRY_METHOD_SOURCE_ID,
                GAS_CONSTANT_SOURCE_ID,
                *CARBONATE_SOURCE_IDS,
            ),
            qualification="user_model",
            context_validator=_validate_context,
        )
    ]


def _validate_context(request: Co2HenryCarbonateHistoryAdapterRequest, context: RunContext) -> None:
    if (context.asset_id, context.location_id, context.time_basis) != (
        request.asset_id,
        request.location_id,
        request.time_basis,
    ):
        raise ValueError("run context must match history asset, location and time basis")
