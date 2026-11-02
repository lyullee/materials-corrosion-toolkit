import pytest

from matintegrity.contracts import RunContext, canonical_digest
from matintegrity.models.service_category_screening import (
    ServiceCategoryCondition,
    ServiceCategoryFact,
    ServiceCategoryProfile,
    ServiceCategoryRule,
    ServiceCategoryScreening,
    service_category_screening,
)
from matintegrity.registry import default_registry


def fact(name="pressure", status="known", value=10, unit="authored_pressure_unit"):
    numeric = name == "pressure"
    return ServiceCategoryFact(
        fact_id=name,
        domain="pressure" if numeric else "owner_decision",
        definition="Authored fact",
        value_kind="number" if numeric else "boolean",
        status=status,
        numeric_value=value if numeric and status == "known" else None,
        unit_token=unit if numeric and status == "known" else None,
        boolean_value=True if not numeric and status == "known" else None,
        unknown_or_invalid_basis=None if status == "known" else "not established",
        evidence_record_id=name,
        source_group_id="authored",
        record_digest="a" * 64,
        evidence=(dict(source_id="authored", origin="synthetic", citation="Authored fact"),),
    )


def profile(**updates):
    raw = dict(
        profile_id="profile",
        category_id="authored-category",
        code_namespace="authored-code",
        code_edition="authored-edition",
        equipment_boundary_id="boundary",
        authority_id="authored-authority",
        revision="1",
        required_fact_ids=("pressure", "owner"),
        authority_scope_and_rule_completeness_reviewed=True,
        rules=(
            ServiceCategoryRule(
                rule_id="rule",
                rule_definition="Authored conjunction",
                conditions=(
                    ServiceCategoryCondition(
                        condition_id="pressure",
                        fact_id="pressure",
                        expected_fact_kind="number",
                        operator="less_than_or_equal",
                        unit_token="authored_pressure_unit",
                        threshold=20,
                        condition_basis="authored",
                    ),
                    ServiceCategoryCondition(
                        condition_id="owner",
                        fact_id="owner",
                        expected_fact_kind="boolean",
                        operator="is_true",
                        condition_basis="authored",
                    ),
                ),
                evidence=(dict(source_id="authored", origin="synthetic", citation="Authored rule"),),
            ),
        ),
    )
    raw.update(updates)
    digest = canonical_digest(
        ServiceCategoryProfile.model_construct(**raw).model_dump(
            mode="json", exclude={"profile_sha256", "evidence"}
        )
    )
    return ServiceCategoryProfile(
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
    raw = dict(
        assessment_id="assessment",
        asset_id="asset",
        location_id="location",
        physical_scope_id="scope",
        equipment_boundary_id="boundary",
        facts=(fact(), fact("owner")),
        profiles=(profile(),),
        facts_units_scope_and_lineage_reviewed=True,
        owner_authority_and_profile_selection_reviewed=True,
    )
    raw.update(updates)
    digest = canonical_digest(
        ServiceCategoryScreening.model_construct(**raw).model_dump(mode="json", exclude={"basis"})
    )
    return ServiceCategoryScreening(
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
                    citation="Authored assessment",
                    license_id="authored-test",
                    sha256=digest,
                ),
            ),
        ),
    )


@pytest.mark.parametrize("pressure,outcome", [(10, "matched"), (30, "not_matched")])
def test_known_caller_criteria(pressure, outcome):
    result = service_category_screening(request(facts=(fact(value=pressure), fact("owner"))))
    assert result.status == "computed"
    assert result.values["category_findings"][0]["outcome"] == outcome
    assert result.values["classification_decision"] == "not_made"


@pytest.mark.parametrize("status", ["unknown", "invalid"])
def test_unresolved_owner_cannot_be_hidden_by_false_pressure(status):
    result = service_category_screening(request(facts=(fact(value=30), fact("owner", status=status))))
    assert result.status == "needs_data"
    assert result.values["matched_profile_ids"] == []
    assert result.values["category_findings"][0]["outcome"] == "indeterminate"


def test_missing_fact_does_not_assign_default_category():
    result = service_category_screening(request(facts=(fact(),)))
    assert result.status == "needs_data"
    assert result.values["category_findings"][0]["missing_required_fact_ids"] == ["owner"]


def test_unit_mismatch_stays_unknown_without_conversion():
    result = service_category_screening(request(facts=(fact(unit="other_unit"), fact("owner"))))
    assert result.status == "needs_data"


def test_unreviewed_authority_is_indeterminate():
    assert (
        service_category_screening(
            request(profiles=(profile(authority_scope_and_rule_completeness_reviewed=False),))
        ).status
        == "needs_data"
    )


def test_multiple_matches_preserve_categories_without_priority():
    result = service_category_screening(
        request(profiles=(profile(), profile(profile_id="second", category_id="another-category")))
    )
    assert result.values["matched_profile_ids"] == ["profile", "second"]
    assert result.values["classification_decision"] == "not_made"


def test_profile_tampering_invalidates_authority_digest():
    raw = profile().model_dump()
    raw["code_edition"] = "altered"
    with pytest.raises(ValueError, match="pin its exact"):
        ServiceCategoryProfile(**raw)


@pytest.mark.parametrize(
    "name,key,value", [("pressure", "numeric_value", True), ("owner", "boolean_value", "false")]
)
def test_fact_types_are_not_coerced_between_booleans_and_numbers(name, key, value):
    raw = fact(name).model_dump()
    raw[key] = value
    with pytest.raises(ValueError):
        ServiceCategoryFact(**raw)


def test_condition_threshold_cannot_be_boolean():
    raw = profile().rules[0].conditions[0].model_dump()
    raw["threshold"] = True
    with pytest.raises(ValueError):
        ServiceCategoryCondition(**raw)


@pytest.mark.parametrize(
    "updates", [dict(equipment_boundary_id="other"), dict(maximum_condition_evaluations=1)]
)
def test_equipment_scope_and_work_budget(updates):
    with pytest.raises(ValueError):
        request(**updates)


def test_default_registry_exchange_and_asset_binding():
    registry = default_registry()
    x = request()
    model = "workflow.service_category_screening"
    context = RunContext(asset_id="asset", location_id="location", time_basis="synthetic")
    assert (
        registry.run(model, x, context).model_dump()
        == registry.run_json(model, x.model_dump_json(), context).model_dump()
    )
    with pytest.raises(ValueError, match="asset and location"):
        registry.run(model, x, context.model_copy(update={"asset_id": "other"}))
