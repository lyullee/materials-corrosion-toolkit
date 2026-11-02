"""Refine an observed gasket contact transition bracket through a caller callback."""

from __future__ import annotations

import math
from collections.abc import Callable
from typing import Literal

from pydantic import Field, model_validator

from ..contracts import (
    AssessmentResult,
    Calculation,
    Contract,
    Evidence,
    RunContext,
    canonical_digest,
)
from ..registry import ModelSpec

_BRACKET_MODEL = "fabrication.gasket_contact_transition_brackets"
_HISTORY_MODELS = {
    "fabrication.flange_viscoelastic_contact_history",
    "fabrication.flange_nonlinear_viscoelastic_contact_history",
}


class GasketContactTransitionRefinement(Contract):
    """Bind one initial state-change bracket to a reviewed provider and budget."""

    schema_version: Literal["matintegrity.gasket_contact_transition_refinement.v1"] = (
        "matintegrity.gasket_contact_transition_refinement.v1"
    )
    assessment_id: str = Field(min_length=1)
    physical_scope_id: str = Field(min_length=1)
    initial_bracket_result: AssessmentResult
    initial_bracket_result_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    contact_history_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    node_id: str = Field(min_length=1)
    from_state: Literal["open", "closed"]
    to_state: Literal["open", "closed"]
    lower_time_s: float = Field(ge=0)
    upper_time_s: float = Field(gt=0)
    provider_id: str = Field(min_length=1)
    provider_revision: str = Field(min_length=1)
    provider_configuration_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    time_tolerance_s: float = Field(gt=0)
    maximum_evaluations: int = Field(ge=1, le=100_000)
    monotonic_single_transition_reviewed: bool
    provider_identity_and_configuration_reviewed: bool
    physical_scope_and_time_basis_reviewed: bool
    computational_use_authorized: bool

    @model_validator(mode="after")
    def bind_initial_observation(self):
        if self.from_state == self.to_state:
            raise ValueError("transition bracket endpoint states must differ")
        if not math.isfinite(self.lower_time_s) or not math.isfinite(self.upper_time_s):
            raise ValueError("transition bracket times must be finite")
        if self.upper_time_s <= self.lower_time_s:
            raise ValueError("upper bracket time must be greater than lower bracket time")
        result = self.initial_bracket_result
        if result.model_id != _BRACKET_MODEL or result.status != "computed":
            raise ValueError("a computed contact-transition bracket assessment is required")
        if canonical_digest(result.model_dump(mode="json")) != self.initial_bracket_result_sha256:
            raise ValueError("initial bracket result digest mismatch")
        expected_input = canonical_digest({
            "model_id": result.model_id,
            "model_version": result.model_version,
            "inputs": result.inputs,
            "context": result.context.model_dump(mode="json"),
        })
        if result.input_digest != expected_input:
            raise ValueError("initial bracket result input/context digest mismatch")
        if (result.values.get("physical_scope_id") != self.physical_scope_id
                or result.values.get("contact_history_sha256") != self.contact_history_sha256):
            raise ValueError("initial bracket source or physical scope does not match this request")

        transition_rows = result.values.get("transition_brackets")
        if not isinstance(transition_rows, list):
            raise ValueError("initial result has no transition bracket rows")
        matches = [
            row for row in transition_rows
            if isinstance(row, dict)
            and row.get("node_id") == self.node_id
            and row.get("from_state") == self.from_state
            and row.get("to_state") == self.to_state
            and row.get("lower_time_s") == self.lower_time_s
            and row.get("upper_time_s") == self.upper_time_s
        ]
        if len(matches) != 1:
            raise ValueError("the requested node/state/time bracket must match exactly one source row")
        if matches[0].get("event_time_s") is not None:
            raise ValueError("the initial source row must remain an unresolved time bracket")

        input_values = result.inputs
        raw_history = input_values.get("contact_history")
        if not isinstance(raw_history, dict):
            raise ValueError("initial bracket request does not retain its source contact history")
        history_result = AssessmentResult.model_validate(raw_history)
        if (history_result.model_id not in _HISTORY_MODELS or history_result.status != "computed"
                or canonical_digest(history_result.model_dump(mode="json")) != self.contact_history_sha256):
            raise ValueError("pinned source contact history does not match the initial bracket")
        expected_history_input = canonical_digest({
            "model_id": history_result.model_id,
            "model_version": history_result.model_version,
            "inputs": history_result.inputs,
            "context": history_result.context.model_dump(mode="json"),
        })
        if history_result.input_digest != expected_history_input:
            raise ValueError("source contact history input/context digest mismatch")
        if history_result.inputs.get("physical_scope_id") != self.physical_scope_id:
            raise ValueError("source contact history does not match the requested physical scope")
        if history_result.context.model_dump(mode="json") != result.context.model_dump(mode="json"):
            raise ValueError("initial bracket and source contact history contexts differ")
        if history_result.units.get("time_history[].time_s") != "s":
            raise ValueError("source contact history must declare seconds")

        endpoints = _source_endpoint_states(history_result, self.node_id, self.lower_time_s, self.upper_time_s)
        if endpoints != (self.from_state, self.to_state):
            raise ValueError("source history endpoint states do not support the requested transition direction")
        return self


