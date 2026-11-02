"""Evaluate ordered caller load snapshots with the bounded elastic-joint model."""

from __future__ import annotations

import math
from typing import Literal

from pydantic import Field, StrictInt, model_validator

from .assembly_calculations import ElasticJointLoad, elastic_joint_load
from .contracts import Calculation, Contract, Nonnegative, RunContext, canonical_digest
from .registry import ModelSpec

SOURCE_ID = "caller_ordered_elastic_joint_load_history"
MODEL_ID = "integration.elastic_joint_load_ordered_history"


class ElasticJointLoadKnot(Contract):
    """One exact-time input snapshot; no values are reconstructed between knots."""

    knot_index: StrictInt = Field(ge=0)
    time_s: Nonnegative
    load_state: ElasticJointLoad


class ElasticJointLoadHistoryRequest(Contract):
    """Finite ordered snapshots for the linear closed-contact two-spring model."""

    schema_version: Literal["matintegrity.elastic_joint_load_ordered_history.v1"] = (
        "matintegrity.elastic_joint_load_ordered_history.v1"
    )
    history_id: str = Field(min_length=1)
    asset_id: str = Field(min_length=1)
    location_id: str = Field(min_length=1)
    time_basis: str = Field(min_length=1)
    knots: tuple[ElasticJointLoadKnot, ...] = Field(min_length=1, max_length=100000)
    minimum_clamp_force_N: Nonnegative
    ordered_time_basis_reviewed: bool
    elastic_closed_contact_model_reviewed: bool
    per_knot_preload_applicability_reviewed: bool
    finite_snapshot_only_interpretation_reviewed: bool

    @model_validator(mode="after")
    def ordered_unique_knots(self):
        if tuple(row.knot_index for row in self.knots) != tuple(range(len(self.knots))):
            raise ValueError("knot indices must be contiguous and follow input order")
        if any(right.time_s <= left.time_s for left, right in zip(self.knots[:-1], self.knots[1:], strict=True)):
            raise ValueError("history times must be strictly increasing")
        return self


