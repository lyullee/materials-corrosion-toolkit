"""Partition-safe accounting for caller-qualified fracture-toughness evidence."""

from __future__ import annotations

from collections import defaultdict
from typing import Literal

from pydantic import Field, model_validator

from ..contracts import Calculation, Contract, Evidence, Nonnegative, Positive
from ..registry import ModelSpec

EvidencePartition = Literal["calibration", "holdout", "application"]
EndpointKind = Literal["initiation", "tearing", "arrest", "user_defined"]


class FractureToughnessTestRecord(Contract):
    record_id: str = Field(min_length=1)
    physical_specimen_id: str = Field(min_length=1)
    source_group_id: str = Field(min_length=1)
    partition: EvidencePartition
    material_id: str = Field(min_length=1)
    material_condition_id: str = Field(min_length=1)
    specimen_geometry_id: str = Field(min_length=1)
    specimen_geometry_descriptor: str = Field(min_length=1)
    notch_orientation_id: str = Field(min_length=1)
    crack_orientation_id: str = Field(min_length=1)
    temperature_K: Positive
    load_rate_value: Nonnegative
    load_rate_unit_token: str = Field(min_length=1)
    environment_id: str = Field(min_length=1)
    endpoint_kind: EndpointKind
    endpoint_definition_id: str = Field(min_length=1)
    user_defined_endpoint_description: str | None = None
    reported_value: float | None = None
    reported_unit_token: str = Field(min_length=1)
    expanded_uncertainty: Nonnegative | None = None
    uncertainty_basis: str | None = None
    provider_id: str = Field(min_length=1)
    provider_revision: str = Field(min_length=1)
    provider_state_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    provider_configuration_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    input_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    result_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    caller_validity_record_id: str = Field(min_length=1)
    record_valid: bool
    supports_declared_endpoint: bool
    invalid_or_limiting_basis: str | None = None
    validity_evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def endpoint_value_and_validity(self):
        if self.endpoint_kind == "user_defined" and not self.user_defined_endpoint_description:
            raise ValueError("a user-defined toughness endpoint requires a description")
        if self.endpoint_kind != "user_defined" and self.user_defined_endpoint_description is not None:
            raise ValueError("only a user-defined toughness endpoint can carry a custom description")
        if self.reported_value is None:
            if self.expanded_uncertainty is not None or self.uncertainty_basis is not None:
                raise ValueError("a missing toughness value cannot carry uncertainty")
        elif self.expanded_uncertainty is None or not self.uncertainty_basis:
            raise ValueError("a reported toughness value requires uncertainty and its basis")
        if (
            not self.record_valid or not self.supports_declared_endpoint
        ) and not self.invalid_or_limiting_basis:
            raise ValueError("invalid or endpoint-limited toughness evidence requires a basis")
        return self


class FractureToughnessEvidenceAssessment(Contract):
    evidence_collection_id: str = Field(min_length=1)
    asset_id: str = Field(min_length=1)
    location_id: str = Field(min_length=1)
    records: tuple[FractureToughnessTestRecord, ...] = Field(min_length=1)
    required_partitions: tuple[EvidencePartition, ...] = Field(min_length=1)
    material_and_condition_identity_reviewed: bool
    physical_specimen_identity_reviewed: bool
    source_group_and_partition_reviewed: bool
    geometry_and_orientation_reviewed: bool
    temperature_rate_and_environment_reviewed: bool
    endpoint_units_and_uncertainty_reviewed: bool
    caller_validity_evidence_reviewed: bool
    provider_lineage_and_digests_reviewed: bool

    @model_validator(mode="after")
    def identities_and_partitions(self):
        record_ids = [row.record_id for row in self.records]
        validity_ids = [row.caller_validity_record_id for row in self.records]
        if len(set(record_ids)) != len(record_ids):
            raise ValueError("fracture-toughness record identifiers must be unique")
        if len(set(validity_ids)) != len(validity_ids):
            raise ValueError("caller validity-record identifiers must be unique")
        if len(set(self.required_partitions)) != len(self.required_partitions):
            raise ValueError("required fracture-toughness partitions must be unique")

        specimen_partitions = defaultdict(set)
        source_partitions = defaultdict(set)
        for row in self.records:
            specimen_partitions[row.physical_specimen_id].add(row.partition)
            source_partitions[row.source_group_id].add(row.partition)
        leaking_specimens = sorted(
            identifier for identifier, partitions in specimen_partitions.items() if len(partitions) > 1
        )
        leaking_sources = sorted(
            identifier for identifier, partitions in source_partitions.items() if len(partitions) > 1
        )
        if leaking_specimens:
            raise ValueError(f"physical specimens cannot cross evidence partitions: {leaking_specimens}")
        if leaking_sources:
            raise ValueError(f"source groups cannot cross evidence partitions: {leaking_sources}")
        return self


