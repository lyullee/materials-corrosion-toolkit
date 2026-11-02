"""Bounded callback-based localization of a reviewed scalar contact transition."""

from __future__ import annotations

import math
from collections.abc import Callable
from typing import Literal

from pydantic import Field, model_validator

from ..contracts import AssessmentResult, Calculation, Contract, Evidence, canonical_digest
from ..registry import ModelSpec

_BRACKET_MODEL_ID = "fabrication.gasket_contact_transition_brackets"


class ContactResponseQuery(Contract):
    """An exact external FE/contact evaluation request for one time and response."""

    schema_version: Literal["matintegrity.contact_response_query.v1"] = (
        "matintegrity.contact_response_query.v1"
    )
    assessment_id: str = Field(min_length=1)
    source_bracket_result_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    source_contact_history_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    context_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    physical_scope_id: str = Field(min_length=1)
    asset_id: str = Field(min_length=1)
    location_id: str = Field(min_length=1)
    time_basis: str = Field(min_length=1)
    node_id: str = Field(min_length=1)
    query_time_s: float = Field(ge=0)
    response_definition_id: str = Field(min_length=1)
    response_unit: str = Field(min_length=1)
    provider_id: str = Field(min_length=1)
    provider_revision: str = Field(min_length=1)
    provider_configuration_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    query_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")

    @model_validator(mode="after")
    def verify_query_digest(self):
        if not math.isfinite(self.query_time_s):
            raise ValueError("query time must be finite")
        expected = canonical_digest(self.model_dump(mode="json", exclude={"query_sha256"}))
        if self.query_sha256 != expected:
            raise ValueError("query digest mismatch")
        return self


class ContactResponseReceipt(Contract):
    """External scalar response tied to an exact query and solver result digest."""

    schema_version: Literal["matintegrity.contact_response_receipt.v1"] = (
        "matintegrity.contact_response_receipt.v1"
    )
    query_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    source_bracket_result_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    source_contact_history_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    physical_scope_id: str = Field(min_length=1)
    asset_id: str = Field(min_length=1)
    location_id: str = Field(min_length=1)
    time_basis: str = Field(min_length=1)
    context_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    node_id: str = Field(min_length=1)
    time_s: float = Field(ge=0)
    response_definition_id: str = Field(min_length=1)
    response_unit: str = Field(min_length=1)
    response_value: float
    provider_id: str = Field(min_length=1)
    provider_revision: str = Field(min_length=1)
    provider_configuration_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    solver_result_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    evidence: tuple[Evidence, ...] = Field(min_length=1)
    result_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")

    @model_validator(mode="after")
    def verify_result_digest(self):
        if not math.isfinite(self.time_s) or not math.isfinite(self.response_value):
            raise ValueError("response time and value must be finite")
        expected = canonical_digest(self.model_dump(mode="json", exclude={"result_sha256"}))
        if self.result_sha256 != expected:
            raise ValueError("provider response result digest mismatch")
        return self


