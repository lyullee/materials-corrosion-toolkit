"""Weighted calibration and holdout diagnostics for a binary event pair."""

from __future__ import annotations

import math
from typing import Literal

from pydantic import Field, model_validator

from ..contracts import Calculation, Contract, Evidence, Nonnegative, Positive
from ..registry import ModelSpec

Partition = Literal["calibration", "holdout"]
CELL_KEYS = ("00", "01", "10", "11")


class BinaryEventPairObservation(Contract):
    observation_id: str = Field(min_length=1)
    physical_sequence_id: str = Field(min_length=1)
    source_group_id: str = Field(min_length=1)
    independence_group_id: str = Field(min_length=1)
    partition: Partition
    observation_start_s: Nonnegative
    observation_end_s: Positive
    event_a_occurs: bool
    event_b_occurs: bool
    sample_weight: Positive
    record_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    record_valid: bool
    invalid_or_missing_basis: str | None = None
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def ordered_valid_observation(self):
        if self.observation_end_s <= self.observation_start_s:
            raise ValueError("binary event-pair observations require positive clock intervals")
        if not self.record_valid and not self.invalid_or_missing_basis:
            raise ValueError("an invalid binary event-pair observation requires a basis")
        return self


class BinaryEventPairCalibration(Contract):
    calibration_id: str = Field(min_length=1)
    asset_id: str = Field(min_length=1)
    location_id: str = Field(min_length=1)
    physical_scope_id: str = Field(min_length=1)
    observation_clock_id: str = Field(min_length=1)
    time_basis: str = Field(min_length=1)
    event_a_id: str = Field(min_length=1)
    event_a_definition: str = Field(min_length=1)
    event_b_id: str = Field(min_length=1)
    event_b_definition: str = Field(min_length=1)
    observations: tuple[BinaryEventPairObservation, ...] = Field(min_length=2)
    symmetric_cell_pseudocount: Nonnegative | None = None
    pseudocount_basis: str | None = None
    minimum_calibration_record_count: int = Field(ge=1)
    minimum_holdout_record_count: int = Field(ge=1)
    minimum_calibration_sequence_count: int = Field(ge=1)
    minimum_holdout_sequence_count: int = Field(ge=1)
    minimum_calibration_source_group_count: int = Field(ge=1)
    minimum_holdout_source_group_count: int = Field(ge=1)
    minimum_holdout_independence_group_count: int = Field(ge=1)
    event_definitions_reviewed: bool
    observation_clock_and_scope_reviewed: bool
    partition_assignments_reviewed: bool
    physical_sequence_source_and_independence_groups_reviewed: bool
    sample_weights_and_missingness_reviewed: bool
    pseudocount_choice_reviewed: bool
    record_digests_reviewed: bool

    @model_validator(mode="after")
    def identities_partitions_and_pseudocount(self):
        if self.event_a_id == self.event_b_id:
            raise ValueError("binary event-pair identifiers must be distinct")
        identifiers = [row.observation_id for row in self.observations]
        if len(set(identifiers)) != len(identifiers):
            raise ValueError("binary event-pair observation identifiers must be unique")
        if self.symmetric_cell_pseudocount is not None and not self.pseudocount_basis:
            raise ValueError("an explicit pseudocount requires a caller-declared basis")
        if self.symmetric_cell_pseudocount is None and self.pseudocount_basis is not None:
            raise ValueError("a pseudocount basis cannot be supplied without a pseudocount")
        for attribute, name in (
            ("physical_sequence_id", "physical sequence"),
            ("source_group_id", "source group"),
            ("independence_group_id", "independence group"),
        ):
            partitions_by_id: dict[str, set[str]] = {}
            for row in self.observations:
                partitions_by_id.setdefault(getattr(row, attribute), set()).add(row.partition)
            crossed = sorted(identifier for identifier, values in partitions_by_id.items() if len(values) > 1)
            if crossed:
                raise ValueError(f"{name} identifiers cannot cross calibration and holdout partitions")
        return self


def _cell_key(row: BinaryEventPairObservation) -> str:
    return f"{int(row.event_a_occurs)}{int(row.event_b_occurs)}"


def _weighted_cells(rows: list[BinaryEventPairObservation]) -> dict[str, float]:
    return {key: math.fsum(row.sample_weight for row in rows if _cell_key(row) == key) for key in CELL_KEYS}


