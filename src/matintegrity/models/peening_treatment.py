"""Peening process and residual-stress evidence against caller envelopes."""

from __future__ import annotations

from pydantic import Field, model_validator

from ..contracts import Calculation, Contract, Evidence, Nonnegative, Positive
from ..registry import ModelSpec


class PeeningTreatmentRecord(Contract):
    treatment_record_id: str = Field(min_length=1)
    zone_id: str = Field(min_length=1)
    method_id: str = Field(min_length=1)
    media_condition_id: str = Field(min_length=1)
    media_lot_id: str = Field(min_length=1)
    equipment_id: str = Field(min_length=1)
    direction_descriptor: str = Field(min_length=1)
    start_time_s: Nonnegative
    end_time_s: Positive
    intensity_metric_definition: str = Field(min_length=1)
    intensity_value: Nonnegative
    intensity_unit_token: str = Field(min_length=1)
    intensity_expanded_uncertainty: Nonnegative
    coverage_metric_definition: str = Field(min_length=1)
    coverage_value: Nonnegative
    coverage_unit_token: str = Field(min_length=1)
    coverage_expanded_uncertainty: Nonnegative
    provider_id: str = Field(min_length=1)
    provider_version: str = Field(min_length=1)
    provider_state_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    result_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    record_valid: bool
    invalid_basis: str | None = None
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def positive_interval_and_basis(self):
        if self.end_time_s <= self.start_time_s:
            raise ValueError("peening treatment interval must have positive duration")
        if not self.record_valid and not self.invalid_basis:
            raise ValueError("an invalid peening record requires a basis")
        return self


class PeeningResidualStressObservation(Contract):
    observation_id: str = Field(min_length=1)
    zone_id: str = Field(min_length=1)
    physical_specimen_id: str = Field(min_length=1)
    source_group_id: str = Field(min_length=1)
    independence_group_id: str = Field(min_length=1)
    partition: str = Field(min_length=1)
    coordinate_frame_id: str = Field(min_length=1)
    stress_component_id: str = Field(min_length=1)
    depth_m: Nonnegative
    method_id: str = Field(min_length=1)
    reported_value: float
    unit_token: str = Field(min_length=1)
    expanded_uncertainty: Nonnegative
    provider_id: str = Field(min_length=1)
    provider_version: str = Field(min_length=1)
    provider_state_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    result_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    record_valid: bool
    invalid_basis: str | None = None
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def invalid_observation_basis(self):
        if not self.record_valid and not self.invalid_basis:
            raise ValueError("an invalid peening stress observation requires a basis")
        return self


class PeeningStressRequirement(Contract):
    requirement_id: str = Field(min_length=1)
    stress_component_id: str = Field(min_length=1)
    method_id: str = Field(min_length=1)
    unit_token: str = Field(min_length=1)
    minimum_depth_m: Nonnegative
    maximum_depth_m: Nonnegative
    minimum_value: float
    maximum_value: float
    minimum_record_count: int = Field(ge=1)
    requirement_basis: str = Field(min_length=1)

    @model_validator(mode="after")
    def ordered_ranges(self):
        if self.maximum_depth_m < self.minimum_depth_m:
            raise ValueError("peening stress depth support must be ordered")
        if self.maximum_value < self.minimum_value:
            raise ValueError("peening stress value support must be ordered")
        return self


class DeclaredPeeningQualificationEnvelope(Contract):
    envelope_id: str = Field(min_length=1)
    material_condition_id: str = Field(min_length=1)
    supported_method_ids: tuple[str, ...] = Field(min_length=1)
    supported_media_condition_ids: tuple[str, ...] = Field(min_length=1)
    supported_direction_descriptors: tuple[str, ...] = Field(min_length=1)
    intensity_metric_definition: str = Field(min_length=1)
    intensity_unit_token: str = Field(min_length=1)
    minimum_intensity_value: Nonnegative
    maximum_intensity_value: Nonnegative
    coverage_metric_definition: str = Field(min_length=1)
    coverage_unit_token: str = Field(min_length=1)
    minimum_coverage_value: Nonnegative
    maximum_coverage_value: Nonnegative
    stress_requirements: tuple[PeeningStressRequirement, ...] = Field(min_length=1)
    minimum_physical_specimen_count: int = Field(ge=1)
    minimum_source_group_count: int = Field(ge=1)
    qualification_basis: str = Field(min_length=1)
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def ordered_unique_support(self):
        if self.maximum_intensity_value < self.minimum_intensity_value:
            raise ValueError("peening intensity support must be ordered")
        if self.maximum_coverage_value < self.minimum_coverage_value:
            raise ValueError("peening coverage support must be ordered")
        for values, label in (
            (self.supported_method_ids, "peening method"),
            (self.supported_media_condition_ids, "peening media condition"),
            (self.supported_direction_descriptors, "peening direction descriptor"),
        ):
            if len(values) != len(set(values)):
                raise ValueError(f"{label} IDs must be unique")
        ids = [row.requirement_id for row in self.stress_requirements]
        if len(ids) != len(set(ids)):
            raise ValueError("peening stress requirement IDs must be unique")
        return self


