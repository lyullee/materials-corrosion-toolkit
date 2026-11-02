"""Summarize stateful fatigue results against their exact ordered source blocks."""

from __future__ import annotations

import math
from typing import Any

from pydantic import Field, model_validator

from .contracts import Calculation, Contract, canonical_digest
from .multiaxial_cycle_exchange import MultiaxialCycleBlockReceipt
from .multiaxial_damage_provider import CallerStatefulMultiaxialDamageRequest
from .registry import ModelSpec


class CycleBlockResultSummaryRequest(Contract):
    """Join one stateful result to its exact bound request and cycle-block receipt."""

    schema_version: str = "matintegrity.multiaxial_cycle_block_result_summary.v1"
    receipt: MultiaxialCycleBlockReceipt
    bound_request: CallerStatefulMultiaxialDamageRequest
    stateful_result: dict[str, Any]
    stateful_result_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")

    @model_validator(mode="after")
    def exact_lineage(self):
        result = self.stateful_result
        if canonical_digest(result) != self.stateful_result_sha256:
            raise ValueError("stateful result digest does not match the supplied result")
        receipt_digest = canonical_digest(self.receipt.model_dump(mode="json"))
        request_digest = canonical_digest(self.bound_request.model_dump(mode="json"))
        if result.get("cycle_exchange_receipt_sha256") != receipt_digest:
            raise ValueError("stateful result is not bound to this exact cycle-block receipt")
        if result.get("input_sha256") != request_digest:
            raise ValueError("stateful result input digest differs from the supplied bound request")
        if self.bound_request.cycle_exchange_receipt_sha256 != receipt_digest:
            raise ValueError("bound damage request does not contain the exact receipt digest")
        if tuple(self.bound_request.cycle_block_order_ids or ()) != tuple(b.block_id for b in self.receipt.blocks):
            raise ValueError("bound damage request block order differs from the receipt")
        for key in (
            "cycle_exchange_provider_id", "cycle_exchange_provider_revision",
            "cycle_exchange_provider_run_id", "cycle_exchange_provider_result_sha256",
            "cycle_exchange_clock_id", "cycle_source_initial_state_sha256",
            "cycle_source_terminal_state_sha256",
        ):
            if result.get(key) != getattr(self.bound_request, key):
                raise ValueError(f"stateful result {key} differs from the bound request")
        return self


def summarize_cycle_block_damage(request: CycleBlockResultSummaryRequest) -> Calculation:
    """Return per-source-block damage/state summaries, preserving incomplete prefixes."""
    result = request.stateful_result
    cycles = [cycle for block in request.receipt.blocks for cycle in block.cycles]
    available = result.get("cycle_results", result.get("computed_cycle_prefix", []))
    if not isinstance(available, list):
        return Calculation(status="out_of_scope", values={"reason": "stateful result has no list-valued cycle ledger"})
    if len(available) > len(cycles):
        return Calculation(status="out_of_scope", values={"reason": "stateful result contains more cycle rows than the receipt"})

    validated: list[dict[str, Any]] = []
    previous_end: float | None = None
    for expected, row in zip(cycles, available, strict=False):
        if not isinstance(row, dict) or row.get("cycle_id") != expected.cycle_id:
            return Calculation(status="out_of_scope", values={"reason": "computed cycle prefix differs from exact receipt order"})
        rep = row.get("repetition_count")
        if isinstance(rep, bool) or not isinstance(rep, int) or rep != int(expected.allocated_cycle_count):
            return Calculation(status="out_of_scope", values={"reason": "computed cycle repetition count differs from receipt"})
        start, end, damage = row.get("sequence_start_time_s"), row.get("sequence_end_time_s"), row.get("cycle_sequence_damage")
        if any(isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(float(v)) for v in (start, end, damage)):
            return Calculation(status="out_of_scope", values={"reason": "cycle ledger requires finite sequence bounds and damage"})
        start, end, damage = float(start), float(end), float(damage)
        if start < 0 or end <= start or damage < 0 or (previous_end is not None and start != previous_end):
            return Calculation(status="out_of_scope", values={"reason": "cycle ledger time or damage sequence is invalid"})
        previous_end = end
        validated.append(row)

    block_rows: list[dict[str, Any]] = []
    offset = 0
    for block in request.receipt.blocks:
        count = len(block.cycles)
        rows = validated[offset:offset + count]
        complete = len(rows) == count
        try:
            damage_sum = math.fsum(float(r["cycle_sequence_damage"]) for r in rows)
        except (OverflowError, ValueError):
            return Calculation(status="out_of_scope", values={"reason": "block damage aggregation exceeds finite numeric support"})
        if not math.isfinite(damage_sum):
            return Calculation(status="out_of_scope", values={"reason": "block damage aggregation is nonfinite"})
        block_rows.append({
            "block_id": block.block_id,
            "sequence_index": block.sequence_index,
            "block_source_sha256": block.block_source_sha256,
            "receipt_cycle_count": count,
            "computed_cycle_count": len(rows),
            "complete": complete,
            "cycle_ids": [r["cycle_id"] for r in rows],
            "sequence_start_time_s": rows[0]["sequence_start_time_s"] if rows else None,
            "sequence_end_time_s": rows[-1]["sequence_end_time_s"] if rows else None,
            "cycle_sequence_damage_sum": damage_sum,
            "state_before": rows[0].get("initial_state") if rows else None,
            "state_after": rows[-1].get("final_state") if rows and complete else None,
        })
        offset += count

    upstream_status = result.get("status")
    fully_computed = upstream_status == "computed" and len(validated) == len(cycles)
    if upstream_status == "computed" and not fully_computed:
        return Calculation(status="out_of_scope", values={"reason": "computed result does not cover every receipt cycle"})
    return Calculation(
        status="computed" if fully_computed else "out_of_scope",
        values={
            "model_id": "integration.multiaxial_cycle_block_result_summary",
            "receipt_sha256": canonical_digest(request.receipt.model_dump(mode="json")),
            "bound_request_sha256": canonical_digest(request.bound_request.model_dump(mode="json")),
            "stateful_result_sha256": request.stateful_result_sha256,
            "upstream_status": upstream_status,
            "computed_cycle_count": len(validated),
            "receipt_cycle_count": len(cycles),
            "completed_blocks": sum(row["complete"] for row in block_rows),
            "block_results": block_rows,
            "damage_basis": "finite ordered cycle-ledger aggregation by exact source block",
            "interpretation_limit": "No new fatigue law, life, probability, or qualification is inferred.",
        },
        notes=("This adapter groups the existing stateful cycle ledger by its exact exchange receipt; it does not recalculate or validate the upstream material model.",),
    )


def specifications() -> list[ModelSpec]:
    return [ModelSpec(
        model_id="integration.multiaxial_cycle_block_result_summary",
        input_type=CycleBlockResultSummaryRequest,
        evaluator=summarize_cycle_block_damage,
        units={"computed_cycle_count": "1", "receipt_cycle_count": "1", "block_results[].cycle_sequence_damage_sum": "1"},
        assumptions=("The stateful damage result, bound request and exchange receipt must have exact matching digests and ordered block lineage.", "This API aggregates existing cycle results and does not add a fatigue law or physical validation."),
        source_ids=("caller_multiaxial_cycle_block_result_summary",),
        qualification="engineering_screening",
    )]
