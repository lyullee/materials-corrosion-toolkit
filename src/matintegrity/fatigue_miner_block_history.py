"""Bind reviewed constant-amplitude fatigue-life results to ordered cycle blocks."""

from __future__ import annotations

import math
from typing import Literal

from pydantic import Field, StrictInt, model_validator

from .contracts import AssessmentResult, Calculation, Contract, canonical_digest
from .registry import ModelSpec

SOURCE_ID = "caller_findley_life_to_ordered_miner_block_history"
FINDLEY_MODEL_ID = "fatigue.critical_plane_findley_calibrated_life"


class FindleyLifeCycleBlock(Contract):
    """One ordered block with a separate computed, calibration-bound life result."""

    block_id: str = Field(min_length=1)
    cycle_count: StrictInt = Field(gt=0, le=2**53)
    life_result: AssessmentResult


class FindleyMinerHistoryRequest(Contract):
    """Caller-authorized linear-damage history over one ordered finite block set."""

    schema_version: Literal["matintegrity.findley_miner_block_history.v1"] = (
        "matintegrity.findley_miner_block_history.v1"
    )
    blocks: tuple[FindleyLifeCycleBlock, ...] = Field(min_length=1, max_length=10000)
    damage_threshold: float = Field(gt=0)
    ordered_blocks_reviewed: bool
    shared_asset_location_material_condition_reviewed: bool
    linear_damage_rule_reviewed: bool
    no_sequence_interaction_assumed: bool

    @model_validator(mode="after")
    def unique_blocks_and_budget(self):
        if len({row.block_id for row in self.blocks}) != len(self.blocks):
            raise ValueError("cycle block IDs must be unique")
        if sum(row.cycle_count for row in self.blocks) > 2**53:
            raise ValueError("total cycle count exceeds exact integer support")
        return self


def _assessment_digest_matches(result: AssessmentResult) -> bool:
    payload = {
        "model_id": result.model_id,
        "model_version": result.model_version,
        "inputs": result.inputs,
        "context": result.context.model_dump(mode="json"),
    }
    return canonical_digest(payload) == result.input_digest


