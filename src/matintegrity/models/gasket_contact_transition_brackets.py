"""Summarize observed contact-state transitions between computed flange-history knots."""

from __future__ import annotations

import math
from typing import Literal

from pydantic import Field, model_validator

from ..contracts import AssessmentResult, Calculation, Contract, RunContext, canonical_digest
from ..registry import ModelSpec

_HISTORY_MODELS = {
    "fabrication.flange_viscoelastic_contact_history",
    "fabrication.flange_nonlinear_viscoelastic_contact_history",
}


class GasketContactTransitionBrackets(Contract):
    """Report node state changes only as brackets bounded by supplied solver knots."""

    schema_version: Literal["matintegrity.gasket_contact_transition_brackets.v1"] = (
        "matintegrity.gasket_contact_transition_brackets.v1"
    )
    assessment_id: str = Field(min_length=1)
    physical_scope_id: str = Field(min_length=1)
    contact_history: AssessmentResult
    contact_history_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    physical_scope_and_time_basis_reviewed: bool
    contact_state_semantics_reviewed: bool
    computational_use_authorized: bool
    maximum_knot_count: int = Field(default=100_000, ge=2, le=1_000_000)
    maximum_node_count: int = Field(default=100_000, ge=1, le=1_000_000)

    @model_validator(mode="after")
    def coherent_source(self):
        result = self.contact_history
        if result.status != "computed" or result.model_id not in _HISTORY_MODELS:
            raise ValueError("a computed supported flange contact-history assessment is required")
        if canonical_digest(result.model_dump(mode="json")) != self.contact_history_sha256:
            raise ValueError("contact-history digest does not match the supplied result")
        expected_input = canonical_digest({
            "model_id": result.model_id,
            "model_version": result.model_version,
            "inputs": result.inputs,
            "context": result.context.model_dump(mode="json"),
        })
        if result.input_digest != expected_input:
            raise ValueError("contact-history input/context digest does not verify")
        if result.inputs.get("physical_scope_id") != self.physical_scope_id:
            raise ValueError("requested physical scope does not match the computed contact history")
        history = result.values.get("time_history")
        if not isinstance(history, list) or len(history) < 2 or len(history) > self.maximum_knot_count:
            raise ValueError("contact history knot count is outside the declared finite budget")
        return self


