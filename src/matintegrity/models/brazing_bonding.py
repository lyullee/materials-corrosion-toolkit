"""Brazing and bonding qualification against caller-owned evidence support."""

from __future__ import annotations

from pydantic import Field, model_validator

from ..contracts import Calculation, Contract, Evidence, Nonnegative, Positive
from ..registry import ModelSpec


class BondingCycleSegment(Contract):
    segment_id: str = Field(min_length=1)
    start_time_s: Nonnegative
    end_time_s: Positive
    minimum_temperature_K: Positive
    maximum_temperature_K: Positive
    minimum_pressure_value: Nonnegative
    maximum_pressure_value: Nonnegative
    pressure_unit_token: str = Field(min_length=1)
    atmosphere_descriptor: str = Field(min_length=1)
    record_valid: bool
    invalid_or_missing_basis: str | None = None
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def ordered_segment(self):
        if self.end_time_s <= self.start_time_s:
            raise ValueError("bonding cycle segments must have positive duration")
        if self.maximum_temperature_K < self.minimum_temperature_K:
            raise ValueError("bonding cycle temperature ranges must be ordered")
        if self.maximum_pressure_value < self.minimum_pressure_value:
            raise ValueError("bonding cycle pressure ranges must be ordered")
        if not self.record_valid and not self.invalid_or_missing_basis:
            raise ValueError("invalid bonding cycle records require a basis")
        return self


class BondingObservation(Contract):
    observation_id: str = Field(min_length=1)
    observation_kind: str = Field(min_length=1)
    metric_id: str = Field(min_length=1)
    metric_definition: str = Field(min_length=1)
    method_id: str = Field(min_length=1)
    reported_value: float | None = None
    unit_token: str = Field(min_length=1)
    expanded_uncertainty: Nonnegative | None = None
    coverage_factor: Positive | None = None
    result_digest: str | None = Field(default=None, pattern=r"^[a-f0-9]{64}$")
    record_available: bool
    missing_or_invalid_basis: str | None = None
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def availability_contract(self):
        if self.record_available:
            if self.reported_value is None or self.result_digest is None:
                raise ValueError("available bonding observations require value and result digest")
        elif not self.missing_or_invalid_basis:
            raise ValueError("unavailable bonding observations require a basis")
        if (self.expanded_uncertainty is None) != (self.coverage_factor is None):
            raise ValueError("expanded uncertainty and coverage factor must be supplied together")
        return self


class BondingQualificationRecord(Contract):
    evidence_record_id: str = Field(min_length=1)
    physical_specimen_id: str = Field(min_length=1)
    source_group_id: str = Field(min_length=1)
    independence_group_id: str = Field(min_length=1)
    member_material_ids: tuple[str, ...] = Field(min_length=2)
    member_surface_condition_ids: tuple[str, ...] = Field(min_length=2)
    bonding_material_id: str = Field(min_length=1)
    bonding_material_lot_id: str = Field(min_length=1)
    process_id: str = Field(min_length=1)
    flux_id: str = Field(min_length=1)
    joint_clearance_value: Nonnegative
    joint_clearance_unit_token: str = Field(min_length=1)
    overlap_value: Positive
    overlap_unit_token: str = Field(min_length=1)
    observations: tuple[BondingObservation, ...] = Field(min_length=1)
    provider_id: str = Field(min_length=1)
    provider_revision: str = Field(min_length=1)
    provider_state_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    input_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    record_valid: bool
    supports_declared_envelope: bool
    invalid_or_limiting_basis: str | None = None
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def aligned_members_and_unique_observations(self):
        if len(self.member_material_ids) != len(self.member_surface_condition_ids):
            raise ValueError("member material and surface-condition arrays must align")
        identifiers = [row.observation_id for row in self.observations]
        if len(set(identifiers)) != len(identifiers):
            raise ValueError("bonding observation identifiers must be unique per record")
        if (
            not self.record_valid or not self.supports_declared_envelope
        ) and not self.invalid_or_limiting_basis:
            raise ValueError("invalid or limiting bonding qualification evidence requires a basis")
        return self


class BondingEvidenceRequirement(Contract):
    requirement_id: str = Field(min_length=1)
    observation_kind: str = Field(min_length=1)
    metric_id: str = Field(min_length=1)
    metric_definition: str = Field(min_length=1)
    unit_token: str = Field(min_length=1)
    minimum_record_count: int = Field(ge=1)
    requirement_basis: str = Field(min_length=1)


