"""Partition-aware comparison of caller-supplied pipe-burst predictions and tests."""

from __future__ import annotations

import math
import statistics
from collections import defaultdict
from typing import Literal

from pydantic import Field, model_validator

from ..contracts import Calculation, Contract, Positive
from ..registry import ModelSpec


class BurstPressureComparisonRow(Contract):
    observation_id: str = Field(min_length=1)
    physical_specimen_id: str | None = Field(default=None, min_length=1)
    source_group_id: str = Field(min_length=1)
    partition: Literal["calibration", "holdout", "external_validation"]
    material_condition_id: str = Field(min_length=1)
    geometry_id: str = Field(min_length=1)
    load_case_id: str = Field(min_length=1)
    observed_pressure_basis: Literal[
        "internal_minus_external",
        "gauge_internal",
        "absolute_internal",
        "unresolved",
    ]
    predicted_pressure_basis: Literal[
        "internal_minus_external",
        "gauge_internal",
        "absolute_internal",
        "unresolved",
    ]
    observed_burst_pressure_Pa: Positive
    predicted_failure_pressure_Pa: Positive
    observation_source_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    prediction_input_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    observation_use_authorized: bool
    experimental_endpoint_reviewed: bool
    geometry_and_material_reviewed: bool
    pressure_basis_reviewed: bool


class BurstPressureComparison(Contract):
    comparison_id: str = Field(min_length=1)
    prediction_provider_id: str = Field(min_length=1)
    prediction_provider_version: str = Field(min_length=1)
    prediction_configuration_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    rows: tuple[BurstPressureComparisonRow, ...] = Field(min_length=1, max_length=10000)
    physical_specimen_independence_reviewed: bool
    source_group_partitioning_reviewed: bool
    prediction_frozen_before_evaluation: bool

    @model_validator(mode="after")
    def identities_and_partitions(self):
        observation_ids = [row.observation_id for row in self.rows]
        if len(observation_ids) != len(set(observation_ids)):
            raise ValueError("burst comparison observation IDs must be unique")
        specimen_ids = [row.physical_specimen_id for row in self.rows if row.physical_specimen_id]
        if len(specimen_ids) != len(set(specimen_ids)):
            raise ValueError("one physical specimen cannot appear in multiple comparison rows")
        if self.physical_specimen_independence_reviewed and any(
            row.physical_specimen_id is None for row in self.rows
        ):
            raise ValueError("reviewed specimen independence requires every physical specimen ID")
        if not any(row.partition in {"holdout", "external_validation"} for row in self.rows):
            raise ValueError("burst comparison requires at least one evaluation row")
        groups: dict[str, set[str]] = defaultdict(set)
        for row in self.rows:
            groups[row.source_group_id].add(row.partition)
        if any("calibration" in partitions and len(partitions) > 1 for partitions in groups.values()):
            raise ValueError("a source group cannot cross from calibration into evaluation partitions")
        return self


