"""Probability semantics are kept distinct from event counts and severity."""

from __future__ import annotations

import math
from statistics import NormalDist
from typing import Any, Literal

from pydantic import Field, field_validator, model_validator

from ..contracts import (
    Calculation,
    Contract,
    Fraction,
    Nonnegative,
    Positive,
    RunContext,
    canonical_digest,
    check_finite,
)
from ..registry import ModelSpec


class WeibullInterval(Contract):
    shape: Positive
    scale_s: Positive
    current_age_s: Nonnegative
    horizon_s: Positive


def weibull_interval(x: WeibullInterval) -> Calculation:
    integrated_hazard = (
        (x.horizon_s / x.scale_s) ** x.shape
        if x.current_age_s == 0
        else (
            (x.current_age_s / x.scale_s) ** x.shape
            * math.expm1(x.shape * math.log1p(x.horizon_s / x.current_age_s))
        )
    )
    return Calculation(
        values=dict(
            probability_given_survival=-math.expm1(-integrated_hazard),
            integrated_hazard=integrated_hazard,
            equivalent_hazard_per_s=integrated_hazard / x.horizon_s,
        )
    )


class IndependentGate(Contract):
    probabilities: list[Fraction] = Field(min_length=1)
    gate: Literal["AND", "OR"]
    independence_declared: bool


def independent_gate(x: IndependentGate) -> Calculation:
    if not x.independence_declared:
        return Calculation(
            status="needs_data",
            values={},
            notes=("Joint event model required when independence is not declared.",),
        )
    p = (
        math.prod(x.probabilities)
        if x.gate == "AND"
        else -math.expm1(sum(math.log1p(-p) for p in x.probabilities))
        if max(x.probabilities) < 1
        else 1.0
    )
    return Calculation(values={"probability": p})


class GaussianMeanShiftImportanceSampling(Contract):
    """Externally evaluated mean-shift importance samples for one finite-period event."""

    schema_version: Literal["matintegrity.gaussian_mean_shift_importance_sampling.v1"] = (
        "matintegrity.gaussian_mean_shift_importance_sampling.v1"
    )
    estimate_id: str = Field(min_length=1)
    asset_id: str = Field(min_length=1)
    location_id: str = Field(min_length=1)
    physical_scope_id: str = Field(min_length=1)
    time_basis: str = Field(min_length=1)
    horizon_start_s: Nonnegative
    horizon_end_s: Positive
    conditioning: str = Field(min_length=1)
    event_id: str = Field(min_length=1)
    event_definition: str = Field(min_length=1)
    event_probability_meaning: Literal["conditional_first_failure_in_period"]
    latent_variable_ids: list[str] = Field(min_length=1, max_length=64)
    target_distribution: Literal["independent_standard_normal"] = "independent_standard_normal"
    proposal_distribution: Literal["independent_unit_normal_mean_shift"] = (
        "independent_unit_normal_mean_shift"
    )
    proposal_shift: list[float]
    sample_ids: list[str] = Field(min_length=2, max_length=2_000_000)
    proposal_samples: list[list[float]] = Field(min_length=2, max_length=2_000_000)
    event_indicators: list[bool] = Field(min_length=2, max_length=2_000_000)
    design_id: str = Field(min_length=1)
    design_content_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    proposal_generator_id: str = Field(min_length=1)
    proposal_generator_revision: str = Field(min_length=1)
    latent_mapping_id: str = Field(min_length=1)
    latent_mapping_revision: str = Field(min_length=1)
    latent_mapping_configuration_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    evaluator_id: str = Field(min_length=1)
    evaluator_revision: str = Field(min_length=1)
    evaluator_configuration_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    confidence_level: float = Field(default=0.95, gt=0.0, lt=1.0)
    samples_drawn_from_declared_proposal: bool
    sample_alignment_reviewed: bool
    latent_mapping_reviewed: bool
    event_indicator_reviewed: bool
    deterministic_evaluator_declared: bool

    @model_validator(mode="after")
    def aligned_samples(self):
        if self.horizon_end_s <= self.horizon_start_s:
            raise ValueError("importance-sampling horizon must have positive duration")
        dimension = len(self.latent_variable_ids)
        if len(set(self.latent_variable_ids)) != dimension:
            raise ValueError("importance-sampling latent-variable identifiers must be unique")
        if len(self.proposal_shift) != dimension:
            raise ValueError("proposal shift must align with latent-variable identifiers")
        count = len(self.sample_ids)
        if len(set(self.sample_ids)) != count:
            raise ValueError("importance-sampling sample identifiers must be unique")
        if len(self.proposal_samples) != count or len(self.event_indicators) != count:
            raise ValueError("sample identifiers, proposal samples and event indicators must align")
        if any(len(row) != dimension for row in self.proposal_samples):
            raise ValueError("each proposal sample must align with the latent-variable identifiers")
        check_finite(self.proposal_shift)
        check_finite(self.proposal_samples)
        return self


def _logsumexp(values: list[float]) -> float:
    if not values:
        return -math.inf
    maximum = max(values)
    return maximum + math.log(math.fsum(math.exp(value - maximum) for value in values))


def _representable_exp(log_value: float) -> float | None:
    if log_value == -math.inf:
        return 0.0
    try:
        value = math.exp(log_value)
    except OverflowError:
        return None
    return value if value > 0.0 and math.isfinite(value) else None


def gaussian_mean_shift_importance_sampling(
    x: GaussianMeanShiftImportanceSampling,
) -> Calculation:
    reviews = (
        x.samples_drawn_from_declared_proposal,
        x.sample_alignment_reviewed,
        x.latent_mapping_reviewed,
        x.event_indicator_reviewed,
        x.deterministic_evaluator_declared,
    )
    if not all(reviews):
        return Calculation(
            status="needs_data",
            values={},
            notes=(
                "The proposal draw, sample alignment, latent mapping, event indicator and deterministic evaluator declarations must all be reviewed.",
            ),
        )
    count = len(x.sample_ids)
    shift_norm_squared = math.fsum(value * value for value in x.proposal_shift)
    log_weights = [
        -math.fsum(shift * sample for shift, sample in zip(x.proposal_shift, row, strict=True))
        + 0.5 * shift_norm_squared
        for row in x.proposal_samples
    ]
    log_weight_sum = _logsumexp(log_weights)
    normalized_weights = [math.exp(value - log_weight_sum) for value in log_weights]
    effective_sample_size = 1.0 / math.fsum(value * value for value in normalized_weights)
    failure_log_weights = [
        value for value, indicator in zip(log_weights, x.event_indicators, strict=True) if indicator
    ]
    failure_count = len(failure_log_weights)
    log_probability_estimate = (
        _logsumexp(failure_log_weights) - math.log(count) if failure_log_weights else -math.inf
    )
    raw_estimate = _representable_exp(log_probability_estimate)
    probability = raw_estimate if raw_estimate is not None and raw_estimate <= 1.0 else None
    self_normalized_probability = (
        math.exp(_logsumexp(failure_log_weights) - log_weight_sum) if failure_log_weights else 0.0
    )
    weight_mean = _representable_exp(log_weight_sum - math.log(count))
    failure_effective_sample_size = (
        math.exp(
            2.0 * _logsumexp(failure_log_weights) - _logsumexp([2.0 * value for value in failure_log_weights])
        )
        if failure_log_weights
        else 0.0
    )

    standard_error = None
    log_standard_error = None
    raw_interval = None
    bounded_interval = None
    if failure_log_weights:
        scale = max(failure_log_weights)
        scaled_values = [math.exp(value - scale) for value in failure_log_weights]
        scaled_mean = math.fsum(scaled_values) / count
        scaled_sum_squared_deviations = (
            math.fsum((value - scaled_mean) ** 2 for value in scaled_values)
            + (count - failure_count) * scaled_mean**2
        )
        scaled_sample_variance = scaled_sum_squared_deviations / (count - 1)
        if scaled_sample_variance > 0.0:
            log_standard_error = scale + 0.5 * math.log(scaled_sample_variance) - 0.5 * math.log(count)
            standard_error = _representable_exp(log_standard_error)
        elif raw_estimate is not None:
            standard_error = 0.0
        if probability is not None and standard_error is not None:
            quantile = NormalDist().inv_cdf(0.5 + 0.5 * x.confidence_level)
            lower = probability - quantile * standard_error
            upper = probability + quantile * standard_error
            raw_interval = [lower, upper]
            bounded_interval = [max(0.0, lower), min(1.0, upper)]

    values = {
        "probability_given_survival": probability,
        "raw_importance_estimate": raw_estimate,
        "log_probability_estimate": (
            log_probability_estimate if math.isfinite(log_probability_estimate) else None
        ),
        "probability_standard_error": standard_error,
        "log_probability_standard_error": log_standard_error,
        "normal_confidence_level": x.confidence_level,
        "normal_confidence_interval_raw": raw_interval,
        "normal_confidence_interval_bounded": bounded_interval,
        "self_normalized_probability_diagnostic": self_normalized_probability,
        "sample_count": count,
        "observed_event_count": failure_count,
        "proposal_event_fraction": failure_count / count,
        "proposal_shift_norm": math.sqrt(shift_norm_squared),
        "importance_weight_mean": weight_mean,
        "log_importance_weight_mean": log_weight_sum - math.log(count),
        "effective_sample_size": effective_sample_size,
        "effective_sample_fraction": effective_sample_size / count,
        "maximum_normalized_weight": max(normalized_weights),
        "importance_weight_coefficient_of_variation": math.sqrt(
            max(0.0, count / effective_sample_size - 1.0)
        ),
        "event_weight_effective_sample_size": failure_effective_sample_size,
        "sample_ids": x.sample_ids,
    }
    notes = [
        "The unbiased estimator is the arithmetic mean of exact target-to-proposal likelihood ratios times the supplied event indicator; the self-normalized value is diagnostic only.",
        "Monte Carlo standard error, normal interval and effective sample size describe this finite proposal sample, not input-distribution, mapping, evaluator or model-form uncertainty.",
        "Independent standard-normal latent coordinates do not assert independence of mapped physical variables; that dependence belongs to the reviewed latent mapping.",
    ]
    if failure_count == 0:
        notes.append(
            "Zero observed proposal events produces a zero point estimate but no normal interval and does not establish zero event probability."
        )
    if raw_estimate is None:
        notes.append(
            "The probability estimate is outside positive finite binary64 representation; use the reported logarithmic estimate."
        )
    elif raw_estimate > 1.0:
        notes.append(
            "The finite-sample unbiased estimate exceeds one, so no probability-valued output is reported; redesign or enlarge the proposal sample."
        )
    return Calculation(values=values, notes=tuple(notes))


def _importance_sampling_context(x: GaussianMeanShiftImportanceSampling, context: RunContext) -> None:
    if x.asset_id != context.asset_id or x.location_id != context.location_id:
        raise ValueError("importance-sampling asset and location must match the evaluation context")
    if x.time_basis != context.time_basis:
        raise ValueError("importance-sampling time basis must match the evaluation context")


class JointEventState(Contract):
    event_occurs: list[bool]
    probability: Fraction
    top_event_occurs: bool