class BrazingBondingQualificationEnvelope(Contract):
    envelope_id: str = Field(min_length=1)
    member_material_ids: tuple[str, ...] = Field(min_length=2)
    member_surface_condition_ids: tuple[str, ...] = Field(min_length=2)
    supported_bonding_material_ids: tuple[str, ...] = Field(min_length=1)
    supported_process_ids: tuple[str, ...] = Field(min_length=1)
    supported_flux_ids: tuple[str, ...] = Field(min_length=1)
    supported_atmosphere_descriptors: tuple[str, ...] = Field(min_length=1)
    minimum_joint_clearance_value: Nonnegative
    maximum_joint_clearance_value: Nonnegative
    joint_clearance_unit_token: str = Field(min_length=1)
    minimum_overlap_value: Positive
    maximum_overlap_value: Positive
    overlap_unit_token: str = Field(min_length=1)
    minimum_temperature_K: Positive
    maximum_temperature_K: Positive
    minimum_pressure_value: Nonnegative
    maximum_pressure_value: Nonnegative
    pressure_unit_token: str = Field(min_length=1)
    maximum_cycle_duration_s: Positive
    evidence_requirements: tuple[BondingEvidenceRequirement, ...] = Field(min_length=1)
    qualification_records: tuple[BondingQualificationRecord, ...] = Field(min_length=1)
    qualification_basis: str = Field(min_length=1)
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def ordered_unique_support(self):
        if len(self.member_material_ids) != len(self.member_surface_condition_ids):
            raise ValueError("envelope member material and surface-condition arrays must align")
        for lower, upper, name in (
            (self.minimum_joint_clearance_value, self.maximum_joint_clearance_value, "clearance"),
            (self.minimum_overlap_value, self.maximum_overlap_value, "overlap"),
            (self.minimum_temperature_K, self.maximum_temperature_K, "temperature"),
            (self.minimum_pressure_value, self.maximum_pressure_value, "pressure"),
        ):
            if upper < lower:
                raise ValueError(f"bonding qualification {name} bounds must be ordered")
        for values, name in (
            (self.supported_bonding_material_ids, "bonding material"),
            (self.supported_process_ids, "process"),
            (self.supported_flux_ids, "flux"),
            (self.supported_atmosphere_descriptors, "atmosphere"),
        ):
            if len(set(values)) != len(values) or any(not value.strip() for value in values):
                raise ValueError(f"supported {name} identifiers must be unique and nonblank")
        requirement_ids = [row.requirement_id for row in self.evidence_requirements]
        if len(set(requirement_ids)) != len(requirement_ids):
            raise ValueError("bonding evidence requirement identifiers must be unique")
        record_ids = [row.evidence_record_id for row in self.qualification_records]
        if len(set(record_ids)) != len(record_ids):
            raise ValueError("bonding qualification record identifiers must be unique")
        specimen_ids = [row.physical_specimen_id for row in self.qualification_records]
        if len(set(specimen_ids)) != len(specimen_ids):
            raise ValueError("a physical specimen cannot appear in multiple bonding records")
        return self


class BrazingBondingJointRecord(Contract):
    joint_id: str = Field(min_length=1)
    member_material_ids: tuple[str, ...] = Field(min_length=2)
    member_surface_condition_ids: tuple[str, ...] = Field(min_length=2)
    bonding_material_id: str = Field(min_length=1)
    bonding_material_lot_id: str = Field(min_length=1)
    process_id: str = Field(min_length=1)
    flux_id: str = Field(min_length=1)
    joint_clearance_value: Nonnegative
    joint_clearance_unit_token: str = Field(min_length=1)
    overlap_value: Positive
    overlap_unit_token: str = Field(min_length=1)
    cycle_segments: tuple[BondingCycleSegment, ...] = Field(min_length=1)
    record_valid: bool
    invalid_or_missing_basis: str | None = None
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def aligned_members_and_ordered_cycle(self):
        if len(self.member_material_ids) != len(self.member_surface_condition_ids):
            raise ValueError("joint member material and surface-condition arrays must align")
        identifiers = [row.segment_id for row in self.cycle_segments]
        if len(set(identifiers)) != len(identifiers):
            raise ValueError("bonding cycle segment identifiers must be unique per joint")
        for first, second in zip(self.cycle_segments, self.cycle_segments[1:], strict=False):
            if second.start_time_s < first.end_time_s:
                raise ValueError("bonding cycle segments must be ordered and cannot overlap")
        if not self.record_valid and not self.invalid_or_missing_basis:
            raise ValueError("invalid bonding joint records require a basis")
        return self


