"""Caller-declared P1 cycle blocks with explicit linear Miner accumulation."""

from __future__ import annotations

import math

from pydantic import Field, model_validator

from .contracts import Calculation, Contract, Evidence, Positive, canonical_digest
from .papadopoulos_p1_calibrated_life import (
    PapadopoulosP1CalibratedLife,
    evaluate_papadopoulos_p1_calibrated_life,
)
from .papadopoulos_p1_finite_integral_screen import PapadopoulosP1FiniteIntegralScreen
from .registry import ModelSpec


class PapadopoulosP1CycleBlock(Contract):
    block_id: str = Field(min_length=1)
    p1_request: PapadopoulosP1FiniteIntegralScreen
    cycle_count_equivalents: Positive


class PapadopoulosP1MinerBlocks(Contract):
    analysis_id: str = Field(min_length=1)
    material_condition_id: str = Field(min_length=1)
    blocks: tuple[PapadopoulosP1CycleBlock, ...] = Field(min_length=1, max_length=10000)
    life_curve_id: str = Field(min_length=1)
    curve_source_id: str = Field(min_length=1)
    curve_source_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    curve_evidence: Evidence
    p1_parameter_points_Pa: list[Positive] = Field(min_length=2, max_length=10000)
    cycles_to_failure: list[Positive] = Field(min_length=2, max_length=10000)
    maximum_total_shear_system_sample_work: int = Field(default=2_000_000, ge=1, le=20_000_000)
    cycle_decomposition_and_counts_reviewed: bool
    curve_and_miner_applicability_reviewed: bool
    linear_miner_rule_reviewed: bool
    curve_rights_and_engineering_use_reviewed: bool

    @model_validator(mode="after")
    def validate_blocks_curve(self):
        if self.curve_evidence.source_id != self.curve_source_id or self.curve_evidence.sha256 != self.curve_source_sha256:
            raise ValueError("curve Evidence must match its declared source and digest")
        if len(self.p1_parameter_points_Pa) != len(self.cycles_to_failure):
            raise ValueError("P1 parameter and life vectors must have equal lengths")
        if any(right <= left for left, right in zip(self.p1_parameter_points_Pa[:-1], self.p1_parameter_points_Pa[1:], strict=True)):
            raise ValueError("P1 curve parameter must be strictly increasing")
        if any(right >= left for left, right in zip(self.cycles_to_failure[:-1], self.cycles_to_failure[1:], strict=True)):
            raise ValueError("cycles to failure must strictly decrease as P1 parameter increases")
        block_ids = [block.block_id for block in self.blocks]
        if len(set(block_ids)) != len(block_ids):
            raise ValueError("cycle-block IDs must be unique")
        if any(block.p1_request.material_condition_id != self.material_condition_id for block in self.blocks):
            raise ValueError("every block must use the declared common material condition")
        return self


