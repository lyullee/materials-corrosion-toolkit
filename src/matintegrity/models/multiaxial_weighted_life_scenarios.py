"""Descriptive weighted moments for complete multiaxial fatigue life scenarios."""

from __future__ import annotations

import math
from bisect import bisect_left, bisect_right
from typing import Literal

from pydantic import Field, model_validator

from ..contracts import Calculation, Contract, Evidence, Positive, RunContext, canonical_digest
from ..registry import ModelSpec
from .multiaxial_life_scenario_envelope import (
    MultiaxialLifeScenarioEnvelope,
    evaluate_multiaxial_life_scenario_envelope,
)


class MultiaxialWeightedLifeScenarioMoments(Contract):
    """Apply an explicit ordered weight vector to complete finite life scenarios."""

    schema_version: Literal["matintegrity.multiaxial_weighted_life_scenario_moments.v1"] = (
        "matintegrity.multiaxial_weighted_life_scenario_moments.v1"
    )
    scenario_envelope: MultiaxialLifeScenarioEnvelope
    scenario_weights: tuple[Positive, ...] = Field(min_length=1, max_length=10000)
    weighted_quantile_levels: tuple[float, ...] = Field(default=(), max_length=1000)
    lower_tail_mass_levels: tuple[float, ...] = Field(default=(), max_length=1000)
    cycle_life_thresholds: tuple[Positive, ...] = Field(default=(), max_length=1000)
    weight_semantics: Literal["empirical_frequency", "quadrature_weight", "user_declared_weight"]
    weight_provider_id: str = Field(min_length=1)
    weight_provider_revision: str = Field(min_length=1)
    weight_record_id: str = Field(min_length=1)
    weight_record_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    weight_evidence: tuple[Evidence, ...] = Field(min_length=1)
    usage_rights_evidence: tuple[Evidence, ...] = Field(min_length=1)
    usage_license_id: str = Field(min_length=1)
    scenario_weight_alignment_reviewed: bool
    weight_semantics_reviewed: bool
    weighted_distribution_summaries_reviewed: bool = False
    cycle_life_threshold_definitions_reviewed: bool = False
    usage_rights_reviewed: bool
    computational_use_authorized: bool

    @model_validator(mode="after")
    def coherent_weighted_manifest(self):
        if len(self.scenario_weights) != len(self.scenario_envelope.scenarios):
            raise ValueError("one strictly positive weight is required for each ordered scenario")
        try:
            weight_sum = math.fsum(self.scenario_weights)
        except OverflowError as error:
            raise ValueError("scenario weight sum must be finite") from error
        if not math.isfinite(weight_sum) or not math.isclose(
            weight_sum, 1.0, rel_tol=0.0, abs_tol=1e-12
        ):
            raise ValueError("scenario weights must already sum to one; automatic normalization is forbidden")
        if canonical_digest(list(self.scenario_weights)) != self.weight_record_sha256:
            raise ValueError("ordered scenario weight vector digest mismatch")
        if not any(
            row.source_id == self.weight_provider_id and row.sha256 == self.weight_record_sha256
            for row in self.weight_evidence
        ):
            raise ValueError("weight provider and vector digest must be linked to matching Evidence")
        if not any(row.license_id == self.usage_license_id for row in self.usage_rights_evidence):
            raise ValueError("usage-rights Evidence must identify the declared license or use basis")
        if any(
            isinstance(level, bool) or not math.isfinite(level) or not 0.0 <= level <= 1.0
            for level in self.weighted_quantile_levels
        ) or len(set(self.weighted_quantile_levels)) != len(self.weighted_quantile_levels):
            raise ValueError("weighted quantile levels must be unique finite values between zero and one")
        if any(
            isinstance(level, bool) or not math.isfinite(level) or not 0.0 < level <= 1.0
            for level in self.lower_tail_mass_levels
        ) or len(set(self.lower_tail_mass_levels)) != len(self.lower_tail_mass_levels):
            raise ValueError("lower-tail mass levels must be unique finite values greater than zero and at most one")
        if bool(self.weighted_quantile_levels or self.lower_tail_mass_levels) != self.weighted_distribution_summaries_reviewed:
            raise ValueError("weighted quantiles or lower-tail means require explicit distribution-summary review, and vice versa")
        if bool(self.cycle_life_thresholds) != self.cycle_life_threshold_definitions_reviewed:
            raise ValueError("cycle-life thresholds require explicit event-definition review, and vice versa")
        if len(set(self.cycle_life_thresholds)) != len(self.cycle_life_thresholds):
            raise ValueError("cycle-life thresholds must be unique")
        return self


