"""Variable-amplitude McDiarmid index-to-life campaign with explicit Miner blocks."""

from __future__ import annotations

import math
from typing import Literal

from pydantic import Field, StrictInt, model_validator

from ..contracts import AssessmentResult, Calculation, Contract, Evidence, Positive, canonical_digest
from ..registry import ModelSpec

MODEL_ID = "fatigue.mcdiarmid_calibrated_miner_campaign"
INDEX_MODEL_ID = "fatigue.multiaxial_mcdiarmid_finite_plane_limit_screen"


class McDiarmidIndexLifePoint(Contract):
    criterion_index: Positive
    cycles_to_failure: Positive


class McDiarmidLifeCurve(Contract):
    material_condition_id: str = Field(min_length=1)
    crack_case: Literal["A", "B"]
    provider_id: str = Field(min_length=1)
    provider_revision: str = Field(min_length=1)
    reference_record_id: str = Field(min_length=1)
    calibration_points: tuple[McDiarmidIndexLifePoint, ...] = Field(min_length=2, max_length=10000)
    calibration_record_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    usage_license_id: str = Field(min_length=1)
    evidence: tuple[Evidence, ...] = Field(min_length=1)


class McDiarmidCycleBlock(Contract):
    block_id: str = Field(min_length=1)
    cycle_count: StrictInt = Field(gt=0, le=2**53)
    index_result: AssessmentResult
    index_result_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")


class McDiarmidMinerCampaign(Contract):
    schema_version: Literal["matintegrity.mcdiarmid_calibrated_miner_campaign.v1"] = (
        "matintegrity.mcdiarmid_calibrated_miner_campaign.v1"
    )
    assessment_id: str = Field(min_length=1)
    blocks: tuple[McDiarmidCycleBlock, ...] = Field(min_length=1, max_length=10000)
    life_curve: McDiarmidLifeCurve
    damage_threshold: Positive
    ordered_blocks_reviewed: bool
    shared_scope_material_and_case_reviewed: bool
    log_log_interpolation_and_support_reviewed: bool
    linear_miner_no_interaction_assumption_reviewed: bool
    computational_use_authorized: bool

    @model_validator(mode="after")
    def validate_curve_and_blocks(self):
        if len({row.block_id for row in self.blocks}) != len(self.blocks):
            raise ValueError("cycle block IDs must be unique")
        if sum(row.cycle_count for row in self.blocks) > 2**53:
            raise ValueError("total campaign cycle count exceeds exact integer support")
        points = self.life_curve.calibration_points
        indices = [row.criterion_index for row in points]
        lives = [row.cycles_to_failure for row in points]
        if any(right <= left for left, right in zip(indices, indices[1:])):
            raise ValueError("calibration criterion indices must increase strictly")
        if any(right >= left for left, right in zip(lives, lives[1:])):
            raise ValueError("fatigue life must decrease strictly as criterion index increases")
        record = {
            "material_condition_id": self.life_curve.material_condition_id,
            "crack_case": self.life_curve.crack_case,
            "provider_id": self.life_curve.provider_id,
            "provider_revision": self.life_curve.provider_revision,
            "reference_record_id": self.life_curve.reference_record_id,
            "calibration_points": [row.model_dump(mode="json") for row in points],
        }
        if canonical_digest(record) != self.life_curve.calibration_record_sha256:
            raise ValueError("calibration record digest does not bind declared points and applicability")
        if not any(
            item.source_id == self.life_curve.provider_id
            and item.sha256 == self.life_curve.calibration_record_sha256
            and item.license_id == self.life_curve.usage_license_id
            for item in self.life_curve.evidence
        ):
            raise ValueError("life curve Evidence must pin the record and computational-use license")
        for block in self.blocks:
            result = block.index_result
            if result.status != "computed" or result.model_id != INDEX_MODEL_ID:
                raise ValueError("each block requires a computed McDiarmid finite-plane index result")
            if canonical_digest(result.model_dump(mode="json")) != block.index_result_sha256:
                raise ValueError("McDiarmid index result digest does not match")
            expected_input_digest = canonical_digest({
                "model_id": result.model_id,
                "model_version": result.model_version,
                "inputs": result.inputs,
                "context": result.context.model_dump(mode="json"),
            })
            if result.input_digest != expected_input_digest:
                raise ValueError("McDiarmid source result input/context digest is inconsistent")
            if result.units.get("maximum_criterion_index") != "1":
                raise ValueError("McDiarmid source index must be dimensionless")
            if result.values.get("material_condition_id") != self.life_curve.material_condition_id:
                raise ValueError("index result and life calibration material conditions differ")
            if result.values.get("crack_case") != self.life_curve.crack_case:
                raise ValueError("index result and life calibration crack cases differ")
            index = result.values.get("maximum_criterion_index")
            if isinstance(index, bool) or not isinstance(index, (int, float)) or not math.isfinite(index):
                raise ValueError("each index result must expose a finite maximum criterion index")
        return self


def _loglog_life(points: tuple[McDiarmidIndexLifePoint, ...], index: float) -> float | None:
    if index < points[0].criterion_index or index > points[-1].criterion_index:
        return None
    for left, right in zip(points, points[1:]):
        if left.criterion_index <= index <= right.criterion_index:
            if index == left.criterion_index:
                return left.cycles_to_failure
            if index == right.criterion_index:
                return right.cycles_to_failure
            fraction = (
                math.log(index / left.criterion_index)
                / math.log(right.criterion_index / left.criterion_index)
            )
            return math.exp(
                math.log(left.cycles_to_failure)
                + fraction * math.log(right.cycles_to_failure / left.cycles_to_failure)
            )
    return None