class GasketContactRootLocalization(Contract):
    """Narrow one caller-reviewed scalar sign-change bracket using an FE callback."""

    schema_version: Literal["matintegrity.gasket_contact_root_localization.v1"] = (
        "matintegrity.gasket_contact_root_localization.v1"
    )
    assessment_id: str = Field(min_length=1)
    physical_scope_id: str = Field(min_length=1)
    source_bracket_result: AssessmentResult
    source_bracket_result_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    node_id: str = Field(min_length=1)
    lower_time_s: float = Field(ge=0)
    upper_time_s: float = Field(gt=0)
    response_definition_id: str = Field(min_length=1)
    response_unit: str = Field(min_length=1)
    provider_id: str = Field(min_length=1)
    provider_revision: str = Field(min_length=1)
    provider_configuration_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    lower_endpoint: ContactResponseReceipt
    upper_endpoint: ContactResponseReceipt
    time_tolerance_s: float = Field(gt=0)
    maximum_evaluations: int = Field(ge=1, le=128)
    single_continuous_monotone_root_reviewed: bool
    contact_response_semantics_reviewed: bool
    physical_scope_and_time_basis_reviewed: bool
    provider_identity_revision_configuration_reviewed: bool
    computational_use_authorized: bool

    @model_validator(mode="after")
    def coherent_bracket_and_lineage(self):
        if not (math.isfinite(self.lower_time_s) and math.isfinite(self.upper_time_s)
                and math.isfinite(self.time_tolerance_s)):
            raise ValueError("times and tolerance must be finite")
        if self.lower_time_s >= self.upper_time_s:
            raise ValueError("lower endpoint time must precede upper endpoint time")
        if self.upper_time_s - self.lower_time_s <= self.time_tolerance_s:
            raise ValueError("initial bracket is already within tolerance")

        source = self.source_bracket_result
        if source.model_id != _BRACKET_MODEL_ID or source.status != "computed":
            raise ValueError("a computed gasket contact-transition bracket result is required")
        if canonical_digest(source.model_dump(mode="json")) != self.source_bracket_result_sha256:
            raise ValueError("source bracket result digest mismatch")
        expected_input_digest = canonical_digest({
            "model_id": source.model_id,
            "model_version": source.model_version,
            "inputs": source.inputs,
            "context": source.context.model_dump(mode="json"),
        })
        if source.input_digest != expected_input_digest:
            raise ValueError("source bracket input/context digest does not verify")
        if source.inputs.get("physical_scope_id") != self.physical_scope_id:
            raise ValueError("physical scope does not match source bracket")
        context_sha = canonical_digest(source.context.model_dump(mode="json"))
        source_history_sha = source.values.get("contact_history_sha256")
        if not isinstance(source_history_sha, str) or len(source_history_sha) != 64:
            raise ValueError("source bracket lacks the contact-history digest")

        matching_brackets = [row for row in source.values.get("transition_brackets", [])
                             if isinstance(row, dict)
                             and row.get("node_id") == self.node_id
                             and row.get("lower_time_s") == self.lower_time_s
                             and row.get("upper_time_s") == self.upper_time_s]
        if len(matching_brackets) != 1:
            raise ValueError("selected interval must match exactly one supplied transition bracket")

        receipts = ((self.lower_endpoint, self.lower_time_s),
                    (self.upper_endpoint, self.upper_time_s))
        for receipt, endpoint_time in receipts:
            query = _query(
                assessment_id=self.assessment_id,
                source=self.source_bracket_result,
                source_bracket_sha=self.source_bracket_result_sha256,
                source_history_sha=source_history_sha,
                physical_scope_id=self.physical_scope_id,
                node_id=self.node_id,
                time_s=endpoint_time,
                response_definition_id=self.response_definition_id,
                response_unit=self.response_unit,
                provider_id=self.provider_id,
                provider_revision=self.provider_revision,
                provider_configuration_sha256=self.provider_configuration_sha256,
            )
            problem = _receipt_problem(query, receipt)
            if problem:
                raise ValueError(f"endpoint receipt does not match the declared source: {problem}")

        left, right = self.lower_endpoint.response_value, self.upper_endpoint.response_value
        if not ((left < 0 < right) or (right < 0 < left)):
            raise ValueError("endpoint responses must have strict opposite signs")
        return self


ContactResponseProvider = Callable[[ContactResponseQuery], ContactResponseReceipt | dict]


