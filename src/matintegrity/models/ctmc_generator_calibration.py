"""Weighted CTMC generator calibration and holdout count diagnostics."""

from __future__ import annotations

import math
from typing import Literal

from pydantic import Field, model_validator

from ..contracts import Calculation, Contract, Evidence, Nonnegative, Positive
from ..registry import ModelSpec

Partition = Literal["calibration", "holdout"]


class CTMCTransitionDefinition(Contract):
    transition_id: str = Field(min_length=1)
    origin_state_id: str = Field(min_length=1)
    destination_state_id: str = Field(min_length=1)
    transition_definition: str = Field(min_length=1)

    @model_validator(mode="after")
    def different_states(self):
        if self.origin_state_id == self.destination_state_id:
            raise ValueError("CTMC transition definitions cannot be self-transitions")
        return self


class CTMCStateExposure(Contract):
    state_id: str = Field(min_length=1)
    exposure_duration: Nonnegative


class CTMCTransitionCount(Contract):
    transition_id: str = Field(min_length=1)
    transition_count: int = Field(ge=0)


class CTMCCountExposureObservation(Contract):
    observation_id: str = Field(min_length=1)
    physical_sequence_id: str = Field(min_length=1)
    source_group_id: str = Field(min_length=1)
    independence_group_id: str = Field(min_length=1)
    partition: Partition
    observation_start_s: Nonnegative
    observation_end_s: Positive
    sample_weight: Positive
    exposure_unit_token: str = Field(min_length=1)
    state_exposures: tuple[CTMCStateExposure, ...] = Field(min_length=1)
    transition_counts: tuple[CTMCTransitionCount, ...] = Field(min_length=1)
    record_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    record_valid: bool
    invalid_or_missing_basis: str | None = None
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def ordered_unique_record(self):
        if self.observation_end_s <= self.observation_start_s:
            raise ValueError("CTMC count/exposure observations require positive clock intervals")
        state_ids = [row.state_id for row in self.state_exposures]
        transition_ids = [row.transition_id for row in self.transition_counts]
        if len(set(state_ids)) != len(state_ids):
            raise ValueError("CTMC state-exposure identifiers must be unique per observation")
        if len(set(transition_ids)) != len(transition_ids):
            raise ValueError("CTMC transition-count identifiers must be unique per observation")
        if not self.record_valid and not self.invalid_or_missing_basis:
            raise ValueError("an invalid CTMC count/exposure observation requires a basis")
        return self


class CTMCGeneratorCalibration(Contract):
    calibration_id: str = Field(min_length=1)
    asset_id: str = Field(min_length=1)
    location_id: str = Field(min_length=1)
    physical_scope_id: str = Field(min_length=1)
    observation_clock_id: str = Field(min_length=1)
    time_basis: str = Field(min_length=1)
    state_ids: tuple[str, ...] = Field(min_length=2)
    state_definitions: tuple[str, ...] = Field(min_length=2)
    transition_definitions: tuple[CTMCTransitionDefinition, ...] = Field(min_length=1)
    observations: tuple[CTMCCountExposureObservation, ...] = Field(min_length=2)
    transition_count_pseudocount: Nonnegative | None = None
    pseudocount_basis: str | None = None
    minimum_calibration_record_count: int = Field(ge=1)
    minimum_holdout_record_count: int = Field(ge=1)
    minimum_calibration_sequence_count: int = Field(ge=1)
    minimum_holdout_sequence_count: int = Field(ge=1)
    minimum_calibration_source_group_count: int = Field(ge=1)
    minimum_holdout_source_group_count: int = Field(ge=1)
    minimum_holdout_independence_group_count: int = Field(ge=1)
    state_and_transition_definitions_reviewed: bool
    observation_clock_scope_and_exposure_units_reviewed: bool
    transition_counts_exposures_and_weights_reviewed: bool
    partition_assignments_reviewed: bool
    physical_sequence_source_and_independence_groups_reviewed: bool
    single_generator_calibration_scope_reviewed: bool
    pseudocount_choice_reviewed: bool
    record_digests_and_missingness_reviewed: bool

    @model_validator(mode="after")
    def aligned_state_transition_records(self):
        if len(set(self.state_ids)) != len(self.state_ids):
            raise ValueError("CTMC state identifiers must be unique")
        if len(self.state_definitions) != len(self.state_ids):
            raise ValueError("CTMC state identifiers and definitions must align")
        transition_ids = [row.transition_id for row in self.transition_definitions]
        transition_pairs = [
            (row.origin_state_id, row.destination_state_id) for row in self.transition_definitions
        ]
        if len(set(transition_ids)) != len(transition_ids):
            raise ValueError("CTMC transition identifiers must be unique")
        if len(set(transition_pairs)) != len(transition_pairs):
            raise ValueError("CTMC directed transition pairs must be unique")
        known_states = set(self.state_ids)
        if any(
            row.origin_state_id not in known_states or row.destination_state_id not in known_states
            for row in self.transition_definitions
        ):
            raise ValueError("CTMC transitions must reference declared states")
        if self.transition_count_pseudocount is not None and not self.pseudocount_basis:
            raise ValueError("an explicit CTMC pseudocount requires a caller-declared basis")
        if self.transition_count_pseudocount is None and self.pseudocount_basis is not None:
            raise ValueError("a CTMC pseudocount basis cannot be supplied without a pseudocount")
        expected_states = set(self.state_ids)
        expected_transitions = set(transition_ids)
        exposure_units = {row.exposure_unit_token for row in self.observations}
        if len(exposure_units) != 1:
            raise ValueError("CTMC observation exposure units must match exactly")
        for row in self.observations:
            if {item.state_id for item in row.state_exposures} != expected_states:
                raise ValueError("every CTMC observation must contain exactly every declared state exposure")
            if {item.transition_id for item in row.transition_counts} != expected_transitions:
                raise ValueError(
                    "every CTMC observation must contain exactly every declared transition count"
                )
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