def fracture_toughness_test_evidence(x: FractureToughnessEvidenceAssessment) -> Calculation:
    missing_reviews = [
        name
        for name in (
            "material_and_condition_identity_reviewed",
            "physical_specimen_identity_reviewed",
            "source_group_and_partition_reviewed",
            "geometry_and_orientation_reviewed",
            "temperature_rate_and_environment_reviewed",
            "endpoint_units_and_uncertainty_reviewed",
            "caller_validity_evidence_reviewed",
            "provider_lineage_and_digests_reviewed",
        )
        if not getattr(x, name)
    ]
    represented_partitions = {row.partition for row in x.records}
    missing_partitions = [
        partition for partition in x.required_partitions if partition not in represented_partitions
    ]
    invalid_record_ids = [row.record_id for row in x.records if not row.record_valid]
    unsupported_endpoint_record_ids = [
        row.record_id for row in x.records if not row.supports_declared_endpoint
    ]
    missing_value_record_ids = [row.record_id for row in x.records if row.reported_value is None]

    partition_rows = []
    for partition in ("calibration", "holdout", "application"):
        records = [row for row in x.records if row.partition == partition]
        endpoint_groups = defaultdict(list)
        for row in records:
            endpoint_groups[
                (
                    row.endpoint_kind,
                    row.endpoint_definition_id,
                    row.reported_unit_token,
                    row.load_rate_unit_token,
                )
            ].append(row)
        endpoint_rows = []
        for key, grouped in sorted(endpoint_groups.items()):
            endpoint_kind, endpoint_definition_id, unit_token, load_rate_unit_token = key
            endpoint_rows.append(
                {
                    "endpoint_kind": endpoint_kind,
                    "endpoint_definition_id": endpoint_definition_id,
                    "reported_unit_token": unit_token,
                    "load_rate_unit_token": load_rate_unit_token,
                    "record_ids": [row.record_id for row in grouped],
                    "reported_values": [row.reported_value for row in grouped],
                    "expanded_uncertainties": [row.expanded_uncertainty for row in grouped],
                }
            )
        partition_rows.append(
            {
                "partition": partition,
                "record_count": len(records),
                "physical_specimen_ids": sorted({row.physical_specimen_id for row in records}),
                "source_group_ids": sorted({row.source_group_id for row in records}),
                "endpoint_groups": endpoint_rows,
            }
        )

    incomplete = bool(
        missing_reviews
        or missing_partitions
        or invalid_record_ids
        or unsupported_endpoint_record_ids
        or missing_value_record_ids
    )
    return Calculation(
        status="needs_data" if incomplete else "computed",
        values={
            "evidence_collection_id": x.evidence_collection_id,
            "record_count": len(x.records),
            "material_ids": sorted({row.material_id for row in x.records}),
            "material_condition_ids": sorted({row.material_condition_id for row in x.records}),
            "specimen_geometry_ids": sorted({row.specimen_geometry_id for row in x.records}),
            "notch_orientation_ids": sorted({row.notch_orientation_id for row in x.records}),
            "crack_orientation_ids": sorted({row.crack_orientation_id for row in x.records}),
            "environment_ids": sorted({row.environment_id for row in x.records}),
            "required_partitions": list(x.required_partitions),
            "missing_required_partitions": missing_partitions,
            "partition_summaries": partition_rows,
            "invalid_record_ids": invalid_record_ids,
            "unsupported_endpoint_record_ids": unsupported_endpoint_record_ids,
            "missing_value_record_ids": missing_value_record_ids,
            "missing_reviews": missing_reviews,
        },
        notes=(
            "Values, units, endpoint definitions, validity statements and uncertainty are retained exactly as supplied; no conversion or standards validity table is applied.",
            "Calibration, holdout and application partitions remain separate, and neither a physical specimen nor a source group can cross them.",
            "This evidence inventory does not produce an FAD input, design value, life, probability, transferability conclusion or acceptance decision.",
        ),
    )


def specifications():
    def same_identity(x, context):
        if (x.asset_id, x.location_id) != (context.asset_id, context.location_id):
            raise ValueError("fracture-toughness evidence asset and location must match the run context")

    return [
        ModelSpec(
            "inspection.fracture_toughness_test_evidence",
            FractureToughnessEvidenceAssessment,
            fracture_toughness_test_evidence,
            {
                "evidence_collection_id": "1",
                "record_count": "count",
                "material_ids": "1",
                "material_condition_ids": "1",
                "specimen_geometry_ids": "1",
                "notch_orientation_ids": "1",
                "crack_orientation_ids": "1",
                "environment_ids": "1",
                "required_partitions": "1",
                "missing_required_partitions": "1",
                "partition_summaries": "mixed",
                "invalid_record_ids": "1",
                "unsupported_endpoint_record_ids": "1",
                "missing_value_record_ids": "1",
                "missing_reviews": "1",
            },
            (
                "Every record preserves material condition, specimen/source identity, geometry/orientation, test conditions, endpoint, unit and caller-supplied validity evidence.",
                "Provider revision and state/configuration/input/result digests are immutable lineage fields, not physical qualification.",
                "Partitions are caller-declared and no independence beyond enforced specimen and source-group separation is inferred.",
            ),
            ("partitioned_fracture_toughness_test_evidence_accounting",),
            context_validator=same_identity,
        )
    ]
