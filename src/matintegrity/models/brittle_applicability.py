"""Brittle-behavior test evidence routed through caller-owned applicability envelopes."""

from __future__ import annotations

import math
from collections import defaultdict
from typing import Literal

from pydantic import Field, model_validator

from ..contracts import Calculation, Contract, Evidence, Nonnegative, Positive
from ..registry import ModelSpec

Digest = str
TestKind = Literal["impact", "toughness", "user_defined"]


class BrittleTestEvidenceRecord(Contract):
    record_id: str = Field(min_length=1)
    physical_specimen_id: str = Field(min_length=1)
    source_group_id: str = Field(min_length=1)
    independence_group_id: str = Field(min_length=1)
    test_kind: TestKind
    result_name: str = Field(min_length=1)
    result_value: float | None = None
    result_unit_token: str = Field(min_length=1)
    expanded_uncertainty: Nonnegative | None = None
    uncertainty_coverage_factor: Positive | None = None
    test_temperature_K: Positive | None = None
    specimen_orientation_id: str = Field(min_length=1)
    specimen_thickness_m: Positive
    method_id: str = Field(min_length=1)
    provider_id: str = Field(min_length=1)
    provider_version: str = Field(min_length=1)
    configuration_digest: Digest = Field(pattern=r"^[a-f0-9]{64}$")
    data_digest: Digest = Field(pattern=r"^[a-f0-9]{64}$")
    result_digest: Digest | None = Field(default=None, pattern=r"^[a-f0-9]{64}$")
    record_valid: bool
    invalid_basis: str | None = None
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def coherent_record(self):
        required = (
            self.result_value,
            self.expanded_uncertainty,
            self.uncertainty_coverage_factor,
            self.test_temperature_K,
            self.result_digest,
        )
        if self.record_valid and any(value is None for value in required):
            raise ValueError(
                "a valid brittle-test record requires result, uncertainty, temperature and result digest"
            )
        if self.result_value is not None and not math.isfinite(self.result_value):
            raise ValueError("brittle-test result must be finite")
        if not self.record_valid and not self.invalid_basis:
            raise ValueError("an invalid brittle-test record requires a basis")
        return self


class BrittleTestEvidenceRequirement(Contract):
    requirement_id: str = Field(min_length=1)
    test_kind: TestKind
    result_name: str = Field(min_length=1)
    result_unit_token: str = Field(min_length=1)
    applicable_orientation_ids: tuple[str, ...] = Field(min_length=1)
    minimum_test_temperature_K: Positive
    maximum_test_temperature_K: Positive
    minimum_record_count: int = Field(ge=1)
    requirement_basis: str = Field(min_length=1)

    @model_validator(mode="after")
    def ordered_unique_support(self):
        if self.maximum_test_temperature_K < self.minimum_test_temperature_K:
            raise ValueError("brittle-test temperature bounds must be ordered")
        if len(self.applicable_orientation_ids) != len(set(self.applicable_orientation_ids)):
            raise ValueError("test-requirement orientation identifiers must be unique")
        return self


class BrittleApplicabilityEnvelope(Contract):
    envelope_id: str = Field(min_length=1)
    material_specification_id: str = Field(min_length=1)
    product_form_id: str = Field(min_length=1)
    material_condition_id: str = Field(min_length=1)
    minimum_thickness_m: Positive
    maximum_thickness_m: Positive
    minimum_supported_service_temperature_K: Positive
    maximum_supported_service_temperature_K: Positive
    applicable_orientation_ids: tuple[str, ...] = Field(min_length=1)
    loading_descriptors: tuple[str, ...] = Field(min_length=1)
    loading_rate_descriptors: tuple[str, ...] = Field(min_length=1)
    evidence_requirements: tuple[BrittleTestEvidenceRequirement, ...] = Field(min_length=1)
    provider_id: str = Field(min_length=1)
    provider_version: str = Field(min_length=1)
    configuration_digest: Digest = Field(pattern=r"^[a-f0-9]{64}$")
    data_digest: Digest = Field(pattern=r"^[a-f0-9]{64}$")
    result_digest: Digest = Field(pattern=r"^[a-f0-9]{64}$")
    applicability_basis: str = Field(min_length=1)
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def ordered_unique_envelope(self):
        if self.maximum_thickness_m < self.minimum_thickness_m:
            raise ValueError("brittle-applicability thickness bounds must be ordered")
        if self.maximum_supported_service_temperature_K < self.minimum_supported_service_temperature_K:
            raise ValueError("brittle-applicability service-temperature bounds must be ordered")
        for values, label in (
            (self.applicable_orientation_ids, "orientation"),
            (self.loading_descriptors, "loading"),
            (self.loading_rate_descriptors, "loading-rate"),
            ([row.requirement_id for row in self.evidence_requirements], "requirement"),
        ):
            if len(values) != len(set(values)):
                raise ValueError(f"brittle-applicability {label} identifiers must be unique")
        return self