class PeeningTreatmentAssessment(Contract):
    assessment_id: str = Field(min_length=1)
    asset_id: str = Field(min_length=1)
    location_id: str = Field(min_length=1)
    physical_scope_id: str = Field(min_length=1)
    component_id: str = Field(min_length=1)
    material_condition_id: str = Field(min_length=1)
    clock_id: str = Field(min_length=1)
    treatment_records: tuple[PeeningTreatmentRecord, ...] = Field(min_length=1)
    residual_stress_observations: tuple[PeeningResidualStressObservation, ...] = Field(min_length=1)
    candidate_envelopes: tuple[DeclaredPeeningQualificationEnvelope, ...] = Field(min_length=1)
    component_material_and_zone_identity_reviewed: bool
    treatment_clock_and_sequence_reviewed: bool
    method_media_equipment_and_direction_reviewed: bool
    intensity_coverage_units_and_uncertainty_reviewed: bool
    stress_coordinate_method_units_and_uncertainty_reviewed: bool
    specimen_source_group_and_partition_reviewed: bool
    provider_lineage_and_digests_reviewed: bool
    qualification_envelope_authority_reviewed: bool
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def unique_ordered_records(self):
        treatment_ids = [row.treatment_record_id for row in self.treatment_records]
        observation_ids = [row.observation_id for row in self.residual_stress_observations]
        envelope_ids = [row.envelope_id for row in self.candidate_envelopes]
        for values, label in (
            (treatment_ids, "peening treatment record"),
            (observation_ids, "peening stress observation"),
            (envelope_ids, "peening envelope"),
        ):
            if len(values) != len(set(values)):
                raise ValueError(f"{label} IDs must be unique")
        ordered = sorted(self.treatment_records, key=lambda row: row.start_time_s)
        if tuple(ordered) != self.treatment_records:
            raise ValueError("peening treatment records must be in time order")
        if any(
            left.end_time_s > right.start_time_s for left, right in zip(ordered, ordered[1:], strict=False)
        ):
            raise ValueError("peening treatment records cannot overlap")
        zones = {row.zone_id for row in self.treatment_records}
        if {row.zone_id for row in self.residual_stress_observations} - zones:
            raise ValueError("every peening stress observation must reference a treated zone")
        return self