class JointEventDistribution(Contract):
    distribution_id: str = Field(min_length=1)
    asset_id: str = Field(min_length=1)
    location_id: str = Field(min_length=1)
    physical_scope_id: str = Field(min_length=1)
    time_basis: str = Field(min_length=1)
    horizon_start_s: Nonnegative
    horizon_end_s: Positive
    conditioning: str = Field(min_length=1)
    top_event_id: str = Field(min_length=1)
    top_event_definition: str = Field(min_length=1)
    event_ids: list[str] = Field(min_length=2, max_length=12)
    event_definitions: list[str]
    states: list[JointEventState] = Field(min_length=1)
    dependence_basis: Literal[
        "empirical_joint_distribution",
        "user_supplied_scenario_weights",
        "model_prediction",
    ]
    provider_id: str = Field(min_length=1)
    provider_version: str = Field(min_length=1)
    source_content_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    common_cause_group_ids: list[str] = Field(default_factory=list)
    state_space_complete_declared: bool
    distribution_reviewed: bool
    normalization_tolerance: Positive = Field(le=1e-6)

    @model_validator(mode="after")
    def complete_joint_state_space(self):
        if self.horizon_end_s <= self.horizon_start_s:
            raise ValueError("joint-event horizon must have positive duration")
        if len(set(self.event_ids)) != len(self.event_ids):
            raise ValueError("joint-event identifiers must be unique")
        if len(self.event_definitions) != len(self.event_ids):
            raise ValueError("joint-event identifiers and definitions must align")
        expected = 2 ** len(self.event_ids)
        if len(self.states) != expected:
            raise ValueError("joint distribution must enumerate every binary event state")
        state_vectors = [tuple(state.event_occurs) for state in self.states]
        if any(len(vector) != len(self.event_ids) for vector in state_vectors):
            raise ValueError("each joint state must align with the declared events")
        if len(set(state_vectors)) != expected:
            raise ValueError("joint distribution states must be unique and exhaustive")
        total = math.fsum(state.probability for state in self.states)
        if not math.isclose(total, 1.0, rel_tol=0.0, abs_tol=self.normalization_tolerance):
            raise ValueError("joint state probabilities must sum to one within the declared tolerance")
        return self


def joint_event_probability(x: JointEventDistribution) -> Calculation:
    if not x.state_space_complete_declared or not x.distribution_reviewed:
        return Calculation(
            status="needs_data",
            values={},
            notes=("A complete state-space declaration and reviewed joint distribution are required.",),
        )
    probabilities = [state.probability for state in x.states]
    marginal = [
        math.fsum(
            probability
            for state, probability in zip(x.states, probabilities, strict=True)
            if state.event_occurs[index]
        )
        for index in range(len(x.event_ids))
    ]
    pair_joint: list[list[float]] = []
    pair_covariance: list[list[float]] = []
    pair_phi: list[list[float | None]] = []
    for first, first_probability in enumerate(marginal):
        joint_row: list[float] = []
        covariance_row: list[float] = []
        phi_row: list[float | None] = []
        for second, second_probability in enumerate(marginal):
            joint = math.fsum(
                probability
                for state, probability in zip(x.states, probabilities, strict=True)
                if state.event_occurs[first] and state.event_occurs[second]
            )
            covariance = joint - first_probability * second_probability
            denominator = math.sqrt(
                first_probability
                * (1.0 - first_probability)
                * second_probability
                * (1.0 - second_probability)
            )
            joint_row.append(joint)
            covariance_row.append(covariance)
            phi_row.append(covariance / denominator if denominator > 0 else None)
        pair_joint.append(joint_row)
        pair_covariance.append(covariance_row)
        pair_phi.append(phi_row)
    top_probability = math.fsum(state.probability for state in x.states if state.top_event_occurs)
    independent_reference = math.fsum(
        math.prod(
            probability if occurs else 1.0 - probability
            for occurs, probability in zip(state.event_occurs, marginal, strict=True)
        )
        for state in x.states
        if state.top_event_occurs
    )
    return Calculation(
        values={
            "probability_given_survival": top_probability,
            "state_probability_sum": math.fsum(probabilities),
            "event_marginal_probabilities": marginal,
            "pairwise_joint_probabilities": pair_joint,
            "pairwise_covariances": pair_covariance,
            "pairwise_phi_coefficients": pair_phi,
            "independent_reference_probability": independent_reference,
            "dependence_probability_delta": top_probability - independent_reference,
            "zero_probability_state_count": sum(probability == 0 for probability in probabilities),
        },
        notes=(
            "The independent reference reuses the declared top-event truth table and fitted marginals; it is a comparison, not an alternative evidence model.",
            "Pairwise coefficients do not prove causality or fully describe higher-order dependence.",
        ),
    )


def _joint_event_context(x: JointEventDistribution, context: RunContext) -> None:
    if x.asset_id != context.asset_id or x.location_id != context.location_id:
        raise ValueError("joint-event asset and location must match the evaluation context")
    if x.time_basis != context.time_basis:
        raise ValueError("joint-event time basis must match the evaluation context")


class ContinuousTimeMarkovChain(Contract):
    chain_id: str = Field(min_length=1)
    asset_id: str = Field(min_length=1)
    location_id: str = Field(min_length=1)
    physical_scope_id: str = Field(min_length=1)
    time_basis: str = Field(min_length=1)
    horizon_start_s: Nonnegative
    horizon_end_s: Positive
    conditioning: str = Field(min_length=1)
    top_event_id: str = Field(min_length=1)
    top_event_definition: str = Field(min_length=1)
    state_ids: list[str] = Field(min_length=2, max_length=64)
    state_definitions: list[str]
    initial_state_probabilities: list[Fraction]
    generator_per_s: list[list[float]]
    top_event_state_ids: list[str] = Field(min_length=1)
    provider_id: str = Field(min_length=1)
    provider_version: str = Field(min_length=1)
    source_content_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    common_cause_group_ids: list[str] = Field(default_factory=list)
    generator_time_homogeneous_declared: bool
    state_semantics_reviewed: bool
    transition_rates_reviewed: bool
    normalization_tolerance: Positive = Field(le=1e-8)
    generator_row_sum_tolerance_per_s: Positive
    numerical_probability_tolerance: Positive = Field(le=1e-8)

    @model_validator(mode="after")
    def valid_generator(self):
        if self.horizon_end_s <= self.horizon_start_s:
            raise ValueError("Markov-chain horizon must have positive duration")
        count = len(self.state_ids)
        if len(set(self.state_ids)) != count:
            raise ValueError("Markov-chain state identifiers must be unique")
        if len(self.state_definitions) != count:
            raise ValueError("Markov-chain state identifiers and definitions must align")
        if len(self.initial_state_probabilities) != count:
            raise ValueError("initial probabilities must align with Markov-chain states")
        if len(self.generator_per_s) != count or any(len(row) != count for row in self.generator_per_s):
            raise ValueError("Markov-chain generator must be a square state-aligned matrix")
        if len(set(self.top_event_state_ids)) != len(self.top_event_state_ids):
            raise ValueError("top-event state identifiers must be unique")
        if not set(self.top_event_state_ids).issubset(self.state_ids):
            raise ValueError("top-event states must belong to the declared state space")
        if not math.isclose(
            math.fsum(self.initial_state_probabilities),
            1.0,
            rel_tol=0.0,
            abs_tol=self.normalization_tolerance,
        ):
            raise ValueError("initial state probabilities must sum to one")
        event_indices = [self.state_ids.index(state_id) for state_id in self.top_event_state_ids]
        if (
            math.fsum(self.initial_state_probabilities[index] for index in event_indices)
            > self.normalization_tolerance
        ):
            raise ValueError("conditional first-entry analysis requires zero initial top-event mass")
        for index, row in enumerate(self.generator_per_s):
            if row[index] > 0:
                raise ValueError("Markov-chain generator diagonal entries must be nonpositive")
            if any(value < 0 for column, value in enumerate(row) if column != index):
                raise ValueError("Markov-chain off-diagonal transition rates must be nonnegative")
            if not math.isclose(
                math.fsum(row),
                0.0,
                rel_tol=0.0,
                abs_tol=self.generator_row_sum_tolerance_per_s,
            ):
                raise ValueError("each Markov-chain generator row must sum to zero")
        return self


class MarkovGeneratorSegment(Contract):
    segment_id: str = Field(min_length=1)
    start_s: Nonnegative
    end_s: Positive
    generator_per_s: list[list[float]]
    transition_basis_id: str = Field(min_length=1)
    provider_revision: str = Field(min_length=1)
    source_content_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    rates_reviewed: bool

    @model_validator(mode="after")
    def positive_duration(self):
        if self.end_s <= self.start_s:
            raise ValueError("Markov-generator segment must have positive duration")
        return self


class PiecewiseContinuousTimeMarkovChain(Contract):
    chain_id: str = Field(min_length=1)
    asset_id: str = Field(min_length=1)
    location_id: str = Field(min_length=1)
    physical_scope_id: str = Field(min_length=1)
    time_basis: str = Field(min_length=1)
    horizon_start_s: Nonnegative
    horizon_end_s: Positive
    conditioning: str = Field(min_length=1)
    top_event_id: str = Field(min_length=1)
    top_event_definition: str = Field(min_length=1)
    state_ids: list[str] = Field(min_length=2, max_length=64)
    state_definitions: list[str]
    initial_state_probabilities: list[Fraction]
    segments: list[MarkovGeneratorSegment] = Field(min_length=1)
    top_event_state_ids: list[str] = Field(min_length=1)
    provider_id: str = Field(min_length=1)
    provider_version: str = Field(min_length=1)
    source_content_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    common_cause_group_ids: list[str] = Field(default_factory=list)
    state_semantics_reviewed: bool
    segment_sequence_reviewed: bool
    normalization_tolerance: Positive = Field(le=1e-8)
    generator_row_sum_tolerance_per_s: Positive
    boundary_time_tolerance_s: Positive
    numerical_probability_tolerance: Positive = Field(le=1e-8)

    @model_validator(mode="after")
    def valid_piecewise_generator(self):
        if self.horizon_end_s <= self.horizon_start_s:
            raise ValueError("piecewise Markov-chain horizon must have positive duration")
        count = len(self.state_ids)
        if len(set(self.state_ids)) != count:
            raise ValueError("piecewise Markov-chain state identifiers must be unique")
        if len(self.state_definitions) != count:
            raise ValueError("piecewise Markov-chain state identifiers and definitions must align")
        if len(self.initial_state_probabilities) != count:
            raise ValueError("initial probabilities must align with piecewise Markov-chain states")
        if len(set(self.top_event_state_ids)) != len(self.top_event_state_ids):
            raise ValueError("top-event state identifiers must be unique")
        if not set(self.top_event_state_ids).issubset(self.state_ids):
            raise ValueError("top-event states must belong to the declared state space")
        if not math.isclose(
            math.fsum(self.initial_state_probabilities),
            1.0,
            rel_tol=0.0,
            abs_tol=self.normalization_tolerance,
        ):
            raise ValueError("initial state probabilities must sum to one")
        event_indices = [self.state_ids.index(state_id) for state_id in self.top_event_state_ids]
        if (
            math.fsum(self.initial_state_probabilities[index] for index in event_indices)
            > self.normalization_tolerance
        ):
            raise ValueError("conditional first-entry analysis requires zero initial top-event mass")
        if len({segment.segment_id for segment in self.segments}) != len(self.segments):
            raise ValueError("piecewise Markov-chain segment identifiers must be unique")
        if not math.isclose(
            self.segments[0].start_s,
            self.horizon_start_s,
            rel_tol=0.0,
            abs_tol=self.boundary_time_tolerance_s,
        ):
            raise ValueError("first Markov segment must start at the declared horizon")
        for previous, current in zip(self.segments, self.segments[1:], strict=False):
            if not math.isclose(
                previous.end_s,
                current.start_s,
                rel_tol=0.0,
                abs_tol=self.boundary_time_tolerance_s,
            ):
                raise ValueError("Markov segments must be supplied in contiguous chronological order")
        if not math.isclose(
            self.segments[-1].end_s,
            self.horizon_end_s,
            rel_tol=0.0,
            abs_tol=self.boundary_time_tolerance_s,
        ):
            raise ValueError("last Markov segment must end at the declared horizon")
        for segment in self.segments:
            generator = segment.generator_per_s
            if len(generator) != count or any(len(row) != count for row in generator):
                raise ValueError("each Markov segment generator must be a square state-aligned matrix")
            for index, row in enumerate(generator):
                if row[index] > 0:
                    raise ValueError("Markov-chain generator diagonal entries must be nonpositive")
                if any(value < 0 for column, value in enumerate(row) if column != index):
                    raise ValueError("Markov-chain off-diagonal transition rates must be nonnegative")
                if not math.isclose(
                    math.fsum(row),
                    0.0,
                    rel_tol=0.0,
                    abs_tol=self.generator_row_sum_tolerance_per_s,
                ):
                    raise ValueError("each Markov-chain generator row must sum to zero")
        return self


