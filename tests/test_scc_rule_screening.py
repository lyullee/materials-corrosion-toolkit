import pytest

from matintegrity.contracts import RunContext
from matintegrity.models.scc_rule_screening import (
    UserDefinedSCCScreening,
    specifications,
    user_defined_scc_screening,
)

EVIDENCE = {"source_id": "authored", "origin": "synthetic", "citation": "authored SCC screening test"}
DIGEST_A = "a" * 64
DIGEST_B = "b" * 64
DIGEST_C = "c" * 64
DIGEST_D = "d" * 64


def numeric_fact(value=350.0, unit="K", status="known", **updates):
    row = {
        "fact_id": "environment.temperature",
        "domain": "environment",
        "definition": "caller-reviewed exposure temperature",
        "value_kind": "number",
        "status": status,
        "numeric_value": value if status == "known" else None,
        "unit_token": unit if status == "known" else None,
        "descriptor_value": None,
        "boolean_value": None,
        "unknown_or_invalid_basis": None if status == "known" else "temperature record unavailable",
        "evidence_record_id": "environment-record-1",
        "source_group_id": "environment-source-1",
        "record_digest": DIGEST_A,
        "evidence": (EVIDENCE,),
    }
    row.update(updates)
    return row


def material_fact(value="caller-susceptible-condition", status="known", **updates):
    row = {
        "fact_id": "material.condition",
        "domain": "material",
        "definition": "caller-defined material screening descriptor",
        "value_kind": "descriptor",
        "status": status,
        "numeric_value": None,
        "unit_token": None,
        "descriptor_value": value if status == "known" else None,
        "boolean_value": None,
        "unknown_or_invalid_basis": None if status == "known" else "material record unavailable",
        "evidence_record_id": "material-record-1",
        "source_group_id": "material-source-1",
        "record_digest": DIGEST_B,
        "evidence": (EVIDENCE,),
    }
    row.update(updates)
    return row


def stress_fact(value=True, status="known", **updates):
    row = {
        "fact_id": "stress.tensile_present",
        "domain": "stress",
        "definition": "caller-reviewed tensile-stress presence",
        "value_kind": "boolean",
        "status": status,
        "numeric_value": None,
        "unit_token": None,
        "descriptor_value": None,
        "boolean_value": value if status == "known" else None,
        "unknown_or_invalid_basis": None if status == "known" else "stress evidence invalid",
        "evidence_record_id": "stress-record-1",
        "source_group_id": "stress-source-1",
        "record_digest": DIGEST_C,
        "evidence": (EVIDENCE,),
    }
    row.update(updates)
    return row


def profile(mechanism="chloride_scc", unknown_policy="indeterminate"):
    return {
        "profile_id": f"{mechanism}-profile-1",
        "profile_version": "1.0.0",
        "mechanism": mechanism,
        "mechanism_definition": "caller-authored conjunction of reviewed screening facts",
        "unknown_policy": unknown_policy,
        "rules": (
            {
                "rule_id": "caller-rule-1",
                "rule_definition": "all three caller-defined conditions are present",
                "conditions": (
                    {
                        "condition_id": "temperature-condition",
                        "fact_id": "environment.temperature",
                        "expected_fact_kind": "number",
                        "operator": "greater_than_or_equal",
                        "unit_token": "K",
                        "threshold": 300.0,
                        "condition_basis": "caller-selected research screening threshold",
                    },
                    {
                        "condition_id": "material-condition",
                        "fact_id": "material.condition",
                        "expected_fact_kind": "descriptor",
                        "operator": "equals",
                        "expected_descriptors": ("caller-susceptible-condition",),
                        "condition_basis": "caller material grouping",
                    },
                    {
                        "condition_id": "stress-condition",
                        "fact_id": "stress.tensile_present",
                        "expected_fact_kind": "boolean",
                        "operator": "is_true",
                        "condition_basis": "caller stress evidence interpretation",
                    },
                ),
                "evidence": (EVIDENCE,),
            },
        ),
        "profile_provider_id": "caller-profile-provider",
        "profile_revision": "rev-1",
        "profile_configuration_digest": DIGEST_C,
        "profile_source_digest": DIGEST_D,
        "screening_only": True,
        "qualification_claimed": False,
        "evidence": (EVIDENCE,),
    }


