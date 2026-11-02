"""Lamellar-tearing applicability against caller-qualified test evidence."""

from __future__ import annotations

from pydantic import Field, model_validator

from ..contracts import Calculation, Contract, Evidence, Nonnegative, Positive
from ..registry import ModelSpec


class ThroughThicknessObservation(Contract):
    observation_id: str = Field(min_length=1)
    observation_kind: str = Field(min_length=1)
    result_name: str = Field(min_length=1)
    direction_id: str = Field(min_length=1)
    method_id: str = Field(min_length=1)
    result_value: float | None = None
    result_unit_token: str = Field(min_length=1)
    expanded_uncertainty: Nonnegative | None = None
    coverage_factor: Positive | None = None
    result_digest: str | None = Field(default=None, pattern=r"^[a-f0-9]{64}$")
    record_available: bool
    missing_or_invalid_basis: str | None = None
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def availability_contract(self):
        if self.record_available:
            if self.result_value is None or self.result_digest is None:
                raise ValueError("available through-thickness observations require value and result digest")
        elif not self.missing_or_invalid_basis:
            raise ValueError("unavailable through-thickness observations require a basis")
        if (self.expanded_uncertainty is None) != (self.coverage_factor is None):
            raise ValueError("expanded uncertainty and coverage factor must be supplied together")
        return self


class LamellarTearingTestEvidence(Contract):
    evidence_record_id: str = Field(min_length=1)
    physical_specimen_id: str = Field(min_length=1)
    source_group_id: str = Field(min_length=1)
    independence_group_id: str = Field(min_length=1)
    parent_material_id: str = Field(min_length=1)
    material_condition_id: str = Field(min_length=1)
    product_form_id: str = Field(min_length=1)
    specimen_thickness_m: Positive
    directionality_descriptor: str = Field(min_length=1)
    provider_id: str = Field(min_length=1)
    provider_revision: str = Field(min_length=1)
    provider_state_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    input_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    observations: tuple[ThroughThicknessObservation, ...] = Field(min_length=1)
    record_valid: bool
    supports_declared_envelope: bool
    invalid_or_limiting_basis: str | None = None
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def unique_observations_and_validity(self):
        identifiers = [row.observation_id for row in self.observations]
        if len(set(identifiers)) != len(identifiers):
            raise ValueError("through-thickness observation identifiers must be unique per record")
        if (
            not self.record_valid or not self.supports_declared_envelope
        ) and not self.invalid_or_limiting_basis:
            raise ValueError("invalid or limiting lamellar-tearing evidence requires a basis")
        return self


class LamellarEvidenceRequirement(Contract):
    requirement_id: str = Field(min_length=1)
    observation_kind: str = Field(min_length=1)
    result_name: str = Field(min_length=1)
    direction_id: str = Field(min_length=1)
    result_unit_token: str = Field(min_length=1)
    minimum_record_count: int = Field(ge=1)
    requirement_basis: str = Field(min_length=1)


class LamellarTearingJointCondition(Contract):
    joint_id: str = Field(min_length=1)
    joint_geometry_descriptor: str = Field(min_length=1)
    governing_thickness_m: Positive
    through_thickness_loading_descriptor: str = Field(min_length=1)
    restraint_descriptor: str = Field(min_length=1)
    weld_process_id: str = Field(min_length=1)
    consumable_id: str = Field(min_length=1)
    minimum_heat_input_value: Nonnegative
    maximum_heat_input_value: Nonnegative
    heat_input_unit_token: str = Field(min_length=1)
    record_valid: bool
    invalid_or_missing_basis: str | None = None
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def ordered_heat_input(self):
        if self.maximum_heat_input_value < self.minimum_heat_input_value:
            raise ValueError("joint heat-input ranges must be ordered")
        if not self.record_valid and not self.invalid_or_missing_basis:
            raise ValueError("invalid joint condition records require a basis")
        return self