class BrittleApplicabilityEvidenceAssessment(Contract):
    assessment_id: str = Field(min_length=1)
    asset_id: str = Field(min_length=1)
    location_id: str = Field(min_length=1)
    material_id: str = Field(min_length=1)
    material_specification_id: str = Field(min_length=1)
    product_form_id: str = Field(min_length=1)
    material_condition_id: str = Field(min_length=1)
    governing_thickness_m: Positive
    governing_orientation_id: str = Field(min_length=1)
    minimum_service_temperature_K: Positive
    loading_descriptor: str = Field(min_length=1)
    loading_rate_descriptor: str = Field(min_length=1)
    test_records: tuple[BrittleTestEvidenceRecord, ...] = Field(min_length=1)
    candidate_envelopes: tuple[BrittleApplicabilityEnvelope, ...] = Field(min_length=1)
    material_specification_and_condition_reviewed: bool
    product_form_thickness_and_orientation_reviewed: bool
    service_temperature_reviewed: bool
    loading_and_rate_descriptors_reviewed: bool
    specimen_and_source_group_partitions_reviewed: bool
    method_and_units_reviewed: bool
    uncertainty_basis_reviewed: bool
    provider_and_digest_lineage_reviewed: bool
    applicability_envelope_authority_reviewed: bool
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def unique_records_and_envelopes(self):
        for values, label in (
            ([row.record_id for row in self.test_records], "test-record"),
            ([row.envelope_id for row in self.candidate_envelopes], "envelope"),
        ):
            if len(values) != len(set(values)):
                raise ValueError(f"brittle-applicability {label} identifiers must be unique")
        specimen_groups: dict[str, tuple[str, str]] = {}
        for row in self.test_records:
            groups = (row.source_group_id, row.independence_group_id)
            previous = specimen_groups.setdefault(row.physical_specimen_id, groups)
            if previous != groups:
                raise ValueError("one physical specimen cannot cross source or independence groups")
        return self


def _identity(envelope: BrittleApplicabilityEnvelope):
    return (
        envelope.material_specification_id,
        envelope.product_form_id,
        envelope.material_condition_id,
    )