def peening_treatment_evidence(x: PeeningTreatmentAssessment) -> Calculation:
    missing_reviews = [
        name
        for name in (
            "component_material_and_zone_identity_reviewed",
            "treatment_clock_and_sequence_reviewed",
            "method_media_equipment_and_direction_reviewed",
            "intensity_coverage_units_and_uncertainty_reviewed",
            "stress_coordinate_method_units_and_uncertainty_reviewed",
            "specimen_source_group_and_partition_reviewed",
            "provider_lineage_and_digests_reviewed",
            "qualification_envelope_authority_reviewed",
        )
        if not getattr(x, name)
    ]
    invalid_treatment_ids = [row.treatment_record_id for row in x.treatment_records if not row.record_valid]
    invalid_observation_ids = [
        row.observation_id for row in x.residual_stress_observations if not row.record_valid
    ]
    matching = [
        envelope
        for envelope in x.candidate_envelopes
        if envelope.material_condition_id == x.material_condition_id
    ]
    if missing_reviews or invalid_treatment_ids or invalid_observation_ids or len(matching) != 1:
        return Calculation(
            status="needs_data",
            values={
                "assessment_id": x.assessment_id,
                "identity_matching_envelope_ids": [row.envelope_id for row in matching],
                "invalid_treatment_record_ids": invalid_treatment_ids,
                "invalid_stress_observation_ids": invalid_observation_ids,
                "missing_reviews": missing_reviews,
            },
            notes=(
                "A unique envelope and complete valid reviewed treatment and stress records are required.",
            ),
        )

    envelope = matching[0]
    definition_mismatch_ids = []
    outside_treatment_ids = []
    treatment_comparisons = []
    for row in x.treatment_records:
        exact = (
            row.intensity_metric_definition == envelope.intensity_metric_definition
            and row.intensity_unit_token == envelope.intensity_unit_token
            and row.coverage_metric_definition == envelope.coverage_metric_definition
            and row.coverage_unit_token == envelope.coverage_unit_token
        )
        if not exact:
            definition_mismatch_ids.append(row.treatment_record_id)
        reasons = []
        if row.method_id not in envelope.supported_method_ids:
            reasons.append("method_id")
        if row.media_condition_id not in envelope.supported_media_condition_ids:
            reasons.append("media_condition_id")
        if row.direction_descriptor not in envelope.supported_direction_descriptors:
            reasons.append("direction_descriptor")
        if exact and not (
            envelope.minimum_intensity_value <= row.intensity_value <= envelope.maximum_intensity_value
        ):
            reasons.append("intensity_value")
        if exact and not (
            envelope.minimum_coverage_value <= row.coverage_value <= envelope.maximum_coverage_value
        ):
            reasons.append("coverage_value")
        if reasons:
            outside_treatment_ids.append(row.treatment_record_id)
        treatment_comparisons.append(
            {
                "treatment_record_id": row.treatment_record_id,
                "zone_id": row.zone_id,
                "exact_metric_and_unit_match": exact,
                "outside_support_reasons": reasons,
            }
        )

    requirement_counts = {}
    outside_observation_ids = []
    for requirement in envelope.stress_requirements:
        candidates = [
            row
            for row in x.residual_stress_observations
            if row.stress_component_id == requirement.stress_component_id
            and row.method_id == requirement.method_id
            and row.unit_token == requirement.unit_token
            and requirement.minimum_depth_m <= row.depth_m <= requirement.maximum_depth_m
        ]
        requirement_counts[requirement.requirement_id] = len(candidates)
        outside_observation_ids.extend(
            row.observation_id
            for row in candidates
            if not (requirement.minimum_value <= row.reported_value <= requirement.maximum_value)
        )
    missing_requirement_ids = [
        requirement.requirement_id
        for requirement in envelope.stress_requirements
        if requirement_counts[requirement.requirement_id] < requirement.minimum_record_count
    ]
    specimen_count = len({row.physical_specimen_id for row in x.residual_stress_observations})
    source_group_count = len({row.source_group_id for row in x.residual_stress_observations})
    partitions_sufficient = (
        specimen_count >= envelope.minimum_physical_specimen_count
        and source_group_count >= envelope.minimum_source_group_count
    )
    if definition_mismatch_ids or missing_requirement_ids or not partitions_sufficient:
        status = "needs_data"
        outcome = "evidence_incomplete"
    elif outside_treatment_ids or outside_observation_ids:
        status = "out_of_scope"
        outcome = "outside_declared_support"
    else:
        status = "computed"
        outcome = "within_support"
    return Calculation(
        status=status,
        values={
            "assessment_id": x.assessment_id,
            "component_id": x.component_id,
            "selected_envelope_id": envelope.envelope_id,
            "declared_qualification_outcome": outcome,
            "treatment_comparisons": treatment_comparisons,
            "definition_or_unit_mismatch_treatment_ids": definition_mismatch_ids,
            "outside_support_treatment_ids": outside_treatment_ids,
            "stress_requirement_counts": requirement_counts,
            "missing_stress_requirement_ids": missing_requirement_ids,
            "outside_support_stress_observation_ids": sorted(set(outside_observation_ids)),
            "physical_specimen_count": specimen_count,
            "source_group_count": source_group_count,
            "evidence_partition_counts_sufficient": partitions_sufficient,
            "missing_reviews": [],
        },
        notes=(
            "Treatment intensity, coverage and residual-stress support are caller-owned and are not extrapolated.",
            "Residual-stress observations retain coordinate, component, depth, specimen, source-group and partition identities.",
            "This model does not predict stress redistribution, fatigue improvement, crack initiation, life, probability, or acceptance.",
        ),
    )


def specifications():
    def same_identity(x, context):
        if (x.asset_id, x.location_id) != (context.asset_id, context.location_id):
            raise ValueError("peening assessment asset and location must match the run context")

    return [
        ModelSpec(
            "welding.peening_treatment_evidence",
            PeeningTreatmentAssessment,
            peening_treatment_evidence,
            {
                "assessment_id": "1",
                "component_id": "1",
                "selected_envelope_id": "1",
                "declared_qualification_outcome": "1",
                "treatment_comparisons": "mixed",
                "definition_or_unit_mismatch_treatment_ids": "1",
                "outside_support_treatment_ids": "1",
                "stress_requirement_counts": "count",
                "missing_stress_requirement_ids": "1",
                "outside_support_stress_observation_ids": "1",
                "physical_specimen_count": "count",
                "source_group_count": "count",
                "evidence_partition_counts_sufficient": "1",
                "missing_reviews": "1",
            },
            (
                "Component, material, zones, treatment clock, method, media, equipment and direction are caller reviewed.",
                "Intensity, coverage and residual-stress metrics, exact units, uncertainty and support are caller-owned.",
                "Qualification observations preserve coordinate, depth, specimen, source-group and partition identities.",
            ),
            ("reviewed_peening_treatment_qualification_envelope",),
            context_validator=same_identity,
        )
    ]
