"""Stability diagnostics for caller-supplied independent Sobol estimate replicates."""

from __future__ import annotations

import math

from pydantic import Field, model_validator

from ..contracts import Calculation, Contract, Evidence, Nonnegative, Positive
from ..registry import ModelSpec


class SobolParameterEstimate(Contract):
    parameter_id: str = Field(min_length=1)
    first_order_index: float
    total_order_index: float
    first_order_estimator_uncertainty: Nonnegative | None = None
    total_order_estimator_uncertainty: Nonnegative | None = None
    uncertainty_definition: str | None = None

    @model_validator(mode="after")
    def aligned_uncertainty(self):
        first_present = self.first_order_estimator_uncertainty is not None
        total_present = self.total_order_estimator_uncertainty is not None
        if first_present != total_present:
            raise ValueError("Sobol first/total estimator uncertainties must be supplied together")
        if first_present and not self.uncertainty_definition:
            raise ValueError("Sobol estimator uncertainty values require a definition")
        if not first_present and self.uncertainty_definition is not None:
            raise ValueError("Sobol uncertainty definition requires uncertainty values")
        return self


class SobolEstimateReplicate(Contract):
    replicate_id: str = Field(min_length=1)
    seed: int = Field(ge=0)
    output_id: str = Field(min_length=1)
    output_definition: str = Field(min_length=1)
    output_unit_token: str = Field(min_length=1)
    parameter_distribution_id: str = Field(min_length=1)
    distribution_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    dependence_assumption_id: str = Field(min_length=1)
    design_family_id: str = Field(min_length=1)
    design_family_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    evaluator_id: str = Field(min_length=1)
    evaluator_revision: str = Field(min_length=1)
    evaluator_configuration_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    sample_count: int | None = Field(default=None, ge=1)
    effective_sample_size: Positive | None = None
    parameter_estimates: tuple[SobolParameterEstimate, ...] = Field(min_length=1)
    result_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    record_valid: bool
    invalid_or_missing_basis: str | None = None
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def unique_complete_metadata(self):
        identifiers = [row.parameter_id for row in self.parameter_estimates]
        if len(set(identifiers)) != len(identifiers):
            raise ValueError("Sobol parameter estimates must be unique per replicate")
        has_all_uncertainty = all(
            row.first_order_estimator_uncertainty is not None for row in self.parameter_estimates
        )
        if not has_all_uncertainty and self.sample_count is None and self.effective_sample_size is None:
            raise ValueError(
                "Sobol replicates require estimator uncertainty, effective sample size or sample count"
            )
        if (
            self.sample_count is not None
            and self.effective_sample_size is not None
            and self.effective_sample_size > self.sample_count
        ):
            raise ValueError("Sobol effective sample size cannot exceed sample count")
        if not self.record_valid and not self.invalid_or_missing_basis:
            raise ValueError("an invalid Sobol replicate requires a basis")
        return self


class SobolReplicateStabilityAssessment(Contract):
    assessment_id: str = Field(min_length=1)
    asset_id: str = Field(min_length=1)
    location_id: str = Field(min_length=1)
    output_id: str = Field(min_length=1)
    output_definition: str = Field(min_length=1)
    output_unit_token: str = Field(min_length=1)
    parameter_ids: tuple[str, ...] = Field(min_length=2)
    parameter_distribution_id: str = Field(min_length=1)
    distribution_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    dependence_assumption_id: str = Field(min_length=1)
    design_family_id: str = Field(min_length=1)
    design_family_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    evaluator_id: str = Field(min_length=1)
    evaluator_revision: str = Field(min_length=1)
    evaluator_configuration_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    replicates: tuple[SobolEstimateReplicate, ...] = Field(min_length=2)
    minimum_replicate_count: int = Field(ge=2)
    maximum_first_order_replicate_range: Nonnegative
    maximum_total_order_replicate_range: Nonnegative
    maximum_pooled_sample_standard_deviation: Nonnegative
    maximum_reported_estimator_uncertainty: Nonnegative
    rank_tie_tolerance: Nonnegative
    output_parameter_distribution_and_dependence_identity_reviewed: bool
    design_family_and_evaluator_identity_reviewed: bool
    replicate_independence_ids_and_seeds_reviewed: bool
    complete_parameter_sets_reviewed: bool
    estimator_uncertainty_ess_and_sample_counts_reviewed: bool
    result_digests_and_missingness_reviewed: bool
    diagnostic_tolerances_and_rank_definition_reviewed: bool

    @model_validator(mode="after")
    def aligned_replicates(self):
        if len(set(self.parameter_ids)) != len(self.parameter_ids):
            raise ValueError("Sobol assessment parameter identifiers must be unique")
        replicate_ids = [row.replicate_id for row in self.replicates]
        seeds = [row.seed for row in self.replicates]
        if len(set(replicate_ids)) != len(replicate_ids):
            raise ValueError("Sobol replicate identifiers must be unique")
        if len(set(seeds)) != len(seeds):
            raise ValueError("Sobol independent replicate seeds must be unique")
        expected_parameters = set(self.parameter_ids)
        identity = (
            self.output_id,
            self.output_definition,
            self.output_unit_token,
            self.parameter_distribution_id,
            self.distribution_digest,
            self.dependence_assumption_id,
            self.design_family_id,
            self.design_family_digest,
            self.evaluator_id,
            self.evaluator_revision,
            self.evaluator_configuration_digest,
        )
        for row in self.replicates:
            row_identity = (
                row.output_id,
                row.output_definition,
                row.output_unit_token,
                row.parameter_distribution_id,
                row.distribution_digest,
                row.dependence_assumption_id,
                row.design_family_id,
                row.design_family_digest,
                row.evaluator_id,
                row.evaluator_revision,
                row.evaluator_configuration_digest,
            )
            if row_identity != identity:
                raise ValueError("all Sobol replicates must share the declared identity and digests")
            if {estimate.parameter_id for estimate in row.parameter_estimates} != expected_parameters:
                raise ValueError("every Sobol replicate must contain the complete declared parameter set")
        return self