class ExternalContactStateQuery(Contract):
    """Exact midpoint query supplied to a caller-owned FE/contact solver callback."""

    schema_version: Literal["matintegrity.external_contact_state_query.v1"] = (
        "matintegrity.external_contact_state_query.v1"
    )
    assessment_id: str
    initial_bracket_result_sha256: str
    contact_history_sha256: str
    physical_scope_id: str
    asset_id: str
    location_id: str
    time_basis: str
    context_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    node_id: str
    query_time_s: float
    expected_endpoint_states: tuple[Literal["open", "closed"], Literal["open", "closed"]]
    provider_id: str
    provider_revision: str
    provider_configuration_sha256: str
    query_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")

    @model_validator(mode="after")
    def coherent_query(self):
        if self.expected_endpoint_states[0] == self.expected_endpoint_states[1]:
            raise ValueError("query endpoint states must differ")
        if not math.isfinite(self.query_time_s) or self.query_time_s < 0:
            raise ValueError("query time must be finite and nonnegative")
        expected = canonical_digest(self.model_dump(mode="json", exclude={"query_sha256"}))
        if self.query_sha256 != expected:
            raise ValueError("provider query digest mismatch")
        return self


class ExternalContactStateResponse(Contract):
    """A provider state observation bound to one exact query and its Evidence."""

    schema_version: Literal["matintegrity.external_contact_state_response.v1"] = (
        "matintegrity.external_contact_state_response.v1"
    )
    query_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    provider_id: str = Field(min_length=1)
    provider_revision: str = Field(min_length=1)
    provider_configuration_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    physical_scope_id: str = Field(min_length=1)
    asset_id: str = Field(min_length=1)
    location_id: str = Field(min_length=1)
    time_basis: str = Field(min_length=1)
    context_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    node_id: str = Field(min_length=1)
    time_s: float = Field(ge=0)
    contact_state: Literal["open", "closed"]
    evidence: tuple[Evidence, ...] = Field(min_length=1)
    result_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")

    @model_validator(mode="after")
    def verify_result_digest(self):
        if not math.isfinite(self.time_s):
            raise ValueError("provider response time must be finite")
        expected = canonical_digest(self.model_dump(mode="json", exclude={"result_sha256"}))
        if self.result_sha256 != expected:
            raise ValueError("provider response digest mismatch")
        return self


ContactStateProvider = Callable[[ExternalContactStateQuery], ExternalContactStateResponse | dict]


def _source_endpoint_states(
    result: AssessmentResult,
    node_id: str,
    lower_time_s: float,
    upper_time_s: float,
) -> tuple[str, str]:
    history = result.values.get("time_history")
    if not isinstance(history, list):
        raise ValueError("source contact history has no time_history")
    found: dict[float, str] = {}
    for knot in history:
        if not isinstance(knot, dict) or knot.get("status") not in (None, "computed"):
            raise ValueError("source contact history contains an incomplete knot")
        time_s = knot.get("time_s")
        field = knot.get("response_field")
        if not isinstance(time_s, (int, float)) or isinstance(time_s, bool) or not math.isfinite(time_s):
            raise ValueError("source contact history contains an invalid time")
        if not isinstance(field, list):
            raise ValueError("source contact history contains a missing response field")
        selected = [row for row in field if isinstance(row, dict) and row.get("node_id") == node_id]
        state = selected[0].get("contact_state") if len(selected) == 1 else None
        if len(selected) != 1 or not isinstance(state, str) or state not in {"open", "closed"}:
            raise ValueError("source endpoint node is missing, duplicated, or has an invalid state")
        found[float(time_s)] = selected[0]["contact_state"]
    if lower_time_s not in found or upper_time_s not in found:
        raise ValueError("initial bracket endpoints must be exact computed source knots")
    return found[lower_time_s], found[upper_time_s]


