"""Exact evaluation of caller-licensed joint-efficiency declarations."""

from __future__ import annotations

from pydantic import Field, model_validator

from ..contracts import Calculation, Contract, Evidence, Fraction
from ..registry import ModelSpec


class JointExaminationRecord(Contract):
    examination_record_id: str = Field(min_length=1)
    joint_id: str = Field(min_length=1)
    physical_scope_id: str = Field(min_length=1)
    examination_method_id: str = Field(min_length=1)
    examined_extent_fraction: Fraction
    extent_definition: str = Field(min_length=1)
    provider_id: str = Field(min_length=1)
    provider_version: str = Field(min_length=1)
    provider_state_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    result_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    record_valid: bool
    invalid_basis: str | None = None
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def invalid_record_basis(self):
        if not self.record_valid and not self.invalid_basis:
            raise ValueError("an invalid joint examination record requires a basis")
        return self


class DeclaredJointEfficiencyRule(Contract):
    rule_id: str = Field(min_length=1)
    rule_set_id: str = Field(min_length=1)
    rule_revision: str = Field(min_length=1)
    joint_configuration_id: str = Field(min_length=1)
    welding_process_id: str = Field(min_length=1)
    material_group_id: str = Field(min_length=1)
    examination_method_id: str = Field(min_length=1)
    minimum_examination_extent_fraction: Fraction
    maximum_examination_extent_fraction: Fraction
    declared_joint_efficiency_factor: Fraction
    provider_id: str = Field(min_length=1)
    provider_version: str = Field(min_length=1)
    provider_state_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    rule_content_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    computational_use_authorized: bool
    authorization_basis: str = Field(min_length=1)
    applicability_basis: str = Field(min_length=1)
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def ordered_extent(self):
        if self.maximum_examination_extent_fraction < self.minimum_examination_extent_fraction:
            raise ValueError("joint-efficiency examination extent support must be ordered")
        return self


class JointEfficiencyDeclaration(Contract):
    assessment_id: str = Field(min_length=1)
    asset_id: str = Field(min_length=1)
    location_id: str = Field(min_length=1)
    joint_id: str = Field(min_length=1)
    physical_scope_id: str = Field(min_length=1)
    joint_configuration_id: str = Field(min_length=1)
    welding_process_id: str = Field(min_length=1)
    material_group_id: str = Field(min_length=1)
    examination_record: JointExaminationRecord
    candidate_rules: tuple[DeclaredJointEfficiencyRule, ...] = Field(min_length=1)
    joint_process_and_material_identity_reviewed: bool
    physical_scope_and_extent_definition_reviewed: bool
    examination_method_and_record_reviewed: bool
    rule_revision_and_applicability_reviewed: bool
    provider_lineage_and_digests_reviewed: bool
    computational_use_authorization_reviewed: bool
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def linked_unique_rules(self):
        if self.examination_record.joint_id != self.joint_id:
            raise ValueError("joint examination record must reference the assessed joint")
        if self.examination_record.physical_scope_id != self.physical_scope_id:
            raise ValueError("joint examination record must reference the assessed physical scope")
        rule_ids = [rule.rule_id for rule in self.candidate_rules]
        if len(rule_ids) != len(set(rule_ids)):
            raise ValueError("joint-efficiency rule IDs must be unique")
        return self


