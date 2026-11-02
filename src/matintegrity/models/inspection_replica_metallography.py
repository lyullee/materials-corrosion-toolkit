"""Replica-metallography evidence mapped to caller-owned observation envelopes."""

from __future__ import annotations

from typing import Literal

from pydantic import Field, model_validator

from ..contracts import Calculation, Contract, Evidence, Nonnegative, Positive
from ..registry import ModelSpec


class ReplicaSiteRecord(Contract):
    replica_site_id: str = Field(min_length=1)
    physical_source_group_id: str = Field(min_length=1)
    location_definition: str = Field(min_length=1)
    replicated_area_m2: Positive
    surface_preparation_id: str = Field(min_length=1)
    surface_preparation_description: str = Field(min_length=1)
    surface_preparation_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    preparation_record_valid: bool
    invalid_preparation_basis: str | None = None
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def invalid_preparation_explained(self):
        if not self.preparation_record_valid and not self.invalid_preparation_basis:
            raise ValueError("an invalid replica preparation record requires a basis")
        return self


class ReplicaProviderQualification(Contract):
    qualification_id: str = Field(min_length=1)
    calibration_dataset_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    holdout_dataset_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    calibration_physical_source_group_count: int = Field(ge=1)
    holdout_physical_source_group_count: int = Field(ge=1)
    calibration_and_holdout_independent: bool
    validation_metric_definition: str = Field(min_length=1)
    validation_metric_value: Nonnegative
    validation_metric_unit: str = Field(min_length=1)
    maximum_supported_validation_metric: Positive
    qualification_basis: str = Field(min_length=1)
    evidence: tuple[Evidence, ...] = Field(min_length=1)


class CallerReplicaObservationEnvelope(Contract):
    envelope_id: str = Field(min_length=1)
    method_id: str = Field(min_length=1)
    microscope_id: str = Field(min_length=1)
    microscope_configuration_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    provider_id: str = Field(min_length=1)
    provider_version: str = Field(min_length=1)
    provider_state_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    supported_morphology_descriptors: tuple[str, ...] = Field(min_length=1)
    metric_definition: str = Field(min_length=1)
    unit: str = Field(min_length=1)
    minimum_supported_value: float
    maximum_supported_value: float
    maximum_supported_expanded_uncertainty: Nonnegative
    minimum_supported_replicated_area_m2: Positive
    maximum_supported_replicated_area_m2: Positive
    applicability_basis: str = Field(min_length=1)
    provider_qualification: ReplicaProviderQualification
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def ordered_support(self):
        if len(set(self.supported_morphology_descriptors)) != len(self.supported_morphology_descriptors):
            raise ValueError("supported replica morphology descriptors must be unique")
        if self.maximum_supported_value < self.minimum_supported_value:
            raise ValueError("replica metric support bounds must be ordered")
        if self.maximum_supported_replicated_area_m2 < self.minimum_supported_replicated_area_m2:
            raise ValueError("replica-area support bounds must be ordered")
        return self


class ReplicaMicrostructureObservation(Contract):
    observation_id: str = Field(min_length=1)
    replica_site_id: str = Field(min_length=1)
    partition: Literal["calibration", "holdout", "application"]
    physical_source_group_id: str = Field(min_length=1)
    method_id: str = Field(min_length=1)
    microscope_id: str = Field(min_length=1)
    microscope_configuration_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    provider_id: str = Field(min_length=1)
    provider_version: str = Field(min_length=1)
    provider_state_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    morphology_descriptor: str | None = None
    metric_definition: str | None = None
    observed_value: float | None = None
    expanded_uncertainty: Nonnegative | None = None
    coverage_factor: Positive | None = None
    unit: str | None = None
    uncertainty_basis: str | None = None
    result_digest: str | None = Field(default=None, pattern=r"^[a-f0-9]{64}$")
    record_available: bool
    missing_basis: str | None = None
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def coherent_record(self):
        result_fields = (
            self.morphology_descriptor,
            self.metric_definition,
            self.observed_value,
            self.expanded_uncertainty,
            self.coverage_factor,
            self.unit,
            self.uncertainty_basis,
            self.result_digest,
        )
        if self.record_available and any(value is None for value in result_fields):
            raise ValueError("an available replica observation requires morphology, metric and uncertainty")
        if not self.record_available and not self.missing_basis:
            raise ValueError("an unavailable replica observation requires a missingness basis")
        if not self.record_available and any(value is not None for value in result_fields):
            raise ValueError("an unavailable replica observation cannot carry observation results")
        return self


