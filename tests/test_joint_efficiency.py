import pytest

from matintegrity.contracts import RunContext
from matintegrity.models.joint_efficiency import (
    JointEfficiencyDeclaration,
    joint_efficiency_declaration,
    specifications,
)
from matintegrity.registry import ModelRegistry

EVIDENCE = {"source_id": "authored", "origin": "synthetic", "citation": "authored test"}
DIGEST_A = "a" * 64
DIGEST_B = "b" * 64


def rule(**updates):
    value = {
        "rule_id": "rule-1",
        "rule_set_id": "caller-rule-set",
        "rule_revision": "revision-1",
        "joint_configuration_id": "joint-configuration-1",
        "welding_process_id": "process-1",
        "material_group_id": "material-group-1",
        "examination_method_id": "examination-1",
        "minimum_examination_extent_fraction": 0.5,
        "maximum_examination_extent_fraction": 1.0,
        "declared_joint_efficiency_factor": 0.85,
        "provider_id": "rule-provider",
        "provider_version": "1",
        "provider_state_digest": DIGEST_A,
        "rule_content_digest": DIGEST_B,
        "computational_use_authorized": True,
        "authorization_basis": "caller confirms licensed computational use",
        "applicability_basis": "caller-reviewed rule applicability",
        "evidence": (EVIDENCE,),
    }
    value.update(updates)
    return value


def payload(**updates):
    value = {
        "assessment_id": "joint-efficiency-1",
        "asset_id": "asset-1",
        "location_id": "joint-location-1",
        "joint_id": "joint-1",
        "physical_scope_id": "scope-1",
        "joint_configuration_id": "joint-configuration-1",
        "welding_process_id": "process-1",
        "material_group_id": "material-group-1",
        "examination_record": {
            "examination_record_id": "examination-record-1",
            "joint_id": "joint-1",
            "physical_scope_id": "scope-1",
            "examination_method_id": "examination-1",
            "examined_extent_fraction": 0.75,
            "extent_definition": "authored examined joint-length fraction",
            "provider_id": "inspection-provider",
            "provider_version": "1",
            "provider_state_digest": DIGEST_A,
            "result_digest": DIGEST_B,
            "record_valid": True,
            "evidence": (EVIDENCE,),
        },
        "candidate_rules": (rule(),),
        "joint_process_and_material_identity_reviewed": True,
        "physical_scope_and_extent_definition_reviewed": True,
        "examination_method_and_record_reviewed": True,
        "rule_revision_and_applicability_reviewed": True,
        "provider_lineage_and_digests_reviewed": True,
        "computational_use_authorization_reviewed": True,
        "evidence": (EVIDENCE,),
    }
    value.update(updates)
    return JointEfficiencyDeclaration(**value)


def test_authorized_exact_rule_returns_declared_factor():
    result = joint_efficiency_declaration(payload())
    assert result.status == "computed"
    assert result.values["declared_requirement_outcome"] == "requirements_satisfied"
    assert result.values["declared_joint_efficiency_factor"] == pytest.approx(0.85)


def test_extent_shortfall_is_computed_without_substitute_factor():
    base = payload()
    record = base.examination_record.model_copy(update={"examined_extent_fraction": 0.25})
    result = joint_efficiency_declaration(base.model_copy(update={"examination_record": record}))
    assert result.status == "computed"
    assert result.values["declared_requirement_outcome"] == "examination_extent_not_satisfied"
    assert result.values["declared_joint_efficiency_factor"] is None


def test_missing_authorization_and_identity_exit_are_separate():
    assert (
        joint_efficiency_declaration(
            payload(candidate_rules=(rule(computational_use_authorized=False),))
        ).status
        == "needs_data"
    )
    result = joint_efficiency_declaration(payload(welding_process_id="other-process"))
    assert result.status == "out_of_scope"
    assert result.values["outside_support_reasons"] == ["rule_identity"]


def test_record_linkage_and_context_identity_are_strict():
    base = payload()
    with pytest.raises(ValueError, match="assessed joint"):
        JointEfficiencyDeclaration(
            **base.model_dump(exclude={"examination_record"}),
            examination_record=base.examination_record.model_copy(update={"joint_id": "other"}),
        )
    registry = ModelRegistry()
    registry.register(specifications()[0])
    with pytest.raises(ValueError, match="must match"):
        registry.run(
            "fabrication.joint_efficiency_declaration",
            base,
            RunContext(asset_id="other", location_id="joint-location-1", time_basis="authored"),
        )
