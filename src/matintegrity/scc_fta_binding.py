"""Bind caller-supplied first-failure probability to a computed SCC growth limit event."""

from __future__ import annotations

from typing import Literal

from pydantic import Field, model_validator

from .consequence_exchange import IntegrityEventBasis
from .contracts import (
    Calculation,
    Contract,
    Evidence,
    Fraction,
    Positive,
    RunContext,
    canonical_digest,
)
from .models.chloride_scc import SCCCrackVelocityHistoryRequest, scc_crack_velocity_history
from .models.fault_tree import FaultTreeBasicEvent
from .registry import ModelSpec

MODEL_ID = "adapter.scc_crack_growth_to_fault_tree_basic_event"
MODEL_VERSION = "1"
SOURCE_MODEL_ID = "degradation.scc_crack_velocity_history"
SOURCE_ID = "caller_scc_crack_advance_limit_probability_binding"


class SCCFaultTreeProbabilityInput(Contract):
    """Explicit caller event and probability provenance for one finite-period event."""

    schema_version: Literal["matintegrity.scc_fta_probability_input.v1"] = (
        "matintegrity.scc_fta_probability_input.v1"
    )
    event_id: str = Field(min_length=1)
    failure_mode: str = Field(min_length=1)
    condition_id: str = Field(min_length=1)
    condition_statement: str = Field(min_length=1)
    probability: Fraction
    probability_meaning: Literal["conditional_first_failure_in_period"]
    conditioning: str = Field(min_length=1)
    probability_scope_id: str = Field(min_length=1)
    probability_evidence: tuple[Evidence, ...] = Field(min_length=1, max_length=128)
    rights_boundary: Literal["local_only", "caller_authorized_open_distribution"]
    rights_authorization_digest: str | None = Field(default=None, pattern=r"^[a-f0-9]{64}$")

    @model_validator(mode="after")
    def validate_rights_boundary(self):
        if self.rights_boundary == "caller_authorized_open_distribution" and self.rights_authorization_digest is None:
            raise ValueError("open distribution requires a caller-supplied authorization digest")
        if self.rights_boundary == "local_only" and self.rights_authorization_digest is not None:
            raise ValueError("local-only boundary must not claim an open-distribution authorization digest")
        return self


class SCCFaultTreeBindingRequest(Contract):
    """One exact SCC history/result pair, a caller limit, and explicit event probability."""

    schema_version: Literal["matintegrity.scc_fta_binding_request.v1"] = (
        "matintegrity.scc_fta_binding_request.v1"
    )
    scc_request: SCCCrackVelocityHistoryRequest
    scc_result: Calculation
    crack_advance_limit_m: Positive
    limit_evidence: Evidence
    probability_input: SCCFaultTreeProbabilityInput


class SCCFaultTreeEventBinding(Contract):
    """Validated FTA event, integrity basis, threshold bracket, and source lineage."""

    schema_version: Literal["matintegrity.scc_fta_event_binding.v1"] = (
        "matintegrity.scc_fta_event_binding.v1"
    )
    basic_event: FaultTreeBasicEvent
    integrity_event_basis: IntegrityEventBasis
    calculation: Calculation
    limit_evidence: Evidence
    probability_evidence: tuple[Evidence, ...]
    rights_boundary: Literal["local_only", "caller_authorized_open_distribution"]
    rights_authorization_digest: str | None = Field(default=None, pattern=r"^[a-f0-9]{64}$")


def _source_context(request: SCCCrackVelocityHistoryRequest) -> dict:
    return {
        "assessment_id": request.assessment_id,
        "asset_id": request.asset_id,
        "location_id": request.location_id,
        "physical_scope_id": request.physical_scope_id,
        "specimen_id": request.specimen_id,
        "clock_id": request.clock_id,
        "horizon_start_s": request.time_s[0],
        "horizon_end_s": request.time_s[-1],
        "time_s": list(request.time_s),
        "material_condition_id": request.material_condition_id,
        "metallurgy_id": request.metallurgy_id,
        "environment_id": request.environment_id,
        "loading_basis_id": request.loading_basis_id,
    }