def _clean_probability(value: float, tolerance: float) -> tuple[float, float]:
    if value < -tolerance or value > 1.0 + tolerance:
        raise ValueError("matrix exponential produced a probability outside numerical tolerance")
    cleaned = 0.0 if value < 0.0 else 1.0 if value > 1.0 else value
    return cleaned, abs(cleaned - value)


def _ctmc_segment_step(initial, first_hit_state, generator, duration_s, event_indices):
    import numpy as np
    from scipy.linalg import expm

    count = len(initial)
    raw_final = initial @ expm(generator * duration_s)
    augmented = np.zeros((2 * count, 2 * count), dtype=float)
    augmented[:count, :count] = generator
    augmented[:count, count:] = np.eye(count)
    occupation_integral = expm(augmented * duration_s)[:count, count:]
    expected_occupancy_s = initial @ occupation_integral
    first_hit_generator = generator.copy()
    first_hit_generator[event_indices, :] = 0.0
    raw_first_hit_state = first_hit_state @ expm(first_hit_generator * duration_s)
    expected_transition_counts = np.zeros_like(generator)
    for origin in range(count):
        for destination in range(count):
            if origin != destination:
                expected_transition_counts[origin, destination] = (
                    expected_occupancy_s[origin] * generator[origin, destination]
                )
    return (
        raw_final,
        raw_first_hit_state,
        expected_occupancy_s,
        expected_transition_counts,
    )


def continuous_time_markov_chain(x: ContinuousTimeMarkovChain) -> Calculation:
    if not (
        x.generator_time_homogeneous_declared and x.state_semantics_reviewed and x.transition_rates_reviewed
    ):
        return Calculation(
            status="needs_data",
            values={},
            notes=(
                "Reviewed state semantics, transition rates and a time-homogeneous generator declaration are required.",
            ),
        )
    import numpy as np

    generator = np.asarray(x.generator_per_s, dtype=float)
    initial = np.asarray(x.initial_state_probabilities, dtype=float)
    duration_s = x.horizon_end_s - x.horizon_start_s
    event_indices = [x.state_ids.index(state_id) for state_id in x.top_event_state_ids]
    raw_final, raw_first_hit_state, expected_occupancy_s, expected_transition_counts = _ctmc_segment_step(
        initial, initial, generator, duration_s, event_indices
    )
    raw_first_hit_probability = float(np.sum(raw_first_hit_state[event_indices]))
    try:
        final_cleaned = [
            _clean_probability(float(value), x.numerical_probability_tolerance) for value in raw_final
        ]
        first_hit, first_hit_correction = _clean_probability(
            raw_first_hit_probability, x.numerical_probability_tolerance
        )
    except ValueError as error:
        return Calculation(
            status="needs_data",
            values={
                "raw_state_probability_sum": float(np.sum(raw_final)),
                "raw_minimum_state_probability": float(np.min(raw_final)),
                "raw_maximum_state_probability": float(np.max(raw_final)),
                "raw_first_hit_probability": raw_first_hit_probability,
            },
            notes=(str(error),),
        )
    final_probabilities = [value for value, _ in final_cleaned]
    corrections = [correction for _, correction in final_cleaned]
    event_occupancy_probability = math.fsum(final_probabilities[index] for index in event_indices)
    return Calculation(
        values={
            "probability_given_survival": first_hit,
            "state_probabilities_at_horizon": final_probabilities,
            "state_probability_sum": math.fsum(final_probabilities),
            "top_event_state_occupancy_probability": event_occupancy_probability,
            "expected_state_occupancy_s": expected_occupancy_s.tolist(),
            "expected_top_event_state_occupancy_s": float(np.sum(expected_occupancy_s[event_indices])),
            "expected_transition_counts": expected_transition_counts.tolist(),
            "total_expected_transition_count": float(np.sum(expected_transition_counts)),
            "maximum_probability_roundoff_correction": max(corrections + [first_hit_correction]),
        },
        notes=(
            "The first-entry probability uses an absorbing copy of the declared top-event states; horizon occupancy uses the original generator and can decrease after repair.",
            "Expected transition counts are model expectations, not observed recurrent-event frequencies.",
        ),
    )


def piecewise_continuous_time_markov_chain(x: PiecewiseContinuousTimeMarkovChain) -> Calculation:
    if not (
        x.state_semantics_reviewed
        and x.segment_sequence_reviewed
        and all(segment.rates_reviewed for segment in x.segments)
    ):
        return Calculation(
            status="needs_data",
            values={},
            notes=("Reviewed state semantics, segment sequence and every segment rate set are required.",),
        )
    import numpy as np

    state = np.asarray(x.initial_state_probabilities, dtype=float)
    first_hit_state = state.copy()
    count = len(x.state_ids)
    event_indices = [x.state_ids.index(state_id) for state_id in x.top_event_state_ids]
    boundary_times_s = [x.horizon_start_s]
    state_probabilities_at_boundaries = [state.tolist()]
    first_hit_probability_at_boundaries = [0.0]
    top_event_state_occupancy_probability_at_boundaries = [0.0]
    per_segment_expected_state_occupancy_s = []
    per_segment_expected_transition_counts = []
    cumulative_occupancy_s = np.zeros(count, dtype=float)
    cumulative_transition_counts = np.zeros((count, count), dtype=float)
    maximum_correction = 0.0
    for segment in x.segments:
        generator = np.asarray(segment.generator_per_s, dtype=float)
        duration_s = segment.end_s - segment.start_s
        state, first_hit_state, segment_occupancy, segment_transitions = _ctmc_segment_step(
            state,
            first_hit_state,
            generator,
            duration_s,
            event_indices,
        )
        raw_first_hit = float(np.sum(first_hit_state[event_indices]))
        try:
            cleaned_state = [
                _clean_probability(float(value), x.numerical_probability_tolerance) for value in state
            ]
            cleaned_first_hit, first_hit_correction = _clean_probability(
                raw_first_hit, x.numerical_probability_tolerance
            )
        except ValueError as error:
            return Calculation(
                status="needs_data",
                values={
                    "failed_segment_id": segment.segment_id,
                    "raw_state_probability_sum": float(np.sum(state)),
                    "raw_minimum_state_probability": float(np.min(state)),
                    "raw_maximum_state_probability": float(np.max(state)),
                    "raw_first_hit_probability": raw_first_hit,
                },
                notes=(str(error),),
            )
        cleaned_values = [value for value, _ in cleaned_state]
        maximum_correction = max(
            maximum_correction,
            first_hit_correction,
            *(correction for _, correction in cleaned_state),
        )
        cumulative_occupancy_s += segment_occupancy
        cumulative_transition_counts += segment_transitions
        boundary_times_s.append(segment.end_s)
        state_probabilities_at_boundaries.append(cleaned_values)
        first_hit_probability_at_boundaries.append(cleaned_first_hit)
        top_event_state_occupancy_probability_at_boundaries.append(
            math.fsum(cleaned_values[index] for index in event_indices)
        )
        per_segment_expected_state_occupancy_s.append(segment_occupancy.tolist())
        per_segment_expected_transition_counts.append(segment_transitions.tolist())
    final_probabilities = state_probabilities_at_boundaries[-1]
    return Calculation(
        values={
            "segment_ids": [segment.segment_id for segment in x.segments],
            "boundary_times_s": boundary_times_s,
            "state_probabilities_at_boundaries": state_probabilities_at_boundaries,
            "first_hit_probability_at_boundaries": first_hit_probability_at_boundaries,
            "top_event_state_occupancy_probability_at_boundaries": (
                top_event_state_occupancy_probability_at_boundaries
            ),
            "probability_given_survival": first_hit_probability_at_boundaries[-1],
            "state_probabilities_at_horizon": final_probabilities,
            "state_probability_sum": math.fsum(final_probabilities),
            "top_event_state_occupancy_probability": (
                top_event_state_occupancy_probability_at_boundaries[-1]
            ),
            "per_segment_expected_state_occupancy_s": per_segment_expected_state_occupancy_s,
            "expected_state_occupancy_s": cumulative_occupancy_s.tolist(),
            "expected_top_event_state_occupancy_s": float(np.sum(cumulative_occupancy_s[event_indices])),
            "per_segment_expected_transition_counts": per_segment_expected_transition_counts,
            "expected_transition_counts": cumulative_transition_counts.tolist(),
            "total_expected_transition_count": float(np.sum(cumulative_transition_counts)),
            "maximum_probability_roundoff_correction": maximum_correction,
        },
        notes=(
            "Segments are propagated exactly in caller-supplied chronological order; gaps, overlaps and implicit sorting are forbidden.",
            "First entry uses a sequential absorbing copy while occupancy and expected transitions retain each original segment generator.",
            "Piecewise-constant rates do not establish semi-Markov, aging or continuously time-varying behavior.",
        ),
    )


def _continuous_time_markov_context(x: ContinuousTimeMarkovChain, context: RunContext) -> None:
    if x.asset_id != context.asset_id or x.location_id != context.location_id:
        raise ValueError("Markov-chain asset and location must match the evaluation context")
    if x.time_basis != context.time_basis:
        raise ValueError("Markov-chain time basis must match the evaluation context")


def _piecewise_markov_context(x: PiecewiseContinuousTimeMarkovChain, context: RunContext) -> None:
    if x.asset_id != context.asset_id or x.location_id != context.location_id:
        raise ValueError("piecewise Markov-chain asset and location must match the evaluation context")
    if x.time_basis != context.time_basis:
        raise ValueError("piecewise Markov-chain time basis must match the evaluation context")


class ThicknessObservation(Contract):
    observation_id: str = Field(min_length=1)
    campaign_id: str = Field(min_length=1)
    physical_location_id: str = Field(min_length=1)
    elapsed_time_s: Nonnegative
    remaining_thickness_m: Positive
    measurement_standard_deviation_m: Positive
    partition: Literal["update", "holdout"]
    source_group_id: str = Field(min_length=1)
    measurement_method_id: str = Field(min_length=1)
    calibration_id: str = Field(min_length=1)
    source_content_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    test_validity_reviewed: bool