def _sample_standard_deviation(values: list[float]) -> float:
    if len(values) < 2:
        return 0.0
    mean = math.fsum(values) / len(values)
    return math.sqrt(math.fsum((value - mean) ** 2 for value in values) / (len(values) - 1))


def _rank_classification(first: float, second: float, tolerance: float) -> int:
    difference = first - second
    return 1 if difference > tolerance else -1 if difference < -tolerance else 0


def sobol_replicate_stability(x: SobolReplicateStabilityAssessment) -> Calculation:
    missing_reviews = [
        name
        for name in (
            "output_parameter_distribution_and_dependence_identity_reviewed",
            "design_family_and_evaluator_identity_reviewed",
            "replicate_independence_ids_and_seeds_reviewed",
            "complete_parameter_sets_reviewed",
            "estimator_uncertainty_ess_and_sample_counts_reviewed",
            "result_digests_and_missingness_reviewed",
            "diagnostic_tolerances_and_rank_definition_reviewed",
        )
        if not getattr(x, name)
    ]
    invalid_replicate_ids = [row.replicate_id for row in x.replicates if not row.record_valid]
    minimum_replicates_met = len(x.replicates) >= x.minimum_replicate_count
    if missing_reviews or invalid_replicate_ids or not minimum_replicates_met:
        return Calculation(
            status="needs_data",
            values={
                "assessment_id": x.assessment_id,
                "missing_reviews": missing_reviews,
                "invalid_replicate_ids": invalid_replicate_ids,
                "replicate_count": len(x.replicates),
                "minimum_replicates_met": minimum_replicates_met,
            },
            notes=("Reviewed, valid and sufficiently numerous Sobol replicates are required.",),
        )

    estimates_by_replicate = {
        row.replicate_id: {item.parameter_id: item for item in row.parameter_estimates}
        for row in x.replicates
    }
    parameter_diagnostics = []
    for parameter_id in x.parameter_ids:
        first_values = [
            estimates_by_replicate[row.replicate_id][parameter_id].first_order_index for row in x.replicates
        ]
        total_values = [
            estimates_by_replicate[row.replicate_id][parameter_id].total_order_index for row in x.replicates
        ]
        reported_uncertainties = [
            value
            for row in x.replicates
            for value in (
                estimates_by_replicate[row.replicate_id][parameter_id].first_order_estimator_uncertainty,
                estimates_by_replicate[row.replicate_id][parameter_id].total_order_estimator_uncertainty,
            )
            if value is not None
        ]
        first_range = max(first_values) - min(first_values)
        total_range = max(total_values) - min(total_values)
        first_sd = _sample_standard_deviation(first_values)
        total_sd = _sample_standard_deviation(total_values)
        maximum_reported_uncertainty = max(reported_uncertainties, default=None)
        criteria_satisfied = (
            first_range <= x.maximum_first_order_replicate_range
            and total_range <= x.maximum_total_order_replicate_range
            and first_sd <= x.maximum_pooled_sample_standard_deviation
            and total_sd <= x.maximum_pooled_sample_standard_deviation
            and (
                maximum_reported_uncertainty is None
                or maximum_reported_uncertainty <= x.maximum_reported_estimator_uncertainty
            )
        )
        parameter_diagnostics.append(
            {
                "parameter_id": parameter_id,
                "first_order_mean": math.fsum(first_values) / len(first_values),
                "total_order_mean": math.fsum(total_values) / len(total_values),
                "first_order_sample_standard_deviation": first_sd,
                "total_order_sample_standard_deviation": total_sd,
                "first_order_minimum": min(first_values),
                "first_order_maximum": max(first_values),
                "first_order_range": first_range,
                "total_order_minimum": min(total_values),
                "total_order_maximum": max(total_values),
                "total_order_range": total_range,
                "maximum_reported_estimator_uncertainty": maximum_reported_uncertainty,
                "declared_dispersion_criteria_satisfied": criteria_satisfied,
            }
        )

    first_order_unstable_pairs = []
    total_order_unstable_pairs = []
    for first_index, first_parameter in enumerate(x.parameter_ids):
        for second_parameter in x.parameter_ids[first_index + 1 :]:
            first_labels = [
                _rank_classification(
                    estimates_by_replicate[row.replicate_id][first_parameter].first_order_index,
                    estimates_by_replicate[row.replicate_id][second_parameter].first_order_index,
                    x.rank_tie_tolerance,
                )
                for row in x.replicates
            ]
            total_labels = [
                _rank_classification(
                    estimates_by_replicate[row.replicate_id][first_parameter].total_order_index,
                    estimates_by_replicate[row.replicate_id][second_parameter].total_order_index,
                    x.rank_tie_tolerance,
                )
                for row in x.replicates
            ]
            if len(set(first_labels)) != 1:
                first_order_unstable_pairs.append(
                    {
                        "parameter_pair": [first_parameter, second_parameter],
                        "replicate_order_labels": first_labels,
                    }
                )
            if len(set(total_labels)) != 1:
                total_order_unstable_pairs.append(
                    {
                        "parameter_pair": [first_parameter, second_parameter],
                        "replicate_order_labels": total_labels,
                    }
                )
    rank_order_stable = not first_order_unstable_pairs and not total_order_unstable_pairs
    dispersion_criteria_satisfied = all(
        row["declared_dispersion_criteria_satisfied"] for row in parameter_diagnostics
    )
    values = {
        "assessment_id": x.assessment_id,
        "asset_id": x.asset_id,
        "location_id": x.location_id,
        "output_id": x.output_id,
        "parameter_ids": list(x.parameter_ids),
        "replicate_ids": [row.replicate_id for row in x.replicates],
        "replicate_seeds": [row.seed for row in x.replicates],
        "sample_counts": {row.replicate_id: row.sample_count for row in x.replicates},
        "effective_sample_sizes": {row.replicate_id: row.effective_sample_size for row in x.replicates},
        "parameter_diagnostics": parameter_diagnostics,
        "first_order_unstable_parameter_pairs": first_order_unstable_pairs,
        "total_order_unstable_parameter_pairs": total_order_unstable_pairs,
        "rank_order_stable_at_declared_tie_tolerance": rank_order_stable,
        "dispersion_criteria_satisfied": dispersion_criteria_satisfied,
        "all_declared_stability_criteria_satisfied": (rank_order_stable and dispersion_criteria_satisfied),
    }
    return Calculation(
        values=values,
        notes=(
            "The reducer uses supplied Sobol estimates and does not run an evaluator or estimate new indices.",
            "Equal replicate weighting summarizes independent declared replicates; ESS and sample counts remain diagnostics.",
            "Indices for dependent physical inputs retain the caller's declared dependence meaning and are not relabelled as independent-input Sobol indices.",
            "Meeting dispersion and rank criteria is not a convergence proof, causal sensitivity claim, probability or validation of the evaluator/distribution.",
        ),
    )


