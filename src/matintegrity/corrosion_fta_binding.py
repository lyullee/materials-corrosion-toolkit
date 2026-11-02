"""Bind an explicit caller probability to a reviewed corrosion thickness condition.

This adapter does not turn deterministic metal-loss calculations into probabilities.
"""

from __future__ import annotations

from typing import Literal

from pydantic import Field, model_validator

from .consequence_exchange import IntegrityEventBasis
from .contracts import Calculation, Contract, Evidence, Fraction, RunContext, canonical_digest
from .corrosion_rate_history import (
    CorrosionRateThicknessHistoryRequest,
    MODEL_ID as CORROSION_MODEL_ID,
)
from .models.fault_tree import FaultTreeBasicEvent
from .registry import ModelSpec

MODEL_ID = "adapter.corrosion_rate_history_to_fault_tree_basic_event"
MODEL_VERSION = "1"
SOURCE_ID = "caller_corrosion_fta_event_probability_binding"


class CorrosionFaultTreeProbabilityInput(Contract):
    """Caller-owned event definition and probability provenance for FTA exchange."""

    schema_version: Literal["matintegrity.corrosion_fta_probability_input.v1"] = (
        "matintegrity.corrosion_fta_probability_input.v1"
    )
    event_id: str = Field(min_length=1)
    failure_mode: str = Field(min_length=1)
    condition_id: str = Field(min_length=1)
    condition_statement: str = Field(min_length=1)
    condition_basis: Literal["required_thickness_crossing_within_history_support"]
    probability: Fraction
    # The mapped condition is a threshold crossing over a finite period, so other
    # probability meanings are not interchangeable inputs for this event.
    probability_meaning: Literal["conditional_first_failure_in_period"]
    conditioning: str = Field(min_length=1)
    probability_scope_id: str = Field(min_length=1)
    probability_evidence: tuple[Evidence, ...] = Field(min_length=1)
    # Explicitly state whether these caller-provided materials may leave the local boundary.
    rights_boundary: Literal["local_only", "caller_authorized_open_distribution"]
    rights_authorization_digest: str | None = Field(default=None, pattern=r"^[a-f0-9]{64}$")

    @model_validator(mode="after")
    def validate_rights_boundary(self):
        if self.rights_boundary == "caller_authorized_open_distribution" and self.rights_authorization_digest is None:
            raise ValueError("open distribution requires a caller-supplied authorization digest")
        if self.rights_boundary == "local_only" and self.rights_authorization_digest is not None:
            raise ValueError("local-only boundary must not claim an open-distribution authorization digest")
        return self


class CorrosionFaultTreeBindingRequest(Contract):
    """Registry input combining one finite corrosion result and caller p basis."""

    schema_version: Literal["matintegrity.corrosion_fta_binding_request.v1"] = (
        "matintegrity.corrosion_fta_binding_request.v1"
    )
    corrosion_request: CorrosionRateThicknessHistoryRequest
    corrosion_result: Calculation
    probability_input: CorrosionFaultTreeProbabilityInput | None = None


class CorrosionFaultTreeEventBinding(Contract):
    """Validated FTA basic event plus the matching integrity-event exchange basis."""

    schema_version: Literal["matintegrity.corrosion_fta_event_binding.v1"] = (
        "matintegrity.corrosion_fta_event_binding.v1"
    )
    basic_event: FaultTreeBasicEvent
    integrity_event_basis: IntegrityEventBasis
    calculation: Calculation
    rights_boundary: Literal["local_only", "caller_authorized_open_distribution"]
    source_evidence: tuple[Evidence, ...]
    probability_evidence: tuple[Evidence, ...]