class BayesianLinearThicknessUpdate(Contract):
    update_id: str = Field(min_length=1)
    asset_id: str = Field(min_length=1)
    location_id: str = Field(min_length=1)
    physical_scope_id: str = Field(min_length=1)
    physical_location_id: str = Field(min_length=1)
    time_basis: str = Field(min_length=1)
    reference_time_s: Nonnegative
    prior_remaining_thickness_mean_m: Positive
    prior_loss_rate_mean_m_s: float
    prior_remaining_thickness_standard_deviation_m: Positive
    prior_loss_rate_standard_deviation_m_s: Positive
    prior_thickness_loss_rate_correlation: float = Field(gt=-1.0, lt=1.0)
    prior_basis_id: str = Field(min_length=1)
    prior_source_content_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    linear_model_basis_id: str = Field(min_length=1)
    measurement_error_model_id: str = Field(min_length=1)
    prediction_support_id: str = Field(min_length=1)
    observations: list[ThicknessObservation] = Field(min_length=1)
    measurement_error_covariance_m2: list[list[float]] | None = None
    measurement_errors_independent_declared: bool
    prediction_times_s: list[Nonnegative] = Field(min_length=1, max_length=1000)
    credible_level: float = Field(gt=0.0, lt=1.0)
    required_thickness_m: Nonnegative | None = None
    prior_basis_reviewed: bool
    constant_linear_model_reviewed: bool
    observation_identities_reviewed: bool
    measurement_error_model_reviewed: bool
    prediction_support_reviewed: bool
    required_thickness_basis_reviewed: bool = False
    holdout_source_independence_reviewed: bool = False
    covariance_symmetry_tolerance_m2: Positive

    @model_validator(mode="after")
    def valid_update(self):
        observation_ids = [row.observation_id for row in self.observations]
        if len(set(observation_ids)) != len(observation_ids):
            raise ValueError("thickness observation identifiers must be unique")
        if any(row.physical_location_id != self.physical_location_id for row in self.observations):
            raise ValueError("every thickness observation must match the declared physical location")
        update_rows = [row for row in self.observations if row.partition == "update"]
        if not update_rows:
            raise ValueError("at least one update-partition thickness observation is required")
        if len(set(self.prediction_times_s)) != len(self.prediction_times_s):
            raise ValueError("prediction times must be unique")
        covariance = self.measurement_error_covariance_m2
        if covariance is None:
            if not self.measurement_errors_independent_declared:
                raise ValueError(
                    "independent measurement errors must be declared when no covariance is supplied"
                )
        else:
            if self.measurement_errors_independent_declared:
                raise ValueError(
                    "supply either an independent-error declaration or a full covariance, not both"
                )
            count = len(update_rows)
            if len(covariance) != count or any(len(row) != count for row in covariance):
                raise ValueError("measurement covariance must align with update rows in supplied order")
            for i in range(count):
                expected = update_rows[i].measurement_standard_deviation_m ** 2
                if not math.isclose(
                    covariance[i][i], expected, rel_tol=1e-8, abs_tol=self.covariance_symmetry_tolerance_m2
                ):
                    raise ValueError(
                        "measurement covariance diagonal must match declared standard deviations"
                    )
                for j in range(count):
                    if not math.isclose(
                        covariance[i][j],
                        covariance[j][i],
                        rel_tol=0.0,
                        abs_tol=self.covariance_symmetry_tolerance_m2,
                    ):
                        raise ValueError("measurement covariance must be symmetric")
        return self


def bayesian_linear_thickness_update(x: BayesianLinearThicknessUpdate) -> Calculation:
    review_gates = (
        x.prior_basis_reviewed,
        x.constant_linear_model_reviewed,
        x.observation_identities_reviewed,
        x.measurement_error_model_reviewed,
        x.prediction_support_reviewed,
    )
    if not all(review_gates) or (
        x.required_thickness_m is not None and not x.required_thickness_basis_reviewed
    ):
        return Calculation(
            status="needs_data",
            values={},
            notes=(
                "Reviewed prior, linear model, observation identities, measurement errors and prediction support are required; a supplied thickness threshold also needs a reviewed basis.",
            ),
        )
    if any(not row.test_validity_reviewed for row in x.observations):
        return Calculation(
            status="needs_data",
            values={},
            notes=("Every update and holdout observation needs a reviewed test-validity declaration.",),
        )

    import numpy as np

    update_rows = [row for row in x.observations if row.partition == "update"]
    holdout_rows = [row for row in x.observations if row.partition == "holdout"]
    prior_mean = np.asarray([x.prior_remaining_thickness_mean_m, x.prior_loss_rate_mean_m_s], dtype=float)
    prior_covariance = np.asarray(
        [
            [
                x.prior_remaining_thickness_standard_deviation_m**2,
                x.prior_thickness_loss_rate_correlation
                * x.prior_remaining_thickness_standard_deviation_m
                * x.prior_loss_rate_standard_deviation_m_s,
            ],
            [
                x.prior_thickness_loss_rate_correlation
                * x.prior_remaining_thickness_standard_deviation_m
                * x.prior_loss_rate_standard_deviation_m_s,
                x.prior_loss_rate_standard_deviation_m_s**2,
            ],
        ],
        dtype=float,
    )
    design = np.asarray(
        [[1.0, -(row.elapsed_time_s - x.reference_time_s)] for row in update_rows],
        dtype=float,
    )
    observations = np.asarray([row.remaining_thickness_m for row in update_rows], dtype=float)
    if x.measurement_error_covariance_m2 is None:
        measurement_covariance = np.diag([row.measurement_standard_deviation_m**2 for row in update_rows])
        error_basis = "declared_independent_diagonal"
    else:
        measurement_covariance = np.asarray(x.measurement_error_covariance_m2, dtype=float)
        error_basis = "caller_supplied_full_covariance"
    try:
        np.linalg.cholesky(prior_covariance)
        np.linalg.cholesky(measurement_covariance)
        innovation_covariance = design @ prior_covariance @ design.T + measurement_covariance
        np.linalg.cholesky(innovation_covariance)
        gain = np.linalg.solve(innovation_covariance, design @ prior_covariance).T
    except np.linalg.LinAlgError:
        return Calculation(
            status="needs_data",
            values={},
            notes=("Prior and measurement covariance matrices must be positive definite.",),
        )
    posterior_mean = prior_mean + gain @ (observations - design @ prior_mean)
    posterior_covariance = prior_covariance - gain @ design @ prior_covariance
    posterior_covariance = 0.5 * (posterior_covariance + posterior_covariance.T)
    try:
        np.linalg.cholesky(posterior_covariance)
    except np.linalg.LinAlgError:
        return Calculation(
            status="needs_data",
            values={},
            notes=("Posterior covariance was not positive definite at machine precision.",),
        )
    posterior_standard_deviations = np.sqrt(np.diag(posterior_covariance))
    posterior_correlation = posterior_covariance[0, 1] / math.prod(posterior_standard_deviations)
    normal = NormalDist()
    credible_z = normal.inv_cdf(0.5 * (1.0 + x.credible_level))

    predicted_mean: list[float] = []
    predicted_standard_deviation: list[float] = []
    predicted_lower: list[float] = []
    predicted_upper: list[float] = []
    threshold_probabilities: list[float] = []
    for prediction_time_s in x.prediction_times_s:
        prediction_design = np.asarray([1.0, -(prediction_time_s - x.reference_time_s)], dtype=float)
        mean = float(prediction_design @ posterior_mean)
        standard_deviation = math.sqrt(float(prediction_design @ posterior_covariance @ prediction_design))
        predicted_mean.append(mean)
        predicted_standard_deviation.append(standard_deviation)
        predicted_lower.append(mean - credible_z * standard_deviation)
        predicted_upper.append(mean + credible_z * standard_deviation)
        if x.required_thickness_m is not None:
            threshold_probabilities.append(normal.cdf((x.required_thickness_m - mean) / standard_deviation))

    holdout_residuals: list[float] = []
    holdout_standardized_residuals: list[float] = []
    for row in holdout_rows:
        holdout_design = np.asarray([1.0, -(row.elapsed_time_s - x.reference_time_s)], dtype=float)
        holdout_mean = float(holdout_design @ posterior_mean)
        predictive_variance = float(
            holdout_design @ posterior_covariance @ holdout_design + row.measurement_standard_deviation_m**2
        )
        residual = row.remaining_thickness_m - holdout_mean
        holdout_residuals.append(residual)
        holdout_standardized_residuals.append(residual / math.sqrt(predictive_variance))

    update_source_groups = {row.source_group_id for row in update_rows}
    holdout_source_groups = {row.source_group_id for row in holdout_rows}
    overlapping_source_groups = sorted(update_source_groups & holdout_source_groups)
    if not holdout_rows:
        holdout_independence = "not_applicable"
    elif overlapping_source_groups:
        holdout_independence = "not_independent_source_group_overlap"
    elif x.holdout_source_independence_reviewed:
        holdout_independence = "reviewed_independent_source_groups"
    else:
        holdout_independence = "unreviewed_source_group_independence"
    return Calculation(
        values={
            "update_observation_ids": [row.observation_id for row in update_rows],
            "holdout_observation_ids": [row.observation_id for row in holdout_rows],
            "measurement_error_basis": error_basis,
            "posterior_remaining_thickness_at_reference_mean_m": float(posterior_mean[0]),
            "posterior_loss_rate_mean_m_s": float(posterior_mean[1]),
            "posterior_covariance": posterior_covariance.tolist(),
            "posterior_remaining_thickness_standard_deviation_m": float(posterior_standard_deviations[0]),
            "posterior_loss_rate_standard_deviation_m_s": float(posterior_standard_deviations[1]),
            "posterior_thickness_loss_rate_correlation": float(posterior_correlation),
            "probability_loss_rate_positive": normal.cdf(
                float(posterior_mean[1] / posterior_standard_deviations[1])
            ),
            "prediction_times_s": x.prediction_times_s,
            "predicted_remaining_thickness_mean_m": predicted_mean,
            "predicted_remaining_thickness_standard_deviation_m": predicted_standard_deviation,
            "credible_level": x.credible_level,
            "predicted_remaining_thickness_credible_lower_m": predicted_lower,
            "predicted_remaining_thickness_credible_upper_m": predicted_upper,
            "required_thickness_m": x.required_thickness_m,
            "probability_below_required_thickness": threshold_probabilities,
            "holdout_residuals_m": holdout_residuals,
            "holdout_standardized_residuals": holdout_standardized_residuals,
            "holdout_source_independence_status": holdout_independence,
            "overlapping_holdout_source_group_ids": overlapping_source_groups,
        },
        notes=(
            "Only update-partition observations influence the posterior; holdout values are diagnostic outputs.",
            "Threshold probabilities are point-in-time model-implied thickness-state probabilities, not period first-failure probabilities.",
            "The conditional constant-linear Gaussian model excludes process noise, model-form uncertainty, POD, missed flaws and future intervention.",
        ),
    )


def _bayesian_thickness_context(x: BayesianLinearThicknessUpdate, context: RunContext) -> None:
    if x.asset_id != context.asset_id or x.location_id != context.location_id:
        raise ValueError("Bayesian thickness-update asset and location must match the evaluation context")
    if x.time_basis != context.time_basis:
        raise ValueError("Bayesian thickness-update time basis must match the evaluation context")


