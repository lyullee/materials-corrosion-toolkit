"""Bind caller-supplied probability to a computed Crevice/Faradaic result for FTA."""

from __future__ import annotations

from typing import Literal

from pydantic import Field, model_validator

from .consequence_exchange import IntegrityEventBasis
from .contracts import Calculation, Contract, Evidence, Fraction, RunContext, canonical_digest
from .crevice_faradaic_spatial_chemistry_coupling import (
    CreviceFaradaicSpatialChemistryRequest,
    MODEL_ID as CREVICE_FARADAIC_MODEL_ID,
)
from .models.fault_tree import FaultTreeBasicEvent, FaultTreeProbabilityMeaning
from .registry import ModelSpec

MODEL_ID = "adapter.crevice_faradaic_to_fault_tree_basic_event"
MODEL_VERSION = "1"
SOURCE_ID = "caller_crevice_faradaic_fta_probability_binding"


class CreviceFaradaicFaultTreeProbabilityInput(Contract):
    """Caller-owned event probability and its scope, semantics and evidence."""

    schema_version: Literal["matintegrity.crevice_faradaic_fta_probability_input.v1"] = (
        "matintegrity.crevice_faradaic_fta_probability_input.v1"
    )
    event_id: str = Field(min_length=1)
    failure_mode: str = Field(min_length=1)
    condition_id: str = Field(min_length=1)
    condition_statement: str = Field(min_length=1)
    probability: Fraction
    probability_meaning: FaultTreeProbabilityMeaning
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


class CreviceFaradaicFaultTreeBindingRequest(Contract):
    """One exact Crevice/Faradaic request/result pair and explicit probability inputs."""

    schema_version: Literal["matintegrity.crevice_faradaic_fta_binding.v1"] = (
        "matintegrity.crevice_faradaic_fta_binding.v1"
    )
    integrity_request: CreviceFaradaicSpatialChemistryRequest
    integrity_result: Calculation
    calculation_evidence: Evidence
    probability_input: CreviceFaradaicFaultTreeProbabilityInput


class CreviceFaradaicFaultTreeEventBinding(Contract):
    """Basic event and integrity basis tied to the source computation and caller p."""

    schema_version: Literal["matintegrity.crevice_faradaic_fta_event_binding.v1"] = (
        "matintegrity.crevice_faradaic_fta_event_binding.v1"
    )
    basic_event: FaultTreeBasicEvent
    integrity_event_basis: IntegrityEventBasis
    calculation: Calculation
    calculation_evidence: Evidence
    probability_evidence: tuple[Evidence, ...]
    rights_boundary: Literal["local_only", "caller_authorized_open_distribution"]
    rights_authorization_digest: str | None = Field(default=None, pattern=r"^[a-f0-9]{64}$")


def _source_context(request: CreviceFaradaicSpatialChemistryRequest) -> dict:
    template = request.mixed_potential_template
    times = template.time_s
    return {
        "asset_id": template.asset_id,
        "location_id": template.location_id,
        "physical_scope_id": template.physical_scope_id,
        "clock_id": template.clock_id,
        "horizon_start_s": times[0],
        "horizon_end_s": times[-1],
        "assessment_id": request.assessment_id,
        "time_s": list(times),
    }


def _validate_source_result(
    request: CreviceFaradaicSpatialChemistryRequest,
    result: Calculation,
) -> tuple[str, str, dict] | Calculation:
    request_digest = canonical_digest(request.model_dump(mode="json"))
    result_digest = canonical_digest(result.model_dump(mode="json"))
    values = result.values
    if values.get("model_id") != CREVICE_FARADAIC_MODEL_ID:
        return Calculation(status="out_of_scope", values={
            "reason": "crevice_faradaic_result_model_id_mismatch",
            "expected_model_id": CREVICE_FARADAIC_MODEL_ID,
            "actual_model_id": values.get("model_id"),
            "probability_inferred": False,
        })
    if values.get("input_sha256") != request_digest:
        return Calculation(status="out_of_scope", values={
            "reason": "crevice_faradaic_result_request_digest_mismatch",
            "request_sha256": request_digest,
            "result_input_sha256": values.get("input_sha256"),
            "crevice_faradaic_result_sha256": result_digest,
            "probability_inferred": False,
        })
    if result.status != "computed":
        return Calculation(status="needs_data", values={
            "reason": "computed_crevice_faradaic_result_required",
            "source_status": result.status,
            "request_sha256": request_digest,
            "crevice_faradaic_result_sha256": result_digest,
            "probability_inferred": False,
        })
    if values.get("status") != "computed":
        return Calculation(status="needs_data", values={
            "reason": "computed_crevice_faradaic_inner_status_required",
            "source_status": result.status,
            "inner_status": values.get("status"),
            "request_sha256": request_digest,
            "crevice_faradaic_result_sha256": result_digest,
            "probability_inferred": False,
        })
    context = _source_context(request)
    expected_times = context["time_s"]
    intervals = values.get("intervals")
    if (
        values.get("assessment_id") != request.assessment_id
        or values.get("all_requested_intervals_committed") is not True
        or values.get("committed_interval_count") != len(expected_times) - 1
        or not isinstance(intervals, list)
        or len(intervals) != len(expected_times) - 1
    ):
        return Calculation(status="out_of_scope", values={
            "reason": "crevice_faradaic_result_incomplete_or_assessment_mismatch",
            "request_sha256": request_digest,
            "crevice_faradaic_result_sha256": result_digest,
            "probability_inferred": False,
        })
    for index, interval in enumerate(intervals):
        if (
            not isinstance(interval, dict)
            or interval.get("committed") is not True
            or interval.get("start_time_s") != expected_times[index]
            or interval.get("end_time_s") != expected_times[index + 1]
        ):
            return Calculation(status="out_of_scope", values={
                "reason": "crevice_faradaic_result_time_basis_or_interval_mismatch",
                "interval_index": index,
                "request_sha256": request_digest,
                "crevice_faradaic_result_sha256": result_digest,
                "probability_inferred": False,
            })
    return request_digest, result_digest, context


