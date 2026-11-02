import pytest

from matintegrity.contracts import RunContext, canonical_digest
from matintegrity.models.damage_mechanism_screening import (
    DamageMechanismFact,
    DamageMechanismProfile,
    DamageMechanismScreening,
    damage_mechanism_screening,
)
from matintegrity.models.scc_rule_screening import SCCRuleCondition, SCCScreeningRule
from matintegrity.registry import default_registry


def fact(name="flow", status="known", value=2.0, unit="m/s"):
    return DamageMechanismFact(
        fact_id=name,
        domain="flow" if name == "flow" else "material",
        definition="Authored fact",
        value_kind="number" if name == "flow" else "descriptor",
        status=status,
        numeric_value=value if name == "flow" and status == "known" else None,
        unit_token=unit if name == "flow" and status == "known" else None,
        descriptor_value="authored-condition" if name != "flow" and status == "known" else None,
        unknown_or_invalid_basis=None if status == "known" else "not established",
        evidence_record_id=name,
        source_group_id="authored",
        record_digest="a" * 64,
        evidence=(dict(source_id="authored", origin="synthetic", citation="Authored fact"),),
    )


def profile(**updates):
    rule = SCCScreeningRule(
        rule_id="r",
        rule_definition="Authored conjunctive criterion",
        conditions=(
            SCCRuleCondition(
                condition_id="speed",
                fact_id="flow",
                expected_fact_kind="number",
                operator="greater_than_or_equal",
                unit_token="m/s",
                threshold=1.0,
                condition_basis="authored",
            ),
            SCCRuleCondition(
                condition_id="condition",
                fact_id="material",
                expected_fact_kind="descriptor",
                operator="equals",
                expected_descriptors=("authored-condition",),
                condition_basis="authored",
            ),
        ),
        evidence=(dict(source_id="authored", origin="synthetic", citation="Authored rule"),),
    )
    raw = (
        dict(
            profile_id="profile",
            mechanism_id="caller-mechanism",
            mechanism_definition="Authored screening target",
            provider_id="authored",
            revision="1",
            required_fact_ids=("flow", "material"),
            rules=(rule,),
            unknown_policy="indeterminate",
            authority_and_rule_completeness_reviewed=True,
        )
        | updates
    )
    digest = canonical_digest(
        DamageMechanismProfile.model_construct(**raw).model_dump(
            mode="json", exclude={"profile_sha256", "evidence"}
        )
    )
    return DamageMechanismProfile(
        **raw,
        profile_sha256=digest,
        evidence=(
            dict(
                source_id="authored",
                origin="synthetic",
                citation="Authored profile",
                license_id="authored-test",
                sha256=digest,
            ),
        ),
    )


def request(**updates):
    raw = (
        dict(
            assessment_id="assessment",
            asset_id="asset",
            location_id="location",
            physical_scope_id="scope",
            material_condition_id="condition",
            facts=(fact(), fact("material")),
            profiles=(profile(),),
            facts_units_lineage_and_physical_scope_reviewed=True,
            screening_boundary_and_profile_selection_reviewed=True,
        )
        | updates
    )
    digest = canonical_digest(
        DamageMechanismScreening.model_construct(**raw).model_dump(mode="json", exclude={"basis"})
    )
    return DamageMechanismScreening(
        **raw,
        basis=dict(
            source_id="authored",
            revision="1",
            license_id="authored-test",
            record_sha256=digest,
            applicability_and_units_reviewed=True,
            computational_use_authorized=True,
            evidence=(
                dict(
                    source_id="authored",
                    origin="synthetic",
                    citation="Authored request",
                    license_id="authored-test",
                    sha256=digest,
                ),
            ),
        ),
    )


@pytest.mark.parametrize("speed,outcome", [(2.0, "potentially_applicable"), (0.0, "not_indicated")])
def test_known_rules_only_screen_caller_selected_mechanism(speed, outcome):
    result = damage_mechanism_screening(request(facts=(fact(value=speed), fact("material"))))
    assert result.status == "computed"
    assert result.values["mechanism_findings"][0]["screening_outcome"] == outcome
    assert result.values["qualification_outcome"] == "not_evaluated"


@pytest.mark.parametrize(
    "policy,outcome", [("indeterminate", "indeterminate"), ("screen_in", "potentially_applicable")]
)
def test_unknown_cannot_be_hidden_by_other_false_condition(policy, outcome):
    result = damage_mechanism_screening(
        request(
            facts=(fact(value=0.0), fact("material", status="unknown")),
            profiles=(profile(unknown_policy=policy),),
        )
    )
    assert result.status == "needs_data"
    row = result.values["mechanism_findings"][0]
    assert row["screening_outcome"] == outcome
    assert row["rule_findings"][0]["rule_outcome"] == "unknown"
    unknown = row["rule_findings"][0]["condition_findings"][1]
    assert unknown["record_digest"] == "a" * 64


@pytest.mark.parametrize(
    "facts",
    [(fact(),), (), (fact(unit="mm/s"), fact("material")), (fact(), fact("material", status="invalid"))],
)
def test_missing_invalid_and_unit_mismatch_remain_indeterminate(facts):
    result = damage_mechanism_screening(request(facts=facts))
    assert result.status == "needs_data"
    assert result.values["mechanism_findings"][0]["screening_outcome"] == "indeterminate"


def test_multiple_profiles_retain_separate_outcomes():
    second = profile(
        profile_id="second", mechanism_id="other", required_fact_ids=("flow", "material", "missing")
    )
    result = damage_mechanism_screening(request(profiles=(profile(), second)))
    assert result.status == "needs_data"
    assert [r["status"] for r in result.values["mechanism_findings"]] == ["computed", "needs_data"]


def test_authority_and_scope_reviews_cannot_be_bypassed_by_screen_in():
    result = damage_mechanism_screening(
        request(
            profiles=(profile(unknown_policy="screen_in", authority_and_rule_completeness_reviewed=False),)
        )
    )
    assert result.values["mechanism_findings"][0]["screening_outcome"] == "indeterminate"
    assert (
        damage_mechanism_screening(request(facts_units_lineage_and_physical_scope_reviewed=False)).status
        == "needs_data"
    )


def test_budget_duplicate_and_profile_digest_validation():
    with pytest.raises(ValueError, match="budget"):
        request(maximum_condition_evaluations=1)
    with pytest.raises(ValueError, match="unique"):
        request(facts=(fact(), fact()))
    raw = profile().model_dump()
    raw["unknown_policy"] = "screen_in"
    with pytest.raises(ValueError, match="pin"):
        DamageMechanismProfile(**raw)


def test_registry_exchange_and_context():
    x = request()
    registry = default_registry()
    model = "degradation.damage_mechanism_screening"
    context = RunContext(asset_id="asset", location_id="location", time_basis="synthetic")
    assert (
        registry.run(model, x.model_dump(), context).values
        == registry.run_json(model, x.model_dump_json(), context).values
    )
    with pytest.raises(ValueError, match="context"):
        registry.run(model, x.model_dump(), context.model_copy(update={"asset_id": "other"}))