class BrazingBondingQualification(Contract):
    assessment_id: str = Field(min_length=1)
    asset_id: str = Field(min_length=1)
    location_id: str = Field(min_length=1)
    physical_scope_id: str = Field(min_length=1)
    joints: tuple[BrazingBondingJointRecord, ...] = Field(min_length=1)
    qualification_envelope: BrazingBondingQualificationEnvelope
    member_material_and_surface_conditions_reviewed: bool
    bonding_material_and_lot_reviewed: bool
    process_atmosphere_and_flux_reviewed: bool
    clearance_overlap_and_geometry_reviewed: bool
    heat_pressure_cycle_and_clock_reviewed: bool
    physical_specimen_and_source_group_partitions_reviewed: bool
    observation_metrics_units_and_uncertainty_reviewed: bool
    provider_lineage_and_digests_reviewed: bool
    qualification_envelope_authority_reviewed: bool
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def unique_joints(self):
        identifiers = [row.joint_id for row in self.joints]
        if len(set(identifiers)) != len(identifiers):
            raise ValueError("brazing/bonding joint identifiers must be unique")
        return self


def brazing_bonding_qualification(x: BrazingBondingQualification) -> Calculation:
    envelope = x.qualification_envelope
    review_fields = (
        "member_material_and_surface_conditions_reviewed",
        "bonding_material_and_lot_reviewed",
        "process_atmosphere_and_flux_reviewed",
        "clearance_overlap_and_geometry_reviewed",
        "heat_pressure_cycle_and_clock_reviewed",
        "physical_specimen_and_source_group_partitions_reviewed",
        "observation_metrics_units_and_uncertainty_reviewed",
        "provider_lineage_and_digests_reviewed",
        "qualification_envelope_authority_reviewed",
    )
    missing_reviews = [name for name in review_fields if not getattr(x, name)]
    invalid_joint_ids = [row.joint_id for row in x.joints if not row.record_valid]
    invalid_segment_ids = [
        row.segment_id for joint in x.joints for row in joint.cycle_segments if not row.record_valid
    ]
    unit_mismatch_joint_ids = [
        joint.joint_id
        for joint in x.joints
        if joint.joint_clearance_unit_token != envelope.joint_clearance_unit_token
        or joint.overlap_unit_token != envelope.overlap_unit_token
        or any(row.pressure_unit_token != envelope.pressure_unit_token for row in joint.cycle_segments)
    ]
    invalid_evidence_ids = []
    unavailable_observation_ids = []
    evidence_identity_mismatches = []
    for record in envelope.qualification_records:
        if not record.record_valid or not record.supports_declared_envelope:
            invalid_evidence_ids.append(record.evidence_record_id)
        mismatches = []
        if record.member_material_ids != envelope.member_material_ids:
            mismatches.append("member_material_ids")
        if record.member_surface_condition_ids != envelope.member_surface_condition_ids:
            mismatches.append("member_surface_condition_ids")
        if record.bonding_material_id not in envelope.supported_bonding_material_ids:
            mismatches.append("bonding_material_id")
        if record.process_id not in envelope.supported_process_ids:
            mismatches.append("process_id")
        if record.flux_id not in envelope.supported_flux_ids:
            mismatches.append("flux_id")
        if mismatches:
            evidence_identity_mismatches.append(
                {"evidence_record_id": record.evidence_record_id, "fields": mismatches}
            )
        unavailable_observation_ids.extend(
            row.observation_id for row in record.observations if not row.record_available
        )

    available_observations = [
        observation
        for record in envelope.qualification_records
        if record.record_valid and record.supports_declared_envelope
        for observation in record.observations
        if observation.record_available
    ]
    requirement_counts = {}
    missing_requirement_ids = []
    for requirement in envelope.evidence_requirements:
        count = sum(
            observation.observation_kind == requirement.observation_kind
            and observation.metric_id == requirement.metric_id
            and observation.metric_definition == requirement.metric_definition
            and observation.unit_token == requirement.unit_token
            for observation in available_observations
        )
        requirement_counts[requirement.requirement_id] = count
        if count < requirement.minimum_record_count:
            missing_requirement_ids.append(requirement.requirement_id)

    if any(
        (
            missing_reviews,
            invalid_joint_ids,
            invalid_segment_ids,
            unit_mismatch_joint_ids,
            invalid_evidence_ids,
            unavailable_observation_ids,
            evidence_identity_mismatches,
            missing_requirement_ids,
        )
    ):
        return Calculation(
            status="needs_data",
            values={
                "assessment_id": x.assessment_id,
                "missing_reviews": missing_reviews,
                "invalid_joint_ids": invalid_joint_ids,
                "invalid_cycle_segment_ids": invalid_segment_ids,
                "unit_mismatch_joint_ids": unit_mismatch_joint_ids,
                "invalid_qualification_record_ids": invalid_evidence_ids,
                "unavailable_observation_ids": unavailable_observation_ids,
                "qualification_identity_mismatches": evidence_identity_mismatches,
                "evidence_requirement_counts": requirement_counts,
                "missing_evidence_requirement_ids": missing_requirement_ids,
            },
            notes=("Qualification comparison is withheld until reviews, units and evidence are complete.",),
        )

    joint_comparisons = []
    outside_joint_ids = []
    for joint in x.joints:
        reasons = []
        if joint.member_material_ids != envelope.member_material_ids:
            reasons.append("member_material_ids")
        if joint.member_surface_condition_ids != envelope.member_surface_condition_ids:
            reasons.append("member_surface_condition_ids")
        if joint.bonding_material_id not in envelope.supported_bonding_material_ids:
            reasons.append("bonding_material_id")
        if joint.process_id not in envelope.supported_process_ids:
            reasons.append("process_id")
        if joint.flux_id not in envelope.supported_flux_ids:
            reasons.append("flux_id")
        if not (
            envelope.minimum_joint_clearance_value
            <= joint.joint_clearance_value
            <= envelope.maximum_joint_clearance_value
        ):
            reasons.append("joint_clearance")
        if not envelope.minimum_overlap_value <= joint.overlap_value <= envelope.maximum_overlap_value:
            reasons.append("overlap")
        duration = joint.cycle_segments[-1].end_time_s - joint.cycle_segments[0].start_time_s
        if duration > envelope.maximum_cycle_duration_s:
            reasons.append("cycle_duration")
        for segment in joint.cycle_segments:
            if segment.atmosphere_descriptor not in envelope.supported_atmosphere_descriptors:
                reasons.append(f"atmosphere:{segment.segment_id}")
            if (
                segment.minimum_temperature_K < envelope.minimum_temperature_K
                or segment.maximum_temperature_K > envelope.maximum_temperature_K
            ):
                reasons.append(f"temperature:{segment.segment_id}")
            if (
                segment.minimum_pressure_value < envelope.minimum_pressure_value
                or segment.maximum_pressure_value > envelope.maximum_pressure_value
            ):
                reasons.append(f"pressure:{segment.segment_id}")
        if reasons:
            outside_joint_ids.append(joint.joint_id)
        joint_comparisons.append(
            {
                "joint_id": joint.joint_id,
                "cycle_duration_s": duration,
                "outside_support_reasons": reasons,
                "within_declared_qualification_support": not reasons,
            }
        )

    values = {
        "assessment_id": x.assessment_id,
        "asset_id": x.asset_id,
        "location_id": x.location_id,
        "physical_scope_id": x.physical_scope_id,
        "qualification_envelope_id": envelope.envelope_id,
        "joint_comparisons": joint_comparisons,
        "outside_support_joint_ids": outside_joint_ids,
        "evidence_requirement_counts": requirement_counts,
        "qualification_evidence_summary": {
            "evidence_record_ids": [row.evidence_record_id for row in envelope.qualification_records],
            "physical_specimen_ids": sorted(
                {row.physical_specimen_id for row in envelope.qualification_records}
            ),
            "source_group_ids": sorted({row.source_group_id for row in envelope.qualification_records}),
            "independence_group_ids": sorted(
                {row.independence_group_id for row in envelope.qualification_records}
            ),
        },
    }
    notes = (
        "The calculation compares production records only with a caller-owned qualification envelope; no proprietary process table is bundled.",
        "Reported mechanical and NDE observations retain their metric, unit, uncertainty and provider lineage; no unreported bond strength is inferred.",
        "No acceptance, defect probability, failure probability or remaining life is produced.",
    )
    if outside_joint_ids:
        return Calculation(status="out_of_scope", values=values, notes=notes)
    values["declared_qualification_outcome"] = "within_support"
    return Calculation(values=values, notes=notes)


def specifications():
    def same_identity(x, context):
        if (x.asset_id, x.location_id) != (context.asset_id, context.location_id):
            raise ValueError("brazing/bonding assessment asset and location must match the run context")

    return [
        ModelSpec(
            "welding.brazing_bonding_qualification",
            BrazingBondingQualification,
            brazing_bonding_qualification,
            {
                "assessment_id": "1",
                "asset_id": "1",
                "location_id": "1",
                "physical_scope_id": "1",
                "qualification_envelope_id": "1",
                "joint_comparisons": "1",
                "outside_support_joint_ids": "1",
                "evidence_requirement_counts": "1",
                "qualification_evidence_summary": "1",
                "declared_qualification_outcome": "1",
            },
            (
                "Member ordering, material and surface-condition identities are preserved and compared exactly.",
                "Clearance, overlap and cycle pressure are compared only under exact caller-declared unit tokens.",
                "Qualification observations and support are caller declarations, not an embedded acceptance code or bond-strength model.",
            ),
            ("reviewed_brazing_bonding_qualification_envelope",),
            context_validator=same_identity,
        )
    ]
