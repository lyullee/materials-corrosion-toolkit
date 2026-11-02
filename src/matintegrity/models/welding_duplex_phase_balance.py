"""Duplex-weld phase records compared with caller-owned regional envelopes."""

from __future__ import annotations

from collections import defaultdict
from typing import Literal

from pydantic import Field, model_validator

from ..contracts import Calculation, Contract, Evidence, Fraction, Positive
from ..registry import ModelSpec

RegionKind = Literal["weld_metal", "heat_affected_zone", "base_material"]


class DuplexPhaseObservation(Contract):
    observation_id: str = Field(min_length=1)
    sample_id: str = Field(min_length=1)
    region_id: str = Field(min_length=1)
    region_kind: RegionKind
    phase_id: str = Field(min_length=1)
    fraction_definition: Literal["volume_fraction"]
    measured_fraction: Fraction | None = None
    expanded_uncertainty_fraction: Fraction | None = None
    uncertainty_coverage_factor: Positive | None = None
    method_id: str = Field(min_length=1)
    method_provider_id: str = Field(min_length=1)
    method_provider_version: str = Field(min_length=1)
    method_state_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    record_state_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    record_valid: bool
    invalid_basis: str | None = None
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def coherent_measurement(self):
        required = (
            self.measured_fraction,
            self.expanded_uncertainty_fraction,
            self.uncertainty_coverage_factor,
        )
        if self.record_valid and any(value is None for value in required):
            raise ValueError(
                "a valid duplex phase observation requires value, expanded uncertainty and coverage factor"
            )
        if not self.record_valid and not self.invalid_basis:
            raise ValueError("an invalid duplex phase observation requires a basis")
        return self


class DuplexRegionalPhaseRange(Contract):
    range_id: str = Field(min_length=1)
    region_id: str = Field(min_length=1)
    region_kind: RegionKind
    phase_id: str = Field(min_length=1)
    fraction_definition: Literal["volume_fraction"]
    minimum_fraction: Fraction
    maximum_fraction: Fraction
    range_basis: str = Field(min_length=1)
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def ordered_range(self):
        if self.maximum_fraction < self.minimum_fraction:
            raise ValueError("duplex phase-fraction bounds must be ordered")
        return self


class DuplexPhaseEnvelope(Contract):
    envelope_id: str = Field(min_length=1)
    material_condition_id: str = Field(min_length=1)
    welding_process_id: str = Field(min_length=1)
    process_history_id: str = Field(min_length=1)
    heat_history_id: str = Field(min_length=1)
    regional_ranges: tuple[DuplexRegionalPhaseRange, ...] = Field(min_length=1)
    envelope_provider_id: str = Field(min_length=1)
    envelope_provider_version: str = Field(min_length=1)
    envelope_state_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    applicability_basis: str = Field(min_length=1)
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def unique_ranges(self):
        identifiers = [row.range_id for row in self.regional_ranges]
        if len(identifiers) != len(set(identifiers)):
            raise ValueError("duplex phase-range identifiers must be unique within an envelope")
        keys = [
            (row.region_id, row.region_kind, row.phase_id, row.fraction_definition)
            for row in self.regional_ranges
        ]
        if len(keys) != len(set(keys)):
            raise ValueError("declare at most one duplex phase range for each regional key")
        return self


class DuplexPhaseBalanceAssessment(Contract):
    assessment_id: str = Field(min_length=1)
    asset_id: str = Field(min_length=1)
    location_id: str = Field(min_length=1)
    weld_id: str = Field(min_length=1)
    material_condition_id: str = Field(min_length=1)
    welding_process_id: str = Field(min_length=1)
    process_history_id: str = Field(min_length=1)
    heat_history_id: str = Field(min_length=1)
    observations: tuple[DuplexPhaseObservation, ...] = Field(min_length=1)
    candidate_envelopes: tuple[DuplexPhaseEnvelope, ...] = Field(min_length=1)
    weld_and_region_mapping_reviewed: bool
    material_and_process_identity_reviewed: bool
    heat_history_identity_reviewed: bool
    phase_and_fraction_definitions_reviewed: bool
    method_applicability_reviewed: bool
    uncertainty_basis_reviewed: bool
    provider_state_digests_reviewed: bool
    envelope_authority_reviewed: bool
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def unique_and_bounded(self):
        observation_ids = [row.observation_id for row in self.observations]
        if len(observation_ids) != len(set(observation_ids)):
            raise ValueError("duplex phase-observation identifiers must be unique")
        envelope_ids = [row.envelope_id for row in self.candidate_envelopes]
        if len(envelope_ids) != len(set(envelope_ids)):
            raise ValueError("duplex phase-envelope identifiers must be unique")
        region_kinds: dict[str, RegionKind] = {}
        sums = defaultdict(float)
        for row in self.observations:
            known_kind = region_kinds.setdefault(row.region_id, row.region_kind)
            if known_kind != row.region_kind:
                raise ValueError("one region identifier cannot have multiple region kinds")
            if row.record_valid:
                sums[(row.sample_id, row.region_id)] += row.measured_fraction
        if any(total > 1.0 + 1e-12 for total in sums.values()):
            raise ValueError("nominal phase fractions for one sample and region cannot exceed one")
        return self