class LinearThicknessStateSpaceUpdate(Contract):
    """Sequential thickness/loss-rate filtering with reviewed additive process noise."""

    schema_version: Literal["matintegrity.linear_thickness_state_space_update.v1"] = (
        "matintegrity.linear_thickness_state_space_update.v1"
    )
    update_id: str = Field(min_length=1)
    asset_id: str = Field(min_length=1)
    location_id: str = Field(min_length=1)
    physical_scope_id: str = Field(min_length=1)
    physical_location_id: str = Field(min_length=1)
    time_basis: str = Field(min_length=1)
    initial_state_time_s: Nonnegative
    initial_remaining_thickness_mean_m: Positive
    initial_loss_rate_mean_m_s: float
    initial_remaining_thickness_standard_deviation_m: Positive
    initial_loss_rate_standard_deviation_m_s: Positive
    initial_thickness_loss_rate_correlation: float = Field(gt=-1.0, lt=1.0)
    prior_basis_id: str = Field(min_length=1)
    prior_source_content_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    transition_model_basis_id: str = Field(min_length=1)
    process_noise_model_id: str = Field(min_length=1)
    process_noise_covariance_rate: list[list[float]]
    measurement_error_model_id: str = Field(min_length=1)
    observations: list[ThicknessObservation] = Field(min_length=1)
    measurement_errors_independent_declared: bool
    analysis_end_time_s: Nonnegative
    prediction_times_s: list[Nonnegative] = Field(min_length=1, max_length=1000)
    credible_level: float = Field(gt=0.0, lt=1.0)
    required_thickness_m: Nonnegative | None = None
    prior_basis_reviewed: bool
    transition_model_reviewed: bool
    process_noise_model_reviewed: bool
    observation_identities_reviewed: bool
    measurement_error_model_reviewed: bool
    prediction_support_reviewed: bool
    required_thickness_basis_reviewed: bool = False
    holdout_source_independence_reviewed: bool = False

    @model_validator(mode="after")
    def valid_state_space_update(self):
        observation_ids = [row.observation_id for row in self.observations]
        if len(set(observation_ids)) != len(observation_ids):
            raise ValueError("thickness observation identifiers must be unique")
        if any(row.physical_location_id != self.physical_location_id for row in self.observations):
            raise ValueError("every thickness observation must match the declared physical location")
        if not any(row.partition == "update" for row in self.observations):
            raise ValueError("at least one update-partition thickness observation is required")
        times = [row.elapsed_time_s for row in self.observations]
        if times[0] < self.initial_state_time_s:
            raise ValueError("the first observation cannot precede the initial state time")
        if any(right <= left for left, right in zip(times, times[1:], strict=False)):
            raise ValueError("state-space observations must be supplied in strictly increasing time order")
        if self.analysis_end_time_s < times[-1]:
            raise ValueError("analysis end time cannot precede the final observation")
        if any(time < self.analysis_end_time_s for time in self.prediction_times_s):
            raise ValueError("prediction times cannot precede the analysis end time")
        if any(
            right <= left
            for left, right in zip(self.prediction_times_s, self.prediction_times_s[1:], strict=False)
        ):
            raise ValueError("prediction times must strictly increase")
        if not self.measurement_errors_independent_declared:
            raise ValueError(
                "this sequential state-space contract requires an explicit independent measurement-error declaration"
            )
        covariance_rate = self.process_noise_covariance_rate
        if len(covariance_rate) != 2 or any(len(row) != 2 for row in covariance_rate):
            raise ValueError("process-noise covariance rate must be a two-by-two matrix")
        check_finite(covariance_rate)
        if covariance_rate[0][0] < 0.0 or covariance_rate[1][1] < 0.0:
            raise ValueError("process-noise covariance-rate diagonal cannot be negative")
        if covariance_rate[0][1] != covariance_rate[1][0]:
            raise ValueError("process-noise covariance rate must be exactly symmetric")
        maximum_covariance = math.sqrt(covariance_rate[0][0] * covariance_rate[1][1])
        if abs(covariance_rate[0][1]) > maximum_covariance * (1.0 + 1e-12):
            raise ValueError("process-noise covariance rate must be positive semidefinite")
        return self


def linear_thickness_state_space_update(x: LinearThicknessStateSpaceUpdate) -> Calculation:
    gates = (
        x.prior_basis_reviewed,
        x.transition_model_reviewed,
        x.process_noise_model_reviewed,
        x.observation_identities_reviewed,
        x.measurement_error_model_reviewed,
        x.prediction_support_reviewed,
    )
    if not all(gates) or (x.required_thickness_m is not None and not x.required_thickness_basis_reviewed):
        return Calculation(
            status="needs_data",
            values={},
            notes=(
                "Reviewed prior, transition, process-noise, observation, measurement-error and prediction-support bases are required; a threshold also needs a reviewed basis.",
            ),
        )
    if any(not row.test_validity_reviewed for row in x.observations):
        return Calculation(
            status="needs_data",
            values={},
            notes=("Every update and holdout observation needs reviewed test validity.",),
        )

    import numpy as np

    state_mean = np.asarray([x.initial_remaining_thickness_mean_m, x.initial_loss_rate_mean_m_s], dtype=float)
    state_covariance = np.asarray(
        [
            [
                x.initial_remaining_thickness_standard_deviation_m**2,
                x.initial_thickness_loss_rate_correlation
                * x.initial_remaining_thickness_standard_deviation_m
                * x.initial_loss_rate_standard_deviation_m_s,
            ],
            [
                x.initial_thickness_loss_rate_correlation
                * x.initial_remaining_thickness_standard_deviation_m
                * x.initial_loss_rate_standard_deviation_m_s,
                x.initial_loss_rate_standard_deviation_m_s**2,
            ],
        ],
        dtype=float,
    )
    process_rate = np.asarray(x.process_noise_covariance_rate, dtype=float)
    try:
        np.linalg.cholesky(state_covariance)
    except np.linalg.LinAlgError:
        return Calculation(
            status="needs_data",
            values={},
            notes=("Initial state covariance must be positive definite.",),
        )

    def propagate(mean, covariance, elapsed_s):
        transition = np.asarray([[1.0, -elapsed_s], [0.0, 1.0]], dtype=float)
        propagated_mean = transition @ mean
        propagated_covariance = transition @ covariance @ transition.T + process_rate * elapsed_s
        propagated_covariance = 0.5 * (propagated_covariance + propagated_covariance.T)
        return propagated_mean, propagated_covariance

    current_time = x.initial_state_time_s
    observation_diagnostics = []
    update_ids = []
    holdout_ids = []
    identity = np.eye(2)
    measurement_row = np.asarray([1.0, 0.0])
    for row in x.observations:
        state_mean, state_covariance = propagate(
            state_mean, state_covariance, row.elapsed_time_s - current_time
        )
        current_time = row.elapsed_time_s
        predicted_measurement = float(state_mean[0])
        innovation_variance = float(state_covariance[0, 0] + row.measurement_standard_deviation_m**2)
        if innovation_variance <= 0.0 or not math.isfinite(innovation_variance):
            return Calculation(
                status="needs_data",
                values={},
                notes=("Sequential predictive measurement variance must remain positive and finite.",),
            )
        residual = row.remaining_thickness_m - predicted_measurement
        standardized_residual = residual / math.sqrt(innovation_variance)
        pre_update_mean = state_mean.copy()
        pre_update_covariance = state_covariance.copy()
        if row.partition == "update":
            gain = state_covariance[:, 0] / innovation_variance
            state_mean = state_mean + gain * residual
            joseph_left = identity - np.outer(gain, measurement_row)
            state_covariance = (
                joseph_left @ state_covariance @ joseph_left.T
                + np.outer(gain, gain) * row.measurement_standard_deviation_m**2
            )
            state_covariance = 0.5 * (state_covariance + state_covariance.T)
            update_ids.append(row.observation_id)
        else:
            holdout_ids.append(row.observation_id)
        observation_diagnostics.append(
            {
                "observation_id": row.observation_id,
                "partition": row.partition,
                "elapsed_time_s": row.elapsed_time_s,
                "predicted_measurement_mean_m": predicted_measurement,
                "predicted_measurement_standard_deviation_m": math.sqrt(innovation_variance),
                "residual_m": residual,
                "standardized_residual": standardized_residual,
                "pre_update_state_mean": pre_update_mean.tolist(),
                "pre_update_state_covariance": pre_update_covariance.tolist(),
                "post_row_state_mean": state_mean.tolist(),
                "post_row_state_covariance": state_covariance.tolist(),
                "state_updated": row.partition == "update",
            }
        )

    state_mean, state_covariance = propagate(
        state_mean, state_covariance, x.analysis_end_time_s - current_time
    )
    state_time_s = x.analysis_end_time_s
    try:
        np.linalg.cholesky(state_covariance)
    except np.linalg.LinAlgError:
        return Calculation(
            status="needs_data",
            values={},
            notes=("Filtered state covariance was not positive definite at the analysis end time.",),
        )
    state_standard_deviations = np.sqrt(np.diag(state_covariance))
    state_correlation = state_covariance[0, 1] / math.prod(state_standard_deviations)
    normal = NormalDist()
    credible_z = normal.inv_cdf(0.5 * (1.0 + x.credible_level))
    predicted_mean = []
    predicted_standard_deviation = []
    predicted_lower = []
    predicted_upper = []
    threshold_probabilities = []
    for prediction_time in x.prediction_times_s:
        prediction_mean, prediction_covariance = propagate(
            state_mean, state_covariance, prediction_time - state_time_s
        )
        thickness_mean = float(prediction_mean[0])
        thickness_standard_deviation = math.sqrt(float(prediction_covariance[0, 0]))
        predicted_mean.append(thickness_mean)
        predicted_standard_deviation.append(thickness_standard_deviation)
        predicted_lower.append(thickness_mean - credible_z * thickness_standard_deviation)
        predicted_upper.append(thickness_mean + credible_z * thickness_standard_deviation)
        if x.required_thickness_m is not None:
            threshold_probabilities.append(
                normal.cdf((x.required_thickness_m - thickness_mean) / thickness_standard_deviation)
            )

    update_source_groups = {row.source_group_id for row in x.observations if row.partition == "update"}
    holdout_source_groups = {row.source_group_id for row in x.observations if row.partition == "holdout"}
    overlapping_source_groups = sorted(update_source_groups & holdout_source_groups)
    if not holdout_ids:
        holdout_independence = "not_applicable"
    elif overlapping_source_groups:
        holdout_independence = "not_independent_source_group_overlap"
    elif x.holdout_source_independence_reviewed:
        holdout_independence = "reviewed_independent_source_groups"
    else:
        holdout_independence = "unreviewed_source_group_independence"
    return Calculation(
        values={
            "update_observation_ids": update_ids,
            "holdout_observation_ids": holdout_ids,
            "observation_diagnostics": observation_diagnostics,
            "state_time_s": state_time_s,
            "posterior_remaining_thickness_at_state_time_mean_m": float(state_mean[0]),
            "posterior_loss_rate_mean_m_s": float(state_mean[1]),
            "posterior_covariance": state_covariance.tolist(),
            "posterior_remaining_thickness_standard_deviation_m": float(state_standard_deviations[0]),
            "posterior_loss_rate_standard_deviation_m_s": float(state_standard_deviations[1]),
            "posterior_thickness_loss_rate_correlation": float(state_correlation),
            "probability_loss_rate_positive": normal.cdf(float(state_mean[1] / state_standard_deviations[1])),
            "prediction_times_s": x.prediction_times_s,
            "predicted_remaining_thickness_mean_m": predicted_mean,
            "predicted_remaining_thickness_standard_deviation_m": predicted_standard_deviation,
            "credible_level": x.credible_level,
            "predicted_remaining_thickness_credible_lower_m": predicted_lower,
            "predicted_remaining_thickness_credible_upper_m": predicted_upper,
            "required_thickness_m": x.required_thickness_m,
            "probability_below_required_thickness": threshold_probabilities,
            "process_noise_covariance_rate": x.process_noise_covariance_rate,
            "measurement_error_basis": "declared_independent_sequential_measurements",
            "holdout_source_independence_status": holdout_independence,
            "overlapping_holdout_source_group_ids": overlapping_source_groups,
        },
        notes=(
            "Update rows sequentially condition the state; holdout rows report one-step-ahead residuals and never alter the state.",
            "Additive process covariance grows linearly with elapsed time in the declared [thickness, signed loss-rate] state coordinates.",
            "Threshold probabilities are point-in-time state probabilities, not first-passage probabilities; no smoother, parameter fitting, nonlinear growth, intervention or inspection-effect model is included.",
        ),
    )