def _normalized_cells(weighted_cells: dict[str, float], pseudocount: float) -> dict[str, float]:
    denominator = math.fsum(weighted_cells.values()) + 4.0 * pseudocount
    return {key: (weighted_cells[key] + pseudocount) / denominator for key in CELL_KEYS}


def binary_event_pair_calibration(x: BinaryEventPairCalibration) -> Calculation:
    missing_reviews = [
        name
        for name in (
            "event_definitions_reviewed",
            "observation_clock_and_scope_reviewed",
            "partition_assignments_reviewed",
            "physical_sequence_source_and_independence_groups_reviewed",
            "sample_weights_and_missingness_reviewed",
            "pseudocount_choice_reviewed",
            "record_digests_reviewed",
        )
        if not getattr(x, name)
    ]
    invalid_record_ids = [row.observation_id for row in x.observations if not row.record_valid]
    calibration = [row for row in x.observations if row.partition == "calibration"]
    holdout = [row for row in x.observations if row.partition == "holdout"]
    calibration_sequences = {row.physical_sequence_id for row in calibration}
    holdout_sequences = {row.physical_sequence_id for row in holdout}
    calibration_sources = {row.source_group_id for row in calibration}
    holdout_sources = {row.source_group_id for row in holdout}
    holdout_independence = {row.independence_group_id for row in holdout}
    count_requirements_met = (
        len(calibration) >= x.minimum_calibration_record_count
        and len(holdout) >= x.minimum_holdout_record_count
        and len(calibration_sequences) >= x.minimum_calibration_sequence_count
        and len(holdout_sequences) >= x.minimum_holdout_sequence_count
        and len(calibration_sources) >= x.minimum_calibration_source_group_count
        and len(holdout_sources) >= x.minimum_holdout_source_group_count
        and len(holdout_independence) >= x.minimum_holdout_independence_group_count
    )
    if missing_reviews or invalid_record_ids or not count_requirements_met:
        return Calculation(
            status="needs_data",
            values={
                "calibration_id": x.calibration_id,
                "missing_reviews": missing_reviews,
                "invalid_observation_ids": invalid_record_ids,
                "count_requirements_met": count_requirements_met,
                "calibration_record_count": len(calibration),
                "holdout_record_count": len(holdout),
                "calibration_sequence_count": len(calibration_sequences),
                "holdout_sequence_count": len(holdout_sequences),
                "calibration_source_group_count": len(calibration_sources),
                "holdout_source_group_count": len(holdout_sources),
                "holdout_independence_group_count": len(holdout_independence),
            },
            notes=("Reviewed, valid and sufficiently partitioned observations are required.",),
        )

    calibration_weighted_cells = _weighted_cells(calibration)
    pseudocount = x.symmetric_cell_pseudocount or 0.0
    probabilities = _normalized_cells(calibration_weighted_cells, pseudocount)
    event_a_probability = probabilities["10"] + probabilities["11"]
    event_b_probability = probabilities["01"] + probabilities["11"]
    joint_probability = probabilities["11"]
    covariance = joint_probability - event_a_probability * event_b_probability
    phi_denominator = math.sqrt(
        event_a_probability * (1.0 - event_a_probability) * event_b_probability * (1.0 - event_b_probability)
    )
    phi = covariance / phi_denominator if phi_denominator > 0 else None

    holdout_weighted_cells = _weighted_cells(holdout)
    holdout_total_weight = math.fsum(holdout_weighted_cells.values())
    zero_probability_holdout_weight = math.fsum(
        row.sample_weight for row in holdout if probabilities[_cell_key(row)] == 0.0
    )
    if zero_probability_holdout_weight > 0:
        holdout_mean_negative_log_score = None
    else:
        holdout_mean_negative_log_score = (
            math.fsum(-row.sample_weight * math.log(probabilities[_cell_key(row)]) for row in holdout)
            / holdout_total_weight
        )
    holdout_multiclass_brier = (
        math.fsum(
            row.sample_weight
            * math.fsum(
                (probabilities[key] - (1.0 if key == _cell_key(row) else 0.0)) ** 2 for key in CELL_KEYS
            )
            for row in holdout
        )
        / holdout_total_weight
    )
    holdout_probabilities = {
        key: value / holdout_total_weight for key, value in holdout_weighted_cells.items()
    }
    values = {
        "calibration_id": x.calibration_id,
        "asset_id": x.asset_id,
        "location_id": x.location_id,
        "physical_scope_id": x.physical_scope_id,
        "observation_clock_id": x.observation_clock_id,
        "event_ids": [x.event_a_id, x.event_b_id],
        "cell_order": list(CELL_KEYS),
        "calibration_raw_record_counts": {
            key: sum(_cell_key(row) == key for row in calibration) for key in CELL_KEYS
        },
        "calibration_weighted_cell_totals": calibration_weighted_cells,
        "calibration_cell_probabilities": probabilities,
        "calibration_event_a_probability": event_a_probability,
        "calibration_event_b_probability": event_b_probability,
        "calibration_joint_probability": joint_probability,
        "calibration_covariance": covariance,
        "calibration_phi": phi,
        "symmetric_cell_pseudocount": x.symmetric_cell_pseudocount,
        "holdout_raw_record_counts": {
            key: sum(_cell_key(row) == key for row in holdout) for key in CELL_KEYS
        },
        "holdout_weighted_cell_totals": holdout_weighted_cells,
        "holdout_empirical_cell_probabilities": holdout_probabilities,
        "holdout_mean_negative_log_score": holdout_mean_negative_log_score,
        "holdout_zero_probability_observation_weight": zero_probability_holdout_weight,
        "holdout_multiclass_brier_score": holdout_multiclass_brier,
        "calibration_sequence_ids": sorted(calibration_sequences),
        "holdout_sequence_ids": sorted(holdout_sequences),
        "calibration_source_group_ids": sorted(calibration_sources),
        "holdout_source_group_ids": sorted(holdout_sources),
        "holdout_independence_group_ids": sorted(holdout_independence),
    }
    return Calculation(
        values=values,
        notes=(
            "Probabilities describe the reviewed weighted calibration observations only; they are not future-period or FTA probabilities.",
            "The multiclass Brier score uses the four mutually exclusive joint cells in the declared cell order.",
            "Covariance and phi are descriptive association measures and do not establish independence or causality.",
            "A missing log score indicates positive holdout weight in a calibration cell with zero probability; it is not clipped.",
        ),
    )