class ReplicaMetallographyEvidenceAssessment(Contract):
    assessment_id: str = Field(min_length=1)
    asset_id: str = Field(min_length=1)
    location_id: str = Field(min_length=1)
    component_id: str = Field(min_length=1)
    material_condition_id: str = Field(min_length=1)
    replica_sites: tuple[ReplicaSiteRecord, ...] = Field(min_length=1)
    observations: tuple[ReplicaMicrostructureObservation, ...] = Field(min_length=1)
    candidate_envelopes: tuple[CallerReplicaObservationEnvelope, ...] = Field(min_length=1)
    component_material_and_locations_reviewed: bool
    physical_source_groups_reviewed: bool
    surface_preparation_records_reviewed: bool
    method_and_microscope_configuration_reviewed: bool
    provider_identity_and_state_reviewed: bool
    morphology_and_metric_definitions_reviewed: bool
    units_and_uncertainty_reviewed: bool
    result_digests_and_missingness_reviewed: bool
    calibration_and_holdout_reviewed: bool
    caller_envelope_authority_reviewed: bool
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def linked_records(self):
        site_ids = [row.replica_site_id for row in self.replica_sites]
        observation_ids = [row.observation_id for row in self.observations]
        envelope_ids = [row.envelope_id for row in self.candidate_envelopes]
        for values, name in (
            (site_ids, "replica site"),
            (observation_ids, "replica observation"),
            (envelope_ids, "replica envelope"),
        ):
            if len(values) != len(set(values)):
                raise ValueError(f"{name} identifiers must be unique")
        sites = {row.replica_site_id: row for row in self.replica_sites}
        for observation in self.observations:
            site = sites.get(observation.replica_site_id)
            if site is None:
                raise ValueError("every replica observation must reference a declared site")
            if observation.physical_source_group_id != site.physical_source_group_id:
                raise ValueError("replica observation and site physical-source groups must match")
        partitions: dict[str, set[str]] = {}
        for observation in self.observations:
            partitions.setdefault(observation.partition, set()).add(observation.physical_source_group_id)
        if partitions.get("calibration", set()) & partitions.get("holdout", set()):
            raise ValueError("replica calibration and holdout physical-source groups must be disjoint")
        return self


def _provider_identity(row):
    return (
        row.method_id,
        row.microscope_id,
        row.microscope_configuration_digest,
        row.provider_id,
        row.provider_version,
        row.provider_state_digest,
    )