def _linear_thickness_state_space_context(x: LinearThicknessStateSpaceUpdate, context: RunContext) -> None:
    if x.asset_id != context.asset_id or x.location_id != context.location_id:
        raise ValueError("state-space thickness-update asset and location must match the evaluation context")
    if x.time_basis != context.time_basis:
        raise ValueError("state-space thickness-update time basis must match the evaluation context")


class GaussianThicknessPosteriorSampleDesign(Contract):
    """Reproducible joint draws from a reviewed linear Gaussian thickness posterior."""

    schema_version: Literal["matintegrity.gaussian_thickness_posterior_sample_design.v1"] = (
        "matintegrity.gaussian_thickness_posterior_sample_design.v1"
    )
    sample_design_id: str = Field(min_length=1)
    asset_id: str = Field(min_length=1)
    location_id: str = Field(min_length=1)
    physical_scope_id: str = Field(min_length=1)
    physical_location_id: str = Field(min_length=1)
    time_basis: str = Field(min_length=1)
    posterior_definition_id: str = Field(min_length=1)
    posterior_source_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    posterior_reference_time_s: Nonnegative
    assessment_time_s: Nonnegative
    posterior_remaining_thickness_at_reference_mean_m: float
    posterior_loss_rate_mean_m_s: float
    posterior_covariance: list[list[float]]
    required_thickness_m: Nonnegative
    requested_accepted_sample_count: int = Field(ge=2, le=100_000)
    maximum_candidate_draw_multiplier: int = Field(ge=1, le=1000)
    random_seed_uint64: int = Field(ge=0, le=2**64 - 1)
    covariance_symmetry_tolerance: Positive = Field(default=1e-24)
    posterior_basis_reviewed: bool
    covariance_reviewed: bool
    assessment_conditioning_reviewed: bool
    required_thickness_basis_reviewed: bool
    deterministic_sampler_reviewed: bool

    @model_validator(mode="after")
    def valid_sample_design(self):
        if self.assessment_time_s < self.posterior_reference_time_s:
            raise ValueError("assessment time cannot precede the posterior reference time")
        covariance = self.posterior_covariance
        if len(covariance) != 2 or any(len(row) != 2 for row in covariance):
            raise ValueError("posterior covariance must be a two-by-two matrix")
        check_finite(
            [
                self.posterior_remaining_thickness_at_reference_mean_m,
                self.posterior_loss_rate_mean_m_s,
                covariance,
            ]
        )
        if covariance[0][0] <= 0.0 or covariance[1][1] <= 0.0:
            raise ValueError("posterior covariance diagonal must be positive")
        if not math.isclose(
            covariance[0][1],
            covariance[1][0],
            rel_tol=0.0,
            abs_tol=self.covariance_symmetry_tolerance,
        ):
            raise ValueError("posterior covariance must be symmetric")
        if self.requested_accepted_sample_count * self.maximum_candidate_draw_multiplier > 2_000_000:
            raise ValueError("candidate draw budget cannot exceed two million")
        return self


_UINT64_MASK = 2**64 - 1
_UNIFORM_53_DENOMINATOR = float(2**53)


def _splitmix64(state: int) -> tuple[int, int]:
    state = (state + 0x9E3779B97F4A7C15) & _UINT64_MASK
    value = state
    value = ((value ^ (value >> 30)) * 0xBF58476D1CE4E5B9) & _UINT64_MASK
    value = ((value ^ (value >> 27)) * 0x94D049BB133111EB) & _UINT64_MASK
    return state, (value ^ (value >> 31)) & _UINT64_MASK


def _open_unit_uniform_from_uint64(value: int) -> float:
    return ((value >> 11) + 0.5) / _UNIFORM_53_DENOMINATOR


def gaussian_thickness_posterior_sample_design(
    x: GaussianThicknessPosteriorSampleDesign,
) -> Calculation:
    gates = {
        "posterior_basis_reviewed": x.posterior_basis_reviewed,
        "covariance_reviewed": x.covariance_reviewed,
        "assessment_conditioning_reviewed": x.assessment_conditioning_reviewed,
        "required_thickness_basis_reviewed": x.required_thickness_basis_reviewed,
        "deterministic_sampler_reviewed": x.deterministic_sampler_reviewed,
    }
    missing_gates = [name for name, reviewed in gates.items() if not reviewed]
    common = {
        "sample_design_id": x.sample_design_id,
        "posterior_definition_id": x.posterior_definition_id,
        "posterior_source_sha256": x.posterior_source_sha256,
        "assessment_time_s": x.assessment_time_s,
        "required_thickness_m": x.required_thickness_m,
        "sampler_algorithm_id": "splitmix64_box_muller_cholesky_rejection_v1",
        "random_seed_uint64": x.random_seed_uint64,
        "sample_design_input_sha256": canonical_digest(x.model_dump(mode="json")),
        "conditioning_definition": (
            "remaining thickness is strictly above required thickness at assessment time and loss rate is nonnegative"
        ),
    }
    if missing_gates:
        return Calculation(
            status="needs_data",
            values={
                **common,
                "sample_design_state": "review_required",
                "missing_review_gates": missing_gates,
            },
            notes=(
                "All posterior, covariance, conditioning, threshold and deterministic-sampler reviews are required.",
            ),
        )

    covariance = x.posterior_covariance
    first_cholesky = math.sqrt(covariance[0][0])
    off_diagonal_cholesky = covariance[1][0] / first_cholesky
    final_variance = covariance[1][1] - off_diagonal_cholesky**2
    if final_variance <= 0.0:
        return Calculation(
            status="needs_data",
            values={**common, "sample_design_state": "invalid_covariance"},
            notes=("Posterior covariance must be positive definite above the declared numerical precision.",),
        )
    second_cholesky = math.sqrt(final_variance)
    elapsed = x.assessment_time_s - x.posterior_reference_time_s
    maximum_draws = x.requested_accepted_sample_count * x.maximum_candidate_draw_multiplier
    state = x.random_seed_uint64
    accepted: list[dict[str, float | str]] = []
    negative_rate_count = 0
    non_surviving_count = 0
    both_condition_failures_count = 0
    candidate_draw_count = 0
    for candidate_index in range(maximum_draws):
        state, first_bits = _splitmix64(state)
        state, second_bits = _splitmix64(state)
        first_uniform = _open_unit_uniform_from_uint64(first_bits)
        second_uniform = _open_unit_uniform_from_uint64(second_bits)
        radius = math.sqrt(-2.0 * math.log(first_uniform))
        angle = 2.0 * math.pi * second_uniform
        first_standard_normal = radius * math.cos(angle)
        second_standard_normal = radius * math.sin(angle)
        reference_thickness = (
            x.posterior_remaining_thickness_at_reference_mean_m + first_cholesky * first_standard_normal
        )
        loss_rate = (
            x.posterior_loss_rate_mean_m_s
            + off_diagonal_cholesky * first_standard_normal
            + second_cholesky * second_standard_normal
        )
        assessment_thickness = reference_thickness - loss_rate * elapsed
        negative_rate = loss_rate < 0.0
        non_surviving = assessment_thickness <= x.required_thickness_m
        candidate_draw_count = candidate_index + 1
        if negative_rate or non_surviving:
            negative_rate_count += int(negative_rate)
            non_surviving_count += int(non_surviving)
            both_condition_failures_count += int(negative_rate and non_surviving)
            continue
        accepted.append(
            {
                "sample_id": f"{x.sample_design_id}-s{len(accepted):06d}",
                "remaining_thickness_at_assessment_m": assessment_thickness,
                "nonnegative_loss_rate_m_s": loss_rate,
                "normalized_weight": 1.0 / x.requested_accepted_sample_count,
            }
        )
        if len(accepted) == x.requested_accepted_sample_count:
            break

    diagnostics = {
        **common,
        "requested_accepted_sample_count": x.requested_accepted_sample_count,
        "accepted_sample_count": len(accepted),
        "candidate_draw_count": candidate_draw_count,
        "maximum_candidate_draw_count": maximum_draws,
        "negative_loss_rate_candidate_count": negative_rate_count,
        "non_surviving_candidate_count": non_surviving_count,
        "both_condition_failures_count": both_condition_failures_count,
        "empirical_acceptance_fraction": len(accepted) / candidate_draw_count,
        "rejection_conditioning_applied": True,
        "samples_conditioned_on_survival_to_assessment": True,
        "constant_nonnegative_loss_model_reviewed": False,
    }
    if len(accepted) < x.requested_accepted_sample_count:
        return Calculation(
            status="needs_data",
            values={**diagnostics, "sample_design_state": "insufficient_accepted_draws"},
            notes=(
                "The fixed candidate-draw budget did not produce the requested conditional sample count; no partial sample set is returned.",
            ),
        )
    joint_sample_source_sha256 = canonical_digest(
        {
            "sample_design_input_sha256": common["sample_design_input_sha256"],
            "sampler_algorithm_id": common["sampler_algorithm_id"],
            "samples": accepted,
        }
    )
    return Calculation(
        values={
            **diagnostics,
            "sample_design_state": "computed",
            "distribution_definition_id": (
                f"{x.posterior_definition_id}:conditioned-nonnegative-rate-and-assessment-survival"
            ),
            "joint_sample_source_sha256": joint_sample_source_sha256,
            "samples": accepted,
            "rejected_unconditional_candidate_count": candidate_draw_count - len(accepted),
            "partial_sample_set_returned": False,
        },
        notes=(
            "The deterministic SplitMix64, open-unit conversion, Box-Muller transform and two-dimensional Cholesky mapping are versioned explicitly rather than delegated to a library RNG distribution method.",
            "Rejection produces the declared Gaussian posterior conditional on nonnegative loss rate and assessment-time survival under the constant linear path; it does not repair model-form, process-noise or field-calibration limitations.",
            "The returned equal-weight rows are directly usable in sampled linear-thickness first-passage after the caller separately reviews the constant nonnegative-loss model and forecast horizons.",
        ),
    )


def _gaussian_thickness_sample_context(
    x: GaussianThicknessPosteriorSampleDesign, context: RunContext
) -> None:
    if x.asset_id != context.asset_id or x.location_id != context.location_id:
        raise ValueError(
            "Gaussian thickness sample-design asset and location must match the evaluation context"
        )
    if x.time_basis != context.time_basis:
        raise ValueError("Gaussian thickness sample-design time basis must match the evaluation context")


class LinearThicknessFirstPassageSample(Contract):
    """One joint thickness/rate row from a caller-qualified conditional distribution."""

    sample_id: str = Field(min_length=1)
    remaining_thickness_at_assessment_m: Positive
    nonnegative_loss_rate_m_s: Nonnegative
    normalized_weight: Positive