def _validate_source_result(request: SCCCrackVelocityHistoryRequest, result: Calculation):
    request_digest = canonical_digest(request.model_dump(mode="json"))
    result_digest = canonical_digest(result.model_dump(mode="json"))
    values = result.values
    expected_context = _source_context(request)
    if values.get("model_id") != SOURCE_MODEL_ID:
        return Calculation(status="out_of_scope", values={
            "reason": "scc_result_model_id_mismatch",
            "expected_model_id": SOURCE_MODEL_ID,
            "actual_model_id": values.get("model_id"),
            "probability_inferred": False,
        })
    if values.get("request_sha256") != request_digest:
        return Calculation(status="out_of_scope", values={
            "reason": "scc_result_request_digest_mismatch",
            "request_sha256": request_digest,
            "result_request_sha256": values.get("request_sha256"),
            "scc_result_sha256": result_digest,
            "probability_inferred": False,
        })
    if result.status != "computed":
        return Calculation(status="needs_data", values={
            "reason": "computed_scc_history_required",
            "scc_status": result.status,
            "request_sha256": request_digest,
            "scc_result_sha256": result_digest,
            "probability_inferred": False,
        })

    # Re-evaluate the pure deterministic source calculation and compare its complete
    # canonical result. A matching request digest by itself does not authenticate values.
    reproduced = scc_crack_velocity_history(request)
    if reproduced.status != "computed" or canonical_digest(reproduced.model_dump(mode="json")) != result_digest:
        return Calculation(status="out_of_scope", values={
            "reason": "scc_result_does_not_match_recomputed_source_calculation",
            "request_sha256": request_digest,
            "scc_result_sha256": result_digest,
            "recomputed_status": reproduced.status,
            "probability_inferred": False,
        })

    required = {
        "assessment_id": expected_context["assessment_id"],
        "asset_id": expected_context["asset_id"],
        "location_id": expected_context["location_id"],
        "physical_scope_id": expected_context["physical_scope_id"],
        "time_s": expected_context["time_s"],
        "material_condition_id": expected_context["material_condition_id"],
        "metallurgy_id": expected_context["metallurgy_id"],
        "environment_id": expected_context["environment_id"],
        "loading_basis_id": expected_context["loading_basis_id"],
    }
    if any(values.get(key) != value for key, value in required.items()):
        return Calculation(status="out_of_scope", values={
            "reason": "scc_result_scope_or_clock_mismatch",
            "request_sha256": request_digest,
            "scc_result_sha256": result_digest,
            "probability_inferred": False,
        })
    advances = values.get("crack_advance_m_by_knot")
    if not isinstance(advances, list) or len(advances) != len(request.time_s):
        return Calculation(status="out_of_scope", values={
            "reason": "scc_result_knot_history_mismatch",
            "request_sha256": request_digest,
            "scc_result_sha256": result_digest,
            "probability_inferred": False,
        })
    return request_digest, result_digest, expected_context, advances