def joint_efficiency_declaration(x: JointEfficiencyDeclaration) -> Calculation:
    missing_reviews = [
        name
        for name in (
            "joint_process_and_material_identity_reviewed",
            "physical_scope_and_extent_definition_reviewed",
            "examination_method_and_record_reviewed",
            "rule_revision_and_applicability_reviewed",
            "provider_lineage_and_digests_reviewed",
            "computational_use_authorization_reviewed",
        )
        if not getattr(x, name)
    ]
    if missing_reviews or not x.examination_record.record_valid:
        return Calculation(
            status="needs_data",
            values={
                "assessment_id": x.assessment_id,
                "invalid_examination_record_id": (
                    None if x.examination_record.record_valid else x.examination_record.examination_record_id
                ),
                "missing_reviews": missing_reviews,
            },
            notes=("A valid examination record and all explicit reviews are required.",),
        )

    identity_matches = [
        rule
        for rule in x.candidate_rules
        if rule.joint_configuration_id == x.joint_configuration_id
        and rule.welding_process_id == x.welding_process_id
        and rule.material_group_id == x.material_group_id
        and rule.examination_method_id == x.examination_record.examination_method_id
    ]
    if not identity_matches:
        return Calculation(
            status="out_of_scope",
            values={
                "assessment_id": x.assessment_id,
                "identity_matching_rule_ids": [],
                "outside_support_reasons": ["rule_identity"],
                "missing_reviews": [],
            },
            notes=("Reviewed joint and examination identities are outside the supplied rule set.",),
        )
    if len(identity_matches) != 1:
        return Calculation(
            status="needs_data",
            values={
                "assessment_id": x.assessment_id,
                "identity_matching_rule_ids": [rule.rule_id for rule in identity_matches],
                "missing_reviews": [],
            },
            notes=("The supplied rule set must select exactly one rule for the reviewed identities.",),
        )

    rule = identity_matches[0]
    if not rule.computational_use_authorized:
        return Calculation(
            status="needs_data",
            values={
                "assessment_id": x.assessment_id,
                "selected_rule_id": rule.rule_id,
                "computational_use_authorized": False,
                "missing_reviews": [],
            },
            notes=("The selected caller rule is not authorized for computational use.",),
        )

    extent = x.examination_record.examined_extent_fraction
    within_extent_support = (
        rule.minimum_examination_extent_fraction <= extent <= rule.maximum_examination_extent_fraction
    )
    outcome = "requirements_satisfied" if within_extent_support else "examination_extent_not_satisfied"
    return Calculation(
        status="computed",
        values={
            "assessment_id": x.assessment_id,
            "joint_id": x.joint_id,
            "physical_scope_id": x.physical_scope_id,
            "selected_rule_id": rule.rule_id,
            "rule_set_id": rule.rule_set_id,
            "rule_revision": rule.rule_revision,
            "declared_requirement_outcome": outcome,
            "examined_extent_fraction": extent,
            "minimum_examination_extent_fraction": rule.minimum_examination_extent_fraction,
            "maximum_examination_extent_fraction": rule.maximum_examination_extent_fraction,
            "declared_joint_efficiency_factor": (
                rule.declared_joint_efficiency_factor if within_extent_support else None
            ),
            "computational_use_authorized": True,
            "missing_reviews": [],
        },
        notes=(
            "The rule value, revision, applicability and computational-use authorization are caller supplied.",
            "An examination-extent shortfall is a computed requirement outcome and is not converted into a different factor.",
            "This declaration does not calculate weld strength, pressure capacity, inspection reliability, code acceptance, life, or probability.",
        ),
    )


def specifications():
    def same_identity(x, context):
        if (x.asset_id, x.location_id) != (context.asset_id, context.location_id):
            raise ValueError("joint-efficiency assessment asset and location must match the run context")

    return [
        ModelSpec(
            "fabrication.joint_efficiency_declaration",
            JointEfficiencyDeclaration,
            joint_efficiency_declaration,
            {
                "assessment_id": "1",
                "joint_id": "1",
                "physical_scope_id": "1",
                "selected_rule_id": "1",
                "rule_set_id": "1",
                "rule_revision": "1",
                "declared_requirement_outcome": "1",
                "examined_extent_fraction": "1",
                "minimum_examination_extent_fraction": "1",
                "maximum_examination_extent_fraction": "1",
                "declared_joint_efficiency_factor": "1",
                "computational_use_authorized": "1",
                "missing_reviews": "1",
            },
            (
                "Joint, process, material group, examination method and physical scope are caller-reviewed exact identities.",
                "Rule revision, extent support, efficiency factor and computational-use authorization are supplied by the caller.",
                "A declared factor is returned only when the exact examination extent lies inside the selected rule support.",
            ),
            ("caller_licensed_joint_efficiency_rule_evaluation",),
            context_validator=same_identity,
        )
    ]