def evaluate_mcdiarmid_miner_campaign(request: McDiarmidMinerCampaign) -> Calculation:
    """Map per-block finite-plane indices into caller curve support and accumulate Miner fractions."""
    digest = canonical_digest(request.model_dump(mode="json"))
    base = {
        "assessment_id": request.assessment_id,
        "input_sha256": digest,
        "model_id": MODEL_ID,
        "life_curve_sha256": request.life_curve.calibration_record_sha256,
        "material_condition_id": request.life_curve.material_condition_id,
        "crack_case": request.life_curve.crack_case,
    }
    reviews = {
        "ordered_blocks_reviewed": request.ordered_blocks_reviewed,
        "shared_scope_material_and_case_reviewed": request.shared_scope_material_and_case_reviewed,
        "log_log_interpolation_and_support_reviewed": request.log_log_interpolation_and_support_reviewed,
        "linear_miner_no_interaction_assumption_reviewed": request.linear_miner_no_interaction_assumption_reviewed,
        "computational_use_authorized": request.computational_use_authorized,
    }
    missing = [name for name, value in reviews.items() if not value]
    if missing:
        return Calculation(status="needs_data", values=base | {"missing_reviews": missing})

    cumulative = 0.0
    total_cycles = 0
    rows = []
    first_crossing = None
    identity: tuple[str, str, str] | None = None
    for sequence_index, block in enumerate(request.blocks, start=1):
        result = block.index_result
        current_identity = (
            result.values.get("physical_scope_id"),
            result.context.asset_id,
            result.context.location_id,
        )
        if identity is None:
            identity = current_identity
        elif current_identity != identity:
            return Calculation(status="out_of_scope", values=base | {
                "reason": "asset_location_or_physical_scope_changes_between_blocks",
                "completed_blocks": rows,
            })
        index = float(result.values["maximum_criterion_index"])
        life = _loglog_life(request.life_curve.calibration_points, index)
        if life is None or not math.isfinite(life) or life <= 0.0:
            return Calculation(status="out_of_scope", values=base | {
                "reason": "criterion_index_outside_caller_life_curve_support",
                "block_id": block.block_id,
                "criterion_index": index,
                "completed_blocks": rows,
            })
        increment = block.cycle_count / life
        end_damage = cumulative + increment
        if not math.isfinite(end_damage):
            return Calculation(status="out_of_scope", values=base | {
                "reason": "linear_damage_exceeds_finite_numeric_support",
                "block_id": block.block_id,
                "completed_blocks": rows,
            })
        if first_crossing is None and cumulative < request.damage_threshold <= end_damage:
            offset = max(1, math.ceil((request.damage_threshold - cumulative) * life))
            offset = min(offset, block.cycle_count)
            while offset > 1 and cumulative + (offset - 1) / life >= request.damage_threshold:
                offset -= 1
            while cumulative + offset / life < request.damage_threshold:
                offset += 1
            first_crossing = {
                "block_id": block.block_id,
                "sequence_index": sequence_index,
                "cycle_offset_within_block": offset,
                "cycle_count_at_crossing_in_supplied_sequence": total_cycles + offset,
                "damage_at_integer_cycle_crossing": cumulative + offset / life,
            }
        rows.append({
            "sequence_index": sequence_index,
            "block_id": block.block_id,
            "cycle_count": block.cycle_count,
            "index_result_sha256": block.index_result_sha256,
            "criterion_index": index,
            "cycles_to_failure_from_caller_curve": life,
            "miner_damage_increment": increment,
            "cumulative_damage_start": cumulative,
            "cumulative_damage_end": end_damage,
        })
        cumulative = end_damage
        total_cycles += block.cycle_count
    return Calculation(values=base | {
        "physical_scope_id": identity[0] if identity else None,
        "block_count": len(rows),
        "total_supplied_cycles": total_cycles,
        "cumulative_miner_damage": cumulative,
        "damage_threshold": request.damage_threshold,
        "first_threshold_crossing_in_supplied_sequence": first_crossing,
        "block_results": rows,
        "life_extrapolated": False,
        "probability_inferred": False,
    }, notes=(
        "Each finite-plane index is mapped by log-log interpolation only between caller calibration points.",
        "Linear Miner accumulation is applied to the exact ordered blocks supplied; sequence interactions and omitted future blocks are not modeled.",
        "This is a caller-calibrated conditional campaign screen, not an independently validated fatigue-life prediction or acceptance decision.",
    ))


def specifications() -> list[ModelSpec]:
    return [ModelSpec(
        MODEL_ID,
        McDiarmidMinerCampaign,
        evaluate_mcdiarmid_miner_campaign,
        {
            "block_results[].criterion_index": "1",
            "block_results[].cycles_to_failure_from_caller_curve": "cycle",
            "block_results[].miner_damage_increment": "1",
            "block_results[].cumulative_damage_start": "1",
            "block_results[].cumulative_damage_end": "1",
            "total_supplied_cycles": "cycle",
            "cumulative_miner_damage": "1",
            "damage_threshold": "1",
            "first_threshold_crossing_in_supplied_sequence.cycle_offset_within_block": "cycle",
            "first_threshold_crossing_in_supplied_sequence.cycle_count_at_crossing_in_supplied_sequence": "cycle",
        },
        (
            "Blocks consume computed McDiarmid finite-plane indices from one physical scope, asset and location.",
            "A caller-provided same-condition monotone index-life curve is interpolated in log-log coordinates without extrapolation.",
            "Linear Miner accumulation and absence of sequence interaction are caller-reviewed assumptions.",
        ),
        (
            "mcdiarmid_shear_stress_critical_plane_1994",
            "caller_mcdiarmid_index_life_curve",
            "caller_ordered_multiaxial_cycle_block_counts",
            "linear_miner_damage_rule_for_mcdiarmid_campaign",
        ),
        qualification="user_model",
    )]