def evaluate_multiaxial_weighted_life_scenario_moments(
    request: MultiaxialWeightedLifeScenarioMoments,
) -> Calculation:
    """Summarize explicitly weighted finite scenario lives without probability inference."""
    envelope = request.scenario_envelope
    base = {
        "assessment_id": envelope.assessment_id,
        "asset_id": envelope.asset_id,
        "location_id": envelope.location_id,
        "time_basis": envelope.time_basis,
        "scenario_manifest_sha256": envelope.scenarios_sha256,
        "input_sha256": canonical_digest(request.model_dump(mode="json")),
        "scenario_count": len(request.scenario_weights),
        "scenario_weights": list(request.scenario_weights),
        "review_flags": {
            "scenario_weight_alignment_reviewed": request.scenario_weight_alignment_reviewed,
            "weight_semantics_reviewed": request.weight_semantics_reviewed,
            "weighted_distribution_summaries_reviewed": request.weighted_distribution_summaries_reviewed,
            "cycle_life_threshold_definitions_reviewed": request.cycle_life_threshold_definitions_reviewed,
            "usage_rights_reviewed": request.usage_rights_reviewed,
            "computational_use_authorized": request.computational_use_authorized,
        },
        "weighted_quantile_levels": list(request.weighted_quantile_levels),
        "lower_tail_mass_levels": list(request.lower_tail_mass_levels),
        "cycle_life_thresholds": list(request.cycle_life_thresholds),
        "weight_semantics": request.weight_semantics,
        "weight_provider_id": request.weight_provider_id,
        "weight_provider_revision": request.weight_provider_revision,
        "weight_record_id": request.weight_record_id,
        "weight_record_sha256": request.weight_record_sha256,
        "usage_license_id": request.usage_license_id,
        "uncertainty_semantics": "descriptive_weighted_moments_over_the_finite_caller_supplied_joint_scenario_set",
        "probability_or_confidence_claim": False,
        "threshold_mass_is_probability": False,
        "continuous_bound_claim": False,
    }
    required_reviews = {
        "scenario_weight_alignment_reviewed": request.scenario_weight_alignment_reviewed,
        "weight_semantics_reviewed": request.weight_semantics_reviewed,
        "usage_rights_reviewed": request.usage_rights_reviewed,
        "computational_use_authorized": request.computational_use_authorized,
    }
    missing = [name for name, passed in required_reviews.items() if not passed]
    if missing:
        return Calculation(status="needs_data", values=base | {"missing_reviews": missing})

    scenario_result = evaluate_multiaxial_life_scenario_envelope(envelope)
    if scenario_result.status != "computed":
        return Calculation(
            status=scenario_result.status,
            values=base | {"scenario_envelope_result": scenario_result.model_dump(mode="json")},
            notes=scenario_result.notes,
        )
    try:
        rows = scenario_result.values["scenario_lives"]
        expected_ids = [scenario.scenario_id for scenario in envelope.scenarios]
        actual_ids = [row["scenario_id"] for row in rows]
        if len(rows) != len(request.scenario_weights) or actual_ids != expected_ids:
            raise ValueError("computed life rows differ from the ordered weighted scenario manifest")
        lives = [float(row["cycles_to_failure"]) for row in rows]
        weighted_mean = math.fsum(
            weight * life for weight, life in zip(request.scenario_weights, lives, strict=True)
        )
        weighted_variance = math.fsum(
            weight * (life - weighted_mean) ** 2
            for weight, life in zip(request.scenario_weights, lives, strict=True)
        )
        weighted_std = math.sqrt(weighted_variance)
        if not all(math.isfinite(value) for value in (weighted_mean, weighted_variance, weighted_std)):
            raise ValueError("weighted scenario life moments exceed finite numeric support")
    except (KeyError, TypeError, ValueError, OverflowError) as error:
        return Calculation(status="out_of_scope", values=base | {"out_of_scope_reason": str(error)})

    minimum_index = min(range(len(lives)), key=lives.__getitem__)
    maximum_index = max(range(len(lives)), key=lives.__getitem__)
    ordered_scenarios = sorted(
        zip(lives, request.scenario_weights, expected_ids, strict=True),
        key=lambda row: (row[0], row[2]),
    )
    cumulative_weights = []
    cumulative = 0.0
    compensation = 0.0
    cumulative_weighted_lives = []
    weighted_life_total = 0.0
    weighted_life_compensation = 0.0
    for _, weight, _ in ordered_scenarios:
        adjusted = weight - compensation
        updated = cumulative + adjusted
        compensation = (updated - cumulative) - adjusted
        cumulative = updated
        cumulative_weights.append(cumulative)
    for life, weight, _ in ordered_scenarios:
        adjusted = weight * life - weighted_life_compensation
        updated = weighted_life_total + adjusted
        weighted_life_compensation = (updated - weighted_life_total) - adjusted
        weighted_life_total = updated
        cumulative_weighted_lives.append(weighted_life_total)
    ordered_lives = [row[0] for row in ordered_scenarios]
    quantiles = []
    for level in request.weighted_quantile_levels:
        selected_index = (
            len(ordered_scenarios) - 1
            if level == 1.0
            else min(bisect_left(cumulative_weights, level), len(ordered_scenarios) - 1)
        )
        selected = ordered_scenarios[selected_index]
        quantiles.append({
            "quantile_level": level,
            "cycles_to_failure": selected[0],
            "witness_scenario_id": selected[2],
            "definition": "left_continuous_weighted_inverse_ecdf_over_finite_manifest",
        })
    lower_tail_means = []
    available_mass = cumulative_weights[-1]
    for requested_mass in request.lower_tail_mass_levels:
        target_mass = min(requested_mass, available_mass)
        boundary_index = min(bisect_left(cumulative_weights, target_mass), len(ordered_scenarios) - 1)
        preceding_mass = cumulative_weights[boundary_index - 1] if boundary_index > 0 else 0.0
        preceding_life_sum = cumulative_weighted_lives[boundary_index - 1] if boundary_index > 0 else 0.0
        boundary_mass = max(0.0, target_mass - preceding_mass)
        weighted_life_sum = preceding_life_sum + boundary_mass * ordered_scenarios[boundary_index][0]
        lower_tail_means.append({
            "requested_lower_tail_mass": requested_mass,
            "realized_lower_tail_mass": target_mass,
            "weighted_mean_cycles_to_failure": weighted_life_sum / target_mass,
            "definition": "mean_of_exact_requested_lowest_weighted_mass_over_finite_scenario_manifest; partial_boundary_scenario_weight_allowed; not probability",
        })
    threshold_masses = [{
        "cycle_life_threshold": threshold,
        "weighted_scenario_mass_at_or_below_threshold": (
            cumulative_weights[bisect_right(ordered_lives, threshold) - 1]
            if bisect_right(ordered_lives, threshold) > 0 else 0.0
        ),
        "scenario_count_at_or_below_threshold": bisect_right(ordered_lives, threshold),
        "definition": "caller_weighted_mass_of_finite_scenarios_with_life_at_or_below_threshold; not a probability",
    } for threshold in request.cycle_life_thresholds]
    return Calculation(values=base | {
        "scenario_lives_sha256": canonical_digest(rows),
        "weighted_mean_cycles_to_failure": weighted_mean,
        "weighted_population_variance_cycles2": weighted_variance,
        "weighted_standard_deviation_cycles": weighted_std,
        "minimum_cycles_to_failure": lives[minimum_index],
        "minimum_witness_scenario_id": rows[minimum_index]["scenario_id"],
        "maximum_cycles_to_failure": lives[maximum_index],
        "maximum_witness_scenario_id": rows[maximum_index]["scenario_id"],
        "scenario_lives": rows,
        "weighted_life_quantiles": quantiles,
        "weighted_lower_tail_mean_cycles_to_failure": lower_tail_means,
        "weighted_cycle_life_threshold_masses": threshold_masses,
        "moment_definition": "weighted_population_moments_of_finite_scenario_lives; no Bessel correction",
        "correlation_preserved_within_each_scenario": True,
    }, notes=(
        "Each complete multiaxial-life result is evaluated before applying its matched caller weight.",
        "Weights describe only this finite manifest and are not interpreted as failure probabilities, confidence levels, or continuous-support bounds.",
    ))