def _records_by_partition(x: CTMCGeneratorCalibration, partition: Partition):
    return [row for row in x.observations if row.partition == partition]


def ctmc_generator_calibration(x: CTMCGeneratorCalibration) -> Calculation:
    missing_reviews = [
        name
        for name in (
            "state_and_transition_definitions_reviewed",
            "observation_clock_scope_and_exposure_units_reviewed",
            "transition_counts_exposures_and_weights_reviewed",
            "partition_assignments_reviewed",
            "physical_sequence_source_and_independence_groups_reviewed",
            "single_generator_calibration_scope_reviewed",
            "pseudocount_choice_reviewed",
            "record_digests_and_missingness_reviewed",
        )
        if not getattr(x, name)
    ]
    invalid_record_ids = [row.observation_id for row in x.observations if not row.record_valid]
    calibration = _records_by_partition(x, "calibration")
    holdout = _records_by_partition(x, "holdout")
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
            notes=("Reviewed, valid and sufficiently partitioned CTMC observations are required.",),
        )

    exposure_unit_token = calibration[0].exposure_unit_token
    transition_by_id = {row.transition_id: row for row in x.transition_definitions}
    state_index = {state_id: index for index, state_id in enumerate(x.state_ids)}
    weighted_calibration_exposure = {state_id: 0.0 for state_id in x.state_ids}
    weighted_calibration_counts = {transition_id: 0.0 for transition_id in transition_by_id}
    for record in calibration:
        for exposure in record.state_exposures:
            weighted_calibration_exposure[exposure.state_id] += (
                record.sample_weight * exposure.exposure_duration
            )
        for count in record.transition_counts:
            weighted_calibration_counts[count.transition_id] += record.sample_weight * count.transition_count
    zero_exposure_transition_ids = [
        transition_id
        for transition_id, definition in transition_by_id.items()
        if weighted_calibration_exposure[definition.origin_state_id] == 0.0
    ]
    if zero_exposure_transition_ids:
        return Calculation(
            status="needs_data",
            values={
                "calibration_id": x.calibration_id,
                "zero_calibration_exposure_transition_ids": zero_exposure_transition_ids,
                "weighted_calibration_state_exposures": weighted_calibration_exposure,
                "weighted_calibration_transition_counts": weighted_calibration_counts,
            },
            notes=("Every declared transition needs positive calibration exposure in its origin state.",),
        )

    pseudocount = x.transition_count_pseudocount or 0.0
    transition_rates = {
        transition_id: (weighted_calibration_counts[transition_id] + pseudocount)
        / weighted_calibration_exposure[definition.origin_state_id]
        for transition_id, definition in transition_by_id.items()
    }
    generator = [[0.0 for _ in x.state_ids] for _ in x.state_ids]
    for transition_id, definition in transition_by_id.items():
        origin = state_index[definition.origin_state_id]
        destination = state_index[definition.destination_state_id]
        generator[origin][destination] = transition_rates[transition_id]
    for index in range(len(x.state_ids)):
        generator[index][index] = -math.fsum(
            value for column, value in enumerate(generator[index]) if column != index
        )

    holdout_negative_log_likelihood = 0.0
    holdout_poisson_deviance = 0.0
    zero_expected_positive_count_weight = 0.0
    holdout_weighted_counts = {transition_id: 0.0 for transition_id in transition_by_id}
    holdout_weighted_expected_counts = {transition_id: 0.0 for transition_id in transition_by_id}
    for record in holdout:
        exposure_by_state = {row.state_id: row.exposure_duration for row in record.state_exposures}
        count_by_transition = {row.transition_id: row.transition_count for row in record.transition_counts}
        for transition_id, definition in transition_by_id.items():
            observed = count_by_transition[transition_id]
            expected = transition_rates[transition_id] * exposure_by_state[definition.origin_state_id]
            weight = record.sample_weight
            holdout_weighted_counts[transition_id] += weight * observed
            holdout_weighted_expected_counts[transition_id] += weight * expected
            if expected == 0.0 and observed > 0:
                zero_expected_positive_count_weight += weight * observed
                continue
            holdout_negative_log_likelihood += weight * (
                expected - observed * math.log(expected) + math.lgamma(observed + 1.0)
                if observed > 0
                else expected
            )
            if observed > 0:
                holdout_poisson_deviance += (
                    2.0 * weight * (observed * math.log(observed / expected) - (observed - expected))
                )
            else:
                holdout_poisson_deviance += 2.0 * weight * expected
    if zero_expected_positive_count_weight > 0:
        holdout_negative_log_likelihood_value = None
        holdout_poisson_deviance_value = None
    else:
        holdout_negative_log_likelihood_value = holdout_negative_log_likelihood
        holdout_poisson_deviance_value = holdout_poisson_deviance
    return Calculation(
        values={
            "calibration_id": x.calibration_id,
            "asset_id": x.asset_id,
            "location_id": x.location_id,
            "physical_scope_id": x.physical_scope_id,
            "observation_clock_id": x.observation_clock_id,
            "state_ids": list(x.state_ids),
            "transition_ids": list(transition_by_id),
            "exposure_unit_token": exposure_unit_token,
            "generator_rate_unit_token": f"1/({exposure_unit_token})",
            "weighted_calibration_state_exposures": weighted_calibration_exposure,
            "weighted_calibration_transition_counts": weighted_calibration_counts,
            "transition_count_pseudocount": x.transition_count_pseudocount,
            "estimated_transition_rates": transition_rates,
            "estimated_generator": generator,
            "holdout_weighted_transition_counts": holdout_weighted_counts,
            "holdout_weighted_expected_transition_counts": holdout_weighted_expected_counts,
            "holdout_total_negative_log_likelihood": holdout_negative_log_likelihood_value,
            "holdout_total_poisson_deviance": holdout_poisson_deviance_value,
            "holdout_zero_expected_positive_count_weight": zero_expected_positive_count_weight,
            "calibration_sequence_ids": sorted(calibration_sequences),
            "holdout_sequence_ids": sorted(holdout_sequences),
            "calibration_source_group_ids": sorted(calibration_sources),
            "holdout_source_group_ids": sorted(holdout_sources),
            "holdout_independence_group_ids": sorted(holdout_independence),
        },
        notes=(
            "Rates are weighted count divided by weighted origin-state exposure under the caller-declared single-generator calibration scope.",
            "Holdout scores use transition-wise Poisson count likelihoods and do not establish stationarity, independence or causal transition mechanisms.",
            "The estimated generator is not propagated into future reliability, repair policy or FTA probabilities.",
            "Undefined holdout scores preserve positive observed counts with zero expected count instead of clipping rates.",
        ),
    )