def bind_scc_crack_advance_probability_to_fta(
    request: SCCFaultTreeBindingRequest,
) -> SCCFaultTreeEventBinding | Calculation:
    """Bind an explicit period probability to an SCC crack-advance limit event.

    The deterministic SCC calculation establishes only whether the caller limit is
    reached in the supplied knot history and the adjacent interval bracket. It never
    calculates, calibrates, or replaces the caller probability.
    """
    checked = _validate_source_result(request.scc_request, request.scc_result)
    if isinstance(checked, Calculation):
        return checked
    request_digest, result_digest, context, advances = checked
    probability_input = request.probability_input
    if request.limit_evidence.origin not in ("measured", "open_dataset", "user_declared", "synthetic"):
        return Calculation(status="out_of_scope", values={
            "reason": "crack_advance_limit_requires_caller_or_observation_evidence",
            "request_sha256": request_digest,
            "scc_result_sha256": result_digest,
            "probability_inferred": False,
        })
    if (
        request.limit_evidence.origin == "synthetic"
        or any(row.origin == "synthetic" for row in probability_input.probability_evidence)
    ) and probability_input.rights_boundary != "local_only":
        return Calculation(status="out_of_scope", values={
            "reason": "synthetic_inputs_cannot_claim_open_distribution",
            "request_sha256": request_digest,
            "scc_result_sha256": result_digest,
            "probability_inferred": False,
        })

    limit = request.crack_advance_limit_m
    if advances[0] >= limit:
        return Calculation(status="out_of_scope", values={
            "reason": "crack_advance_limit_already_reached_at_horizon_start",
            "crack_advance_limit_m": limit,
            "initial_crack_advance_m": advances[0],
            "horizon_start_s": context["horizon_start_s"],
            "probability_inferred": False,
        })
    crossing_index = next((index for index, advance in enumerate(advances[1:], start=1) if advance >= limit), None)
    crossing_bracket = None if crossing_index is None else {
        "interval_index": crossing_index - 1,
        "start_time_s": context["time_s"][crossing_index - 1],
        "end_time_s": context["time_s"][crossing_index],
        "left_crack_advance_m": advances[crossing_index - 1],
        "right_crack_advance_m": advances[crossing_index],
        "limit_m": limit,
        "exact_crossing_time_reported": False,
    }
    input_digest = canonical_digest({
        "source_model_id": SOURCE_MODEL_ID,
        "source_request_sha256": request_digest,
        "source_result_sha256": result_digest,
        "source_context": context,
        "crack_advance_limit_m": limit,
        "limit_evidence": request.limit_evidence.model_dump(mode="json"),
        "probability_input": probability_input.model_dump(mode="json"),
    })
    result_binding_digest = canonical_digest({
        "adapter_model_id": MODEL_ID,
        "adapter_model_version": MODEL_VERSION,
        "binding_input_sha256": input_digest,
        "source_result_sha256": result_digest,
        "condition_id": probability_input.condition_id,
        "condition_statement": probability_input.condition_statement,
        "crack_advance_limit_m": limit,
        "limit_reached_by_period_end": crossing_index is not None,
        "crossing_interval": crossing_bracket,
        "probability": probability_input.probability,
        "probability_meaning": probability_input.probability_meaning,
        "conditioning": probability_input.conditioning,
        "probability_scope_id": probability_input.probability_scope_id,
        "probability_evidence": [row.model_dump(mode="json") for row in probability_input.probability_evidence],
        "rights_boundary": probability_input.rights_boundary,
        "rights_authorization_digest": probability_input.rights_authorization_digest,
    })
    basis = IntegrityEventBasis(
        event_id=probability_input.event_id,
        asset_id=context["asset_id"],
        location_id=context["location_id"],
        failure_mode=probability_input.failure_mode,
        physical_scope_id=context["physical_scope_id"],
        clock_id=context["clock_id"],
        horizon_start_s=context["horizon_start_s"],
        horizon_end_s=context["horizon_end_s"],
        event_probability=probability_input.probability,
        probability_semantics=probability_input.probability_meaning,
        probability_conditioning=probability_input.conditioning,
        integrity_model_id=MODEL_ID,
        integrity_model_version=MODEL_VERSION,
        integrity_input_digest=input_digest,
        integrity_result_digest=result_binding_digest,
    )
    basic_event = FaultTreeBasicEvent(
        event_id=basis.event_id,
        probability=basis.event_probability,
        probability_meaning=basis.probability_semantics,
        conditioning=basis.probability_conditioning,
        probability_scope_id=probability_input.probability_scope_id,
        evidence_digest=basis.integrity_result_digest,
        integrity_event_basis=basis,
    )
    binding_calculation = Calculation(values={
        "adapter_model_id": MODEL_ID,
        "adapter_model_version": MODEL_VERSION,
        "event_id": basis.event_id,
        "basic_event": basic_event.model_dump(mode="json"),
        "integrity_event_basis": basis.model_dump(mode="json"),
        "source_model_id": SOURCE_MODEL_ID,
        "source_request_sha256": request_digest,
        "source_result_sha256": result_digest,
        "binding_input_sha256": input_digest,
        "binding_result_sha256": result_binding_digest,
        "asset_id": context["asset_id"],
        "location_id": context["location_id"],
        "physical_scope_id": context["physical_scope_id"],
        "clock_id": context["clock_id"],
        "horizon_start_s": context["horizon_start_s"],
        "horizon_end_s": context["horizon_end_s"],
        "condition_id": probability_input.condition_id,
        "condition_statement": probability_input.condition_statement,
        "crack_advance_limit_m": limit,
        "initial_crack_advance_m": advances[0],
        "final_crack_advance_m": advances[-1],
        "nominal_limit_reached_by_period_end": crossing_index is not None,
        "crossing_interval_bracket": crossing_bracket,
        "probability_inferred": False,
        "probability_source": "caller_supplied_with_explicit_evidence",
        "limit_evidence": request.limit_evidence.model_dump(mode="json"),
        "probability_evidence": [row.model_dump(mode="json") for row in probability_input.probability_evidence],
        "rights_boundary": probability_input.rights_boundary,
        "rights_authorization_digest": probability_input.rights_authorization_digest,
    })
    return SCCFaultTreeEventBinding(
        basic_event=basic_event,
        integrity_event_basis=basis,
        calculation=binding_calculation,
        limit_evidence=request.limit_evidence,
        probability_evidence=probability_input.probability_evidence,
        rights_boundary=probability_input.rights_boundary,
        rights_authorization_digest=probability_input.rights_authorization_digest,
    )


