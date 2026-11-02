"""Reproducible pCN subset simulation for deterministic caller limit-state functions."""

from __future__ import annotations

import math
from collections.abc import Callable
from typing import Literal

import numpy as np
from pydantic import Field, model_validator

from .contracts import Contract, EventProbability, Fraction, Positive, canonical_digest


class SubsetSimulationRequest(Contract):
    schema_version: Literal["matintegrity.subset_simulation_request.v1"] = (
        "matintegrity.subset_simulation_request.v1"
    )
    estimate_id: str = Field(min_length=1)
    event_id: str = Field(min_length=1)
    event_definition: str = Field(min_length=1)
    failure_mode: str = Field(min_length=1)
    asset_id: str = Field(min_length=1)
    location_id: str = Field(min_length=1)
    physical_scope_id: str = Field(min_length=1)
    time_basis: str = Field(min_length=1)
    horizon_start_s: float = Field(ge=0)
    horizon_end_s: Positive
    conditioning: str = Field(min_length=1)
    latent_variable_ids: tuple[str, ...] = Field(min_length=1, max_length=32)
    evaluator_id: str = Field(min_length=1)
    evaluator_revision: str = Field(min_length=1)
    evaluator_configuration_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    random_seed: int = Field(ge=0, le=2**64 - 1)
    samples_per_level: int = Field(ge=100, le=200_000)
    conditional_probability: Fraction = Field(gt=0, lt=1)
    pcn_beta: Positive = Field(le=1)
    maximum_levels: int = Field(ge=1, le=20)
    latent_mapping_reviewed: bool
    event_semantics_reviewed: bool
    event_is_first_failure_in_period_reviewed: bool
    deterministic_evaluator_declared: bool

    @model_validator(mode="after")
    def coherent_sampling_contract(self):
        if self.horizon_end_s <= self.horizon_start_s:
            raise ValueError("subset-simulation horizon must have positive duration")
        if len(set(self.latent_variable_ids)) != len(self.latent_variable_ids):
            raise ValueError("latent-variable identifiers must be unique")
        if math.ceil(self.conditional_probability * self.samples_per_level) < 2:
            raise ValueError("at least two seeds must be selected at each conditional level")
        return self


class SubsetSimulationLevel(Contract):
    level_index: int = Field(ge=0)
    threshold_value: float
    conditional_probability_estimate: Fraction
    conditioned_seed_count: int = Field(ge=0)
    samples_per_level: int = Field(gt=0)
    proposal_count: int = Field(ge=0)
    proposal_acceptance_fraction: Fraction | None
    distinct_adjacent_state_fraction: Fraction | None
    cumulative_probability_estimate: Fraction
    cumulative_log_probability_estimate: float


class SubsetSimulationResult(Contract):
    schema_version: Literal["matintegrity.subset_simulation_result.v1"] = (
        "matintegrity.subset_simulation_result.v1"
    )
    estimate_id: str = Field(min_length=1)
    event_id: str = Field(min_length=1)
    event_definition: str = Field(min_length=1)
    failure_mode: str = Field(min_length=1)
    asset_id: str = Field(min_length=1)
    location_id: str = Field(min_length=1)
    physical_scope_id: str = Field(min_length=1)
    horizon_start_s: float = Field(ge=0)
    horizon_end_s: Positive
    conditioning: str = Field(min_length=1)
    event_is_first_failure_in_period_reviewed: bool
    sampler_algorithm_id: Literal["pcn_subset.v1"] = "pcn_subset.v1"
    evaluator_id: str = Field(min_length=1)
    evaluator_revision: str = Field(min_length=1)
    evaluator_configuration_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    latent_variable_ids: tuple[str, ...]
    samples_per_level: int = Field(ge=100, le=200_000)
    conditional_probability: Fraction = Field(gt=0, lt=1)
    pcn_beta: Positive = Field(le=1)
    maximum_levels: int = Field(ge=1, le=20)
    latent_mapping_reviewed: bool
    event_semantics_reviewed: bool
    deterministic_evaluator_declared: bool
    random_seed: int = Field(ge=0)
    random_generator_id: Literal["numpy.PCG64"] = "numpy.PCG64"
    numpy_version: str = Field(min_length=1)
    status: Literal["computed", "needs_data"]
    probability_estimate: Fraction | None
    log_probability_estimate: float | None
    partial_probability_estimate: Fraction | None
    log_partial_probability_estimate: float | None
    level_count: int = Field(ge=0)
    total_limit_state_evaluations: int = Field(ge=0)
    levels: tuple[SubsetSimulationLevel, ...]
    uncertainty_status: Literal["not_estimated"] = "not_estimated"
    notes: tuple[str, ...]