def payload(mechanism="chloride_scc", facts=None, unknown_policy="indeterminate", **updates):
    row = {
        "assessment_id": f"{mechanism}-screen-1",
        "asset_id": "asset-1",
        "location_id": "location-1",
        "physical_scope_id": "scope-1",
        "material_condition_id": "material-condition-1",
        "mechanism": mechanism,
        "facts": facts or (numeric_fact(), material_fact(), stress_fact()),
        "mechanism_profile": profile(mechanism, unknown_policy),
        "environment_evidence_reviewed": True,
        "material_evidence_reviewed": True,
        "stress_evidence_reviewed": True,
        "fact_definitions_units_and_digests_reviewed": True,
        "mechanism_profile_rules_and_unknown_policy_reviewed": True,
        "screening_and_qualification_boundary_reviewed": True,
        "evidence": (EVIDENCE,),
    }
    row.update(updates)
    return UserDefinedSCCScreening.model_validate(row)


def test_caller_rules_can_screen_in_each_supported_mechanism_without_qualification():
    for mechanism in ("chloride_scc", "ammonia_scc", "alkaline_scc"):
        result = user_defined_scc_screening(payload(mechanism))
        assert result.status == "computed"
        assert result.values["screening_outcome"] == "potentially_applicable"
        assert result.values["rule_findings"][0]["rule_outcome"] == "met"
        assert result.values["screening_only"] is True
        assert result.values["qualification_outcome"] == "not_evaluated"


def test_all_false_rules_produce_not_indicated_screening_only():
    facts = (numeric_fact(value=290.0), material_fact(), stress_fact())
    result = user_defined_scc_screening(payload("ammonia_scc", facts=facts))
    assert result.status == "computed"
    assert result.values["screening_outcome"] == "not_indicated"
    finding = result.values["rule_findings"][0]["condition_findings"][0]
    assert finding["outcome"] == "false"
    assert finding["observed"] == {"value": 290.0, "unit": "K"}


def test_unknown_policy_never_screens_out_unknown_evidence():
    facts = (numeric_fact(status="unknown"), material_fact(), stress_fact())
    indeterminate = user_defined_scc_screening(
        payload("alkaline_scc", facts=facts, unknown_policy="indeterminate")
    )
    assert indeterminate.status == "needs_data"
    assert indeterminate.values["screening_outcome"] == "indeterminate"
    conservative = user_defined_scc_screening(
        payload("alkaline_scc", facts=facts, unknown_policy="screen_in")
    )
    assert conservative.status == "computed"
    assert conservative.values["screening_outcome"] == "potentially_applicable"


def test_unit_mismatch_is_explainable_unknown_and_invalid_evidence_needs_data():
    unit_mismatch = user_defined_scc_screening(
        payload(facts=(numeric_fact(unit="degC"), material_fact(), stress_fact()))
    )
    assert unit_mismatch.status == "needs_data"
    finding = unit_mismatch.values["rule_findings"][0]["condition_findings"][0]
    assert finding["outcome"] == "unknown"
    assert "no conversion" in finding["basis"]

    invalid = user_defined_scc_screening(
        payload(facts=(numeric_fact(), material_fact(), stress_fact(status="invalid")))
    )
    assert invalid.status == "needs_data"
    assert invalid.values["invalid_fact_ids"] == ["stress.tensile_present"]


def test_digests_are_deterministic_and_three_local_specs_enforce_identity():
    assessment = payload()
    first = user_defined_scc_screening(assessment)
    second = user_defined_scc_screening(assessment)
    assert first.values["input_digest"] == second.values["input_digest"]
    assert first.values["result_digest"] == second.values["result_digest"]
    specs = specifications()
    assert [row.model_id for row in specs] == [
        "degradation.chloride_scc_user_screening",
        "degradation.ammonia_scc_user_screening",
        "degradation.alkaline_scc_user_screening",
    ]
    assert all(row.source_ids == ("authored_caller_defined_scc_rule_screening",) for row in specs)
    context = RunContext(asset_id="asset-1", location_id="location-1", time_basis="screening snapshot")
    specs[0].context_validator(assessment, context)
    with pytest.raises(ValueError, match="matching mechanism profile"):
        specs[1].context_validator(assessment, context)