class SampledLinearThicknessFirstPassage(Contract):
    """Push a joint discrete distribution through a monotone linear crossing time."""

    schema_version: Literal["matintegrity.sampled_linear_thickness_first_passage.v1"] = (
        "matintegrity.sampled_linear_thickness_first_passage.v1"
    )
    forecast_id: str = Field(min_length=1)
    asset_id: str = Field(min_length=1)
    location_id: str = Field(min_length=1)
    physical_scope_id: str = Field(min_length=1)
    physical_location_id: str = Field(min_length=1)
    time_basis: str = Field(min_length=1)
    assessment_time_s: Nonnegative
    conditioning: str = Field(min_length=1)
    event_id: str = Field(min_length=1)
    event_definition: str = Field(min_length=1)
    required_thickness_m: Nonnegative
    distribution_definition_id: str = Field(min_length=1)
    sample_design_id: str = Field(min_length=1)
    joint_sample_source_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    source_lineage: dict[str, Any] = Field(default_factory=dict)
    review_reference_ids: dict[str, str] = Field(default_factory=dict)
    samples: list[LinearThicknessFirstPassageSample] = Field(min_length=2)
    candidate_horizon_end_s: list[Positive] = Field(min_length=2, max_length=100_000)
    maximum_weight_sum_error: Positive = 1e-12
    samples_conditioned_on_survival_to_assessment: bool
    constant_nonnegative_loss_model_reviewed: bool
    joint_sample_distribution_reviewed: bool
    required_thickness_basis_reviewed: bool
    candidate_horizons_reviewed: bool

    @field_validator("source_lineage")
    @classmethod
    def finite_source_lineage(cls, value: dict[str, Any]) -> dict[str, Any]:
        return check_finite(value)

    @model_validator(mode="after")
    def aligned_distribution(self):
        ids = [row.sample_id for row in self.samples]
        if len(set(ids)) != len(ids):
            raise ValueError("first-passage sample IDs must be unique")
        if any(
            not key.strip() or not reference.strip() for key, reference in self.review_reference_ids.items()
        ):
            raise ValueError("review reference IDs must be non-blank")
        weight_sum = math.fsum(row.normalized_weight for row in self.samples)
        if abs(weight_sum - 1.0) > self.maximum_weight_sum_error:
            raise ValueError("first-passage sample weights must sum to one")
        if any(time <= self.assessment_time_s for time in self.candidate_horizon_end_s):
            raise ValueError("candidate horizons must end after the assessment time")
        if any(
            right <= left
            for left, right in zip(
                self.candidate_horizon_end_s,
                self.candidate_horizon_end_s[1:],
                strict=False,
            )
        ):
            raise ValueError("candidate horizons must strictly increase")
        return self


def sampled_linear_thickness_first_passage(
    x: SampledLinearThicknessFirstPassage,
) -> Calculation:
    gates = {
        "samples_conditioned_on_survival_to_assessment": (x.samples_conditioned_on_survival_to_assessment),
        "constant_nonnegative_loss_model_reviewed": x.constant_nonnegative_loss_model_reviewed,
        "joint_sample_distribution_reviewed": x.joint_sample_distribution_reviewed,
        "required_thickness_basis_reviewed": x.required_thickness_basis_reviewed,
        "candidate_horizons_reviewed": x.candidate_horizons_reviewed,
    }
    missing_gates = [name for name, reviewed in gates.items() if not reviewed]
    common = {
        "forecast_id": x.forecast_id,
        "asset_id": x.asset_id,
        "location_id": x.location_id,
        "physical_scope_id": x.physical_scope_id,
        "physical_location_id": x.physical_location_id,
        "time_basis": x.time_basis,
        "assessment_time_s": x.assessment_time_s,
        "conditioning": x.conditioning,
        "event_id": x.event_id,
        "event_definition": x.event_definition,
        "required_thickness_m": x.required_thickness_m,
        "distribution_definition_id": x.distribution_definition_id,
        "sample_design_id": x.sample_design_id,
        "joint_sample_source_sha256": x.joint_sample_source_sha256,
        "source_lineage": x.source_lineage,
        "review_reference_ids": x.review_reference_ids,
        "event_probability_meaning": "conditional_first_failure_in_period",
        "probability_basis": "model_implied_joint_sample_push_forward",
        "forecast_input_sha256": canonical_digest(x.model_dump(mode="json")),
        "missing_review_gates": missing_gates,
    }
    if missing_gates:
        return Calculation(
            status="needs_data",
            values={**common, "forecast_state": "review_required"},
            notes=(
                "Survival conditioning, the constant nonnegative-loss model, joint distribution, threshold and candidate horizons all require review.",
            ),
        )
    conditioning_conflicts = [
        row.sample_id
        for row in x.samples
        if row.remaining_thickness_at_assessment_m <= x.required_thickness_m
    ]
    if conditioning_conflicts:
        return Calculation(
            status="needs_data",
            values={
                **common,
                "forecast_state": "conditioning_conflict_at_assessment",
                "conditioning_conflict_sample_ids": conditioning_conflicts,
            },
            notes=(
                "At least one supplied sample has already crossed the threshold at assessment; do not discard or silently recondition those rows.",
            ),
        )
    weight_sum = math.fsum(row.normalized_weight for row in x.samples)
    sample_rows = []
    for row in x.samples:
        effective_weight = row.normalized_weight / weight_sum
        crossing_time = (
            None
            if row.nonnegative_loss_rate_m_s == 0.0
            else x.assessment_time_s
            + (row.remaining_thickness_at_assessment_m - x.required_thickness_m)
            / row.nonnegative_loss_rate_m_s
        )
        sample_rows.append(
            {
                "sample_id": row.sample_id,
                "remaining_thickness_at_assessment_m": row.remaining_thickness_at_assessment_m,
                "nonnegative_loss_rate_m_s": row.nonnegative_loss_rate_m_s,
                "supplied_normalized_weight": row.normalized_weight,
                "effective_normalized_weight": effective_weight,
                "first_crossing_time_s": crossing_time,
            }
        )
    forecast_points = []
    for index, horizon in enumerate(x.candidate_horizon_end_s):
        probability = math.fsum(
            row["effective_normalized_weight"]
            for row in sample_rows
            if row["first_crossing_time_s"] is not None and row["first_crossing_time_s"] <= horizon
        )
        forecast_points.append(
            {
                "forecast_point_id": f"{x.forecast_id}-h{index:06d}",
                "horizon_end_s": horizon,
                "cumulative_probability_given_survival": probability,
                "cumulative_probability_upper_bound": None,
            }
        )
    never_crossing_probability = math.fsum(
        row["effective_normalized_weight"] for row in sample_rows if row["first_crossing_time_s"] is None
    )
    final_probability = forecast_points[-1]["cumulative_probability_given_survival"]
    crossing_after_final_probability = math.fsum(
        row["effective_normalized_weight"]
        for row in sample_rows
        if row["first_crossing_time_s"] is not None
        and row["first_crossing_time_s"] > x.candidate_horizon_end_s[-1]
    )
    return Calculation(
        values={
            **common,
            "forecast_state": "computed",
            "supplied_weight_sum": weight_sum,
            "weight_normalization_factor": 1.0 / weight_sum,
            "sample_count": len(sample_rows),
            "sample_results": sample_rows,
            "forecast_points": forecast_points,
            "final_horizon_probability_given_survival": final_probability,
            "never_crossing_probability_under_constant_rate": never_crossing_probability,
            "positive_rate_crossing_after_final_horizon_probability": crossing_after_final_probability,
            "confidence_bound_computed": False,
            "failed_samples_discarded": False,
        },
        notes=(
            "Each positive-rate sample crosses exactly once under its reviewed constant monotone loss path; zero-rate samples never cross after assessment.",
            "The cumulative probabilities are a discrete joint-input-distribution push-forward, not a confidence bound, field calibration or model-form validation.",
            "The returned forecast points are directly composable with estimate-basis threshold inspection scheduling after the caller reviews the shared event, scope and conditioning.",
        ),
    )


def _sampled_first_passage_context(x: SampledLinearThicknessFirstPassage, context: RunContext) -> None:
    if x.asset_id != context.asset_id or x.location_id != context.location_id:
        raise ValueError("first-passage forecast asset and location must match the evaluation context")
    if x.time_basis != context.time_basis:
        raise ValueError("first-passage forecast time basis must match the evaluation context")


class ExclusivePaths(Contract):
    initiating_frequency_per_s: Nonnegative
    conditional_probabilities: list[Fraction] = Field(min_length=1)

    @model_validator(mode="after")
    def close(self):
        if not math.isclose(sum(self.conditional_probabilities), 1.0, rel_tol=0, abs_tol=1e-10):
            raise ValueError("mutually exclusive complete path probabilities must sum to one")
        return self


def exclusive_paths(x: ExclusivePaths) -> Calculation:
    return Calculation(
        values={
            "path_frequencies_per_s": [x.initiating_frequency_per_s * p for p in x.conditional_probabilities]
        }
    )


class GammaPoisson(Contract):
    prior_shape: Positive
    prior_exposure_s: Positive
    confirmed_events: int = Field(ge=0)
    exposure_s: Positive
    complete_ascertainment: bool


def gamma_poisson(x: GammaPoisson) -> Calculation:
    if not x.complete_ascertainment:
        return Calculation(
            status="needs_data",
            values={},
            notes=("Detection/ascertainment model required for incomplete event capture.",),
        )
    shape = x.prior_shape + x.confirmed_events
    exposure = x.prior_exposure_s + x.exposure_s
    return Calculation(
        values=dict(
            posterior_shape=shape,
            posterior_exposure_s=exposure,
            mean_frequency_per_s=shape / exposure,
            variance_frequency_per_s2=shape / exposure**2,
        )
    )