def specifications():
    def same_identity(x, context):
        if (x.asset_id, x.location_id) != (context.asset_id, context.location_id):
            raise ValueError("CTMC generator calibration asset and location must match run context")
        if x.time_basis != context.time_basis:
            raise ValueError("CTMC generator calibration time basis must match run context")

    return [
        ModelSpec(
            "reliability.ctmc_generator_calibration",
            CTMCGeneratorCalibration,
            ctmc_generator_calibration,
            {
                "calibration_id": "1",
                "asset_id": "1",
                "location_id": "1",
                "physical_scope_id": "1",
                "observation_clock_id": "1",
                "state_ids": "1",
                "transition_ids": "1",
                "exposure_unit_token": "1",
                "generator_rate_unit_token": "1",
                "weighted_calibration_state_exposures": "weighted exposure",
                "weighted_calibration_transition_counts": "weighted count",
                "transition_count_pseudocount": "count",
                "estimated_transition_rates": "1/exposure unit",
                "estimated_generator": "1/exposure unit",
                "holdout_weighted_transition_counts": "weighted count",
                "holdout_weighted_expected_transition_counts": "weighted count",
                "holdout_total_negative_log_likelihood": "1",
                "holdout_total_poisson_deviance": "1",
                "holdout_zero_expected_positive_count_weight": "weighted count",
                "calibration_sequence_ids": "1",
                "holdout_sequence_ids": "1",
                "calibration_source_group_ids": "1",
                "holdout_source_group_ids": "1",
                "holdout_independence_group_ids": "1",
            },
            (
                "State/transition definitions and exposure units are exact caller-reviewed identities.",
                "Calibration and holdout sequences, source groups and independence groups are disjoint.",
                "Estimated rates and holdout diagnostics do not establish stationary physics or future risk.",
            ),
            ("reviewed_ctmc_transition_count_exposure_observations",),
            context_validator=same_identity,
        )
    ]
