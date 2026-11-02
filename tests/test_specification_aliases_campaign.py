from matintegrity.models.specification_aliases_campaign import (
    SpecificationAliasProfileSetAudit,
    SpecificationAliasQuery,
    SpecificationProfileMaterialBinding,
    specification_alias_profile_set_audit,
    specifications,
)
from matintegrity.specification_aliases import (
    SpecificationAlias,
    SpecificationDesignation,
    SpecificationProfile,
)

E = {"source_id": "caller", "origin": "user_declared", "citation": "caller alias mapping"}
D = "7" * 64


def designation(value):
    return SpecificationDesignation(
        namespace="caller-namespace",
        designation=value,
        edition="2026",
        product_form="plate",
        condition="normalized",
    )


def profile(pid="profile-a", alias="LOCAL-A", canonical="CANONICAL-A"):
    return SpecificationProfile(
        profile_id=pid,
        canonical_designation=designation(canonical),
        aliases=(
            SpecificationAlias(
                alias_id=f"alias-{pid}",
                designation=designation(alias),
                mapping_basis="caller-reviewed exact mapping",
                evidence=(E,),
            ),
        ),
        profile_revision="1",
        profile_authority_id="caller-authority",
        profile_source_digest=D,
        evidence=(E,),
    )


def query(qid, value):
    return SpecificationAliasQuery(
        query_id=qid,
        designation=designation(value),
        query_source_id="caller-query-source",
        query_record_digest=D,
        evidence=(E,),
    )


def binding(pid="profile-a", family="caller-family", condition="normalized"):
    return SpecificationProfileMaterialBinding(
        profile_id=pid,
        material_family_id=family,
        material_condition_id=condition,
        binding_source_id="caller-material-register",
        binding_record_digest=D,
        evidence=(E,),
    )


def audit(profiles=None, queries=None, **updates):
    selected_profiles = profiles or (profile(),)
    value = {
        "audit_id": "audit-1",
        "profile_set_id": "profile-set-1",
        "profile_set_revision": "1",
        "profiles": selected_profiles,
        "material_bindings": tuple(binding(row.profile_id) for row in selected_profiles),
        "queries": queries or (query("q1", "CANONICAL-A"), query("q2", "LOCAL-A")),
        "exact_namespace_designation_edition_form_and_condition_reviewed": True,
        "profile_authorities_sources_evidence_and_digests_reviewed": True,
        "duplicate_ambiguity_and_unregistered_policy_reviewed": True,
        "query_sources_and_record_digests_reviewed": True,
        "evidence": (E,),
    }
    value.update(updates)
    return SpecificationAliasProfileSetAudit(**value)


def test_profile_set_exact_resolution_coverage_and_provenance():
    result = specification_alias_profile_set_audit(audit())
    assert result.values["audit_outcome"] == "exactly_resolved"
    assert result.values["resolution_counts"] == {
        "exact": 1,
        "resolved_alias": 1,
        "unknown": 0,
        "ambiguous": 0,
    }
    assert result.values["resolved_query_fraction"] == 1.0
    assert result.values["query_resolution_rows"][1]["query_record_digest"] == D
    assert result.values["query_resolution_rows"][1]["material_family_id"] == "caller-family"
    assert (
        result.values["query_resolution_rows"][1]["material_binding_source_id"] == "caller-material-register"
    )
    assert result.values["fuzzy_matching_performed"] is False
    assert result.values["standard_equivalence_claim"] is False


def test_unknown_and_cross_profile_ambiguity_are_explicit():
    unknown = specification_alias_profile_set_audit(audit(queries=(query("q1", "local-a"),)))
    ambiguous = specification_alias_profile_set_audit(
        audit(
            profiles=(profile(), profile("profile-b", alias="LOCAL-A", canonical="CANONICAL-B")),
            queries=(query("q1", "LOCAL-A"),),
        )
    )
    assert unknown.values["audit_outcome"] == "incomplete_coverage"
    assert unknown.values["query_resolution_rows"][0]["resolution_status"] == "unknown"
    assert ambiguous.values["audit_outcome"] == "ambiguous"
    assert ambiguous.values["query_resolution_rows"][0]["candidate_profile_ids"] == [
        "profile-a",
        "profile-b",
    ]
    assert ambiguous.values["ambiguous_profile_identities"]


def test_missing_review_needs_data_and_local_specification_has_source_id():
    result = specification_alias_profile_set_audit(audit(query_sources_and_record_digests_reviewed=False))
    assert result.status == "needs_data"
    spec = specifications()[0]
    assert spec.model_id == "materials.specification_aliases"
    assert spec.input_type is SpecificationAliasProfileSetAudit
    assert spec.source_ids == ("authored_exact_specification_alias_profile_set_audit",)


def test_material_binding_must_cover_each_profile_exactly_once():
    try:
        audit(material_bindings=(binding("not-a-profile"),))
    except ValueError as exc:
        assert "exactly one material binding" in str(exc)
    else:
        raise AssertionError("mismatched profile binding should be rejected")
