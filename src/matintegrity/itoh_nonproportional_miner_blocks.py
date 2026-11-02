"""Caller-counted Itoh non-proportional life blocks with linear Miner damage."""

from __future__ import annotations

import math

from pydantic import Field, StrictInt, model_validator

from .contracts import Calculation, Contract, Positive, canonical_digest
from .itoh_nonproportional_strain_life import (
    CURVE_SOURCE_ID,
    ItohNonproportionalStrainLife,
    STRAIN_DEFINITION_ID,
    evaluate_itoh_nonproportional_strain_life,
)
from .itoh_nonproportional_strain_parameter import CALIBRATION_SOURCE_ID, METHOD_SOURCE_ID
from .models.fatigue import MinerDamage, miner_damage
from .registry import ModelSpec

MODEL_ID = "fatigue.itoh_nonproportional_miner_blocks"
SOURCE_ID = "caller_itoh_nonproportional_miner_block_decomposition"
MAX_EXACT_INTEGER_COUNT = 2**53


class ItohMinerCycleBlock(Contract):
    """One caller-decomposed representative cycle and its calibrated life request."""

    block_id: str = Field(min_length=1)
    cycle_count: StrictInt = Field(gt=0, le=MAX_EXACT_INTEGER_COUNT)
    life_request: ItohNonproportionalStrainLife


class ItohNonproportionalMinerBlocks(Contract):
    """Apply a reviewed Miner sum to complete, condition-matched Itoh blocks."""

    analysis_id: str = Field(min_length=1)
    asset_id: str = Field(min_length=1)
    physical_scope_id: str = Field(min_length=1)
    location_id: str = Field(min_length=1)
    time_basis: str = Field(min_length=1)
    material_condition_id: str = Field(min_length=1)
    blocks: tuple[ItohMinerCycleBlock, ...] = Field(min_length=1, max_length=10000)
    declared_damage_limit: Positive
    cycle_decomposition_and_integer_counts_reviewed: bool
    curve_condition_and_strain_definition_reviewed: bool
    linear_miner_rule_reviewed: bool
    sequence_effects_excluded_reviewed: bool
    computational_use_and_curve_rights_reviewed: bool

    @model_validator(mode="after")
    def consistent_identity_and_budget(self):
        block_ids = [block.block_id for block in self.blocks]
        cycle_ids = [block.life_request.parameter_request.cycle_id for block in self.blocks]
        analysis_ids = [block.life_request.analysis_id for block in self.blocks]
        if len(set(block_ids)) != len(block_ids):
            raise ValueError("caller cycle-block IDs must be unique")
        if len(set(cycle_ids)) != len(cycle_ids):
            raise ValueError("each block must reference a distinct caller-declared cycle ID")
        if len(set(analysis_ids)) != len(analysis_ids):
            raise ValueError("each life mapping request must have a distinct analysis ID")
        if sum(block.cycle_count for block in self.blocks) > MAX_EXACT_INTEGER_COUNT:
            raise ValueError("total integer cycle count exceeds exact numeric support")

        first = self.blocks[0].life_request
        first_parameter = first.parameter_request
        common_identity = (
            first.curve_material_condition_id,
            first.curve_strain_definition_id,
            _curve_digest(first),
            first_parameter.calibration_source_id,
            first_parameter.calibration_sha256,
            first_parameter.hardening_coefficient_alpha,
            first_parameter.strain_shear_convention,
        )
        if first.curve_strain_definition_id != STRAIN_DEFINITION_ID:
            raise ValueError("cycle campaign must use the exact supported Itoh strain definition")
        for block in self.blocks:
            request = block.life_request
            parameter = request.parameter_request
            if parameter.material_condition_id != self.material_condition_id:
                raise ValueError("all Itoh parameter histories must match the campaign material condition")
            identity = (
                request.curve_material_condition_id,
                request.curve_strain_definition_id,
                _curve_digest(request),
                parameter.calibration_source_id,
                parameter.calibration_sha256,
                parameter.hardening_coefficient_alpha,
                parameter.strain_shear_convention,
            )
            if identity != common_identity:
                raise ValueError(
                    "all blocks must share one exact life curve, strain definition, material condition, alpha calibration and tensor shear convention"
                )
        if first.curve_material_condition_id != self.material_condition_id:
            raise ValueError("life-curve material condition must match the campaign")
        return self