def brittle_applicability_evidence(x: BrittleApplicabilityEvidenceAssessment) -> Calculation:
    missing_reviews = [
        name
        for name in (
            "material_specification_and_condition_reviewed",
            "product_form_thickness_and_orientation_reviewed",
            "service_temperature_reviewed",
            "loading_and_rate_descriptors_reviewed",
            "specimen_and_source_group_partitions_reviewed",
            "method_and_units_reviewed",
            "uncertainty_basis_reviewed",
            "provider_and_digest_lineage_reviewed",
            "applicability_envelope_authority_reviewed",
        )
        if not getattr(x, name)
    ]
    invalid = [row.record_id for row in x.test_records if not row.record_valid]
    target_identity = (
        x.material_specification_id,
        x.product_form_id,
        x.material_condition_id,
    )
    identity_matches = [row for row in x.candidate_envelopes if _identity(row) == target_identity]
    supported = [
        row
        for row in identity_matches
        if row.minimum_thickness_m <= x.governing_thickness_m <= row.maximum_thickness_m
        and row.minimum_supported_service_temperature_K
        <= x.minimum_service_temperature_K
        <= row.maximum_supported_service_temperature_K
        and x.governing_orientation_id in row.applicable_orientation_ids
        and x.loading_descriptor in row.loading_descriptors
        and x.loading_rate_descriptor in row.loading_rate_descriptors
    ]
    selection = {
        "assessment_id": x.assessment_id,
        "identity_matching_envelope_ids": [row.envelope_id for row in identity_matches],
        "supported_envelope_ids": [row.envelope_id for row in supported],
        "invalid_test_record_ids": invalid,
        "missing_reviews": missing_reviews,
    }
    if missing_reviews or invalid or not identity_matches or len(supported) > 1:
        return Calculation(
            status="needs_data",
            values=selection,
            notes=("A unique reviewed caller-owned applicability envelope and valid records are required.",),
        )
    if not supported:
        return Calculation(
            status="out_of_scope",
            values=selection,
            notes=("The declared service case is outside the matching caller-owned envelope.",),
        )

    envelope = supported[0]
    requirement_rows = []
    missing_requirements = []
    used_record_ids = set()
    for requirement in envelope.evidence_requirements:
        matches = [
            row
            for row in x.test_records
            if row.test_kind == requirement.test_kind
            and row.result_name == requirement.result_name
            and row.result_unit_token == requirement.result_unit_token
            and row.specimen_orientation_id in requirement.applicable_orientation_ids
            and requirement.minimum_test_temperature_K
            <= row.test_temperature_K
            <= requirement.maximum_test_temperature_K
        ]
        used_record_ids.update(row.record_id for row in matches)
        sufficient = len(matches) >= requirement.minimum_record_count
        if not sufficient:
            missing_requirements.append(requirement.requirement_id)
        requirement_rows.append(
            {
                "requirement_id": requirement.requirement_id,
                "matching_record_ids": [row.record_id for row in matches],
                "matching_physical_specimen_ids": sorted({row.physical_specimen_id for row in matches}),
                "matching_source_group_ids": sorted({row.source_group_id for row in matches}),
                "matching_independence_group_ids": sorted({row.independence_group_id for row in matches}),
                "minimum_record_count": requirement.minimum_record_count,
                "record_count_sufficient": sufficient,
            }
        )

    partitions = defaultdict(list)
    for row in x.test_records:
        partitions[(row.source_group_id, row.independence_group_id)].append(row.record_id)
    partition_rows = [
        {
            "source_group_id": source_group_id,
            "independence_group_id": independence_group_id,
            "record_ids": sorted(record_ids),
        }
        for (source_group_id, independence_group_id), record_ids in sorted(partitions.items())
    ]
    evidence_rows = [
        {
            "record_id": row.record_id,
            "physical_specimen_id": row.physical_specimen_id,
            "source_group_id": row.source_group_id,
            "independence_group_id": row.independence_group_id,
            "test_kind": row.test_kind,
            "result_name": row.result_name,
            "result_value": row.result_value,
            "result_unit_token": row.result_unit_token,
            "expanded_uncertainty": row.expanded_uncertainty,
            "uncertainty_coverage_factor": row.uncertainty_coverage_factor,
            "test_temperature_K": row.test_temperature_K,
            "specimen_orientation_id": row.specimen_orientation_id,
            "specimen_thickness_m": row.specimen_thickness_m,
        }
        for row in x.test_records
    ]
    status = "needs_data" if missing_requirements else "computed"
    return Calculation(
        status=status,
        values={
            "assessment_id": x.assessment_id,
            "selected_envelope_id": envelope.envelope_id,
            "test_evidence_summary": evidence_rows,
            "evidence_requirement_summary": requirement_rows,
            "source_and_independence_group_partitions": partition_rows,
            "unused_test_record_ids": sorted(
                row.record_id for row in x.test_records if row.record_id not in used_record_ids
            ),
            "missing_evidence_requirement_ids": missing_requirements,
        },
        notes=(
            "Result values and expanded uncertainties remain evidence records and are not compared with hidden acceptance thresholds.",
            "Physical specimens, source groups and independence groups are reported without statistical pooling.",
            "No code exemption curve, reference-temperature conversion, fracture response, life or probability is calculated.",
        ),
    )


def specifications():
    def same_identity(x, context):
        if (x.asset_id, x.location_id) != (context.asset_id, context.location_id):
            raise ValueError("brittle-applicability asset and location must match the run context")

    return [
        ModelSpec(
            "materials.brittle_applicability_evidence",
            BrittleApplicabilityEvidenceAssessment,
            brittle_applicability_evidence,
            {
                "assessment_id": "1",
                "selected_envelope_id": "1",
                "test_evidence_summary": "mixed",
                "evidence_requirement_summary": "mixed",
                "source_and_independence_group_partitions": "mixed",
                "unused_test_record_ids": "1",
                "missing_evidence_requirement_ids": "1",
            },
            (
                "Material, product form, condition, thickness, orientation and service descriptors are reviewed caller identities.",
                "Every test value carries an exact unit token, expanded uncertainty and immutable provider lineage.",
            ),
            ("reviewed_brittle_test_applicability_evidence",),
            context_validator=same_identity,
        )
    ]