def specifications():
    def same_identity(x, context):
        if (x.asset_id, x.location_id) != (context.asset_id, context.location_id):
            raise ValueError("Sobol replicate stability asset and location must match run context")

    return [
        ModelSpec(
            "reliability.sobol_replicate_stability",
            SobolReplicateStabilityAssessment,
            sobol_replicate_stability,
            {
                "assessment_id": "1",
                "asset_id": "1",
                "location_id": "1",
                "output_id": "1",
                "parameter_ids": "1",
                "replicate_ids": "1",
                "replicate_seeds": "1",
                "sample_counts": "sample",
                "effective_sample_sizes": "sample",
                "parameter_diagnostics": "mixed",
                "first_order_unstable_parameter_pairs": "1",
                "total_order_unstable_parameter_pairs": "1",
                "rank_order_stable_at_declared_tie_tolerance": "1",
                "dispersion_criteria_satisfied": "1",
                "all_declared_stability_criteria_satisfied": "1",
            },
            (
                "All replicates share exact output, parameter, distribution, dependence, design and evaluator identities.",
                "Replicate IDs and seeds are unique and every replicate contains the complete parameter set.",
                "Stability diagnostics do not prove convergence, causality or physical-model validity.",
            ),
            ("caller_supplied_sobol_replicate_estimates",),
            context_validator=same_identity,
        )
    ]