def audit_gasket_contact_transition_brackets(
    request: GasketContactTransitionBrackets,
) -> Calculation:
    """Locate state changes as endpoint brackets without inventing event times."""

    source = request.contact_history
    base = {
        "assessment_id": request.assessment_id,
        "asset_id": source.context.asset_id,
        "location_id": source.context.location_id,
        "time_basis": source.context.time_basis,
        "physical_scope_id": request.physical_scope_id,
        "contact_history_model_id": source.model_id,
        "contact_history_sha256": request.contact_history_sha256,
        "contact_history_input_digest": source.input_digest,
        "contact_history_context": source.context.model_dump(mode="json"),
        "contact_transition_event_time_claimed": False,
        "hidden_transitions_inferred": False,
        "seal_acceptance_or_leakage_inferred": False,
        "failure_probability_inferred": False,
    }
    reviews = {
        "physical_scope_and_time_basis_reviewed": request.physical_scope_and_time_basis_reviewed,
        "contact_state_semantics_reviewed": request.contact_state_semantics_reviewed,
        "computational_use_authorized": request.computational_use_authorized,
    }
    missing_reviews = [name for name, reviewed in reviews.items() if not reviewed]
    if missing_reviews:
        return Calculation(status="needs_data", values=base | {
            "missing_reviews": missing_reviews,
            "review_flags": reviews,
        })
    if source.units.get("time_history[].time_s") != "s":
        return Calculation(status="out_of_scope", values=base | {
            "out_of_scope_reason": "upstream_time_unit_not_explicitly_seconds",
        })

    history = source.values["time_history"]
    times: list[float] = []
    fields: list[list[dict]] = []
    ordered_nodes: list[str] | None = None
    for knot_index, knot in enumerate(history):
        if not isinstance(knot, dict) or knot.get("status") not in (None, "computed"):
            return Calculation(status="needs_data", values=base | {
                "out_of_scope_reason": "contact_history_contains_incomplete_knot",
                "failed_knot_index": knot_index,
                "validated_knot_count": len(times),
            })
        time_s = knot.get("time_s")
        if (isinstance(time_s, bool) or not isinstance(time_s, (int, float))
                or not math.isfinite(time_s) or time_s < 0):
            return Calculation(status="out_of_scope", values=base | {
                "out_of_scope_reason": "invalid_contact_history_time",
                "failed_knot_index": knot_index,
                "validated_knot_count": len(times),
            })
        field = knot.get("response_field")
        if not isinstance(field, list) or not field or len(field) > request.maximum_node_count:
            return Calculation(status="out_of_scope", values=base | {
                "out_of_scope_reason": "missing_or_over_budget_contact_field",
                "failed_knot_index": knot_index,
                "validated_knot_count": len(times),
            })
        node_ids: list[str] = []
        for node in field:
            if not isinstance(node, dict):
                return Calculation(status="out_of_scope", values=base | {
                    "out_of_scope_reason": "malformed_contact_field_row",
                    "failed_knot_index": knot_index,
                    "validated_knot_count": len(times),
                })
            node_id, state = node.get("node_id"), node.get("contact_state")
            if (not isinstance(node_id, str) or not node_id
                    or not isinstance(state, str) or state not in {"open", "closed"}):
                return Calculation(status="out_of_scope", values=base | {
                    "out_of_scope_reason": "missing_node_identity_or_unrecognized_contact_state",
                    "failed_knot_index": knot_index,
                    "validated_knot_count": len(times),
                })
            node_ids.append(node_id)
        if len(set(node_ids)) != len(node_ids):
            return Calculation(status="out_of_scope", values=base | {
                "out_of_scope_reason": "duplicate_node_id_within_contact_field",
                "failed_knot_index": knot_index,
                "validated_knot_count": len(times),
            })
        if ordered_nodes is None:
            ordered_nodes = node_ids
        elif node_ids != ordered_nodes:
            return Calculation(status="out_of_scope", values=base | {
                "out_of_scope_reason": "node_identity_or_order_changed_between_knots",
                "failed_knot_index": knot_index,
                "validated_knot_count": len(times),
            })
        if times and time_s <= times[-1]:
            return Calculation(status="out_of_scope", values=base | {
                "out_of_scope_reason": "contact_history_times_not_strictly_increasing",
                "failed_knot_index": knot_index,
                "validated_knot_count": len(times),
            })
        times.append(float(time_s))
        fields.append(field)

    transitions: list[dict] = []
    per_node: dict[str, dict] = {
        node_id: {"node_id": node_id, "observed_transition_count": 0,
                  "observed_opening_count": 0, "observed_closing_count": 0}
        for node_id in (ordered_nodes or [])
    }
    for interval_index, (left, right) in enumerate(zip(fields[:-1], fields[1:], strict=True)):
        t0, t1 = times[interval_index], times[interval_index + 1]
        for node_id, left_row, right_row in zip(ordered_nodes or [], left, right, strict=True):
            state0, state1 = left_row["contact_state"], right_row["contact_state"]
            if state0 == state1:
                continue
            transition = {
                "node_id": node_id,
                "from_state": state0,
                "to_state": state1,
                "transition_kind": "opening" if state0 == "closed" else "closing",
                "lower_time_s": t0,
                "upper_time_s": t1,
                "bracket_width_s": t1 - t0,
                "lower_endpoint_contact_force_N": left_row.get("contact_force_N"),
                "upper_endpoint_contact_force_N": right_row.get("contact_force_N"),
                "lower_endpoint_contact_gap_m": left_row.get("contact_gap_m"),
                "upper_endpoint_contact_gap_m": right_row.get("contact_gap_m"),
                "event_time_s": None,
            }
            transitions.append(transition)
            summary = per_node[node_id]
            summary["observed_transition_count"] += 1
            summary["observed_opening_count"] += int(state0 == "closed")
            summary["observed_closing_count"] += int(state0 == "open")

    return Calculation(values=base | {
        "knot_times_s": times,
        "ordered_node_ids": ordered_nodes or [],
        "transition_brackets": transitions,
        "transition_bracket_count": len(transitions),
        "per_node_observed_transition_counts": list(per_node.values()),
        "transition_definition": "adjacent supplied solver knots with different caller-source contact_state values",
        "event_time_method": "not computed; exact event timing requires additional solver evaluations or a reviewed within-interval response law",
        "same_state_endpoint_intervals_may_contain_hidden_transitions": True,
        "seal_acceptance_or_leakage_inferred": False,
        "failure_probability_inferred": False,
    }, notes=(
        "Transition brackets identify only changes visible between adjacent computed solver knots; no event time is interpolated or solved.",
        "Equal endpoint states do not rule out hidden within-interval contact changes. This is not a seal-acceptance, leakage, stress, or qualification result.",
    ))


def _validate_context(request: GasketContactTransitionBrackets, context: RunContext) -> None:
    source = request.contact_history.context
    if (context.asset_id, context.location_id, context.time_basis) != (
        source.asset_id, source.location_id, source.time_basis,
    ):
        raise ValueError("gasket transition RunContext must match the source contact history")


def specifications() -> list[ModelSpec]:
    return [ModelSpec(
        "fabrication.gasket_contact_transition_brackets",
        GasketContactTransitionBrackets,
        audit_gasket_contact_transition_brackets,
        {
            "knot_times_s[]": "s",
            "transition_brackets[].lower_time_s": "s",
            "transition_brackets[].upper_time_s": "s",
            "transition_brackets[].bracket_width_s": "s",
            "transition_brackets[].lower_endpoint_contact_force_N": "N",
            "transition_brackets[].upper_endpoint_contact_force_N": "N",
            "transition_brackets[].lower_endpoint_contact_gap_m": "m",
            "transition_brackets[].upper_endpoint_contact_gap_m": "m",
        },
        (
            "Summarize contact-state changes visible between adjacent computed flange-history knots as time brackets.",
            "The adapter does not solve transition time or infer hidden transitions, seal acceptance, leakage, stress, or failure probability.",
        ),
        ("caller_computed_flange_contact_history",),
        context_validator=_validate_context,
    )]
