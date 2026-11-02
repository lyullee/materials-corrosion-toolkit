"""Explicit strain-life model evaluation and caller-declared linear cycle accumulation."""

from __future__ import annotations
import math

from typing import Literal

from pydantic import Field, model_validator

from .contracts import Contract, Nonnegative, canonical_digest
from .models.constitutive import (
    MorrowStrainLife,
    SWTStrainLife,
    StrainLife,
    morrow_strain_life,
    strain_life,
    swt_strain_life,
)


class StrainLifeBlock(Contract):
    block_id: str = Field(min_length=1)
    cycle_count: Nonnegative
    model: Literal["fully_reversed", "morrow", "swt"]
    inputs: StrainLife | MorrowStrainLife | SWTStrainLife

    @model_validator(mode="after")
    def selected_input_type(self):
        expected = {"fully_reversed": StrainLife, "morrow": MorrowStrainLife, "swt": SWTStrainLife}
        if type(self.inputs) is not expected[self.model]:
            raise ValueError("block model and strain-life input contract must match")
        return self


class StrainLifeCampaign(Contract):
    campaign_id: str = Field(min_length=1)
    material_condition_id: str = Field(min_length=1)
    history_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    blocks: tuple[StrainLifeBlock, ...] = Field(min_length=1)
    linear_accumulation_reviewed: bool
    material_coefficients_and_cycle_basis_reviewed: bool

    @model_validator(mode="after")
    def unique_blocks(self):
        if len({row.block_id for row in self.blocks}) != len(self.blocks):
            raise ValueError("strain-life block identifiers must be unique")
        return self


class StrainLifeBlockResult(Contract):
    block_id: str
    status: Literal["computed", "needs_data", "out_of_scope"]
    cycle_count: Nonnegative
    cycles_to_failure: float | None
    linear_damage_fraction: float | None


class StrainLifeCampaignResult(Contract):
    schema_version: Literal["matintegrity.strain_life_campaign.v1"] = "matintegrity.strain_life_campaign.v1"
    campaign_id: str
    input_sha256: str
    status: Literal["computed", "needs_data", "out_of_scope"]
    block_results: tuple[StrainLifeBlockResult, ...]
    total_linear_damage: float | None
    notes: tuple[str, ...]


def evaluate_strain_life_campaign(request: StrainLifeCampaign) -> StrainLifeCampaignResult:
    """Evaluate each declared block and withhold the aggregate if any positive-count block fails."""
    digest = canonical_digest(request.model_dump(mode="json"))
    if not request.linear_accumulation_reviewed or not request.material_coefficients_and_cycle_basis_reviewed:
        return StrainLifeCampaignResult(
            campaign_id=request.campaign_id,
            input_sha256=digest,
            status="needs_data",
            block_results=(),
            total_linear_damage=None,
            notes=("Material coefficient, cycle basis and linear accumulation reviews are required.",),
        )
    evaluators = {"fully_reversed": strain_life, "morrow": morrow_strain_life, "swt": swt_strain_life}
    rows = []
    numeric_failures = []
    for block in request.blocks:
        if block.cycle_count == 0:
            rows.append(
                StrainLifeBlockResult(
                    block_id=block.block_id,
                    status="computed",
                    cycle_count=0.0,
                    cycles_to_failure=None,
                    linear_damage_fraction=0.0,
                )
            )
            continue
        result = evaluators[block.model](block.inputs)
        life = result.values.get("cycles_to_failure") if result.status == "computed" else None
        damage = block.cycle_count / life if life is not None else None
        row_status = result.status
        if damage is not None and not math.isfinite(damage):
            damage = None
            row_status = "out_of_scope"
            numeric_failures.append(block.block_id)
        rows.append(
            StrainLifeBlockResult(
                block_id=block.block_id,
                status=row_status,
                cycle_count=block.cycle_count,
                cycles_to_failure=life,
                linear_damage_fraction=damage,
            )
        )
    statuses = {row.status for row in rows}
    status = (
        "needs_data"
        if "needs_data" in statuses
        else "out_of_scope"
        if "out_of_scope" in statuses
        else "computed"
    )
    total = None
    if status == "computed":
        try:
            total = math.fsum(row.linear_damage_fraction for row in rows)
            if not math.isfinite(total):
                raise OverflowError("nonfinite damage sum")
        except OverflowError:
            status = "out_of_scope"
            total = None
            numeric_failures.append("aggregate")
    return StrainLifeCampaignResult(
        campaign_id=request.campaign_id,
        input_sha256=digest,
        status=status,
        block_results=tuple(rows),
        total_linear_damage=total,
        notes=(
            "Linear cycle fractions are a caller-declared accumulation model; sequence effects, residual-stress relaxation, creep interaction and failure probability require separate models.",
        )
        + (("Numeric range exceeded for: " + ", ".join(numeric_failures),) if numeric_failures else ()),
    )