def specifications():
    def same_identity(x, context):
        if (x.asset_id, x.location_id) != (context.asset_id, context.location_id):
            raise ValueError("binary event-pair calibration asset and location must match run context")
        if x.time_basis != context.time_basis:
            raise ValueError("binary event-pair calibration time basis must match run context")

    return [
        ModelSpec(
            "reliability.binary_event_pair_calibration",
            BinaryEventPairCalibration,
            binary_event_pair_calibration,
            {
                "calibration_id": "1",
                "asset_id": "1",
                "location_id": "1",
                "physical_scope_id": "1",
                "observation_clock_id": "1",
                "event_ids": "1",
                "cell_order": "1",
                "calibration_raw_record_counts": "1",
                "calibration_weighted_cell_totals": "weight",
                "calibration_cell_probabilities": "1",
                "calibration_event_a_probability": "1",
                "calibration_event_b_probability": "1",
                "calibration_joint_probability": "1",
                "calibration_covariance": "1",
                "calibration_phi": "1",
                "symmetric_cell_pseudocount": "weight",
                "holdout_raw_record_counts": "1",
                "holdout_weighted_cell_totals": "weight",
                "holdout_empirical_cell_probabilities": "1",
                "holdout_mean_negative_log_score": "1",
                "holdout_zero_probability_observation_weight": "weight",
                "holdout_multiclass_brier_score": "1",
                "calibration_sequence_ids": "1",
                "holdout_sequence_ids": "1",
                "calibration_source_group_ids": "1",
                "holdout_source_group_ids": "1",
                "holdout_independence_group_ids": "1",
            },
            (
                "Calibration and holdout physical sequences, source groups and independence groups are disjoint.",
                "Weights and any symmetric cell pseudocount are explicit caller-reviewed inputs.",
                "Empirical pair probabilities are observation-distribution diagnostics, not FTA or future risk.",
            ),
            ("reviewed_binary_event_pair_calibration_holdout_observations",),
            context_validator=same_identity,
            probability_semantics={
                "calibration_event_a_probability": "unscoped_event_probability",
                "calibration_event_b_probability": "unscoped_event_probability",
                "calibration_joint_probability": "unscoped_event_probability",
            },
        )
    ]