class LamellarTearingQualificationEnvelope(Contract):
    envelope_id: str = Field(min_length=1)
    parent_material_id: str = Field(min_length=1)
    material_condition_id: str = Field(min_length=1)
    product_form_id: str = Field(min_length=1)
    directionality_descriptor: str = Field(min_length=1)
    minimum_thickness_m: Positive
    maximum_thickness_m: Positive
    supported_joint_geometry_descriptors: tuple[str, ...] = Field(min_length=1)
    supported_through_thickness_loading_descriptors: tuple[str, ...] = Field(min_length=1)
    supported_restraint_descriptors: tuple[str, ...] = Field(min_length=1)
    supported_weld_process_ids: tuple[str, ...] = Field(min_length=1)
    supported_consumable_ids: tuple[str, ...] = Field(min_length=1)
    minimum_heat_input_value: Nonnegative
    maximum_heat_input_value: Nonnegative
    heat_input_unit_token: str = Field(min_length=1)
    evidence_requirements: tuple[LamellarEvidenceRequirement, ...] = Field(min_length=1)
    test_evidence: tuple[LamellarTearingTestEvidence, ...] = Field(min_length=1)
    qualification_basis: str = Field(min_length=1)
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def ordered_unique_support(self):
        if self.maximum_thickness_m < self.minimum_thickness_m:
            raise ValueError("qualification thickness bounds must be ordered")
        if self.maximum_heat_input_value < self.minimum_heat_input_value:
            raise ValueError("qualification heat-input bounds must be ordered")
        for values, name in (
            (self.supported_joint_geometry_descriptors, "joint geometry"),
            (self.supported_through_thickness_loading_descriptors, "loading"),
            (self.supported_restraint_descriptors, "restraint"),
            (self.supported_weld_process_ids, "weld process"),
            (self.supported_consumable_ids, "consumable"),
        ):
            if len(set(values)) != len(values) or any(not item.strip() for item in values):
                raise ValueError(f"supported {name} identifiers must be unique and nonblank")
        requirement_ids = [row.requirement_id for row in self.evidence_requirements]
        if len(set(requirement_ids)) != len(requirement_ids):
            raise ValueError("lamellar evidence requirement identifiers must be unique")
        evidence_ids = [row.evidence_record_id for row in self.test_evidence]
        if len(set(evidence_ids)) != len(evidence_ids):
            raise ValueError("lamellar test evidence identifiers must be unique")
        specimen_ids = [row.physical_specimen_id for row in self.test_evidence]
        if len(set(specimen_ids)) != len(specimen_ids):
            raise ValueError("a physical specimen cannot appear in multiple lamellar evidence records")
        return self


class LamellarTearingApplicability(Contract):
    assessment_id: str = Field(min_length=1)
    asset_id: str = Field(min_length=1)
    location_id: str = Field(min_length=1)
    physical_scope_id: str = Field(min_length=1)
    parent_material_id: str = Field(min_length=1)
    material_condition_id: str = Field(min_length=1)
    product_form_id: str = Field(min_length=1)
    directionality_descriptor: str = Field(min_length=1)
    joints: tuple[LamellarTearingJointCondition, ...] = Field(min_length=1)
    qualification_envelope: LamellarTearingQualificationEnvelope
    material_product_and_condition_reviewed: bool
    directionality_and_thickness_reviewed: bool
    joint_geometry_and_through_thickness_loading_reviewed: bool
    restraint_descriptor_reviewed: bool
    welding_process_consumable_and_heat_input_reviewed: bool
    physical_specimen_and_source_group_partitions_reviewed: bool
    test_method_units_and_uncertainty_reviewed: bool
    provider_lineage_and_digests_reviewed: bool
    qualification_envelope_authority_reviewed: bool
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def unique_joints(self):
        identifiers = [row.joint_id for row in self.joints]
        if len(set(identifiers)) != len(identifiers):
            raise ValueError("lamellar-tearing joint identifiers must be unique")
        return self