def run_subset_simulation(
    limit_state: Callable[[np.ndarray], float], request: SubsetSimulationRequest
) -> SubsetSimulationResult:
    """Estimate ``P(g(X) <= 0)`` using pCN chains for independent standard-normal latent X.

    The caller maps the latent vector to its physical inputs inside ``limit_state``. MCMC draws
    within conditional levels are correlated; this implementation reports chain diagnostics but
    deliberately does not apply an iid confidence interval or claim physical qualification.
    """
    if not callable(limit_state):
        raise TypeError("limit_state must be a deterministic callable accepting one latent vector")
    if not (
        request.latent_mapping_reviewed
        and request.event_semantics_reviewed
        and request.deterministic_evaluator_declared
    ):
        return _result(
            request,
            status="needs_data",
            probability=None,
            log_probability=None,
            partial_probability=None,
            log_partial_probability=None,
            levels=(),
            evaluations=0,
            note="Reviewed latent mapping, event definition and deterministic evaluator declarations are required.",
        )

    rng = np.random.Generator(np.random.PCG64(request.random_seed))
    dimension = len(request.latent_variable_ids)
    sample_count = request.samples_per_level
    evaluations = 0

    def evaluate(values: np.ndarray) -> float:
        nonlocal evaluations
        point = np.asarray(values, dtype=np.float64).copy()
        if point.shape != (dimension,) or not np.isfinite(point).all():
            raise ValueError("latent sample has invalid shape or non-finite values")
        point.setflags(write=False)
        raw = limit_state(point)
        scalar = np.asarray(raw)
        if scalar.ndim != 0:
            raise ValueError("limit-state evaluator must return one scalar")
        if scalar.dtype.kind not in "iuf":
            raise ValueError("limit-state evaluator must return a real numeric scalar")
        result = float(scalar)
        if not math.isfinite(result):
            raise ValueError("limit-state evaluator returned a non-finite value")
        evaluations += 1
        return result

    population = rng.standard_normal((sample_count, dimension))
    performance = np.fromiter((evaluate(row) for row in population), dtype=float, count=sample_count)
    threshold_fraction = request.conditional_probability
    target_seed_count = max(2, math.ceil(threshold_fraction * sample_count))
    cumulative = 1.0
    log_cumulative = 0.0
    levels: list[SubsetSimulationLevel] = []
    prior_threshold: float | None = None
    proposal_count = 0
    accepted_count = 0
    generated_states = 0

    for level_index in range(request.maximum_levels):
        order = np.argsort(performance, kind="stable")
        threshold = float(performance[order[target_seed_count - 1]])
        seed_indices = np.flatnonzero(performance <= threshold)
        seed_count = int(seed_indices.size)
        conditional_fraction = seed_count / sample_count

        if threshold <= 0.0:
            event_fraction = float(np.count_nonzero(performance <= 0.0) / sample_count)
            cumulative *= event_fraction
            log_cumulative += math.log(event_fraction)
            levels.append(
                SubsetSimulationLevel(
                    level_index=level_index,
                    threshold_value=0.0,
                    conditional_probability_estimate=event_fraction,
                    conditioned_seed_count=seed_count,
                    samples_per_level=sample_count,
                    proposal_count=proposal_count,
                    proposal_acceptance_fraction=(
                        accepted_count / proposal_count if proposal_count else None
                    ),
                    distinct_adjacent_state_fraction=(
                        generated_states / proposal_count if proposal_count else None
                    ),
                    cumulative_probability_estimate=cumulative,
                    cumulative_log_probability_estimate=log_cumulative,
                )
            )
            return _result(
                request,
                status="computed",
                probability=cumulative,
                log_probability=log_cumulative,
                partial_probability=cumulative,
                log_partial_probability=log_cumulative,
                levels=tuple(levels),
                evaluations=evaluations,
                note="Conditional pCN samples are correlated; no independent-sample confidence interval is reported.",
            )

        if prior_threshold is not None and not threshold < prior_threshold:
            return _result(
                request,
                status="needs_data",
                probability=None,
                log_probability=None,
                partial_probability=cumulative,
                log_partial_probability=log_cumulative,
                levels=tuple(levels),
                evaluations=evaluations,
                note="The intermediate threshold did not decrease; increase the sample budget or review the event mapping.",
            )

        cumulative *= conditional_fraction
        log_cumulative += math.log(conditional_fraction)
        levels.append(
            SubsetSimulationLevel(
                level_index=level_index,
                threshold_value=threshold,
                conditional_probability_estimate=conditional_fraction,
                conditioned_seed_count=seed_count,
                samples_per_level=sample_count,
                proposal_count=proposal_count,
                proposal_acceptance_fraction=(accepted_count / proposal_count if proposal_count else None),
                distinct_adjacent_state_fraction=(
                    generated_states / proposal_count if proposal_count else None
                ),
                cumulative_probability_estimate=cumulative,
                cumulative_log_probability_estimate=log_cumulative,
            )
        )
        if level_index + 1 == request.maximum_levels:
            return _result(
                request,
                status="needs_data",
                probability=None,
                log_probability=None,
                partial_probability=cumulative,
                log_partial_probability=log_cumulative,
                levels=tuple(levels),
                evaluations=evaluations,
                note="Maximum intermediate levels reached before the limit-state event was sampled.",
            )

        prior_threshold = threshold
        proposal_count = 0
        accepted_count = 0
        generated_states = 0
        next_population = np.empty_like(population)
        next_performance = np.empty_like(performance)
        write_index = 0
        chain_length = math.ceil(sample_count / seed_count)
        innovation_scale = request.pcn_beta
        persistence = math.sqrt(max(0.0, 1.0 - innovation_scale * innovation_scale))
        for seed_index in seed_indices:
            state = population[seed_index].copy()
            state_performance = float(performance[seed_index])
            for _ in range(chain_length):
                proposal = persistence * state + innovation_scale * rng.standard_normal(dimension)
                proposal_performance = evaluate(proposal)
                proposal_count += 1
                if proposal_performance <= threshold:
                    state = proposal
                    state_performance = proposal_performance
                    accepted_count += 1
                    generated_states += 1
                next_population[write_index] = state
                next_performance[write_index] = state_performance
                write_index += 1
                if write_index == sample_count:
                    break
            if write_index == sample_count:
                break
        population, performance = next_population, next_performance

    raise RuntimeError("subset simulation exited without a terminal status")