def bind_corrosion_history_probability_to_fta(
    request: CorrosionRateThicknessHistoryRequest,
    corrosion_result: Calculation,
    probability_input: CorrosionFaultTreeProbabilityInput | None,
) -> CorrosionFaultTreeEventBinding | Calculation:
    """Create a consistent FTA event only from an explicit external probability input.

    The selected condition is the request's required-thickness crossing over the finite
    supplied history support. Probability, semantics, conditioning, scope and evidence
    are caller supplied and are never calculated or defaulted by this adapter.
    """
    request_digest = canonical_digest(request.model_dump(mode="json"))
    result_digest = canonical_digest(corrosion_result.model_dump(mode="json"))
    if corrosion_result.values.get("model_id") != CORROSION_MODEL_ID:
        return Calculation(status="out_of_scope", values={"reason": "corrosion_result_model_id_mismatch"})
    if corrosion_result.values.get("request_sha256") != request_digest:
        return Calculation(status="out_of_scope", values={"reason": "corrosion_result_request_digest_mismatch"})
    if corrosion_result.status != "computed" or corrosion_result.values.get("status") != "computed":
        return Calculation(status="needs_data", values={
            "reason": "computed_corrosion_history_required",
            "corrosion_status": corrosion_result.status,
            "request_sha256": request_digest,
            "corrosion_result_sha256": result_digest,
            "probability_inferred": False,
        })
    if probability_input is None:
        return Calculation(status="needs_data", values={
            "reason": "caller_probability_conditioning_scope_evidence_and_rights_boundary_required",
            "request_sha256": request_digest,
            "corrosion_result_sha256": result_digest,
            "probability_inferred": False,
        })

    expected_context = {
        "asset_id": request.asset_id,
        "location_id": request.location_id,
        "physical_scope_id": request.physical_scope_id,
        "time_basis": request.time_basis,
        "support_start_s": request.knots[0].time_s,
        "support_end_s": request.knots[-1].time_s,
        "required_thickness_m": request.required_thickness_m,
        "condition_basis": probability_input.condition_basis,
        "condition_id": probability_input.condition_id,
        "condition_statement": probability_input.condition_statement,
    }
    if (
        corrosion_result.values.get("asset_id") != request.asset_id
        or corrosion_result.values.get("location_id") != request.location_id
        or corrosion_result.values.get("physical_scope_id") != request.physical_scope_id
        or corrosion_result.values.get("time_basis") != request.time_basis
        or corrosion_result.values.get("support_start_s") != request.knots[0].time_s
        or corrosion_result.values.get("support_end_s") != request.knots[-1].time_s
        or corrosion_result.values.get("required_thickness_m") != request.required_thickness_m
    ):
        return Calculation(status="out_of_scope", values={
            "reason": "corrosion_result_scope_time_or_condition_input_mismatch",
            "request_sha256": request_digest,
            "corrosion_result_sha256": result_digest,
            "probability_inferred": False,
        })

    evidence_records = {
        "source_evidence": [row.model_dump(mode="json") for knot in request.knots for row in knot.evidence]
        + [request.baseline_evidence.model_dump(mode="json"), request.required_thickness_evidence.model_dump(mode="json")],
        "probability_evidence": [row.model_dump(mode="json") for row in probability_input.probability_evidence],
    }
    event_input_digest = canonical_digest({
        "corrosion_request_sha256": request_digest,
        "corrosion_result_sha256": result_digest,
        "probability_input": probability_input.model_dump(mode="json"),
    })
    # The integrity-result digest represents this explicit event binding and retains both
    # upstream digests; it is not a digest of a probability inferred from corrosion loss.
    bound_result_digest = canonical_digest({
        "adapter_model_id": MODEL_ID,
        "adapter_model_version": MODEL_VERSION,
        "input_sha256": event_input_digest,
        "corrosion_result_sha256": result_digest,
        "condition": expected_context,
        "probability": probability_input.probability,
        "probability_meaning": probability_input.probability_meaning,
        "conditioning": probability_input.conditioning,
        "probability_scope_id": probability_input.probability_scope_id,
        "evidence": evidence_records,
        "rights_boundary": probability_input.rights_boundary,
        "rights_authorization_digest": probability_input.rights_authorization_digest,
    })
    basis = IntegrityEventBasis(
        event_id=probability_input.event_id,
        asset_id=request.asset_id,
        location_id=request.location_id,
        failure_mode=probability_input.failure_mode,
        physical_scope_id=request.physical_scope_id,
        clock_id=request.time_basis,
        horizon_start_s=request.knots[0].time_s,
        horizon_end_s=request.knots[-1].time_s,
        event_probability=probability_input.probability,
        probability_semantics=probability_input.probability_meaning,
        probability_conditioning=probability_input.conditioning,
        integrity_model_id=MODEL_ID,
        integrity_model_version=MODEL_VERSION,
        integrity_input_digest=event_input_digest,
        integrity_result_digest=bound_result_digest,
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
        "corrosion_request_sha256": request_digest,
        "corrosion_result_sha256": result_digest,
        "integrity_input_sha256": event_input_digest,
        "integrity_result_sha256": bound_result_digest,
        "condition": expected_context,
        "probability_inferred": False,
        "probability_source": "caller_supplied_with_explicit_evidence",
        "source_evidence": evidence_records["source_evidence"],
        "probability_evidence": evidence_records["probability_evidence"],
        "rights_boundary": probability_input.rights_boundary,
        "rights_authorization_digest": probability_input.rights_authorization_digest,
        "deterministic_crossing_observation": corrosion_result.values.get("first_required_thickness_crossing"),
        "horizon_start_s": basis.horizon_start_s,
        "horizon_end_s": basis.horizon_end_s,
        "time_basis": request.time_basis,
    })
    return CorrosionFaultTreeEventBinding(
        basic_event=basic_event,
        integrity_event_basis=basis,
        calculation=binding_calculation,
        rights_boundary=probability_input.rights_boundary,
        source_evidence=tuple(
            [row for knot in request.knots for row in knot.evidence]
            + [request.baseline_evidence, request.required_thickness_evidence]
        ),
        probability_evidence=probability_input.probability_evidence,
    )


def evaluate_corrosion_fault_tree_binding(request: CorrosionFaultTreeBindingRequest) -> Calculation:
    """Return a registry-compatible result containing the explicit FTA payload."""
    result = bind_corrosion_history_probability_to_fta(
        request.corrosion_request,
        request.corrosion_result,
        request.probability_input,
    )
    return result if isinstance(result, Calculation) else result.calculation


def _validate_binding_context(request: CorrosionFaultTreeBindingRequest, context: RunContext) -> None:
    source = request.corrosion_request
    if (context.asset_id, context.location_id, context.time_basis) != (
        source.asset_id, source.location_id, source.time_basis
    ):
        raise ValueError("FTA binding RunContext must match the corrosion history asset, location and time basis")


def specifications() -> list[ModelSpec]:
    return [ModelSpec(
        model_id=MODEL_ID,
        input_type=CorrosionFaultTreeBindingRequest,
        evaluator=evaluate_corrosion_fault_tree_binding,
        units={
            "basic_event.probability": "1",
            "integrity_event_basis.horizon_start_s": "s",
            "integrity_event_basis.horizon_end_s": "s",
        },
        assumptions=(
            "The deterministic corrosion calculation defines the reviewed condition and finite support but never supplies an event probability.",
            "The mapped event is first crossing of required thickness within the finite supplied period; only conditional first-failure-in-period probability semantics are accepted, while probability, conditioning, shared scope, Evidence and rights remain caller-owned.",
            "The output is an exchange binding for the existing FTA basic-event contract; it neither evaluates the tree nor validates the caller probability.",
        ),
        source_ids=(SOURCE_ID,),
        qualification="user_model",
        context_validator=_validate_binding_context,
    )]