def localize_gasket_contact_response_root(
    request: GasketContactRootLocalization,
    *,
    contact_response_provider: ContactResponseProvider,
) -> Calculation:
    """Bisect one signed response bracket, preserving receipts and stopping on first fault."""

    source = request.source_bracket_result
    history_sha = source.values["contact_history_sha256"]
    reviews = {
        "single_continuous_monotone_root_reviewed": request.single_continuous_monotone_root_reviewed,
        "contact_response_semantics_reviewed": request.contact_response_semantics_reviewed,
        "physical_scope_and_time_basis_reviewed": request.physical_scope_and_time_basis_reviewed,
        "provider_identity_revision_configuration_reviewed": request.provider_identity_revision_configuration_reviewed,
        "computational_use_authorized": request.computational_use_authorized,
    }
    base = {
        "assessment_id": request.assessment_id,
        "physical_scope_id": request.physical_scope_id,
        "asset_id": source.context.asset_id,
        "location_id": source.context.location_id,
        "time_basis": source.context.time_basis,
        "node_id": request.node_id,
        "response_definition_id": request.response_definition_id,
        "response_unit": request.response_unit,
        "source_bracket_result_sha256": request.source_bracket_result_sha256,
        "source_contact_history_sha256": history_sha,
        "provider_id": request.provider_id,
        "provider_revision": request.provider_revision,
        "provider_configuration_sha256": request.provider_configuration_sha256,
        "initial_lower_time_s": request.lower_time_s,
        "initial_upper_time_s": request.upper_time_s,
        "requested_time_tolerance_s": request.time_tolerance_s,
        "maximum_evaluations": request.maximum_evaluations,
        "event_time_s": None,
        "exact_event_time_claimed": False,
        "hidden_or_multiple_roots_searched": False,
        "seal_acceptance_or_leakage_inferred": False,
        "failure_probability_inferred": False,
    }
    missing = [name for name, reviewed in reviews.items() if not reviewed]
    if missing:
        return Calculation(status="needs_data", values=base | {
            "missing_reviews": missing,
            "evaluation_prefix": [],
            "first_failure": {"reason": "required_review_missing"},
        })
    if not callable(contact_response_provider):
        return Calculation(status="needs_data", values=base | {
            "evaluation_prefix": [],
            "first_failure": {"reason": "provider_callback_not_callable"},
        })

    lower_t, upper_t = request.lower_time_s, request.upper_time_s
    lower_r = request.lower_endpoint.response_value
    upper_r = request.upper_endpoint.response_value
    current_lower_receipt_sha = request.lower_endpoint.result_sha256
    current_upper_receipt_sha = request.upper_endpoint.result_sha256
    prefix: list[dict] = []
    for evaluation_index in range(request.maximum_evaluations):
        width = upper_t - lower_t
        if width <= request.time_tolerance_s:
            return Calculation(values=base | {
                "localized_bracket_lower_time_s": lower_t,
                "localized_bracket_upper_time_s": upper_t,
                "localized_bracket_width_s": width,
                "lower_endpoint_response_value": lower_r,
                "upper_endpoint_response_value": upper_r,
                "lower_endpoint_receipt_sha256": current_lower_receipt_sha,
                "upper_endpoint_receipt_sha256": current_upper_receipt_sha,
                "completed_evaluation_count": len(prefix),
                "evaluation_prefix": prefix,
                "time_tolerance_met": True,
                "reviewed_single_monotone_root_assumption_used": True,
                "root_estimate_time_s": None,
                "meaning": "caller-reviewed single-root sign-change interval narrowed by external response evaluations",
            }, notes=(
                "The returned interval remains a bracket; it is not an exact root or transition time.",
                "The algorithm searches only the declared interval and does not discover hidden or multiple roots.",
            ))

        midpoint = lower_t + width * 0.5
        if not math.isfinite(midpoint) or midpoint <= lower_t or midpoint >= upper_t:
            return _incomplete(base, lower_t, upper_t, lower_r, upper_r, prefix, {
                "reason": "floating_point_midpoint_cannot_shrink_bracket",
                "evaluation_index": evaluation_index,
            })
        query = _query(
            assessment_id=request.assessment_id,
            source=source,
            source_bracket_sha=request.source_bracket_result_sha256,
            source_history_sha=history_sha,
            physical_scope_id=request.physical_scope_id,
            node_id=request.node_id,
            time_s=midpoint,
            response_definition_id=request.response_definition_id,
            response_unit=request.response_unit,
            provider_id=request.provider_id,
            provider_revision=request.provider_revision,
            provider_configuration_sha256=request.provider_configuration_sha256,
        )
        try:
            raw = contact_response_provider(query)
            receipt = ContactResponseReceipt.model_validate(raw)
        except Exception as exc:
            return _incomplete(base, lower_t, upper_t, lower_r, upper_r, prefix, {
                "reason": "provider_call_or_receipt_validation_failed",
                "evaluation_index": evaluation_index,
                "query_time_s": midpoint,
                "query_sha256": query.query_sha256,
                "error_type": type(exc).__name__,
            })
        problem = _receipt_problem(query, receipt)
        if problem:
            return _incomplete(base, lower_t, upper_t, lower_r, upper_r, prefix,
                               problem | {"evaluation_index": evaluation_index})

        value = receipt.response_value
        if not min(lower_r, upper_r) <= value <= max(lower_r, upper_r):
            return _incomplete(base, lower_t, upper_t, lower_r, upper_r, prefix, {
                "reason": "provider_response_violates_declared_monotone_endpoint_range",
                "evaluation_index": evaluation_index,
                "query_time_s": midpoint,
                "response_value": value,
                "response_result_sha256": receipt.result_sha256,
            })
        if value == 0:
            prefix.append(_prefix_row(evaluation_index, query, receipt))
            return Calculation(values=base | {
                "localized_bracket_lower_time_s": midpoint,
                "localized_bracket_upper_time_s": midpoint,
                "localized_bracket_width_s": 0.0,
                "lower_endpoint_response_value": value,
                "upper_endpoint_response_value": value,
                "zero_response_receipt_sha256": receipt.result_sha256,
                "completed_evaluation_count": len(prefix),
                "evaluation_prefix": prefix,
                "time_tolerance_met": True,
                "reviewed_single_monotone_root_assumption_used": True,
                "root_estimate_time_s": None,
                "zero_response_observed_at_query": True,
                "meaning": "external solver returned an exactly zero declared response at the queried time; event-time identity is not asserted",
            }, notes=(
                "An exact zero scalar response was returned by the provider for this query; this does not establish a physical event time.",
                "No search for additional or hidden roots was performed.",
            ))

        prefix.append(_prefix_row(evaluation_index, query, receipt))
        if (lower_r < 0 < upper_r and value < 0) or (upper_r < 0 < lower_r and value > 0):
            lower_t, lower_r = midpoint, value
            current_lower_receipt_sha = receipt.result_sha256
        elif (lower_r < 0 < upper_r and value > 0) or (upper_r < 0 < lower_r and value < 0):
            upper_t, upper_r = midpoint, value
            current_upper_receipt_sha = receipt.result_sha256
        else:
            return _incomplete(base, lower_t, upper_t, lower_r, upper_r, prefix, {
                "reason": "midpoint_response_no_longer_brackets_a_sign_change",
                "evaluation_index": evaluation_index,
                "query_time_s": midpoint,
                "response_value": value,
                "response_result_sha256": receipt.result_sha256,
            })

    return _incomplete(base, lower_t, upper_t, lower_r, upper_r, prefix, {
        "reason": "maximum_provider_evaluations_reached_before_time_tolerance",
        "evaluation_index": request.maximum_evaluations,
    })