def compare_burst_pressures(x: BurstPressureComparison) -> Calculation:
    if not all(
        (
            x.physical_specimen_independence_reviewed,
            x.source_group_partitioning_reviewed,
            x.prediction_frozen_before_evaluation,
        )
    ):
        return Calculation(
            status="needs_data",
            values={},
            notes=(
                "Review physical specimen independence, source-group partitioning and prediction freezing before comparison.",
            ),
        )
    row_reviews = (
        row.observation_use_authorized
        and row.experimental_endpoint_reviewed
        and row.geometry_and_material_reviewed
        and row.pressure_basis_reviewed
        and row.physical_specimen_id is not None
        and row.observed_pressure_basis != "unresolved"
        and row.observed_pressure_basis == row.predicted_pressure_basis
        for row in x.rows
    )
    if not all(row_reviews):
        return Calculation(
            status="needs_data",
            values={},
            notes=(
                "Every row needs authorized use, a reviewed experimental endpoint, geometry/material identity, a physical specimen ID and matching reviewed pressure bases.",
            ),
        )

    pointwise = []
    ratios_by_partition: dict[str, list[float]] = defaultdict(list)
    for row in x.rows:
        ratio = row.predicted_failure_pressure_Pa / row.observed_burst_pressure_Pa
        log_ratio = math.log(ratio)
        if not math.isfinite(ratio) or not math.isfinite(log_ratio):
            return Calculation(
                status="out_of_scope",
                values={},
                notes=("A pressure ratio exceeds the finite numerical range.",),
            )
        ratios_by_partition[row.partition].append(ratio)
        pointwise.append(
            dict(
                observation_id=row.observation_id,
                physical_specimen_id=row.physical_specimen_id,
                source_group_id=row.source_group_id,
                partition=row.partition,
                material_condition_id=row.material_condition_id,
                geometry_id=row.geometry_id,
                load_case_id=row.load_case_id,
                pressure_basis=row.observed_pressure_basis,
                predicted_to_observed_pressure_ratio=ratio,
                log_predicted_to_observed_pressure_ratio=log_ratio,
                observation_source_sha256=row.observation_source_sha256,
                prediction_input_digest=row.prediction_input_digest,
            )
        )

    summaries = {}
    for partition in ("calibration", "holdout", "external_validation"):
        ratios = ratios_by_partition.get(partition, [])
        if not ratios:
            continue
        log_ratios = [math.log(value) for value in ratios]
        summaries[partition] = dict(
            observations=len(ratios),
            source_group_ids=sorted({row.source_group_id for row in x.rows if row.partition == partition}),
            arithmetic_mean_predicted_to_observed_ratio=statistics.fmean(ratios),
            median_predicted_to_observed_ratio=statistics.median(ratios),
            minimum_predicted_to_observed_ratio=min(ratios),
            maximum_predicted_to_observed_ratio=max(ratios),
            mean_log_ratio=statistics.fmean(log_ratios),
            root_mean_square_log_error=math.sqrt(statistics.fmean(value * value for value in log_ratios)),
            mean_absolute_relative_error=statistics.fmean(abs(value - 1.0) for value in ratios),
        )

    return Calculation(
        values=dict(
            comparison_id=x.comparison_id,
            prediction_provider_id=x.prediction_provider_id,
            prediction_provider_version=x.prediction_provider_version,
            prediction_configuration_digest=x.prediction_configuration_digest,
            partition_summaries=summaries,
            pointwise_comparisons=pointwise,
            observation_count=len(pointwise),
        ),
        notes=(
            "Ratios are caller-supplied predicted failure pressure divided by reviewed experimental burst pressure on an identical declared pressure basis; no pressure model or standard coefficient is bundled.",
            "Calibration, holdout and external-validation summaries remain separate. Source groups cannot cross from calibration into evaluation, and every physical specimen can appear only once.",
            "These descriptive errors do not establish code acceptance, a safety factor, prediction intervals, population coverage, independence beyond the caller review, remaining life or failure probability.",
        ),
    )


def specifications():
    return [
        ModelSpec(
            "structural.burst_pressure_comparison",
            BurstPressureComparison,
            compare_burst_pressures,
            {
                "partition_summaries.calibration.arithmetic_mean_predicted_to_observed_ratio": "1",
                "partition_summaries.holdout.arithmetic_mean_predicted_to_observed_ratio": "1",
                "partition_summaries.external_validation.arithmetic_mean_predicted_to_observed_ratio": "1",
                "partition_summaries.calibration.root_mean_square_log_error": "1",
                "partition_summaries.holdout.root_mean_square_log_error": "1",
                "partition_summaries.external_validation.root_mean_square_log_error": "1",
                "pointwise_comparisons.predicted_to_observed_pressure_ratio": "1",
                "pointwise_comparisons.log_predicted_to_observed_pressure_ratio": "1",
                "observation_count": "1",
            },
            (
                "Partition-aware descriptive comparison of caller-supplied pressure predictions with qualified burst tests; no pressure equation, acceptance limit or standard table is bundled.",
            ),
            ("burst_prediction_comparison_definition",),
        )
    ]
