"""Measured phase-fraction evidence compared with caller-owned ranges."""

from __future__ import annotations

from collections import defaultdict

from pydantic import Field, model_validator

from ..contracts import Calculation, Contract, Evidence, Fraction
from ..registry import ModelSpec


class PhaseFractionObservation(Contract):
    observation_id: str = Field(min_length=1)
    sample_id: str = Field(min_length=1)
    region_id: str = Field(min_length=1)
    phase_id: str = Field(min_length=1)
    measured_fraction: Fraction | None = None
    expanded_uncertainty_fraction: Fraction | None = None
    method_id: str = Field(min_length=1)
    record_valid: bool
    invalid_basis: str | None = None
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def coherent_measurement(self):
        if self.record_valid and (
            self.measured_fraction is None or self.expanded_uncertainty_fraction is None
        ):
            raise ValueError("a valid phase observation requires value and expanded uncertainty")
        if not self.record_valid and not self.invalid_basis:
            raise ValueError("an invalid phase observation requires a basis")
        return self


class DeclaredPhaseFractionRange(Contract):
    requirement_id: str = Field(min_length=1)
    region_id: str = Field(min_length=1)
    phase_id: str = Field(min_length=1)
    minimum_fraction: Fraction
    maximum_fraction: Fraction
    requirement_basis: str = Field(min_length=1)
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def ordered_range(self):
        if self.maximum_fraction < self.minimum_fraction:
            raise ValueError("declared phase-fraction bounds must be ordered")
        return self


class PhaseMicrostructureAssessment(Contract):
    assessment_id: str = Field(min_length=1)
    asset_id: str = Field(min_length=1)
    location_id: str = Field(min_length=1)
    material_condition_id: str = Field(min_length=1)
    processing_history_id: str = Field(min_length=1)
    observations: tuple[PhaseFractionObservation, ...] = Field(min_length=1)
    declared_ranges: tuple[DeclaredPhaseFractionRange, ...] = Field(min_length=1)
    sample_and_region_mapping_reviewed: bool
    material_and_processing_identity_reviewed: bool
    method_applicability_reviewed: bool
    uncertainty_basis_reviewed: bool
    phase_identity_reviewed: bool
    requirement_authority_reviewed: bool

    @model_validator(mode="after")
    def unique_and_bounded(self):
        observation_ids = [row.observation_id for row in self.observations]
        requirement_ids = [row.requirement_id for row in self.declared_ranges]
        if len(observation_ids) != len(set(observation_ids)):
            raise ValueError("phase observation identifiers must be unique")
        if len(requirement_ids) != len(set(requirement_ids)):
            raise ValueError("phase requirement identifiers must be unique")
        keys = [(row.region_id, row.phase_id) for row in self.declared_ranges]
        if len(keys) != len(set(keys)):
            raise ValueError("declare at most one range for each region and phase")
        sums = defaultdict(float)
        for row in self.observations:
            if row.record_valid:
                sums[(row.sample_id, row.region_id)] += row.measured_fraction
        if any(total > 1.0 + 1e-12 for total in sums.values()):
            raise ValueError("nominal phase fractions for one sample and region cannot exceed one")
        return self


def phase_microstructure_assessment(x: PhaseMicrostructureAssessment) -> Calculation:
    missing_reviews = [
        name
        for name in (
            "sample_and_region_mapping_reviewed",
            "material_and_processing_identity_reviewed",
            "method_applicability_reviewed",
            "uncertainty_basis_reviewed",
            "phase_identity_reviewed",
            "requirement_authority_reviewed",
        )
        if not getattr(x, name)
    ]
    invalid = [row.observation_id for row in x.observations if not row.record_valid]
    rows = []
    missing_requirement_observations = []
    outside_observations = []
    for requirement in x.declared_ranges:
        observations = [
            row
            for row in x.observations
            if row.record_valid
            and row.region_id == requirement.region_id
            and row.phase_id == requirement.phase_id
        ]
        if not observations:
            missing_requirement_observations.append(requirement.requirement_id)
        for observation in observations:
            lower = max(0.0, observation.measured_fraction - observation.expanded_uncertainty_fraction)
            upper = min(1.0, observation.measured_fraction + observation.expanded_uncertainty_fraction)
            within = lower >= requirement.minimum_fraction and upper <= requirement.maximum_fraction
            if not within:
                outside_observations.append(observation.observation_id)
            rows.append(
                {
                    "requirement_id": requirement.requirement_id,
                    "observation_id": observation.observation_id,
                    "sample_id": observation.sample_id,
                    "region_id": observation.region_id,
                    "phase_id": observation.phase_id,
                    "uncertainty_interval_fraction": [lower, upper],
                    "within_declared_range": within,
                }
            )

    status = "needs_data" if missing_reviews or invalid or missing_requirement_observations else "computed"
    return Calculation(
        status=status,
        values={
            "assessment_id": x.assessment_id,
            "comparison_rows": rows,
            "invalid_observation_ids": invalid,
            "missing_requirement_observation_ids": missing_requirement_observations,
            "outside_declared_range_observation_ids": outside_observations,
            "missing_reviews": missing_reviews,
            "all_observations_within_declared_ranges": (
                not outside_observations if status == "computed" else None
            ),
        },
        notes=(
            "Phase identities and fraction ranges are caller-owned and are not embedded material or welding acceptance rules.",
            "Measured phase fractions and uncertainty do not predict strength, toughness, corrosion resistance, cracking or service life.",
            "Unmeasured phases are not inferred from the remainder to one.",
        ),
    )


def specifications():
    def same_identity(x, context):
        if (x.asset_id, x.location_id) != (context.asset_id, context.location_id):
            raise ValueError("microstructure asset and location must match the run context")

    return [
        ModelSpec(
            "materials.phase_microstructure_assessment",
            PhaseMicrostructureAssessment,
            phase_microstructure_assessment,
            {
                "assessment_id": "1",
                "comparison_rows": "mixed",
                "invalid_observation_ids": "1",
                "missing_requirement_observation_ids": "1",
                "outside_declared_range_observation_ids": "1",
                "missing_reviews": "1",
                "all_observations_within_declared_ranges": "1",
            },
            (
                "Every phase fraction and expanded uncertainty is a reviewed measurement on an explicit sample and region.",
                "Caller-owned ranges are compared without inferring unmeasured phase balance or material properties.",
            ),
            ("declared_phase_fraction_evidence_comparison",),
            context_validator=same_identity,
        )
    ]