def _query(
    *, assessment_id: str, source: AssessmentResult, source_bracket_sha: str,
    source_history_sha: str, physical_scope_id: str, node_id: str, time_s: float,
    response_definition_id: str, response_unit: str, provider_id: str,
    provider_revision: str, provider_configuration_sha256: str,
) -> ContactResponseQuery:
    context = source.context
    body = {
        "schema_version": "matintegrity.contact_response_query.v1",
        "assessment_id": assessment_id,
        "source_bracket_result_sha256": source_bracket_sha,
        "source_contact_history_sha256": source_history_sha,
        "context_sha256": canonical_digest(context.model_dump(mode="json")),
        "physical_scope_id": physical_scope_id,
        "asset_id": context.asset_id,
        "location_id": context.location_id,
        "time_basis": context.time_basis,
        "node_id": node_id,
        "query_time_s": time_s,
        "response_definition_id": response_definition_id,
        "response_unit": response_unit,
        "provider_id": provider_id,
        "provider_revision": provider_revision,
        "provider_configuration_sha256": provider_configuration_sha256,
    }
    return ContactResponseQuery(**(body | {"query_sha256": canonical_digest(body)}))


def _receipt_problem(query: ContactResponseQuery, receipt: ContactResponseReceipt) -> dict | None:
    exact_fields = {
        "query_sha256": query.query_sha256,
        "source_bracket_result_sha256": query.source_bracket_result_sha256,
        "source_contact_history_sha256": query.source_contact_history_sha256,
        "physical_scope_id": query.physical_scope_id,
        "asset_id": query.asset_id,
        "location_id": query.location_id,
        "time_basis": query.time_basis,
        "context_sha256": query.context_sha256,
        "node_id": query.node_id,
        "time_s": query.query_time_s,
        "response_definition_id": query.response_definition_id,
        "response_unit": query.response_unit,
        "provider_id": query.provider_id,
        "provider_revision": query.provider_revision,
        "provider_configuration_sha256": query.provider_configuration_sha256,
    }
    mismatch = [key for key, expected in exact_fields.items()
                if getattr(receipt, key) != expected]
    if mismatch:
        return {"reason": "provider_receipt_does_not_match_exact_query", "mismatched_fields": mismatch}
    if not any(item.source_id == query.provider_id for item in receipt.evidence):
        return {"reason": "provider_evidence_missing_declared_provider_identity"}
    return None


