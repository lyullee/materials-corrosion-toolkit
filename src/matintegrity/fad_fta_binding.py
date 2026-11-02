"""Bind a caller probability to a computed FAD first-boundary-passage event."""

from __future__ import annotations

from typing import Literal

from pydantic import Field, model_validator

from .consequence_exchange import IntegrityEventBasis
from .contracts import Calculation, Contract, Evidence, Fraction, Positive, RunContext, canonical_digest
from .fad_history import (
    FADAssessmentHistoryRequest,
    MODEL_ID as FAD_HISTORY_MODEL_ID,
    evaluate_failure_assessment_history,
)
from .models.fault_tree import FaultTreeBasicEvent
from .registry import ModelSpec

MODEL_ID = "adapter.fad_assessment_history_to_fault_tree_basic_event"
MODEL_VERSION = "1"
SOURCE_ID = "caller_fad_boundary_first_passage_probability_binding"


class FADFaultTreeProbabilityInput(Contract):
    """Explicit caller probability and physical scope for the period event."""

    schema_version: Literal["matintegrity.fad_fta_probability_input.v1"] = (
        "matintegrity.fad_fta_probability_input.v1"
    )
    event_id: str = Field(min_length=1)
    failure_mode: str = Field(min_length=1)
    event_condition: Literal["first_outside_pinned_fad_boundary_during_period"]
    condition_id: str = Field(min_length=1)
    condition_statement: str = Field(min_length=1)
    probability: Fraction
    probability_meaning: Literal["conditional_first_failure_in_period"]
    conditioning: str = Field(min_length=1)
    probability_scope_id: str = Field(min_length=1)
    probability_evidence: tuple[Evidence, ...] = Field(min_length=1, max_length=128)
    rights_boundary: Literal["local_only", "caller_authorized_open_distribution"]
    rights_authorization_digest: str | None = Field(default=None, pattern=r"^[a-f0-9]{64}$")
    asset_id: str = Field(min_length=1)
    location_id: str = Field(min_length=1)
    physical_scope_id: str = Field(min_length=1)
    clock_id: str = Field(min_length=1)
    horizon_start_s: float = Field(ge=0)
    horizon_end_s: Positive
    material_condition_id: str = Field(min_length=1)
    geometry_basis_id: str = Field(min_length=1)
    load_history_id: str = Field(min_length=1)

    @model_validator(mode="after")
    def validate_period_and_rights(self):
        if self.horizon_end_s <= self.horizon_start_s:
            raise ValueError("probability event horizon must have positive duration")
        if self.rights_boundary == "caller_authorized_open_distribution" and self.rights_authorization_digest is None:
            raise ValueError("open distribution requires a caller-supplied authorization digest")
        if self.rights_boundary == "local_only" and self.rights_authorization_digest is not None:
            raise ValueError("local-only boundary must not claim an open-distribution authorization digest")
        return self


class FADFaultTreeBindingRequest(Contract):
    """Exact FAD history request/result, plus caller-defined FTA probability."""

    schema_version: Literal["matintegrity.fad_fta_binding_request.v1"] = (
        "matintegrity.fad_fta_binding_request.v1"
    )
    fad_request: FADAssessmentHistoryRequest
    fad_result: Calculation
    probability_input: FADFaultTreeProbabilityInput


class FADFaultTreeEventBinding(Contract):
    """Validated FTA payload, FAD history lineage and nominal interval bracket."""

    schema_version: Literal["matintegrity.fad_fta_event_binding.v1"] = (
        "matintegrity.fad_fta_event_binding.v1"
    )
    basic_event: FaultTreeBasicEvent
    integrity_event_basis: IntegrityEventBasis
    calculation: Calculation
    probability_evidence: tuple[Evidence, ...]
    rights_boundary: Literal["local_only", "caller_authorized_open_distribution"]
    rights_authorization_digest: str | None = Field(default=None, pattern=r"^[a-f0-9]{64}$")