def _result(
    request: SubsetSimulationRequest,
    *,
    status: Literal["computed", "needs_data"],
    probability: float | None,
    log_probability: float | None,
    partial_probability: float | None,
    log_partial_probability: float | None,
    levels: tuple[SubsetSimulationLevel, ...],
    evaluations: int,
    note: str,
) -> SubsetSimulationResult:
    return SubsetSimulationResult(
        estimate_id=request.estimate_id,
        event_id=request.event_id,
        event_definition=request.event_definition,
        failure_mode=request.failure_mode,
        asset_id=request.asset_id,
        location_id=request.location_id,
        physical_scope_id=request.physical_scope_id,
        horizon_start_s=request.horizon_start_s,
        horizon_end_s=request.horizon_end_s,
        conditioning=request.conditioning,
        event_is_first_failure_in_period_reviewed=request.event_is_first_failure_in_period_reviewed,
        sampler_algorithm_id="pcn_subset.v1",
        evaluator_id=request.evaluator_id,
        evaluator_revision=request.evaluator_revision,
        evaluator_configuration_sha256=request.evaluator_configuration_sha256,
        latent_variable_ids=request.latent_variable_ids,
        samples_per_level=request.samples_per_level,
        conditional_probability=request.conditional_probability,
        pcn_beta=request.pcn_beta,
        maximum_levels=request.maximum_levels,
        latent_mapping_reviewed=request.latent_mapping_reviewed,
        event_semantics_reviewed=request.event_semantics_reviewed,
        deterministic_evaluator_declared=request.deterministic_evaluator_declared,
        random_seed=request.random_seed,
        numpy_version=np.__version__,
        status=status,
        probability_estimate=probability,
        log_probability_estimate=log_probability,
        partial_probability_estimate=partial_probability,
        log_partial_probability_estimate=log_partial_probability,
        level_count=len(levels),
        total_limit_state_evaluations=evaluations,
        levels=levels,
        notes=(note,),
    )


def subset_simulation_event_probability(result: SubsetSimulationResult) -> EventProbability:
    """Convert a completed, explicitly reviewed first-failure estimate to the neutral exchange contract."""
    if result.status != "computed" or result.probability_estimate is None:
        raise ValueError("only a completed subset-simulation estimate can be exchanged")
    if not result.event_is_first_failure_in_period_reviewed:
        raise ValueError("the callback event must be reviewed as first failure within the declared interval")
    return EventProbability(
        event_id=result.event_id,
        asset_id=result.asset_id,
        physical_scope_id=result.physical_scope_id,
        failure_mode=result.failure_mode,
        horizon_start_s=result.horizon_start_s,
        horizon_end_s=result.horizon_end_s,
        probability_given_survival=result.probability_estimate,
        conditioning=result.conditioning,
        model_result_digest=canonical_digest(result.model_dump(mode="json")),
    )
