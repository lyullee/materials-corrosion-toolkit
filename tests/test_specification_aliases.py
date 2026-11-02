import pytest

from matintegrity.specification_aliases import (
    SpecificationAlias,
    SpecificationDesignation,
    SpecificationProfile,
    resolve_specification_alias,
)

E = {"source_id": "caller", "origin": "user_declared", "citation": "caller alias record"}
D = "a" * 64


def designation(name="GRADE-A"):
    return SpecificationDesignation(
        namespace="caller-system",
        designation=name,
        edition="2026",
        product_form="plate",
        condition="normalized",
    )


def profile(profile_id="profile-a", alias_name="A-LOCAL"):
    return SpecificationProfile(
        profile_id=profile_id,
        canonical_designation=designation(),
        aliases=(
            SpecificationAlias(
                alias_id=f"alias-{profile_id}",
                designation=designation(alias_name),
                mapping_basis="caller-reviewed exact mapping",
                evidence=(E,),
            ),
        ),
        profile_revision="1",
        profile_authority_id="caller-authority",
        profile_source_digest=D,
        evidence=(E,),
    )


def test_exact_and_alias_resolution_are_deterministic():
    item = profile()
    exact = resolve_specification_alias(designation(), (item,))
    alias = resolve_specification_alias(designation("A-LOCAL"), (item,))
    assert exact.status == "exact"
    assert alias.status == "resolved_alias"
    assert alias.profile_digest == item.deterministic_digest
    assert alias == resolve_specification_alias(designation("A-LOCAL"), (item,))


def test_unknown_and_ambiguous_evidence_are_explicit():
    unknown = resolve_specification_alias(designation("NO-MATCH"), (profile(),))
    assert (unknown.status, unknown.evidence_state) == ("unknown", "unknown")
    second = profile("profile-b", "A-LOCAL")
    ambiguous = resolve_specification_alias(designation("A-LOCAL"), (profile(), second))
    assert ambiguous.status == "ambiguous"
    assert ambiguous.candidate_profile_ids == ("profile-a", "profile-b")


def test_duplicate_alias_and_profile_ids_are_rejected():
    duplicate = SpecificationAlias(
        alias_id="two",
        designation=designation("A-LOCAL"),
        mapping_basis="duplicate identity",
        evidence=(E,),
    )
    with pytest.raises(ValueError, match="must be unique"):
        profile().model_copy(update={"aliases": profile().aliases + (duplicate,)}).model_validate(
            profile().model_copy(update={"aliases": profile().aliases + (duplicate,)}).model_dump()
        )
    with pytest.raises(ValueError, match="profile identifiers"):
        resolve_specification_alias(designation(), (profile(), profile()))