def _history_scope(request: FADAssessmentHistoryRequest) -> dict:
    return {
        "assessment_id": request.assessment_id,
        "asset_id": request.asset_id,
        "location_id": request.location_id,
        "physical_scope_id": request.physical_scope_id,
        "clock_id": request.clock_id,
        "horizon_start_s": request.knots[0].time_s,
        "horizon_end_s": request.knots[-1].time_s,
        "time_s": [knot.time_s for knot in request.knots],
        "material_condition_id": request.material_condition_id,
        "geometry_basis_id": request.geometry_basis_id,
        "load_history_id": request.load_history_id,
    }


def _validate_history_result(
    request: FADAssessmentHistoryRequest, result: Calculation
) -> tuple[str, str, dict, list[dict]] | Calculation:
    request_digest = canonical_digest(request.model_dump(mode="json"))
    result_digest = canonical_digest(result.model_dump(mode="json"))
    values = result.values
    context = _history_scope(request)
    if values.get("model_id") != FAD_HISTORY_MODEL_ID:
        return Calculation(status="out_of_scope", values={
            "reason": "fad_history_model_id_mismatch",
            "expected_model_id": FAD_HISTORY_MODEL_ID,
            "actual_model_id": values.get("model_id"),
            "probability_inferred": False,
        })
    if values.get("input_sha256") != request_digest:
        return Calculation(status="out_of_scope", values={
            "reason": "fad_history_request_digest_mismatch",
            "input_sha256": request_digest,
            "result_input_sha256": values.get("input_sha256"),
            "fad_result_sha256": result_digest,
            "probability_inferred": False,
        })
    if values.get("curve_sha256") != request.curve_sha256:
        return Calculation(status="out_of_scope", values={
            "reason": "fad_curve_digest_mismatch",
            "expected_curve_sha256": request.curve_sha256,
            "result_curve_sha256": values.get("curve_sha256"),
            "probability_inferred": False,
        })
    if result.status != "computed":
        return Calculation(status="needs_data", values={
            "reason": "computed_fad_history_required",
            "fad_status": result.status,
            "input_sha256": request_digest,
            "fad_result_sha256": result_digest,
            "probability_inferred": False,
        })

    reproduced = evaluate_failure_assessment_history(request)
    if (
        reproduced.status != "computed"
        or canonical_digest(reproduced.model_dump(mode="json")) != result_digest
    ):
        return Calculation(status="out_of_scope", values={
            "reason": "fad_result_does_not_match_recomputed_source_calculation",
            "input_sha256": request_digest,
            "fad_result_sha256": result_digest,
            "recomputed_status": reproduced.status,
            "probability_inferred": False,
        })

    required = {
        "assessment_id": context["assessment_id"],
        "asset_id": context["asset_id"],
        "location_id": context["location_id"],
        "physical_scope_id": context["physical_scope_id"],
        "clock_id": context["clock_id"],
        "horizon_start_s": context["horizon_start_s"],
        "horizon_end_s": context["horizon_end_s"],
        "material_condition_id": context["material_condition_id"],
        "geometry_basis_id": context["geometry_basis_id"],
        "load_history_id": context["load_history_id"],
    }
    if any(values.get(key) != value for key, value in required.items()):
        return Calculation(status="out_of_scope", values={
            "reason": "fad_result_scope_or_horizon_mismatch",
            "input_sha256": request_digest,
            "fad_result_sha256": result_digest,
            "probability_inferred": False,
        })
    rows = values.get("knot_results")
    if not isinstance(rows, list) or len(rows) != len(request.knots):
        return Calculation(status="out_of_scope", values={
            "reason": "fad_result_knot_history_mismatch",
            "input_sha256": request_digest,
            "fad_result_sha256": result_digest,
            "probability_inferred": False,
        })
    if [row.get("time_s") for row in rows] != context["time_s"]:
        return Calculation(status="out_of_scope", values={
            "reason": "fad_result_time_knots_mismatch",
            "input_sha256": request_digest,
            "fad_result_sha256": result_digest,
            "probability_inferred": False,
        })
    if values.get("initially_outside_boundary") is True:
        return Calculation(status="out_of_scope", values={
            "reason": "fad_boundary_already_outside_at_horizon_start",
            "initial_margin": rows[0].get("vertical_toughness_ratio_margin"),
            "horizon_start_s": context["horizon_start_s"],
            "probability_inferred": False,
        })
    if values.get("exact_crossing_time_reported") is not False:
        return Calculation(status="out_of_scope", values={
            "reason": "unexpected_exact_crossing_time_claim",
            "input_sha256": request_digest,
            "fad_result_sha256": result_digest,
            "probability_inferred": False,
        })
    return request_digest, result_digest, context, rows