def refine_gasket_contact_transition_bracket(
    request: GasketContactTransitionRefinement,
    *,
    contact_state_provider: ContactStateProvider,
) -> Calculation:
    """Use provider midpoint states to narrow a bracket, never to claim an exact event time."""

    source = request.initial_bracket_result
    missing_reviews = [
        name for name, reviewed in {
            "monotonic_single_transition_reviewed": request.monotonic_single_transition_reviewed,
            "provider_identity_and_configuration_reviewed": request.provider_identity_and_configuration_reviewed,
            "physical_scope_and_time_basis_reviewed": request.physical_scope_and_time_basis_reviewed,
            "computational_use_authorized": request.computational_use_authorized,
        }.items() if not reviewed
    ]
    base = {
        "assessment_id": request.assessment_id,
        "asset_id": source.context.asset_id,
        "location_id": source.context.location_id,
        "time_basis": source.context.time_basis,
        "physical_scope_id": request.physical_scope_id,
        "node_id": request.node_id,
        "from_state": request.from_state,
        "to_state": request.to_state,
        "provider_id": request.provider_id,
        "provider_revision": request.provider_revision,
        "provider_configuration_sha256": request.provider_configuration_sha256,
        "initial_bracket_result_sha256": request.initial_bracket_result_sha256,
        "contact_history_sha256": request.contact_history_sha256,
        "initial_bracket_lower_time_s": request.lower_time_s,
        "initial_bracket_upper_time_s": request.upper_time_s,
        "requested_time_tolerance_s": request.time_tolerance_s,
        "maximum_evaluations": request.maximum_evaluations,
        "event_time_s": None,
        "exact_event_time_claimed": False,
        "seal_acceptance_or_leakage_inferred": False,
        "failure_probability_inferred": False,
    }
    if missing_reviews:
        return Calculation(status="needs_data", values=base | {
            "missing_reviews": missing_reviews,
            "completed_evaluation_count": 0,
            "evaluation_prefix": [],
            "first_failure": {"reason": "required_review_missing"},
        })
    if not callable(contact_state_provider):
        return Calculation(status="needs_data", values=base | {
            "completed_evaluation_count": 0,
            "evaluation_prefix": [],
            "first_failure": {"reason": "provider_callback_not_callable"},
        })

    lower, upper = request.lower_time_s, request.upper_time_s
    lower_state, upper_state = request.from_state, request.to_state
    prefix: list[dict] = []
    for evaluation_index in range(request.maximum_evaluations):
        width = upper - lower
        if width <= request.time_tolerance_s:
            return Calculation(values=base | {
                "refined_bracket_lower_time_s": lower,
                "refined_bracket_upper_time_s": upper,
                "refined_bracket_width_s": width,
                "lower_endpoint_state": lower_state,
                "upper_endpoint_state": upper_state,
                "completed_evaluation_count": len(prefix),
                "evaluation_prefix": prefix,
                "bracket_tolerance_met": True,
                "monotonic_single_transition_assumption_used": True,
                "event_time_s": None,
                "meaning": "caller-reviewed provider bracket refinement only; transition time remains between reported endpoints",
            }, notes=(
                "The requested bracket width was reached using exact midpoint state evaluations from the declared external provider.",
                "The returned interval is not an exact event time or a seal-acceptance, leakage, or probability result.",
            ))

        midpoint = lower + width * 0.5
        if not math.isfinite(midpoint) or midpoint <= lower or midpoint >= upper:
            failure = {"reason": "floating_point_midpoint_cannot_shrink_bracket", "evaluation_index": evaluation_index}
            return _incomplete_result(base, lower, upper, lower_state, upper_state, prefix, failure)
        query_body = {
            "schema_version": "matintegrity.external_contact_state_query.v1",
            "assessment_id": request.assessment_id,
            "initial_bracket_result_sha256": request.initial_bracket_result_sha256,
            "contact_history_sha256": request.contact_history_sha256,
            "physical_scope_id": request.physical_scope_id,
            "asset_id": source.context.asset_id,
            "location_id": source.context.location_id,
            "time_basis": source.context.time_basis,
            "context_sha256": canonical_digest(source.context.model_dump(mode="json")),
            "node_id": request.node_id,
            "query_time_s": midpoint,
            "expected_endpoint_states": (lower_state, upper_state),
            "provider_id": request.provider_id,
            "provider_revision": request.provider_revision,
            "provider_configuration_sha256": request.provider_configuration_sha256,
        }
        query = ExternalContactStateQuery(**(query_body | {"query_sha256": canonical_digest(query_body)}))
        try:
            raw_response = contact_state_provider(query)
            response = ExternalContactStateResponse.model_validate(raw_response)
        except Exception as exc:
            failure = {
                "reason": "provider_call_or_response_validation_failed",
                "evaluation_index": evaluation_index,
                "query_time_s": midpoint,
                "query_sha256": query.query_sha256,
                "error_type": type(exc).__name__,
            }
            return _incomplete_result(base, lower, upper, lower_state, upper_state, prefix, failure)

        response_problem = _response_problem(request, query, response)
        if response_problem is not None:
            failure = response_problem | {"evaluation_index": evaluation_index}
            return _incomplete_result(base, lower, upper, lower_state, upper_state, prefix, failure)
        if response.contact_state not in {lower_state, upper_state}:
            failure = {
                "reason": "provider_state_conflicts_with_monotonic_single_transition_bracket",
                "evaluation_index": evaluation_index,
                "provider_state": response.contact_state,
            }
            return _incomplete_result(base, lower, upper, lower_state, upper_state, prefix, failure)

        prefix.append({
            "evaluation_index": evaluation_index,
            "query_time_s": midpoint,
            "query_sha256": query.query_sha256,
            "provider_id": response.provider_id,
            "provider_revision": response.provider_revision,
            "provider_configuration_sha256": response.provider_configuration_sha256,
            "contact_state": response.contact_state,
            "response_sha256": response.result_sha256,
            "evidence": [item.model_dump(mode="json") for item in response.evidence],
        })
        if response.contact_state == lower_state:
            lower = midpoint
        else:
            upper = midpoint

    failure = {
        "reason": "maximum_provider_evaluations_reached_before_time_tolerance",
        "evaluation_index": request.maximum_evaluations,
    }
    return _incomplete_result(base, lower, upper, lower_state, upper_state, prefix, failure)