def evaluate_findley_miner_block_history(request: FindleyMinerHistoryRequest) -> Calculation:
    """Accumulate caller-reviewed Miner fractions; summarize only supplied cycles."""
    required = {
        "ordered_blocks_reviewed": request.ordered_blocks_reviewed,
        "shared_asset_location_material_condition_reviewed": request.shared_asset_location_material_condition_reviewed,
        "linear_damage_rule_reviewed": request.linear_damage_rule_reviewed,
        "no_sequence_interaction_assumed": request.no_sequence_interaction_assumed,
    }
    absent = [name for name, value in required.items() if not value]
    if absent:
        return Calculation(status="needs_data", values={"missing_reviews": absent, "block_results": []})

    reference = request.blocks[0].life_result
    if reference.status != "computed":
        return Calculation(status="needs_data", values={"reason": "life_result_not_computed", "block_id": request.blocks[0].block_id})
    if (
        reference.model_id != FINDLEY_MODEL_ID
        or not _assessment_digest_matches(reference)
        or reference.units.get("cycles_to_failure") != "cycle"
    ):
        return Calculation(status="out_of_scope", values={"reason": "life_result_model_digest_or_unit_invalid", "block_id": request.blocks[0].block_id})
    material_condition = reference.values.get("material_condition_id")
    if not isinstance(material_condition, str) or not material_condition.strip():
        return Calculation(status="out_of_scope", values={"reason": "material_condition_identity_missing"})

    common_context = (
        reference.context.asset_id,
        reference.context.location_id,
        reference.context.time_basis,
        material_condition,
    )
    cumulative = 0.0
    rows: list[dict] = []
    first_crossing: dict | None = None
    total_cycles = 0
    result_digests: list[str] = []
    for sequence_index, block in enumerate(request.blocks, start=1):
        result = block.life_result
        if result.status != "computed":
            return Calculation(status="needs_data", values={
                "reason": "life_result_not_computed", "block_id": block.block_id,
                "completed_blocks": rows, "cumulative_damage_before_block": cumulative,
            })
        if (
            result.model_id != FINDLEY_MODEL_ID
            or not _assessment_digest_matches(result)
            or result.units.get("cycles_to_failure") != "cycle"
        ):
            return Calculation(status="out_of_scope", values={
                "reason": "life_result_model_digest_or_unit_invalid", "block_id": block.block_id,
                "completed_blocks": rows, "cumulative_damage_before_block": cumulative,
            })
        identity = (
            result.context.asset_id,
            result.context.location_id,
            result.context.time_basis,
            result.values.get("material_condition_id"),
        )
        if identity != common_context:
            return Calculation(status="out_of_scope", values={
                "reason": "asset_location_or_material_condition_changes_between_blocks", "block_id": block.block_id,
                "completed_blocks": rows, "cumulative_damage_before_block": cumulative,
            })
        life = result.values.get("cycles_to_failure")
        if isinstance(life, bool) or not isinstance(life, (int, float)) or not math.isfinite(life) or life <= 0:
            return Calculation(status="out_of_scope", values={
                "reason": "computed_Findley_life_missing_or_nonpositive", "block_id": block.block_id,
                "completed_blocks": rows, "cumulative_damage_before_block": cumulative,
            })
        digest = canonical_digest(result.model_dump(mode="json"))
        result_digests.append(digest)
        start_damage = cumulative
        increment = block.cycle_count / float(life)
        end_damage = start_damage + increment
        if not math.isfinite(end_damage):
            return Calculation(status="out_of_scope", values={"reason": "damage_sum_exceeds_finite_support", "block_id": block.block_id, "completed_blocks": rows})
        row = {
            "sequence_index": sequence_index,
            "block_id": block.block_id,
            "cycle_count": block.cycle_count,
            "findley_life_result_sha256": digest,
            "cycles_to_failure": float(life),
            "damage_increment": increment,
            "cumulative_damage_start": start_damage,
            "cumulative_damage_end": end_damage,
        }
        if first_crossing is None and start_damage < request.damage_threshold <= end_damage:
            needed = (request.damage_threshold - start_damage) * float(life)
            offset = max(1, math.ceil(needed))
            offset = min(offset, block.cycle_count)
            while offset > 1 and start_damage + (offset - 1) / float(life) >= request.damage_threshold:
                offset -= 1
            while start_damage + offset / float(life) < request.damage_threshold:
                offset += 1
            first_crossing = {
                "block_id": block.block_id,
                "sequence_index": sequence_index,
                "cycle_offset_within_block": offset,
                "cycle_count_at_crossing_in_supplied_sequence": total_cycles + offset,
                "damage_at_integer_cycle_crossing": start_damage + offset / float(life),
                "threshold": request.damage_threshold,
            }
        rows.append(row)
        cumulative = end_damage
        total_cycles += block.cycle_count

    return Calculation(values={
        "model_id": "integration.findley_miner_ordered_block_history",
        "damage_basis": "caller_declared_linear_cycles_over_calibrated_life",
        "asset_id": reference.context.asset_id,
        "location_id": reference.context.location_id,
        "material_condition_id": material_condition,
        "block_count": len(rows),
        "total_supplied_cycles": total_cycles,
        "cumulative_damage": cumulative,
        "damage_threshold": request.damage_threshold,
        "first_threshold_crossing_in_supplied_sequence": first_crossing,
        "block_results": rows,
        "ordered_life_result_digests": result_digests,
        "request_sha256": canonical_digest(request.model_dump(mode="json")),
        "probability_inferred": False,
        "remaining_life_extrapolated": False,
    }, notes=(
        "Applies only the caller-reviewed linear damage sum to the exact ordered finite blocks supplied.",
        "The result is not a probability, service-life forecast, sequence-sensitive damage law, independent qualification, or acceptance decision.",
    ))


def specifications() -> list[ModelSpec]:
    return [ModelSpec(
        model_id="integration.findley_miner_ordered_block_history",
        input_type=FindleyMinerHistoryRequest,
        evaluator=evaluate_findley_miner_block_history,
        units={
            "total_supplied_cycles": "cycle",
            "cumulative_damage": "1",
            "damage_threshold": "1",
            "block_results[].cycles_to_failure": "cycle",
            "block_results[].damage_increment": "1",
            "first_threshold_crossing_in_supplied_sequence.cycle_count_at_crossing_in_supplied_sequence": "cycle",
            "first_threshold_crossing_in_supplied_sequence.cycle_offset_within_block": "cycle",
        },
        assumptions=(
            "Every block carries a computed, digest-consistent calibrated Findley life result for one shared asset, location and material condition.",
            "The caller supplies exact block order and explicitly reviews a linear cumulative damage rule with no sequence interaction.",
            "The calculation covers only the supplied finite cycle sequence and does not extrapolate remaining life or infer probability.",
        ),
        source_ids=(SOURCE_ID,),
        qualification="user_model",
    )]