def evaluate_elastic_joint_load_history(request: ElasticJointLoadHistoryRequest) -> Calculation:
    """Evaluate each supplied knot independently and summarize threshold witnesses."""
    reviews = {
        "ordered_time_basis_reviewed": request.ordered_time_basis_reviewed,
        "elastic_closed_contact_model_reviewed": request.elastic_closed_contact_model_reviewed,
        "per_knot_preload_applicability_reviewed": request.per_knot_preload_applicability_reviewed,
        "finite_snapshot_only_interpretation_reviewed": request.finite_snapshot_only_interpretation_reviewed,
    }
    missing = [key for key, accepted in reviews.items() if not accepted]
    request_digest = canonical_digest(request.model_dump(mode="json"))
    base = {
        "model_id": MODEL_ID,
        "history_id": request.history_id,
        "asset_id": request.asset_id,
        "location_id": request.location_id,
        "time_basis": request.time_basis,
        "minimum_clamp_force_N": request.minimum_clamp_force_N,
        "request_sha256": request_digest,
        "interpolation_between_knots": False,
        "leakage_or_seal_acceptance_inferred": False,
        "probability_inferred": False,
    }
    if missing:
        return Calculation(status="needs_data", values=base | {"missing_reviews": missing})

    rows: list[dict] = []
    first_below: dict | None = None
    for knot in request.knots:
        load_result = elastic_joint_load(knot.load_state)
        knot_digest = canonical_digest(knot.model_dump(mode="json"))
        row = {
            "knot_index": knot.knot_index,
            "time_s": knot.time_s,
            "knot_input_sha256": knot_digest,
            "load_input_sha256": canonical_digest(knot.load_state.model_dump(mode="json")),
            "status": load_result.get("status"),
        }
        if load_result.get("status") == "needs_data":
            return Calculation(status="needs_data", values=base | {
                "completed_knot_results": rows,
                "failed_knot_index": knot.knot_index,
                "reason": "closed_contact_applicability_not_reviewed_at_knot",
            })
        if load_result.get("status") != "computed":
            return Calculation(status="out_of_scope", values=base | {
                "completed_knot_results": rows,
                "failed_knot_index": knot.knot_index,
                "unclipped_bolt_force_N": load_result.get("unclipped_bolt_force_N"),
                "unclipped_clamp_force_N": load_result.get("unclipped_clamp_force_N"),
                "reason": "linear_closed_contact_model_predicts_contact_loss_at_knot",
            })
        force = load_result.get("clamp_force_N", load_result.get("unclipped_clamp_force_N"))
        if isinstance(force, bool) or not isinstance(force, (float, int)) or not math.isfinite(force):
            return Calculation(status="out_of_scope", values=base | {
                "completed_knot_results": rows,
                "failed_knot_index": knot.knot_index,
                "reason": "joint_clamp_force_not_finite_or_available",
            })
        row["bolt_force_N"] = load_result.get("bolt_force_N", load_result.get("unclipped_bolt_force_N"))
        row["clamp_force_N"] = float(force)
        row["thermal_preload_change_N"] = load_result.get("thermal_preload_change_N")
        row["closed_contact_state"] = load_result.get("status") == "computed"
        rows.append(row)
        if first_below is None and force < request.minimum_clamp_force_N:
            first_below = {
                "knot_index": knot.knot_index,
                "time_s": knot.time_s,
                "clamp_force_N": float(force),
                "minimum_clamp_force_N": request.minimum_clamp_force_N,
                "event_semantics": "first_supplied_snapshot_below_caller_threshold",
            }
    return Calculation(values=base | {
        "status": "computed",
        "snapshot_count": len(rows),
        "joint_load_history": rows,
        "minimum_observed_clamp_force_N": min(row["clamp_force_N"] for row in rows),
        "maximum_observed_clamp_force_N": max(row["clamp_force_N"] for row in rows),
        "first_supplied_snapshot_below_minimum_clamp_force": first_below,
        "crossing_time_interpolated": False,
        "threshold_is_seal_acceptance": False,
        "basis": "finite caller snapshots evaluated independently with an elastic two-spring closed-contact load partition",
    }, notes=(
        "The result applies only at exact supplied snapshots; no between-knot response is inferred.",
        "The elastic two-spring model does not represent gasket constitutive response, creep relaxation, leakage, sealing acceptance, probability or qualification.",
    ))


def _validate_context(request: ElasticJointLoadHistoryRequest, context: RunContext) -> None:
    if (context.asset_id, context.location_id, context.time_basis) != (
        request.asset_id, request.location_id, request.time_basis
    ):
        raise ValueError("RunContext must match the ordered load-history identity")


def specifications() -> list[ModelSpec]:
    return [ModelSpec(
        model_id=MODEL_ID,
        input_type=ElasticJointLoadHistoryRequest,
        evaluator=evaluate_elastic_joint_load_history,
        units={
            "minimum_clamp_force_N": "N",
            "joint_load_history[].time_s": "s",
            "joint_load_history[].bolt_force_N": "N",
            "joint_load_history[].clamp_force_N": "N",
            "joint_load_history[].thermal_preload_change_N": "N",
            "minimum_observed_clamp_force_N": "N",
            "maximum_observed_clamp_force_N": "N",
            "first_supplied_snapshot_below_minimum_clamp_force.time_s": "s",
        },
        assumptions=(
            "Each ordered snapshot is evaluated independently with the declared elastic two-spring closed-contact model.",
            "The caller reviews time basis, per-knot preload applicability, and finite-snapshot interpretation; no interpolation is used.",
            "Clamp-force threshold is caller-defined and does not establish gasket seal acceptance, leakage, probability or qualification.",
        ),
        source_ids=(SOURCE_ID,),
        qualification="user_model",
        context_validator=_validate_context,
    )]