def _response_problem(
    request: GasketContactTransitionRefinement,
    query: ExternalContactStateQuery,
    response: ExternalContactStateResponse,
) -> dict | None:
    if response.query_sha256 != query.query_sha256:
        return {"reason": "provider_response_query_digest_mismatch"}
    if response.provider_id != request.provider_id:
        return {"reason": "provider_identity_mismatch"}
    if response.provider_revision != request.provider_revision:
        return {"reason": "provider_revision_mismatch"}
    if response.provider_configuration_sha256 != request.provider_configuration_sha256:
        return {"reason": "provider_configuration_digest_mismatch"}
    if response.node_id != request.node_id:
        return {"reason": "provider_node_identity_mismatch"}
    if (response.physical_scope_id != request.physical_scope_id
            or response.asset_id != query.asset_id
            or response.location_id != query.location_id
            or response.time_basis != query.time_basis
            or response.context_sha256 != query.context_sha256):
        return {"reason": "provider_response_context_mismatch"}
    if response.time_s != query.query_time_s:
        return {"reason": "provider_time_does_not_match_exact_query"}
    if not any(row.source_id == request.provider_id for row in response.evidence):
        return {"reason": "provider_evidence_missing_declared_provider_identity"}
    return None


def _incomplete_result(
    base: dict,
    lower: float,
    upper: float,
    lower_state: str,
    upper_state: str,
    prefix: list[dict],
    failure: dict,
) -> Calculation:
    return Calculation(status="needs_data", values=base | {
        "refined_bracket_lower_time_s": lower,
        "refined_bracket_upper_time_s": upper,
        "refined_bracket_width_s": upper - lower,
        "lower_endpoint_state": lower_state,
        "upper_endpoint_state": upper_state,
        "completed_evaluation_count": len(prefix),
        "evaluation_prefix": prefix,
        "bracket_tolerance_met": False,
        "monotonic_single_transition_assumption_used": True,
        "event_time_s": None,
        "first_failure": failure,
    }, notes=(
        "The refinement stopped without meeting the requested time tolerance; the complete successful provider prefix and first failure are retained.",
        "No exact transition time or acceptance, leakage, or failure probability is claimed.",
    ))


def _validate_context(request: GasketContactTransitionRefinement, context: RunContext) -> None:
    source = request.initial_bracket_result.context
    if (context.asset_id, context.location_id, context.time_basis) != (
        source.asset_id, source.location_id, source.time_basis,
    ):
        raise ValueError("refinement RunContext must match the initial bracket source")


def specifications() -> list[ModelSpec]:
    return [ModelSpec(
        "fabrication.gasket_contact_transition_refinement",
        GasketContactTransitionRefinement,
        refine_gasket_contact_transition_bracket,
        {
            "lower_time_s": "s",
            "upper_time_s": "s",
            "time_tolerance_s": "s",
            "refined_bracket_lower_time_s": "s",
            "refined_bracket_upper_time_s": "s",
            "refined_bracket_width_s": "s",
            "evaluation_prefix[].query_time_s": "s",
        },
        (
            "Refine one caller-selected contact-state bracket only with exact provider midpoint evaluations, matching provider identity/revision/configuration and Evidence-bound response digests.",
            "A reviewed monotonic single transition in the starting bracket is required. The result is a bounded bracket, not an exact event time or local FE qualification.",
        ),
        ("caller_external_flange_contact_state_provider",),
        qualification="user_model",
        context_validator=_validate_context,
        runtime_dependency_names=("contact_state_provider",),
    )]