def evaluate_scc_fta_binding(request: SCCFaultTreeBindingRequest) -> Calculation:
    result = bind_scc_crack_advance_probability_to_fta(request)
    return result if isinstance(result, Calculation) else result.calculation


def _validate_binding_context(request: SCCFaultTreeBindingRequest, context: RunContext) -> None:
    source = request.scc_request
    if (context.asset_id, context.location_id, context.time_basis) != (
        source.asset_id, source.location_id, source.clock_id
    ):
        raise ValueError("SCC FTA binding RunContext must match the source asset, location and clock")


def specifications() -> list[ModelSpec]:
    return [ModelSpec(
        model_id=MODEL_ID,
        input_type=SCCFaultTreeBindingRequest,
        evaluator=evaluate_scc_fta_binding,
        units={
            "basic_event.probability": "1",
            "crack_advance_limit_m": "m",
            "initial_crack_advance_m": "m",
            "final_crack_advance_m": "m",
            "horizon_start_s": "s",
            "horizon_end_s": "s",
            "crossing_interval_bracket.start_time_s": "s",
            "crossing_interval_bracket.end_time_s": "s",
            "crossing_interval_bracket.left_crack_advance_m": "m",
            "crossing_interval_bracket.right_crack_advance_m": "m",
            "crossing_interval_bracket.limit_m": "m",
        },
        assumptions=(
            "Only the exact computed degradation.scc_crack_velocity_history result for the supplied request is eligible; the complete source calculation is recomputed and digest-compared.",
            "The event condition is caller-defined crack-advance limit reached within the exact finite SCC history support; the output records endpoint status and an interval bracket only.",
            "Probability and conditional_first_failure_in_period semantics, conditioning, common scope, Evidence and rights boundary are explicit caller inputs; probability is never inferred from deterministic growth.",
            "The output is an existing FaultTreeBasicEvent exchange payload and does not evaluate the FTA, validate the caller probability, or qualify the SCC growth law.",
        ),
        source_ids=(SOURCE_ID,),
        qualification="user_model",
        context_validator=_validate_binding_context,
    )]