def bind_fad_history_probability_to_fta(
    request: FADFaultTreeBindingRequest,
) -> FADFaultTreeEventBinding | Calculation:
    """Bind a separate caller probability to first FAD-boundary passage in a period."""

    checked = _validate_history_result(request.fad_request, request.fad_result)
    if isinstance(checked, Calculation):
        return checked
    request_digest, result_digest, context, rows = checked
    probability = request.probability_input
    expected_scope = {
        "asset_id": context["asset_id"],
        "location_id": context["location_id"],
        "physical_scope_id": context["physical_scope_id"],
        "clock_id": context["clock_id"],
        "horizon_start_s": context["horizon_start_s"],
        "horizon_end_s": context["horizon_end_s"],
        "material_condition_id": context["material_condition_id"],
        "geometry_basis_id": context["geometry_basis_id"],
        "load_history_id": context["load_history_id"],
    }
    if any(getattr(probability, key) != value for key, value in expected_scope.items()):
        return Calculation(status="out_of_scope", values={
            "reason": "caller_probability_scope_or_horizon_mismatch",
            "input_sha256": request_digest,
            "fad_result_sha256": result_digest,
            "probability_inferred": False,
        })

    crossing_bracket = request.fad_result.values.get("first_outside_boundary_interval_bracket")
    nominal_status = request.fad_result.values.get("first_outside_boundary_status")
    binding_digest = canonical_digest({
        "adapter_model_id": MODEL_ID,
        "adapter_model_version": MODEL_VERSION,
        "fad_request_sha256": request_digest,
        "fad_result_sha256": result_digest,
        "source_scope": context,
        "event_condition_id": probability.condition_id,
        "event_condition": probability.event_condition,
        "event_condition_statement": probability.condition_statement,
        "event_probability": probability.probability,
        "probability_meaning": probability.probability_meaning,
        "conditioning": probability.conditioning,
        "probability_scope_id": probability.probability_scope_id,
        "probability_evidence": [row.model_dump(mode="json") for row in probability.probability_evidence],
        "rights_boundary": probability.rights_boundary,
        "rights_authorization_digest": probability.rights_authorization_digest,
    })
    result_binding_digest = canonical_digest({
        "binding_input_sha256": binding_digest,
        "fad_result_sha256": result_digest,
        "event_id": probability.event_id,
        "nominal_fad_status": nominal_status,
        "crossing_interval_bracket": crossing_bracket,
        "probability": probability.probability,
        "probability_meaning": probability.probability_meaning,
        "conditioning": probability.conditioning,
        "probability_scope_id": probability.probability_scope_id,
        "rights_boundary": probability.rights_boundary,
        "rights_authorization_digest": probability.rights_authorization_digest,
    })
    basis = IntegrityEventBasis(
        event_id=probability.event_id,
        asset_id=context["asset_id"],
        location_id=context["location_id"],
        failure_mode=probability.failure_mode,
        physical_scope_id=context["physical_scope_id"],
        clock_id=context["clock_id"],
        horizon_start_s=context["horizon_start_s"],
        horizon_end_s=context["horizon_end_s"],
        event_probability=probability.probability,
        probability_semantics=probability.probability_meaning,
        probability_conditioning=probability.conditioning,
        integrity_model_id=MODEL_ID,
        integrity_model_version=MODEL_VERSION,
        integrity_input_digest=binding_digest,
        integrity_result_digest=result_binding_digest,
    )
    basic_event = FaultTreeBasicEvent(
        event_id=basis.event_id,
        probability=basis.event_probability,
        probability_meaning=basis.probability_semantics,
        conditioning=basis.probability_conditioning,
        probability_scope_id=probability.probability_scope_id,
        evidence_digest=basis.integrity_result_digest,
        integrity_event_basis=basis,
    )
    calculation = Calculation(values={
        "adapter_model_id": MODEL_ID,
        "adapter_model_version": MODEL_VERSION,
        "basic_event": basic_event.model_dump(mode="json"),
        "integrity_event_basis": basis.model_dump(mode="json"),
        "fad_model_id": FAD_HISTORY_MODEL_ID,
        "fad_request_sha256": request_digest,
        "fad_result_sha256": result_digest,
        "binding_input_sha256": binding_digest,
        "binding_result_sha256": result_binding_digest,
        "asset_id": context["asset_id"],
        "location_id": context["location_id"],
        "physical_scope_id": context["physical_scope_id"],
        "clock_id": context["clock_id"],
        "horizon_start_s": context["horizon_start_s"],
        "horizon_end_s": context["horizon_end_s"],
        "material_condition_id": context["material_condition_id"],
        "geometry_basis_id": context["geometry_basis_id"],
        "load_history_id": context["load_history_id"],
        "event_condition_id": probability.condition_id,
        "event_condition": probability.event_condition,
        "event_condition_statement": probability.condition_statement,
        "nominal_fad_status": nominal_status,
        "nominal_first_outside_boundary_interval_bracket": crossing_bracket,
        "initial_margin": rows[0]["vertical_toughness_ratio_margin"],
        "final_margin": rows[-1]["vertical_toughness_ratio_margin"],
        "probability": probability.probability,
        "probability_meaning": probability.probability_meaning,
        "probability_inferred": False,
        "probability_source": "caller_supplied_with_explicit_evidence",
        "probability_evidence": [row.model_dump(mode="json") for row in probability.probability_evidence],
        "rights_boundary": probability.rights_boundary,
        "rights_authorization_digest": probability.rights_authorization_digest,
    })
    return FADFaultTreeEventBinding(
        basic_event=basic_event,
        integrity_event_basis=basis,
        calculation=calculation,
        probability_evidence=probability.probability_evidence,
        rights_boundary=probability.rights_boundary,
        rights_authorization_digest=probability.rights_authorization_digest,
    )