def specifications():
    return [
        ModelSpec(
            "reliability.weibull_interval",
            WeibullInterval,
            weibull_interval,
            {"probability_given_survival": "1", "integrated_hazard": "1", "equivalent_hazard_per_s": "1/s"},
            (
                "Conditional on survival to current age and a fixed Weibull lifetime model; repair/replacement excluded.",
            ),
            ("weibull_survival",),
            probability_semantics={"probability_given_survival": "conditional_first_failure_in_period"},
        ),
        ModelSpec(
            "reliability.independent_gate",
            IndependentGate,
            independent_gate,
            {"probability": "1"},
            (
                "Input events share a horizon and conditioning; statistical independence must be explicitly declared.",
            ),
            ("probability_axioms",),
            probability_semantics={"probability": "unscoped_event_probability"},
        ),
        ModelSpec(
            "reliability.gaussian_mean_shift_importance_sampling",
            GaussianMeanShiftImportanceSampling,
            gaussian_mean_shift_importance_sampling,
            {
                "probability_given_survival": "1",
                "raw_importance_estimate": "1",
                "log_probability_estimate": "1",
                "probability_standard_error": "1",
                "log_probability_standard_error": "1",
                "normal_confidence_level": "1",
                "normal_confidence_interval_raw": "1",
                "normal_confidence_interval_bounded": "1",
                "self_normalized_probability_diagnostic": "1",
                "sample_count": "count",
                "observed_event_count": "count",
                "proposal_event_fraction": "1",
                "proposal_shift_norm": "1",
                "importance_weight_mean": "1",
                "log_importance_weight_mean": "1",
                "effective_sample_size": "count",
                "effective_sample_fraction": "1",
                "maximum_normalized_weight": "1",
                "importance_weight_coefficient_of_variation": "1",
                "event_weight_effective_sample_size": "count",
                "sample_ids": "1",
            },
            (
                "Caller-reviewed samples are drawn from an independent unit-normal mean-shift proposal in a named latent space and evaluated by one deterministic finite-period event indicator.",
                "The exact Gaussian target-to-proposal likelihood ratio is used without clipping; latent mapping, event semantics, horizon, conditioning and evaluator identity remain external reviewed inputs.",
                "Estimator diagnostics quantify Monte Carlo behavior only and do not cover input-distribution, mapping, model-form, physical-data or consequence uncertainty.",
            ),
            ("gaussian_mean_shift_importance_sampling_derivation",),
            context_validator=_importance_sampling_context,
            probability_semantics={"probability_given_survival": "conditional_first_failure_in_period"},
        ),
        ModelSpec(
            "reliability.joint_event_probability",
            JointEventDistribution,
            joint_event_probability,
            {
                "probability_given_survival": "1",
                "state_probability_sum": "1",
                "event_marginal_probabilities": "1",
                "pairwise_joint_probabilities": "1",
                "pairwise_covariances": "1",
                "pairwise_phi_coefficients": "1",
                "independent_reference_probability": "1",
                "dependence_probability_delta": "1",
                "zero_probability_state_count": "count",
            },
            (
                "Caller-reviewed exhaustive joint distribution over binary events sharing one physical scope, horizon and conditioning basis.",
                "The top-event truth value is supplied for every state; no independence or causal common-cause structure is inferred.",
            ),
            ("finite_joint_probability_space",),
            context_validator=_joint_event_context,
            probability_semantics={"probability_given_survival": "conditional_first_failure_in_period"},
        ),
        ModelSpec(
            "reliability.continuous_time_markov_chain",
            ContinuousTimeMarkovChain,
            continuous_time_markov_chain,
            {
                "probability_given_survival": "1",
                "state_probabilities_at_horizon": "1",
                "state_probability_sum": "1",
                "top_event_state_occupancy_probability": "1",
                "expected_state_occupancy_s": "s",
                "expected_top_event_state_occupancy_s": "s",
                "expected_transition_counts": "count",
                "total_expected_transition_count": "count",
                "maximum_probability_roundoff_correction": "1",
            },
            (
                "Caller-reviewed finite-state time-homogeneous continuous-time Markov generator over one physical scope and interval.",
                "State occupancy, first entry into declared top-event states and expected transition counts are distinct outputs; rates and state meanings are not inferred.",
            ),
            ("finite_state_ctmc",),
            context_validator=_continuous_time_markov_context,
            probability_semantics={
                "probability_given_survival": "conditional_first_failure_in_period",
                "top_event_state_occupancy_probability": "unscoped_event_probability",
            },
        ),
        ModelSpec(
            "reliability.piecewise_continuous_time_markov_chain",
            PiecewiseContinuousTimeMarkovChain,
            piecewise_continuous_time_markov_chain,
            {
                "segment_ids": "1",
                "boundary_times_s": "s",
                "state_probabilities_at_boundaries": "1",
                "first_hit_probability_at_boundaries": "1",
                "top_event_state_occupancy_probability_at_boundaries": "1",
                "probability_given_survival": "1",
                "state_probabilities_at_horizon": "1",
                "state_probability_sum": "1",
                "top_event_state_occupancy_probability": "1",
                "per_segment_expected_state_occupancy_s": "s",
                "expected_state_occupancy_s": "s",
                "expected_top_event_state_occupancy_s": "s",
                "per_segment_expected_transition_counts": "count",
                "expected_transition_counts": "count",
                "total_expected_transition_count": "count",
                "maximum_probability_roundoff_correction": "1",
            },
            (
                "Caller-reviewed finite-state piecewise-constant continuous-time Markov generators over contiguous chronological segments.",
                "Segment order, boundaries, rate basis and source digests are preserved; gaps, overlaps and implicit sorting are forbidden.",
                "State occupancy, first entry and expected transitions are distinct outputs; piecewise-constant rates do not qualify aging or semi-Markov behavior.",
            ),
            ("piecewise_finite_state_ctmc",),
            context_validator=_piecewise_markov_context,
            probability_semantics={
                "probability_given_survival": "conditional_first_failure_in_period",
                "top_event_state_occupancy_probability": "unscoped_event_probability",
            },
        ),
        ModelSpec(
            "reliability.bayesian_linear_thickness_update",
            BayesianLinearThicknessUpdate,
            bayesian_linear_thickness_update,
            {
                "update_observation_ids": "1",
                "holdout_observation_ids": "1",
                "measurement_error_basis": "1",
                "posterior_remaining_thickness_at_reference_mean_m": "m",
                "posterior_loss_rate_mean_m_s": "m/s",
                "posterior_covariance": "mixed SI covariance [m,m/s]",
                "posterior_remaining_thickness_standard_deviation_m": "m",
                "posterior_loss_rate_standard_deviation_m_s": "m/s",
                "posterior_thickness_loss_rate_correlation": "1",
                "probability_loss_rate_positive": "1",
                "prediction_times_s": "s",
                "predicted_remaining_thickness_mean_m": "m",
                "predicted_remaining_thickness_standard_deviation_m": "m",
                "credible_level": "1",
                "predicted_remaining_thickness_credible_lower_m": "m",
                "predicted_remaining_thickness_credible_upper_m": "m",
                "required_thickness_m": "m",
                "probability_below_required_thickness": "1",
                "holdout_residuals_m": "m",
                "holdout_standardized_residuals": "1",
                "holdout_source_independence_status": "1",
                "overlapping_holdout_source_group_ids": "1",
            },
            (
                "Caller-reviewed Gaussian prior and thickness measurement-error model for one physical location under a constant linear thickness-loss relation.",
                "Calibration and holdout partitions are fixed before updating; holdout observations never influence the posterior.",
                "No process noise, model-form uncertainty, POD, missed flaws, interventions or period first-passage calculation is included.",
            ),
            ("bayesian_linear_thickness_update_derivation",),
            context_validator=_bayesian_thickness_context,
            probability_semantics={
                "probability_loss_rate_positive": "posterior_parameter_probability",
                "probability_below_required_thickness": "point_in_time_state_probability",
            },
        ),
        ModelSpec(
            "reliability.linear_thickness_state_space_update",
            LinearThicknessStateSpaceUpdate,
            linear_thickness_state_space_update,
            {
                "observation_diagnostics": "mixed SI [s,m,m/s,m^2,m^2/s,m^2/s^2,1]",
                "state_time_s": "s",
                "posterior_remaining_thickness_at_state_time_mean_m": "m",
                "posterior_loss_rate_mean_m_s": "m/s",
                "posterior_covariance": "mixed SI covariance [m,m/s]",
                "posterior_remaining_thickness_standard_deviation_m": "m",
                "posterior_loss_rate_standard_deviation_m_s": "m/s",
                "posterior_thickness_loss_rate_correlation": "1",
                "probability_loss_rate_positive": "1",
                "prediction_times_s": "s",
                "predicted_remaining_thickness_mean_m": "m",
                "predicted_remaining_thickness_standard_deviation_m": "m",
                "predicted_remaining_thickness_credible_lower_m": "m",
                "predicted_remaining_thickness_credible_upper_m": "m",
                "required_thickness_m": "m",
                "probability_below_required_thickness": "1",
                "process_noise_covariance_rate": "mixed SI covariance rate [m,m/s] per s",
            },
            (
                "Caller-reviewed two-state linear thickness/loss-rate transition with additive covariance rate and independent sequential thickness-measurement errors.",
                "Update and holdout rows are chronological and distinct; holdout values never alter the filtered state.",
                "The filter supplies no process-noise calibration, smoother, nonlinear growth, intervention, POD, first-passage probability or field qualification.",
            ),
            ("linear_thickness_state_space_filter_derivation",),
            context_validator=_linear_thickness_state_space_context,
            probability_semantics={
                "probability_loss_rate_positive": "posterior_parameter_probability",
                "probability_below_required_thickness": "point_in_time_state_probability",
            },
        ),
        ModelSpec(
            "reliability.gaussian_thickness_posterior_sample_design",
            GaussianThicknessPosteriorSampleDesign,
            gaussian_thickness_posterior_sample_design,
            {
                "assessment_time_s": "s",
                "required_thickness_m": "m",
                "accepted_sample_count": "count",
                "candidate_draw_count": "count",
                "maximum_candidate_draw_count": "count",
                "negative_loss_rate_candidate_count": "count",
                "non_surviving_candidate_count": "count",
                "both_condition_failures_count": "count",
                "empirical_acceptance_fraction": "1",
                "samples": "mixed SI [m,m/s,1]",
            },
            (
                "Caller-reviewed two-dimensional Gaussian posterior for reference-time thickness and signed constant loss rate at one physical location.",
                "A versioned deterministic draw stream preserves thickness-rate correlation and uses explicit rejection to condition on nonnegative rate and assessment-time survival.",
                "The conditional sample design supplies no process noise, nonlinear growth, intervention, confidence bound, field calibration or constant-rate qualification.",
            ),
            ("gaussian_thickness_posterior_sampling_derivation",),
            context_validator=_gaussian_thickness_sample_context,
        ),
        ModelSpec(
            "reliability.sampled_linear_thickness_first_passage",
            SampledLinearThicknessFirstPassage,
            sampled_linear_thickness_first_passage,
            {
                "assessment_time_s": "s",
                "required_thickness_m": "m",
                "sample_count": "count",
                "supplied_weight_sum": "1",
                "weight_normalization_factor": "1",
                "sample_results": "mixed SI [m,m/s,s,1]",
                "forecast_points": "mixed SI [s,1]",
                "final_horizon_probability_given_survival": "1",
                "never_crossing_probability_under_constant_rate": "1",
                "positive_rate_crossing_after_final_horizon_probability": "1",
            },
            (
                "Caller-reviewed joint weighted samples describe remaining thickness and a nonnegative constant loss rate at one physical location, conditional on no threshold crossing by assessment time.",
                "Each positive-rate row is pushed through its exact linear first-crossing time and zero-rate rows never cross; failed or conditioning-conflicting rows are not discarded.",
                "The empirical cumulative curve represents the declared joint input distribution only and supplies no confidence bound, process noise, model-form uncertainty, inspection effect or field qualification.",
            ),
            ("sampled_linear_thickness_first_passage_derivation",),
            context_validator=_sampled_first_passage_context,
            probability_semantics={
                "final_horizon_probability_given_survival": ("conditional_first_failure_in_period"),
                "never_crossing_probability_under_constant_rate": "unscoped_event_probability",
                "positive_rate_crossing_after_final_horizon_probability": ("unscoped_event_probability"),
            },
        ),
        ModelSpec(
            "reliability.exclusive_paths",
            ExclusivePaths,
            exclusive_paths,
            {"path_frequencies_per_s": "1/s"},
            ("Mutually exclusive and complete conditional paths allocate initiation exactly once.",),
            ("total_probability",),
        ),
        ModelSpec(
            "reliability.gamma_poisson",
            GammaPoisson,
            gamma_poisson,
            {
                "posterior_shape": "1",
                "posterior_exposure_s": "s",
                "mean_frequency_per_s": "1/s",
                "variance_frequency_per_s2": "1/s^2",
            },
            (
                "Stationary Poisson event counts with Gamma(shape, exposure) prior and complete ascertainment.",
            ),
            ("gamma_poisson_conjugacy",),
        ),
    ]