def replica_metallography_evidence(x: ReplicaMetallographyEvidenceAssessment) -> Calculation:
    missing_reviews = [
        name
        for name in (
            "component_material_and_locations_reviewed",
            "physical_source_groups_reviewed",
            "surface_preparation_records_reviewed",
            "method_and_microscope_configuration_reviewed",
            "provider_identity_and_state_reviewed",
            "morphology_and_metric_definitions_reviewed",
            "units_and_uncertainty_reviewed",
            "result_digests_and_missingness_reviewed",
            "calibration_and_holdout_reviewed",
            "caller_envelope_authority_reviewed",
        )
        if not getattr(x, name)
    ]
    sites = {row.replica_site_id: row for row in x.replica_sites}
    envelopes_by_identity: dict[tuple[str, ...], list[CallerReplicaObservationEnvelope]] = {}
    invalid_qualification_envelope_ids = []
    for envelope in x.candidate_envelopes:
        envelopes_by_identity.setdefault(_provider_identity(envelope), []).append(envelope)
        qualification = envelope.provider_qualification
        if (
            not qualification.calibration_and_holdout_independent
            or qualification.validation_metric_value > qualification.maximum_supported_validation_metric
        ):
            invalid_qualification_envelope_ids.append(envelope.envelope_id)

    unavailable_observation_ids = []
    unmatched_observation_ids = []
    ambiguous_observation_ids = []
    comparison_rows = []
    for observation in x.observations:
        if not observation.record_available:
            unavailable_observation_ids.append(observation.observation_id)
            continue
        candidates = envelopes_by_identity.get(_provider_identity(observation), [])
        exact = [
            row
            for row in candidates
            if observation.metric_definition == row.metric_definition and observation.unit == row.unit
        ]
        if not exact:
            unmatched_observation_ids.append(observation.observation_id)
            continue
        if len(exact) != 1:
            ambiguous_observation_ids.append(observation.observation_id)
            continue
        envelope = exact[0]
        site = sites[observation.replica_site_id]
        morphology_supported = observation.morphology_descriptor in envelope.supported_morphology_descriptors
        value_supported = (
            envelope.minimum_supported_value <= observation.observed_value <= envelope.maximum_supported_value
        )
        uncertainty_supported = (
            observation.expanded_uncertainty <= envelope.maximum_supported_expanded_uncertainty
        )
        area_supported = (
            envelope.minimum_supported_replicated_area_m2
            <= site.replicated_area_m2
            <= envelope.maximum_supported_replicated_area_m2
        )
        qualification_supported = envelope.envelope_id not in invalid_qualification_envelope_ids
        comparison_rows.append(
            {
                "observation_id": observation.observation_id,
                "partition": observation.partition,
                "replica_site_id": observation.replica_site_id,
                "physical_source_group_id": observation.physical_source_group_id,
                "envelope_id": envelope.envelope_id,
                "morphology_descriptor": observation.morphology_descriptor,
                "morphology_descriptor_supported": morphology_supported,
                "observed_value": observation.observed_value,
                "expanded_uncertainty": observation.expanded_uncertainty,
                "uncertainty_interval_minimum": observation.observed_value - observation.expanded_uncertainty,
                "uncertainty_interval_maximum": observation.observed_value + observation.expanded_uncertainty,
                "unit": observation.unit,
                "value_within_declared_support": value_supported,
                "uncertainty_within_declared_support": uncertainty_supported,
                "replicated_area_within_declared_support": area_supported,
                "provider_qualification_supported": qualification_supported,
                "observation_within_declared_envelope": (
                    morphology_supported
                    and value_supported
                    and uncertainty_supported
                    and area_supported
                    and qualification_supported
                ),
            }
        )

    invalid_preparation_site_ids = [
        row.replica_site_id for row in x.replica_sites if not row.preparation_record_valid
    ]
    incomplete = (
        missing_reviews
        or invalid_preparation_site_ids
        or unavailable_observation_ids
        or unmatched_observation_ids
        or ambiguous_observation_ids
        or invalid_qualification_envelope_ids
    )
    application_rows = [row for row in comparison_rows if row["partition"] == "application"]
    return Calculation(
        status="needs_data" if incomplete else "computed",
        values={
            "assessment_id": x.assessment_id,
            "component_id": x.component_id,
            "material_condition_id": x.material_condition_id,
            "replica_site_count": len(x.replica_sites),
            "total_replicated_area_m2": sum(row.replicated_area_m2 for row in x.replica_sites),
            "invalid_preparation_site_ids": invalid_preparation_site_ids,
            "observation_count": len(x.observations),
            "partition_counts": {
                partition: sum(row.partition == partition for row in x.observations)
                for partition in ("calibration", "holdout", "application")
            },
            "unavailable_observation_ids": unavailable_observation_ids,
            "unmatched_observation_ids": unmatched_observation_ids,
            "ambiguous_observation_ids": ambiguous_observation_ids,
            "invalid_qualification_envelope_ids": sorted(set(invalid_qualification_envelope_ids)),
            "observation_comparisons": comparison_rows,
            "all_application_observations_within_declared_envelopes": bool(application_rows)
            and all(bool(row["observation_within_declared_envelope"]) for row in application_rows),
            "missing_reviews": missing_reviews,
        },
        notes=(
            "Replica location, sampled area, surface preparation, optical configuration and provider state remain explicit evidence lineage.",
            "Morphology labels and metric support are caller-owned evidence descriptors, not fabricated material grades, phases or aging classes.",
            "No damage rate, creep life, remaining life, failure probability or acceptance decision is inferred.",
        ),
    )


def specifications():
    def same_identity(x, context):
        if (x.asset_id, x.location_id) != (context.asset_id, context.location_id):
            raise ValueError("replica-metallography assessment asset and location must match the run context")

    return [
        ModelSpec(
            "inspection.replica_metallography_evidence",
            ReplicaMetallographyEvidenceAssessment,
            replica_metallography_evidence,
            {
                "assessment_id": "1",
                "component_id": "1",
                "material_condition_id": "1",
                "replica_site_count": "1",
                "total_replicated_area_m2": "m^2",
                "invalid_preparation_site_ids": "1",
                "observation_count": "1",
                "partition_counts": "1",
                "unavailable_observation_ids": "1",
                "unmatched_observation_ids": "1",
                "ambiguous_observation_ids": "1",
                "invalid_qualification_envelope_ids": "1",
                "observation_comparisons": "mixed",
                "all_application_observations_within_declared_envelopes": "1",
                "missing_reviews": "1",
            },
            (
                "Replica sites and physical source groups retain caller-reviewed mappings.",
                "Surface preparation, microscope configuration and provider state are traceable by identifiers and digests.",
                "Observation envelopes and qualification limits are supplied and reviewed by the caller.",
            ),
            ("reviewed_replica_metallography_evidence",),
            context_validator=same_identity,
        )
    ]