def evaluate_fad_fta_binding(request: FADFaultTreeBindingRequest) -> Calculation:
    result = bind_fad_history_probability_to_fta(request)
    return result if isinstance(result, Calculation) else result.calculation


def _validate_binding_context(request: FADFaultTreeBindingRequest, context: RunContext) -> None:
    source = request.fad_request
    if (context.asset_id, context.location_id, context.time_basis) != (
        source.asset_id, source.location_id, source.clock_id
    ):
        raise ValueError("FAD FTA binding RunContext must match source asset, location and clock")


def specifications() -> list[ModelSpec]:
    return [ModelSpec(
        model_id=MODEL_ID,
        input_type=FADFaultTreeBindingRequest,
        evaluator=evaluate_fad_fta_binding,
        units={
            "basic_event.probability": "1",
            "horizon_start_s": "s",
            "horizon_end_s": "s",
            "initial_margin": "1",
            "final_margin": "1",
            "nominal_first_outside_boundary_interval_bracket.left_time_s": "s",
            "nominal_first_outside_boundary_interval_bracket.right_time_s": "s",
            "nominal_first_outside_boundary_interval_bracket.left_margin": "1",
            "nominal_first_outside_boundary_interval_bracket.right_margin": "1",
        },
        assumptions=(
            "Only the exact computed structural.failure_assessment_history result for the supplied request is eligible; the full deterministic source calculation is recomputed and digest-compared.",
            "The event is caller-defined first passage outside the exact pinned FAD boundary during the finite source history; only the source knot interval bracket is reported.",
            "Probability, conditional_first_failure_in_period semantics, conditioning, shared probability scope, Evidence and rights boundary are explicit caller inputs; probability is never inferred from FAD margins.",
            "The output is an existing FaultTreeBasicEvent exchange payload and does not evaluate the FTA, validate probability calibration, or qualify provider mechanics or the FAD curve.",
        ),
        source_ids=(SOURCE_ID,),
        qualification="user_model",
        context_validator=_validate_binding_context,
    )]