def lamellar_tearing_applicability(x: LamellarTearingApplicability) -> Calculation:
    envelope = x.qualification_envelope
    review_fields = (
        "material_product_and_condition_reviewed",
        "directionality_and_thickness_reviewed",
        "joint_geometry_and_through_thickness_loading_reviewed",
        "restraint_descriptor_reviewed",
        "welding_process_consumable_and_heat_input_reviewed",
        "physical_specimen_and_source_group_partitions_reviewed",
        "test_method_units_and_uncertainty_reviewed",
        "provider_lineage_and_digests_reviewed",
        "qualification_envelope_authority_reviewed",
    )
    missing_reviews = [name for name in review_fields if not getattr(x, name)]
    identity_fields = (
        "parent_material_id",
        "material_condition_id",
        "product_form_id",
        "directionality_descriptor",
    )
    identity_mismatches = [name for name in identity_fields if getattr(x, name) != getattr(envelope, name)]
    invalid_joint_ids = [row.joint_id for row in x.joints if not row.record_valid]
    unit_mismatch_joint_ids = [
        row.joint_id for row in x.joints if row.heat_input_unit_token != envelope.heat_input_unit_token
    ]
    invalid_evidence_ids = []
    unavailable_observation_ids = []
    evidence_identity_mismatches = []
    for record in envelope.test_evidence:
        if not record.record_valid or not record.supports_declared_envelope:
            invalid_evidence_ids.append(record.evidence_record_id)
        mismatches = [name for name in identity_fields if getattr(record, name) != getattr(envelope, name)]
        if mismatches:
            evidence_identity_mismatches.append(
                {"evidence_record_id": record.evidence_record_id, "fields": mismatches}
            )
        unavailable_observation_ids.extend(
            row.observation_id for row in record.observations if not row.record_available
        )

    missing_requirement_ids = []
    requirement_counts = {}
    available_observations = [
        observation
        for record in envelope.test_evidence
        if record.record_valid and record.supports_declared_envelope
        for observation in record.observations
        if observation.record_available
    ]
    for requirement in envelope.evidence_requirements:
        count = sum(
            observation.observation_kind == requirement.observation_kind
            and observation.result_name == requirement.result_name
            and observation.direction_id == requirement.direction_id
            and observation.result_unit_token == requirement.result_unit_token
            for observation in available_observations
        )
        requirement_counts[requirement.requirement_id] = count
        if count < requirement.minimum_record_count:
            missing_requirement_ids.append(requirement.requirement_id)

    if any(
        (
            missing_reviews,
            identity_mismatches,
            invalid_joint_ids,
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
                "identity_mismatch_fields": identity_mismatches,
                "invalid_joint_ids": invalid_joint_ids,
                "heat_input_unit_mismatch_joint_ids": unit_mismatch_joint_ids,
                "invalid_test_evidence_ids": invalid_evidence_ids,
                "unavailable_observation_ids": unavailable_observation_ids,
                "test_evidence_identity_mismatches": evidence_identity_mismatches,
                "evidence_requirement_counts": requirement_counts,
                "missing_evidence_requirement_ids": missing_requirement_ids,
            },
            notes=(
                "Applicability is withheld until identity, unit, review and evidence requirements are complete.",
            ),
        )

    comparisons = []
    outside_joint_ids = []
    for joint in x.joints:
        reasons = []
        if not envelope.minimum_thickness_m <= joint.governing_thickness_m <= envelope.maximum_thickness_m:
            reasons.append("governing_thickness")
        if joint.joint_geometry_descriptor not in envelope.supported_joint_geometry_descriptors:
            reasons.append("joint_geometry_descriptor")
        if (
            joint.through_thickness_loading_descriptor
            not in envelope.supported_through_thickness_loading_descriptors
        ):
            reasons.append("through_thickness_loading_descriptor")
        if joint.restraint_descriptor not in envelope.supported_restraint_descriptors:
            reasons.append("restraint_descriptor")
        if joint.weld_process_id not in envelope.supported_weld_process_ids:
            reasons.append("weld_process_id")
        if joint.consumable_id not in envelope.supported_consumable_ids:
            reasons.append("consumable_id")
        if (
            joint.minimum_heat_input_value < envelope.minimum_heat_input_value
            or joint.maximum_heat_input_value > envelope.maximum_heat_input_value
        ):
            reasons.append("heat_input_range")
        if reasons:
            outside_joint_ids.append(joint.joint_id)
        comparisons.append(
            {
                "joint_id": joint.joint_id,
                "outside_support_reasons": reasons,
                "within_declared_qualification_support": not reasons,
            }
        )

    evidence_summary = {
        "evidence_record_ids": [row.evidence_record_id for row in envelope.test_evidence],
        "physical_specimen_ids": sorted({row.physical_specimen_id for row in envelope.test_evidence}),
        "source_group_ids": sorted({row.source_group_id for row in envelope.test_evidence}),
        "independence_group_ids": sorted({row.independence_group_id for row in envelope.test_evidence}),
        "observation_ids": [
            observation.observation_id for row in envelope.test_evidence for observation in row.observations
        ],
    }
    values = {
        "assessment_id": x.assessment_id,
        "asset_id": x.asset_id,
        "location_id": x.location_id,
        "physical_scope_id": x.physical_scope_id,
        "qualification_envelope_id": envelope.envelope_id,
        "joint_comparisons": comparisons,
        "outside_support_joint_ids": outside_joint_ids,
        "evidence_requirement_counts": requirement_counts,
        "test_evidence_summary": evidence_summary,
    }
    notes = (
        "Applicability is limited to a caller-owned qualification envelope; no material or joint susceptibility table is bundled.",
        "Through-thickness tests and inspections retain specimen, source-group, method, unit, uncertainty and provider lineage.",
        "No tearing initiation, flaw size, acceptance, remaining life or failure probability is produced.",
    )
    if outside_joint_ids:
        return Calculation(status="out_of_scope", values=values, notes=notes)
    values["declared_applicability_outcome"] = "within_support"
    return Calculation(values=values, notes=notes)


def specifications():
    def same_identity(x, context):
        if (x.asset_id, x.location_id) != (context.asset_id, context.location_id):
            raise ValueError("lamellar-tearing assessment asset and location must match the run context")

    return [
        ModelSpec(
            "welding.lamellar_tearing_applicability",
            LamellarTearingApplicability,
            lamellar_tearing_applicability,
            {
                "assessment_id": "1",
                "asset_id": "1",
                "location_id": "1",
                "physical_scope_id": "1",
                "qualification_envelope_id": "1",
                "joint_comparisons": "1",
                "outside_support_joint_ids": "1",
                "evidence_requirement_counts": "1",
                "test_evidence_summary": "1",
                "declared_applicability_outcome": "1",
            },
            (
                "Parent material, product form, material condition and directionality identity match caller qualification evidence exactly.",
                "Heat input is compared only under an exact caller-declared unit token; no conversion or code limit is inferred.",
                "Joint geometry, through-thickness loading, restraint, welding process and consumable support are caller declarations.",
            ),
            ("reviewed_lamellar_tearing_qualification_envelope",),
            context_validator=same_identity,
        )
    ]