def _identity(envelope: DuplexPhaseEnvelope):
    return (
        envelope.material_condition_id,
        envelope.welding_process_id,
        envelope.process_history_id,
        envelope.heat_history_id,
    )


def duplex_phase_balance(x: DuplexPhaseBalanceAssessment) -> Calculation:
    missing_reviews = [
        name
        for name in (
            "weld_and_region_mapping_reviewed",
            "material_and_process_identity_reviewed",
            "heat_history_identity_reviewed",
            "phase_and_fraction_definitions_reviewed",
            "method_applicability_reviewed",
            "uncertainty_basis_reviewed",
            "provider_state_digests_reviewed",
            "envelope_authority_reviewed",
        )
        if not getattr(x, name)
    ]
    invalid = [row.observation_id for row in x.observations if not row.record_valid]
    target_identity = (
        x.material_condition_id,
        x.welding_process_id,
        x.process_history_id,
        x.heat_history_id,
    )
    identity_matches = [row for row in x.candidate_envelopes if _identity(row) == target_identity]
    if missing_reviews or invalid or len(identity_matches) != 1:
        return Calculation(
            status="needs_data",
            values={
                "assessment_id": x.assessment_id,
                "identity_matching_envelope_ids": [row.envelope_id for row in identity_matches],
                "invalid_observation_ids": invalid,
                "missing_reviews": missing_reviews,
            },
            notes=("A unique reviewed caller-owned phase envelope and valid records are required.",),
        )

    envelope = identity_matches[0]
    ranges = {
        (row.region_id, row.region_kind, row.phase_id, row.fraction_definition): row
        for row in envelope.regional_ranges
    }
    observations_by_key = defaultdict(list)
    for observation in x.observations:
        key = (
            observation.region_id,
            observation.region_kind,
            observation.phase_id,
            observation.fraction_definition,
        )
        observations_by_key[key].append(observation)

    missing_range_observations = [
        row.observation_id
        for row in x.observations
        if (
            row.region_id,
            row.region_kind,
            row.phase_id,
            row.fraction_definition,
        )
        not in ranges
    ]
    missing_observation_ranges = [row.range_id for key, row in ranges.items() if not observations_by_key[key]]
    comparison_rows = []
    outside = []
    for key, phase_range in ranges.items():
        for observation in observations_by_key[key]:
            lower = max(0.0, observation.measured_fraction - observation.expanded_uncertainty_fraction)
            upper = min(1.0, observation.measured_fraction + observation.expanded_uncertainty_fraction)
            within = lower >= phase_range.minimum_fraction and upper <= phase_range.maximum_fraction
            if not within:
                outside.append(observation.observation_id)
            comparison_rows.append(
                {
                    "range_id": phase_range.range_id,
                    "observation_id": observation.observation_id,
                    "sample_id": observation.sample_id,
                    "region_id": observation.region_id,
                    "region_kind": observation.region_kind,
                    "phase_id": observation.phase_id,
                    "fraction_definition": observation.fraction_definition,
                    "measured_fraction": observation.measured_fraction,
                    "expanded_uncertainty_fraction": observation.expanded_uncertainty_fraction,
                    "uncertainty_coverage_factor": observation.uncertainty_coverage_factor,
                    "uncertainty_interval_fraction": [lower, upper],
                    "within_declared_phase_envelope": within,
                }
            )

    status = "needs_data" if missing_range_observations or missing_observation_ranges else "computed"
    return Calculation(
        status=status,
        values={
            "assessment_id": x.assessment_id,
            "selected_envelope_id": envelope.envelope_id,
            "comparison_rows": comparison_rows,
            "missing_range_observation_ids": missing_range_observations,
            "missing_observation_range_ids": missing_observation_ranges,
            "outside_declared_envelope_observation_ids": outside,
            "all_uncertainty_intervals_within_declared_phase_envelope": (
                not outside if status == "computed" else None
            ),
        },
        notes=(
            "Each expanded uncertainty interval is compared with an exact caller-declared region, phase and volume-fraction range.",
            "No unmeasured phase is inferred, and the comparison does not predict properties, corrosion, cracking or service life.",
            "The result is not a welding-code or production acceptance decision.",
        ),
    )


def specifications():
    def same_identity(x, context):
        if (x.asset_id, x.location_id) != (context.asset_id, context.location_id):
            raise ValueError("duplex phase-balance asset and location must match the run context")

    return [
        ModelSpec(
            "welding.duplex_phase_balance",
            DuplexPhaseBalanceAssessment,
            duplex_phase_balance,
            {
                "assessment_id": "1",
                "selected_envelope_id": "1",
                "comparison_rows": "mixed",
                "missing_range_observation_ids": "1",
                "missing_observation_range_ids": "1",
                "outside_declared_envelope_observation_ids": "1",
                "all_uncertainty_intervals_within_declared_phase_envelope": "1",
            },
            (
                "Region, material, welding-process and thermal-history identities are reviewed caller records.",
                "Measured volume fractions and expanded uncertainties use an explicit method and immutable provider-state identifiers.",
            ),
            ("reviewed_duplex_weld_phase_envelope_comparison",),
            context_validator=same_identity,
        )
    ]
