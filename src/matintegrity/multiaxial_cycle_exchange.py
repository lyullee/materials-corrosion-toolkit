"""Bind ordered external tensor-cycle blocks to the stateful fatigue integrator."""

from __future__ import annotations

import math

from typing import Literal

from pydantic import Field, model_validator

from .contracts import Contract, Evidence, canonical_digest
from .models.multiaxial_work_life import ClosedTensorCycle
from .multiaxial_damage_provider import CallerStatefulMultiaxialDamageRequest


class OrderedTensorCycleBlock(Contract):
    block_id: str = Field(min_length=1)
    sequence_index: int = Field(ge=0)
    block_source_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    material_state_before_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    material_state_after_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    cycles: tuple[ClosedTensorCycle, ...] = Field(min_length=1, max_length=10000)
    ordered_cycle_payload_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def exact_ordered_payload(self):
        if canonical_digest([row.model_dump(mode="json") for row in self.cycles]) != self.ordered_cycle_payload_sha256:
            raise ValueError("ordered cycle payload digest mismatch")
        if not any(row.sha256 == self.block_source_sha256 for row in self.evidence):
            raise ValueError("cycle block source digest must be represented by Evidence")
        ids = [row.cycle_id for row in self.cycles]
        if len(ids) != len(set(ids)):
            raise ValueError("cycle IDs must be unique inside each block")
        for cycle in self.cycles:
            if cycle.sample_time_s is None or len(cycle.sample_time_s) < 2:
                raise ValueError("each imported cycle requires ordered time-resolved tensor samples")
            repetitions = cycle.allocated_cycle_count
            if not math.isfinite(repetitions) or repetitions < 1 or repetitions != math.floor(repetitions):
                raise ValueError("stateful block repetitions must be positive integers")
        return self


class MultiaxialCycleBlockReceipt(Contract):
    """Ordered, source-pinned cycle blocks with explicit material-state endpoints."""

    receipt_id: str = Field(min_length=1)
    provider_id: str = Field(min_length=1)
    provider_revision: str = Field(min_length=1)
    provider_run_id: str = Field(min_length=1)
    provider_result_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    material_condition_id: str = Field(min_length=1)
    location_id: str = Field(min_length=1)
    clock_id: str = Field(min_length=1)
    stress_history_source_id: str = Field(min_length=1)
    stress_history_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    strain_history_source_id: str = Field(min_length=1)
    strain_history_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    strain_shear_convention: Literal["tensor", "engineering"]
    initial_material_state_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    terminal_material_state_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    blocks: tuple[OrderedTensorCycleBlock, ...] = Field(min_length=1, max_length=10000)
    provider_result_evidence: tuple[Evidence, ...] = Field(min_length=1)
    block_sequence_and_order_reviewed: bool
    cycle_count_and_repetition_semantics_reviewed: bool
    material_state_identity_and_transition_reviewed: bool
    tensor_units_order_and_shear_convention_reviewed: bool
    computational_use_authorized: bool

    @model_validator(mode="after")
    def contiguous_block_sequence(self):
        if not any(row.source_id == self.provider_id and row.sha256 == self.provider_result_sha256
                   for row in self.provider_result_evidence):
            raise ValueError("provider result digest must be bound to provider Evidence")
        if tuple(row.sequence_index for row in self.blocks) != tuple(range(len(self.blocks))):
            raise ValueError("cycle blocks must be supplied in exact zero-based sequence order")
        if len({row.block_id for row in self.blocks}) != len(self.blocks):
            raise ValueError("block IDs must be unique")
        cycle_ids = [cycle.cycle_id for block in self.blocks for cycle in block.cycles]
        if len(cycle_ids) != len(set(cycle_ids)):
            raise ValueError("cycle IDs must be unique across the complete ordered receipt")
        if self.blocks[0].material_state_before_sha256 != self.initial_material_state_sha256:
            raise ValueError("first block state must match receipt initial material-state identity")
        for previous, following in zip(self.blocks[:-1], self.blocks[1:], strict=True):
            if previous.material_state_after_sha256 != following.material_state_before_sha256:
                raise ValueError("material-state identity discontinuity between adjacent cycle blocks")
        if self.blocks[-1].material_state_after_sha256 != self.terminal_material_state_sha256:
            raise ValueError("last block state must match receipt terminal material-state identity")
        if not all((self.block_sequence_and_order_reviewed,
                    self.cycle_count_and_repetition_semantics_reviewed,
                    self.material_state_identity_and_transition_reviewed,
                    self.tensor_units_order_and_shear_convention_reviewed,
                    self.computational_use_authorized)):
            raise ValueError("cycle order, state continuity, tensor meaning and use reviews are required")
        return self


def bind_ordered_multiaxial_cycle_blocks(
    request: CallerStatefulMultiaxialDamageRequest,
    receipt: MultiaxialCycleBlockReceipt,
) -> CallerStatefulMultiaxialDamageRequest:
    """Require exact cycle and source alignment and add receipt lineage to a stateful request."""
    flattened = tuple(cycle for block in receipt.blocks for cycle in block.cycles)
    if request.material_condition_id != receipt.material_condition_id or request.location_id != receipt.location_id:
        raise ValueError("cycle receipt material/location differs from the stateful damage request")
    if (request.stress_history_source_id, request.stress_history_sha256,
        request.strain_history_source_id, request.strain_history_sha256,
        request.strain_shear_convention) != (
        receipt.stress_history_source_id, receipt.stress_history_sha256,
        receipt.strain_history_source_id, receipt.strain_history_sha256,
        receipt.strain_shear_convention,
    ):
        raise ValueError("cycle receipt and damage request stress/strain sources or shear basis differ")
    request_cycles = [row.model_dump(mode="json") for row in request.cycles]
    receipt_cycles = [row.model_dump(mode="json") for row in flattened]
    if request_cycles != receipt_cycles:
        raise ValueError("damage request cycles must exactly match receipt block and cycle order")
    if request.cycle_exchange_receipt_sha256 is not None:
        raise ValueError("stateful request is already bound to a cycle exchange receipt")
    receipt_sha256 = canonical_digest(receipt.model_dump(mode="json"))
    return request.model_copy(update={
        "cycle_exchange_receipt_sha256": receipt_sha256,
        "cycle_block_order_ids": tuple(row.block_id for row in receipt.blocks),
        "cycle_exchange_clock_id": receipt.clock_id,
        "cycle_exchange_provider_id": receipt.provider_id,
        "cycle_exchange_provider_revision": receipt.provider_revision,
        "cycle_exchange_provider_run_id": receipt.provider_run_id,
        "cycle_exchange_provider_result_sha256": receipt.provider_result_sha256,
        "cycle_source_initial_state_sha256": receipt.initial_material_state_sha256,
        "cycle_source_terminal_state_sha256": receipt.terminal_material_state_sha256,
    })