def bind_crevice_faradaic_probability_to_fta(
    request: CreviceFaradaicFaultTreeBindingRequest,
) -> CreviceFaradaicFaultTreeEventBinding | Calculation:
    """Create an FTA event only from an exact computed result and caller probability.

    This adapter does not convert corrosion, Faradaic current, reaction extent, or a
    deterministic calculation into an event probability.
    """
    validated = _validate_source_result(request.integrity_request, request.integrity_result)
    if isinstance(validated, Calculation):
        return validated
    request_digest, result_digest, context = validated
    probability_input = request.probability_input
    if (
        request.calculation_evidence.source_id != CREVICE_FARADAIC_MODEL_ID
        or request.calculation_evidence.origin != "model_prediction"
        or request.calculation_evidence.sha256 != result_digest
    ):
        return Calculation(status="out_of_scope", values={
            "reason": "calculation_evidence_must_pin_exact_computed_result",
            "request_sha256": request_digest,
            "crevice_faradaic_result_sha256": result_digest,
            "probability_inferred": False,
        })

    input_digest = canonical_digest({
        "source_model_id": CREVICE_FARADAIC_MODEL_ID,
        "source_request_sha256": request_digest,
        "source_result_sha256": result_digest,
        "source_context": context,
        "calculation_evidence": request.calculation_evidence.model_dump(mode="json"),
        "probability_input": probability_input.model_dump(mode="json"),
    })
    result_binding_digest = canonical_digest({
        "adapter_model_id": MODEL_ID,
        "adapter_model_version": MODEL_VERSION,
        "binding_input_sha256": input_digest,
        "source_model_id": CREVICE_FARADAIC_MODEL_ID,
        "source_request_sha256": request_digest,
        "source_result_sha256": result_digest,
        "asset_id": context["asset_id"],
        "location_id": context["location_id"],
        "physical_scope_id": context["physical_scope_id"],
        "clock_id": context["clock_id"],
        "horizon_start_s": context["horizon_start_s"],
        "horizon_end_s": context["horizon_end_s"],
        "condition_id": probability_input.condition_id,
        "condition_statement": probability_input.condition_statement,
        "failure_mode": probability_input.failure_mode,
        "probability": probability_input.probability,
        "probability_meaning": probability_input.probability_meaning,
        "conditioning": probability_input.conditioning,
        "probability_scope_id": probability_input.probability_scope_id,
        "probability_evidence": [e.model_dump(mode="json") for e in probability_input.probability_evidence],
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
        "source_model_id": CREVICE_FARADAIC_MODEL_ID,
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
        "probability_inferred": False,
        "probability_source": "caller_supplied_with_explicit_evidence",
        "calculation_evidence": request.calculation_evidence.model_dump(mode="json"),
        "probability_evidence": [e.model_dump(mode="json") for e in probability_input.probability_evidence],
        "rights_boundary": probability_input.rights_boundary,
        "rights_authorization_digest": probability_input.rights_authorization_digest,
    })
    return CreviceFaradaicFaultTreeEventBinding(
        basic_event=basic_event,
        integrity_event_basis=basis,
        calculation=binding_calculation,
        calculation_evidence=request.calculation_evidence,
        probability_evidence=probability_input.probability_evidence,
        rights_boundary=probability_input.rights_boundary,
        rights_authorization_digest=probability_input.rights_authorization_digest,
    )


def evaluate_crevice_faradaic_fta_binding(request: CreviceFaradaicFaultTreeBindingRequest) -> Calculation:
    result = bind_crevice_faradaic_probability_to_fta(request)
    return result if isinstance(result, Calculation) else result.calculation


def _validate_binding_context(request: CreviceFaradaicFaultTreeBindingRequest, context: RunContext) -> None:
    basis = request.integrity_request.mixed_potential_template
    if (context.asset_id, context.location_id, context.time_basis) != (
        basis.asset_id, basis.location_id, basis.clock_id
    ):
        raise ValueError("FTA binding RunContext must match Crevice/Faradaic asset, location and clock")


def specifications() -> tuple[ModelSpec, ...]:
    return (ModelSpec(
        model_id=MODEL_ID,
        input_type=CreviceFaradaicFaultTreeBindingRequest,
        evaluator=evaluate_crevice_faradaic_fta_binding,
        units={"basic_event.probability": "1", "horizon_start_s": "s", "horizon_end_s": "s"},
        assumptions=(
            "Only a computed integration.crevice_faradaic_spatial_chemistry_coupling result whose model ID, exact request digest, assessment ID and all interval endpoints match is eligible for binding.",
            "Asset, location, physical scope and clock are carried from the matching caller request; the finite event horizon is its exact time support.",
            "Probability, probability meaning, conditioning, probability scope and probability Evidence are explicit caller inputs and are never inferred from transport or Faradaic quantities.",
            "The calculation Evidence must be a model-prediction record whose digest equals the complete source Calculation digest.",
            "This module creates an existing FaultTreeBasicEvent payload; it does not assess the fault tree or qualify the underlying integrity model.",
        ),
        source_ids=(SOURCE_ID,),
        qualification="user_model",
        context_validator=_validate_binding_context,
    ),)