def _prefix_row(index: int, query: ContactResponseQuery,
                receipt: ContactResponseReceipt) -> dict:
    return {
        "evaluation_index": index,
        "query_time_s": query.query_time_s,
        "query_sha256": query.query_sha256,
        "response_value": receipt.response_value,
        "response_definition_id": receipt.response_definition_id,
        "response_unit": receipt.response_unit,
        "provider_id": receipt.provider_id,
        "provider_revision": receipt.provider_revision,
        "provider_configuration_sha256": receipt.provider_configuration_sha256,
        "solver_result_sha256": receipt.solver_result_sha256,
        "receipt_sha256": receipt.result_sha256,
        "evidence": [item.model_dump(mode="json") for item in receipt.evidence],
    }


def _incomplete(base: dict, lower_t: float, upper_t: float,
                lower_r: float, upper_r: float, prefix: list[dict],
                first_failure: dict) -> Calculation:
    return Calculation(status="needs_data", values=base | {
        "localized_bracket_lower_time_s": lower_t,
        "localized_bracket_upper_time_s": upper_t,
        "localized_bracket_width_s": upper_t - lower_t,
        "lower_endpoint_response_value": lower_r,
        "upper_endpoint_response_value": upper_r,
        "completed_evaluation_count": len(prefix),
        "evaluation_prefix": prefix,
        "time_tolerance_met": False,
        "reviewed_single_monotone_root_assumption_used": True,
        "root_estimate_time_s": None,
        "first_failure": first_failure,
    }, notes=(
        "Refinement stopped without meeting the requested interval width; successful receipts and the first failure are retained.",
        "No event-time, hidden-root, multiple-root, leakage, acceptance, or probability claim is made.",
    ))


def specifications() -> list[ModelSpec]:
    return [ModelSpec(
        model_id="fabrication.gasket_contact_root_localization",
        input_type=GasketContactRootLocalization,
        evaluator=localize_gasket_contact_response_root,
        units={
            "localized_bracket_lower_time_s": "s",
            "localized_bracket_upper_time_s": "s",
            "localized_bracket_width_s": "s",
            "evaluation_prefix[].query_time_s": "s",
        },
        assumptions=(
            "A computed caller-supplied contact-transition bracket and digest-matched endpoint responses with strict opposite signs are required.",
            "The caller reviews that exactly one continuous monotone response root exists in the selected bracket; hidden or multiple roots are not searched.",
            "Each midpoint response comes from the declared external provider callback and is checked against query, solver, context and evidence digests.",
            "The result is a narrowed interval or incomplete prefix, not an exact event time, leak rate, seal acceptance or probability.",
        ),
        source_ids=("caller_gasket_contact_response_root_localization",),
        qualification="user_model",
        runtime_dependency_names=("contact_response_provider",),
    )]