def _curve_digest(request: ItohNonproportionalStrainLife) -> str:
    """Hash the full curve identity with the same fields used by its life mapper."""
    return canonical_digest({
        "life_curve_id": request.life_curve_id,
        "material_condition_id": request.curve_material_condition_id,
        "strain_definition_id": request.curve_strain_definition_id,
        "curve_condition_descriptor_sha256": request.curve_condition_descriptor_sha256,
        "source_id": request.curve_source_id,
        "source_sha256": request.curve_source_sha256,
        "curve_license_id": request.curve_license_id,
        "nonproportional_strain_range_points": request.nonproportional_strain_range_points,
        "cycles_to_failure": request.cycles_to_failure,
    })


def evaluate_itoh_nonproportional_miner_blocks(
    request: ItohNonproportionalMinerBlocks,
) -> Calculation:
    """Map all supplied blocks and sum only complete caller-counted Miner fractions."""
    input_digest = canonical_digest(request.model_dump(mode="json"))
    first = request.blocks[0].life_request
    base = {
        "analysis_id": request.analysis_id,
        "asset_id": request.asset_id,
        "physical_scope_id": request.physical_scope_id,
        "location_id": request.location_id,
        "time_basis": request.time_basis,
        "material_condition_id": request.material_condition_id,
        "strain_definition_id": first.curve_strain_definition_id,
        "life_curve_id": first.life_curve_id,
        "normalized_curve_sha256": _curve_digest(first),
        "curve_source_id": first.curve_source_id,
        "curve_source_sha256": first.curve_source_sha256,
        "curve_condition_descriptor_sha256": first.curve_condition_descriptor_sha256,
        "alpha_calibration_source_id": first.parameter_request.calibration_source_id,
        "alpha_calibration_sha256": first.parameter_request.calibration_sha256,
        "input_sha256": input_digest,
        "block_count": len(request.blocks),
        "cycle_counting_performed": False,
        "cycle_decomposition_performed": False,
        "sequence_effects_modeled": False,
        "failure_probability_inferred": False,
    }
    reviews = {
        "cycle_decomposition_and_integer_counts_reviewed": request.cycle_decomposition_and_integer_counts_reviewed,
        "curve_condition_and_strain_definition_reviewed": request.curve_condition_and_strain_definition_reviewed,
        "linear_miner_rule_reviewed": request.linear_miner_rule_reviewed,
        "sequence_effects_excluded_reviewed": request.sequence_effects_excluded_reviewed,
        "computational_use_and_curve_rights_reviewed": request.computational_use_and_curve_rights_reviewed,
    }
    missing_reviews = [name for name, reviewed in reviews.items() if not reviewed]
    if missing_reviews:
        return Calculation(status="needs_data", values=base | {
            "missing_reviews": missing_reviews,
            "completed_block_count": 0,
            "block_damage_ledger": [],
            "miner_result": None,
            "cumulative_miner_damage": None,
        })

    ledger: list[dict] = []
    counts: list[float] = []
    lives: list[float] = []
    for sequence_index, block in enumerate(request.blocks):
        life_result = evaluate_itoh_nonproportional_strain_life(block.life_request)
        values = life_result.values
        row = {
            "sequence_index": sequence_index,
            "block_id": block.block_id,
            "cycle_id": block.life_request.parameter_request.cycle_id,
            "caller_cycle_count": block.cycle_count,
            "life_request_sha256": canonical_digest(block.life_request.model_dump(mode="json")),
            "life_result_sha256": canonical_digest(life_result.model_dump(mode="json")),
            "life_result": life_result.model_dump(mode="json"),
            "status": life_result.status,
            "strain_definition_id": block.life_request.curve_strain_definition_id,
            "normalized_curve_sha256": values.get("normalized_curve_sha256"),
            "parameter_input_sha256": values.get("parameter_input_sha256"),
        }
        if life_result.status != "computed":
            return Calculation(status=life_result.status, values=base | {
                "completed_block_count": len(ledger),
                "block_damage_ledger": ledger + [row],
                "failed_block_id": block.block_id,
                "failed_block_index": sequence_index,
                "miner_result": None,
                "cumulative_miner_damage": None,
                "prefix_policy": "cumulative Miner damage is withheld unless every declared block maps to an in-support life",
            }, notes=("No damage sum is reported from a partial set of cycle blocks.",))
        life = values.get("cycles_to_failure")
        strain_range = values.get("itoh_strain_range")
        if (isinstance(life, bool) or not isinstance(life, (int, float))
                or not math.isfinite(life) or life <= 0.0
                or isinstance(strain_range, bool) or not isinstance(strain_range, (int, float))
                or not math.isfinite(strain_range) or strain_range <= 0.0):
            return Calculation(status="out_of_scope", values=base | {
                "completed_block_count": len(ledger),
                "block_damage_ledger": ledger + [row],
                "failed_block_id": block.block_id,
                "reason": "mapped_life_or_Itoh_strain_range_not_positive_finite",
                "miner_result": None,
                "cumulative_miner_damage": None,
            })
        increment = block.cycle_count / float(life)
        if not math.isfinite(increment) or increment < 0.0:
            return Calculation(status="out_of_scope", values=base | {
                "completed_block_count": len(ledger),
                "block_damage_ledger": ledger + [row],
                "failed_block_id": block.block_id,
                "reason": "block_damage_fraction_not_finite",
                "miner_result": None,
                "cumulative_miner_damage": None,
            })
        row.update({
            "itoh_nonproportional_strain_range": float(strain_range),
            "cycles_to_failure": float(life),
            "miner_damage_fraction": increment,
        })
        ledger.append(row)
        counts.append(float(block.cycle_count))
        lives.append(float(life))

    try:
        miner = miner_damage(MinerDamage(
            cycle_counts=counts,
            cycles_to_failure=lives,
            declared_damage_limit=request.declared_damage_limit,
        ))
        damage = miner.values.get("damage")
        if isinstance(damage, bool) or not isinstance(damage, (int, float)) or not math.isfinite(damage):
            raise ValueError("Miner damage result is not finite")
    except (OverflowError, ValueError, TypeError):
        return Calculation(status="out_of_scope", values=base | {
            "completed_block_count": len(ledger),
            "block_damage_ledger": ledger,
            "reason": "Miner_accumulation_outside_finite_numeric_support",
            "miner_result": None,
            "cumulative_miner_damage": None,
        })
    return Calculation(status=miner.status, values=base | {
        "completed_block_count": len(ledger),
        "block_damage_ledger": ledger,
        "declared_damage_limit": request.declared_damage_limit,
        "miner_result": miner.model_dump(mode="json"),
        "cumulative_miner_damage": damage,
        "damage_margin_to_caller_limit": miner.values.get("damage_margin"),
        "summation_basis": "existing linear Miner sum over the complete caller-counted Itoh blocks",
        "not_inferred": [
            "cycle decomposition or counts", "sequence effects", "damage interaction", "failure probability",
            "acceptance", "remaining life", "material qualification",
        ],
    }, notes=(
        "The caller supplies the block order, cycle counts, same-condition Itoh strain-life curve and linear Miner assumption.",
        "No cycles are detected, no sequence effect or probability is inferred, and total damage is not acceptance or qualification.",
    ) + miner.notes)


def specifications() -> list[ModelSpec]:
    return [ModelSpec(
        model_id=MODEL_ID,
        input_type=ItohNonproportionalMinerBlocks,
        evaluator=evaluate_itoh_nonproportional_miner_blocks,
        units={
            "block_damage_ledger[].caller_cycle_count": "cycle",
            "block_damage_ledger[].itoh_nonproportional_strain_range": "1",
            "block_damage_ledger[].cycles_to_failure": "cycle",
            "block_damage_ledger[].miner_damage_fraction": "1",
            "cumulative_miner_damage": "1",
            "declared_damage_limit": "1",
        },
        assumptions=(
            "Caller-decomposed blocks each use a distinct closed Itoh strain cycle and a same-condition digest-pinned strain-life curve.",
            "All blocks share the exact material condition, strain definition, life curve digest and non-proportional hardening calibration.",
            "Linear Miner accumulation applies only to the complete caller-supplied block set; sequence effects, interaction, cycle counting, probability and qualification are excluded.",
        ),
        source_ids=(SOURCE_ID, CURVE_SOURCE_ID, CALIBRATION_SOURCE_ID, METHOD_SOURCE_ID),
        qualification="user_model",
    )]