def evaluate_papadopoulos_p1_miner_blocks(request: PapadopoulosP1MinerBlocks) -> Calculation:
    """Map each caller block to P1 life, then sum declared count/life fractions."""
    input_digest = canonical_digest(request.model_dump(mode="json"))
    work = math.fsum(len(block.p1_request.sample_ids) * len(block.p1_request.shear_systems) for block in request.blocks)
    base = {
        "analysis_id": request.analysis_id,
        "material_condition_id": request.material_condition_id,
        "life_curve_id": request.life_curve_id,
        "curve_source_id": request.curve_source_id,
        "curve_source_sha256": request.curve_source_sha256,
        "normalized_curve_sha256": canonical_digest({
            "life_curve_id": request.life_curve_id,
            "material_condition_id": request.material_condition_id,
            "source_id": request.curve_source_id,
            "source_sha256": request.curve_source_sha256,
            "p1_parameter_points_Pa": request.p1_parameter_points_Pa,
            "cycles_to_failure": request.cycles_to_failure,
        }),
        "input_sha256": input_digest,
        "block_count": len(request.blocks),
        "total_shear_system_sample_work": work,
    }
    if not all((
        request.cycle_decomposition_and_counts_reviewed,
        request.curve_and_miner_applicability_reviewed,
        request.linear_miner_rule_reviewed,
        request.curve_rights_and_engineering_use_reviewed,
    )):
        return Calculation(status="needs_data", values=base | {
            "reason": "cycle_decomposition_curve_miner_and_rights_reviews_required",
            "block_damage_ledger": None,
            "cumulative_miner_damage": None,
        })
    if work > request.maximum_total_shear_system_sample_work:
        return Calculation(status="out_of_scope", values=base | {
            "reason": "total_cycle_block_quadrature_work_budget_exceeded",
            "maximum_total_shear_system_sample_work": request.maximum_total_shear_system_sample_work,
            "block_damage_ledger": None,
            "cumulative_miner_damage": None,
        })
    curve_input = {
        "life_curve_id": request.life_curve_id,
        "curve_material_condition_id": request.material_condition_id,
        "curve_source_id": request.curve_source_id,
        "curve_source_sha256": request.curve_source_sha256,
        "curve_evidence": request.curve_evidence.model_dump(mode="python"),
        "p1_parameter_points_Pa": request.p1_parameter_points_Pa,
        "cycles_to_failure": request.cycles_to_failure,
        "curve_material_match_and_test_basis_reviewed": True,
        "curve_rights_and_engineering_use_reviewed": True,
        "log_log_interpolation_and_finite_life_scope_reviewed": True,
    }
    ledger = []
    for block in request.blocks:
        life_request = PapadopoulosP1CalibratedLife.model_validate({
            "analysis_id": f"{request.analysis_id}:{block.block_id}",
            "p1_request": block.p1_request.model_dump(mode="python"),
            **curve_input,
        })
        life_result = evaluate_papadopoulos_p1_calibrated_life(life_request)
        if life_result.status != "computed":
            return Calculation(status=life_result.status, values=base | {
                "reason": "one_or_more_blocks_could_not_be_mapped_to_caller_life_curve",
                "failed_block_id": block.block_id,
                "underlying_values": life_result.values,
                "block_damage_ledger": None,
                "cumulative_miner_damage": None,
            })
        cycles_to_failure = life_result.values["cycles_to_failure"]
        damage = block.cycle_count_equivalents / cycles_to_failure
        if not math.isfinite(damage) or damage < 0.0:
            return Calculation(status="out_of_scope", values=base | {
                "reason": "block_damage_outside_finite_numeric_support",
                "failed_block_id": block.block_id,
                "block_damage_ledger": None,
                "cumulative_miner_damage": None,
            })
        ledger.append({
            "block_id": block.block_id,
            "p1_parameter_Pa": life_result.values["p1_parameter_Pa"],
            "cycle_count_equivalents": block.cycle_count_equivalents,
            "cycles_to_failure_at_block_parameter": cycles_to_failure,
            "miner_damage_fraction": damage,
            "p1_input_sha256": life_result.values["p1_input_sha256"],
            "curve_sha256": life_result.values["normalized_curve_sha256"],
        })
    try:
        total_damage = math.fsum(row["miner_damage_fraction"] for row in ledger)
    except (OverflowError, ValueError):
        total_damage = math.inf
    if not math.isfinite(total_damage):
        return Calculation(status="out_of_scope", values=base | {
            "reason": "cumulative_miner_damage_outside_finite_numeric_support",
            "block_damage_ledger": ledger,
            "cumulative_miner_damage": None,
        })
    return Calculation(values=base | {
        "status": "computed",
        "block_damage_ledger": ledger,
        "cumulative_miner_damage": total_damage,
        "failure_threshold_interpretation": "caller-selected_linear_miner_threshold; not a failure probability or acceptance decision",
        "limitations": [
            "Cycle decomposition, repetitions, constant-amplitude equivalence and linear Miner accumulation are caller assumptions.",
            "Every block P1 parameter must lie within a same-condition caller S-N curve; no extrapolation is performed.",
            "The underlying P1 orientation integral is a finite caller quadrature with no continuous-orientation error bound.",
            "Sequence effects, interaction, mean-stress evolution, scatter, probability and material qualification are not modeled.",
        ],
    })


def specifications() -> list[ModelSpec]:
    return [ModelSpec(
        "fatigue.papadopoulos_p1_miner_blocks",
        PapadopoulosP1MinerBlocks,
        evaluate_papadopoulos_p1_miner_blocks,
        {"block_damage_ledger[].miner_damage_fraction": "1", "cumulative_miner_damage": "1"},
        (
            "Caller supplies cycle blocks, repetitions, closed stress-cycle histories and the common material condition.",
            "Block lives come only from bounded log-log interpolation on a caller P1-parameter life curve.",
            "Linear Miner summation is an explicit caller-selected assumption; total damage is not a probability or qualified failure criterion.",
        ),
        ("caller_papadopoulos_p1_cycle_block_life_and_linear_miner_accumulation",),
        qualification="user_model",
    )]