def _validate_context(request: MultiaxialWeightedLifeScenarioMoments, context: RunContext) -> None:
    envelope = request.scenario_envelope
    if (context.asset_id, context.location_id, context.time_basis) != (
        envelope.asset_id, envelope.location_id, envelope.time_basis
    ):
        raise ValueError("weighted scenario RunContext must match the nested envelope context")


def specifications() -> list[ModelSpec]:
    return [ModelSpec(
        "fatigue.multiaxial_weighted_life_scenario_moments",
        MultiaxialWeightedLifeScenarioMoments,
        evaluate_multiaxial_weighted_life_scenario_moments,
        {
            "weighted_mean_cycles_to_failure": "cycle",
            "weighted_population_variance_cycles2": "cycle^2",
            "weighted_standard_deviation_cycles": "cycle",
            "minimum_cycles_to_failure": "cycle",
            "maximum_cycles_to_failure": "cycle",
            "weighted_life_quantiles[].quantile_level": "1",
            "weighted_life_quantiles[].cycles_to_failure": "cycle",
            "weighted_lower_tail_mean_cycles_to_failure[].requested_lower_tail_mass": "1",
            "weighted_lower_tail_mean_cycles_to_failure[].realized_lower_tail_mass": "1",
            "weighted_lower_tail_mean_cycles_to_failure[].weighted_mean_cycles_to_failure": "cycle",
            "weighted_cycle_life_threshold_masses[].cycle_life_threshold": "cycle",
            "weighted_cycle_life_threshold_masses[].weighted_scenario_mass_at_or_below_threshold": "1",
        },
        (
            "Compute descriptive weighted moments over complete digest-pinned multiaxial fatigue life scenarios with caller-supplied ordered weights.",
            "Optional left-continuous inverse weighted ECDF quantiles, exact lower-tail weighted means, and threshold masses apply only to the finite declared scenario set; threshold masses are not event probabilities, and no confidence interval or continuous uncertainty bound is inferred.",
        ),
        ("caller_weighted_finite_multiaxial_life_scenario_moments",),
        qualification="user_model",
        context_validator=_validate_context,
    )]
